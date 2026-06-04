"""
db.py — schema e accesso al database.

Tabelle:
  assets      -> i token in osservazione (UNIQUE su chain+contract -> NIENTE DUPLICATI)
  signals     -> storico di ogni segnale misurato (una riga per misura)
  baselines   -> media mobile per asset (lo spike è SEMPRE relativo alla storia del token)
  scores      -> voto corrente + prezzo al momento del voto (serve per verificare l'edge)
  exclusions  -> LISTA NERA PERMANENTE: una volta dentro, il token non rientra MAI più

Per passare a Postgres: cambi solo get_conn() e i "?" in "%s". Lo schema è quasi identico.
"""
import sqlite3
import time
from contextlib import contextmanager
from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS assets (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    chain             TEXT NOT NULL,
    contract_address  TEXT NOT NULL,
    ticker            TEXT,
    name              TEXT,
    pair_address      TEXT,
    discovery_source  TEXT,
    discovered_at     REAL NOT NULL,
    last_enriched_at  REAL,
    status            TEXT NOT NULL DEFAULT 'active',  -- active | archived | excluded
    UNIQUE (chain, contract_address)                   -- <<< DEDUP A LIVELLO DB
);

CREATE TABLE IF NOT EXISTS signals (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id    INTEGER NOT NULL,
    stage       TEXT NOT NULL,        -- 'discovery' | 'enrichment'
    signal_type TEXT NOT NULL,
    value       REAL,
    weight      REAL,
    detected_at REAL NOT NULL,
    FOREIGN KEY (asset_id) REFERENCES assets(id)
);

CREATE TABLE IF NOT EXISTS baselines (
    asset_id        INTEGER PRIMARY KEY,
    avg_liquidity   REAL,
    avg_volume      REAL,
    avg_holders     REAL,
    samples         INTEGER DEFAULT 0,
    updated_at      REAL,
    FOREIGN KEY (asset_id) REFERENCES assets(id)
);

CREATE TABLE IF NOT EXISTS scores (
    asset_id        INTEGER PRIMARY KEY,
    current_score   REAL NOT NULL,
    breakdown       TEXT,             -- JSON: da dove viene il punteggio (trasparenza)
    price_at_score  REAL,            -- prezzo quando lo score è stato calcolato
    updated_at      REAL NOT NULL,
    FOREIGN KEY (asset_id) REFERENCES assets(id)
);

-- LISTA NERA PERMANENTE. Il discovery la consulta SEMPRE: un token qui dentro
-- non viene mai reinserito, così non si spreca enrichment a riscoprire spazzatura.
CREATE TABLE IF NOT EXISTS exclusions (
    chain            TEXT NOT NULL,
    contract_address TEXT NOT NULL,
    reason           TEXT NOT NULL,
    permanent        INTEGER NOT NULL DEFAULT 1,  -- 1 = per sempre, 0 = a tempo
    excluded_at      REAL NOT NULL,
    expires_at       REAL,                        -- usato solo se permanent=0
    PRIMARY KEY (chain, contract_address)
);

-- OUTCOMES: la METRICA DI VERITA'. Per ogni "entrata ipotetica" (quando uno score
-- supera la soglia di tracking) registriamo prezzo+liquidita' di partenza, poi misuriamo
-- il prezzo a 24h/72h/168h e il rendimento NETTO di slippage+fee simulati. Serve a dire,
-- coi dati, se gli score alti corrispondono davvero a movimenti (o se l'edge non c'e').
CREATE TABLE IF NOT EXISTS outcomes (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id            INTEGER NOT NULL,
    chain               TEXT,
    contract_address    TEXT,
    ticker              TEXT,
    score_at_entry      REAL,
    signals_at_entry    TEXT,   -- JSON: QUALI segnali erano accesi (materiale per imparare)
    price_at_entry      REAL,
    liquidity_at_entry  REAL,
    entered_at          REAL NOT NULL,
    price_24h  REAL, ret_24h_gross  REAL, ret_24h_net  REAL,
    price_72h  REAL, ret_72h_gross  REAL, ret_72h_net  REAL,
    price_168h REAL, ret_168h_gross REAL, ret_168h_net REAL,
    status              TEXT NOT NULL DEFAULT 'open',   -- open | closed
    closed_at           REAL,
    FOREIGN KEY (asset_id) REFERENCES assets(id)
);

-- LEARNED_WEIGHTS: il sistema che IMPARA. Per ogni segnale tiene un moltiplicatore
-- appreso dagli esiti reali (1.0 = neutro, >1 = ha funzionato, <1 = ha deluso/portato a zero).
-- Lo scoring lo applica. Si muove a piccoli passi e SOLO con abbastanza dati (no overfitting).
CREATE TABLE IF NOT EXISTS learned_weights (
    signal      TEXT PRIMARY KEY,
    multiplier  REAL NOT NULL DEFAULT 1.0,
    n           INTEGER DEFAULT 0,
    avg_net     REAL,
    updated_at  REAL
);

-- WALLETS + WALLET_BUYS: la smart-money scoperta DAL BASSO. Quando il radar entra su un
-- token, fotografiamo chi lo compra (wallet_buys). I wallet che RICORRONO sui token che poi
-- performano prendono smart_score alto: sono quelli da seguire (i loro buy = entrata, sell = uscita).
CREATE TABLE IF NOT EXISTS wallets (
    address      TEXT PRIMARY KEY,
    first_seen   REAL,
    buys_count   INTEGER DEFAULT 0,    -- su quanti token distinti l'abbiamo visto comprare presto
    smart_score  REAL DEFAULT 0,       -- appreso dagli esiti dei suoi token (ricorrenza x performance)
    avg_net      REAL,
    updated_at   REAL
);

CREATE TABLE IF NOT EXISTS wallet_buys (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    address     TEXT NOT NULL,
    asset_id    INTEGER,
    mint        TEXT,
    ticker      TEXT,
    bought_at   REAL,
    captured_at REAL NOT NULL,
    UNIQUE (address, mint)              -- un wallet conta una volta per token
);

-- NOTIFIED: per non rimandare la stessa notifica Telegram dello stesso pick.
CREATE TABLE IF NOT EXISTS notified (
    contract_address TEXT PRIMARY KEY,
    ticker           TEXT,
    score            REAL,
    notified_at      REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_signals_asset ON signals(asset_id, detected_at);
CREATE INDEX IF NOT EXISTS idx_assets_status ON assets(status);
CREATE INDEX IF NOT EXISTS idx_outcomes_status ON outcomes(status);
"""


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")   # letture concorrenti (Excel mentre gira)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as c:
        c.executescript(SCHEMA)
        _migrate(c)


def _migrate(c):
    """Aggiunte di colonne idempotenti: CREATE TABLE IF NOT EXISTS non altera tabelle già esistenti.
    Serve per i DB creati prima di aggiungere una colonna (es. il radar.db già nel cloud)."""
    cols = [r[1] for r in c.execute("PRAGMA table_info(outcomes)").fetchall()]
    if "signals_at_entry" not in cols:
        c.execute("ALTER TABLE outcomes ADD COLUMN signals_at_entry TEXT")
    # qualifica PnL dei wallet (accumulata e cachata, non si ricalcola ogni giro)
    wc = [r[1] for r in c.execute("PRAGMA table_info(wallets)").fetchall()]
    for col, ddl in [("pnl_sol", "REAL"), ("win_rate", "REAL"),
                     ("closed_count", "INTEGER"), ("qualified_at", "REAL"),
                     ("verified", "INTEGER DEFAULT 0"), ("is_bot", "INTEGER DEFAULT 0"),
                     ("tx_per_day", "REAL"), ("top_wins", "TEXT"),
                     ("deep_at", "REAL"), ("snowballed", "INTEGER DEFAULT 0"),
                     ("tokens_count", "INTEGER"), ("open_count", "INTEGER")]:
        if wc and col not in wc:
            c.execute(f"ALTER TABLE wallets ADD COLUMN {col} {ddl}")


# --- ESCLUSIONI -----------------------------------------------------------

def is_excluded(c, chain, contract):
    row = c.execute(
        "SELECT permanent, expires_at FROM exclusions WHERE chain=? AND contract_address=?",
        (chain, contract),
    ).fetchone()
    if not row:
        return False
    if row["permanent"] == 1:
        return True
    # esclusione a tempo: ancora valida?
    return row["expires_at"] is not None and row["expires_at"] > time.time()


def exclude(c, chain, contract, reason, permanent=True, ttl_hours=None):
    expires = None if permanent else time.time() + (ttl_hours or 24) * 3600
    c.execute(
        """INSERT INTO exclusions (chain, contract_address, reason, permanent, excluded_at, expires_at)
           VALUES (?,?,?,?,?,?)
           ON CONFLICT(chain, contract_address) DO UPDATE SET
             reason=excluded.reason, permanent=excluded.permanent,
             excluded_at=excluded.excluded_at, expires_at=excluded.expires_at""",
        (chain, contract, reason, 1 if permanent else 0, time.time(), expires),
    )
    # se era un asset attivo, marcalo escluso
    c.execute(
        "UPDATE assets SET status='excluded' WHERE chain=? AND contract_address=?",
        (chain, contract),
    )


# --- ASSET ----------------------------------------------------------------

def upsert_asset(c, chain, contract, ticker, name, pair, source):
    """Inserisce l'asset SOLO se non esiste e non è in lista nera. Ritorna asset_id o None."""
    if is_excluded(c, chain, contract):
        return None
    existing = c.execute(
        "SELECT id FROM assets WHERE chain=? AND contract_address=?", (chain, contract)
    ).fetchone()
    if existing:
        return existing["id"]  # gia' visto, niente duplicato
    cur = c.execute(
        """INSERT INTO assets (chain, contract_address, ticker, name, pair_address,
                               discovery_source, discovered_at, status)
           VALUES (?,?,?,?,?,?,?, 'active')""",
        (chain, contract, ticker, name, pair, source, time.time()),
    )
    return cur.lastrowid


def add_signal(c, asset_id, stage, signal_type, value, weight):
    c.execute(
        """INSERT INTO signals (asset_id, stage, signal_type, value, weight, detected_at)
           VALUES (?,?,?,?,?,?)""",
        (asset_id, stage, signal_type, value, weight, time.time()),
    )


def update_baseline(c, asset_id, liquidity, volume, holders=None):
    """Media mobile incrementale: lo spike di domani sara' relativo a questa storia."""
    row = c.execute("SELECT * FROM baselines WHERE asset_id=?", (asset_id,)).fetchone()
    if row is None:
        c.execute(
            """INSERT INTO baselines (asset_id, avg_liquidity, avg_volume, avg_holders, samples, updated_at)
               VALUES (?,?,?,?,1,?)""",
            (asset_id, liquidity, volume, holders, time.time()),
        )
        return
    n = row["samples"]
    def ema(old, new, k=0.3):
        if new is None:
            return old
        if old is None:
            return new
        return old * (1 - k) + new * k
    c.execute(
        """UPDATE baselines SET avg_liquidity=?, avg_volume=?, avg_holders=?,
                                samples=?, updated_at=? WHERE asset_id=?""",
        (ema(row["avg_liquidity"], liquidity), ema(row["avg_volume"], volume),
         ema(row["avg_holders"], holders), n + 1, time.time(), asset_id),
    )


def get_baseline(c, asset_id):
    return c.execute("SELECT * FROM baselines WHERE asset_id=?", (asset_id,)).fetchone()


# --- OUTCOMES (validazione onesta) ---------------------------------------

def has_open_outcome(c, asset_id):
    """True se c'è già un'entrata aperta per questo asset (un paper-trade alla volta)."""
    row = c.execute(
        "SELECT 1 FROM outcomes WHERE asset_id=? AND status='open' LIMIT 1", (asset_id,)
    ).fetchone()
    return row is not None


def open_outcome(c, asset_id, chain, contract, ticker, score, price, liquidity, signals=None):
    """Apre un'entrata ipotetica (paper trade) da validare nel tempo.
    `signals` (JSON) registra QUALI segnali erano accesi: serve a imparare dopo."""
    c.execute(
        """INSERT INTO outcomes (asset_id, chain, contract_address, ticker,
               score_at_entry, signals_at_entry, price_at_entry, liquidity_at_entry, entered_at, status)
           VALUES (?,?,?,?,?,?,?,?,?, 'open')""",
        (asset_id, chain, contract, ticker, score, signals, price, liquidity, time.time()),
    )


# --- NOTIFICHE (anti-spam) -----------------------------------------------

def asset_has_wallet_capture(c, asset_id):
    return c.execute("SELECT 1 FROM wallet_buys WHERE asset_id=? LIMIT 1", (asset_id,)).fetchone() is not None


def record_wallet_buy(c, address, asset_id, mint, ticker, bought_at):
    """Registra che `address` ha comprato un token su cui il radar è entrato. Dedup per (wallet, mint)."""
    c.execute(
        """INSERT OR IGNORE INTO wallet_buys (address, asset_id, mint, ticker, bought_at, captured_at)
           VALUES (?,?,?,?,?,?)""",
        (address, asset_id, mint, ticker, bought_at, time.time()),
    )
    c.execute(
        """INSERT INTO wallets (address, first_seen, buys_count, updated_at)
           VALUES (?,?,1,?)
           ON CONFLICT(address) DO UPDATE SET
             buys_count = (SELECT COUNT(DISTINCT mint) FROM wallet_buys WHERE address=?),
             updated_at = excluded.updated_at""",
        (address, time.time(), time.time(), address),
    )


def set_wallet_score(c, address, smart_score, avg_net):
    c.execute("UPDATE wallets SET smart_score=?, avg_net=?, updated_at=? WHERE address=?",
              (smart_score, avg_net, time.time(), address))


def wallets_to_qualify(c, requalify_after_s, limit):
    """Wallet mai qualificati o con qualifica vecchia. Evita di sprecare crediti su quelli già fatti."""
    cutoff = time.time() - requalify_after_s
    return [r["address"] for r in c.execute(
        """SELECT address FROM wallets
           WHERE qualified_at IS NULL OR qualified_at < ?
           ORDER BY qualified_at IS NOT NULL, buys_count DESC LIMIT ?""",
        (cutoff, limit)).fetchall()]


def set_wallet_pnl(c, address, pnl_sol, win_rate, closed_count):
    c.execute(
        """UPDATE wallets SET pnl_sol=?, win_rate=?, closed_count=?, qualified_at=? WHERE address=?""",
        (pnl_sol, win_rate, closed_count, time.time(), address))


def wallets_to_deepdive(c, limit):
    """Candidati al deep-dive: passati lo screen veloce (PnL>0, posizioni chiuse), non ancora verificati."""
    return [r["address"] for r in c.execute(
        """SELECT address FROM wallets
           WHERE pnl_sol > 0 AND closed_count >= 1 AND (verified IS NULL OR verified=0)
           ORDER BY closed_count DESC LIMIT ?""", (limit,)).fetchall()]


def set_wallet_deep(c, address, pnl_sol, win_rate, closed_count, tx_per_day, is_bot,
                    top_wins, tokens_count, open_count):
    import json as _json
    c.execute(
        """UPDATE wallets SET pnl_sol=?, win_rate=?, closed_count=?, tx_per_day=?,
                  is_bot=?, verified=1, top_wins=?, tokens_count=?, open_count=?,
                  deep_at=?, qualified_at=? WHERE address=?""",
        (pnl_sol, win_rate, closed_count, tx_per_day, 1 if is_bot else 0,
         _json.dumps(top_wins), tokens_count, open_count, time.time(), time.time(), address))


def whales_to_snowball(c, limit):
    """Whale VERIFICATE (deep, profittevoli, non bot) da cui espandere la rete (non ancora fatte)."""
    return c.execute(
        """SELECT address, top_wins FROM wallets
           WHERE verified=1 AND is_bot=0 AND pnl_sol>0 AND (snowballed IS NULL OR snowballed=0)
           ORDER BY pnl_sol DESC LIMIT ?""", (limit,)).fetchall()


def mark_snowballed(c, address):
    c.execute("UPDATE wallets SET snowballed=1 WHERE address=?", (address,))


def seed_wallet(c, address):
    """Aggiunge un wallet-candidato (scoperto via snowball) da qualificare nei prossimi giri."""
    c.execute(
        """INSERT INTO wallets (address, first_seen, buys_count, updated_at)
           VALUES (?,?,0,?) ON CONFLICT(address) DO NOTHING""",
        (address, time.time(), time.time()))


def get_learned_multipliers(c):
    """Dizionario {signal: moltiplicatore} appreso dagli esiti. Default vuoto = tutto 1.0."""
    return {r["signal"]: r["multiplier"]
            for r in c.execute("SELECT signal, multiplier FROM learned_weights").fetchall()}


def set_learned_weight(c, signal, multiplier, n, avg_net):
    c.execute(
        """INSERT INTO learned_weights (signal, multiplier, n, avg_net, updated_at)
           VALUES (?,?,?,?,?)
           ON CONFLICT(signal) DO UPDATE SET
             multiplier=excluded.multiplier, n=excluded.n,
             avg_net=excluded.avg_net, updated_at=excluded.updated_at""",
        (signal, multiplier, n, avg_net, time.time()),
    )


def is_notified(c, contract):
    return c.execute("SELECT 1 FROM notified WHERE contract_address=?", (contract,)).fetchone() is not None


def mark_notified(c, contract, ticker, score):
    c.execute(
        """INSERT INTO notified (contract_address, ticker, score, notified_at) VALUES (?,?,?,?)
           ON CONFLICT(contract_address) DO UPDATE SET score=excluded.score, notified_at=excluded.notified_at""",
        (contract, ticker, score, time.time()),
    )


def get_open_outcomes(c):
    return c.execute("SELECT * FROM outcomes WHERE status='open'").fetchall()


def set_outcome_point(c, outcome_id, horizon, price, ret_gross, ret_net):
    """Scrive il punto a un orizzonte (24/72/168). Non sovrascrive se già presente."""
    col_p, col_g, col_n = f"price_{horizon}h", f"ret_{horizon}h_gross", f"ret_{horizon}h_net"
    c.execute(
        f"UPDATE outcomes SET {col_p}=?, {col_g}=?, {col_n}=? WHERE id=? AND {col_p} IS NULL",
        (price, ret_gross, ret_net, outcome_id),
    )


def close_outcome(c, outcome_id):
    c.execute("UPDATE outcomes SET status='closed', closed_at=? WHERE id=?",
              (time.time(), outcome_id))
