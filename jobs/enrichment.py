"""
jobs/enrichment.py — l'INVESTIGATORE.

Gira SOLO sui candidati attivi (mai su migliaia di token: i costi esploderebbero).
Frequenza decrescente: i nuovi spesso, i vecchi raramente, poi archivia.

Fa DUE cose nettamente separate:
  1) FILTRI DI SICUREZZA (sì/no) -> se falliscono, ESCLUSIONE PERMANENTE.
     - liquidità non bloccata (rugpull), concentrazione wallet, ecc.
  2) ANTI-DISTRIBUZIONE -> se è in corso una cascata di Sell di pochi wallet
     mentre il prezzo è in alto, è "exit liquidity in tempo reale": TIENITI FUORI.
     Questo è il filtro che ti tiene dalla parte giusta del trade.
  3) SEGNALI DI QUALITÀ (graduali) -> scritti in `signals`, li somma lo scoring.

NB: i pezzi marcati [RPC] richiedono un endpoint on-chain (free tier). Senza chiave
il job gira lo stesso e marca quei segnali "non disponibili" — non si rompe niente.
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import ENRICHMENT, LIMITS
from db import (get_conn, init_db, add_signal, update_baseline, get_baseline,
                exclude)
from net import RateLimiter, get_json

DEX_BASE = "https://api.dexscreener.com"
limiter = RateLimiter(LIMITS["dexscreener_max_calls_per_min"])


def _due_for_refresh(row, now):
    """Frequenza decrescente in base all'età della scoperta (controllo costi)."""
    age_min = (now - row["discovered_at"]) / 60.0
    last = row["last_enriched_at"] or 0
    since = (now - last) / 60.0
    if age_min < 6 * 60:
        return since >= ENRICHMENT["refresh_fresh_minutes"]
    if age_min < 48 * 60:
        return since >= ENRICHMENT["refresh_warm_minutes"]
    return since >= ENRICHMENT["refresh_cold_minutes"]


def _safety_checks(c, asset, pair):
    """KILLER ASSOLUTI. Ritorna (ok, motivo). Se non ok -> esclusione permanente."""
    chain, token = asset["chain"], asset["contract_address"]

    # Liquidità bloccata? DEXScreener a volte espone i lock; in dubbio, prudenza.
    # [RPC] Per certezza leggi il contratto del LP on-chain. Qui usiamo l'euristica.
    labels = pair.get("labels") or []
    liq = pair.get("liquidity") or {}
    locked = liq.get("locked")
    if ENRICHMENT["require_liquidity_locked"]:
        if locked is False:
            return False, "liquidità NON bloccata (rischio rugpull)"

    # Impersonazione di brand reali (pattern classico dei pump: "SpaceX", "Tesla"...).
    # Controlla NOME e TICKER: "SPCX" come ticker sfuggiva al solo check sul nome.
    bt = pair.get("baseToken") or {}
    name = (bt.get("name", "") or "")
    symbol = (bt.get("symbol", "") or "")
    text = f"{name} {symbol}".lower()
    suspicious_brands = ["spacex", "spcx", "tesla", "tsla", "apple", "nvidia", "nvda",
                         "openai", "binance official", "blackrock", "microsoft", "msft"]
    if any(b in text for b in suspicious_brands):
        return False, f"impersona un brand reale ({name}/{symbol})"

    # [RPC] Concentrazione holder: richiede chiamata on-chain. Placeholder onesto:
    # se non hai RPC, questo check è "non disponibile" e NON esclude da solo.
    top1 = asset.get("_top1_pct")     # popolato da _onchain_holders se RPC presente
    top10 = asset.get("_top10_pct")
    if top1 is not None and top1 > ENRICHMENT["max_top_holder_pct"]:
        return False, f"1 wallet detiene {top1:.0%} della supply"
    if top10 is not None and top10 > ENRICHMENT["max_top10_holder_pct"]:
        return False, f"top10 wallet detengono {top10:.0%}"

    return True, None


def _distribution_check(pair):
    """Cascata di Sell = distribuzione in corso. Ritorna True se è in distribuzione."""
    txns = pair.get("txns") or {}
    h1 = txns.get("h1") or {}
    buys, sells = h1.get("buys") or 0, h1.get("sells") or 0
    total = buys + sells
    if total < 5:
        return False  # troppo pochi dati per dire
    sell_ratio = sells / total
    return sell_ratio >= ENRICHMENT["distribution_sell_ratio"]


def _quality_signals(c, asset_id, pair):
    """Segnali graduali -> punteggio. Misura e basta, NON giudica."""
    txns = pair.get("txns") or {}
    h6 = txns.get("h6") or {}
    buys, sells = h6.get("buys") or 0, h6.get("sells") or 0

    # Buy pressure (proxy economico, finché non hai netflow on-chain)
    if buys + sells >= 10:
        bp = (buys - sells) / (buys + sells)
        if bp > 0:
            add_signal(c, asset_id, "enrichment", "buy_pressure",
                       round(bp, 3), ENRICHMENT["weight_buy_pressure"])

    # [RPC] exchange_netflow_out e holder_growth: i segnali PIÙ anticipati.
    # Richiedono on-chain. Quando metti la chiave RPC in config, popoli qui.
    # Esempio di come andrebbero scritti (lasciato pronto):
    #   netflow_out = _onchain_exchange_netflow(asset)   # >0 = accumulo
    #   if netflow_out > soglia:
    #       add_signal(c, asset_id, "enrichment", "exchange_netflow_out",
    #                  netflow_out, ENRICHMENT["weight_exchange_netflow_out"])

    # aggiorna baseline coi numeri freschi
    update_baseline(
        c, asset_id,
        (pair.get("liquidity") or {}).get("usd") or 0,
        (pair.get("volume") or {}).get("h24") or 0,
    )


def enrich_once():
    init_db()
    now = time.time()
    processed, excluded_n = 0, 0
    with get_conn() as c:
        rows = c.execute(
            """SELECT * FROM assets WHERE status='active'
               ORDER BY discovered_at DESC LIMIT ?""",
            (ENRICHMENT["max_active_assets"],),
        ).fetchall()

        for asset in rows:
            if not _due_for_refresh(asset, now):
                continue

            # archivia gli asset fermi da troppo
            if (now - asset["discovered_at"]) > ENRICHMENT["archive_after_days"] * 86400:
                c.execute("UPDATE assets SET status='archived' WHERE id=?", (asset["id"],))
                continue

            pd = get_json(f"{DEX_BASE}/latest/dex/tokens/{asset['contract_address']}", limiter)
            pairs = (pd or {}).get("pairs") or []
            if not pairs:
                c.execute("UPDATE assets SET last_enriched_at=? WHERE id=?", (now, asset["id"]))
                continue
            pair = max(pairs, key=lambda p: (p.get("liquidity") or {}).get("usd") or 0)
            a = dict(asset)
            processed += 1

            # 1) SICUREZZA -> esclusione PERMANENTE se fallisce
            ok, why = _safety_checks(c, a, pair)
            if not ok:
                exclude(c, a["chain"], a["contract_address"], reason=why, permanent=True)
                excluded_n += 1
                continue

            # 2) DISTRIBUZIONE -> esclusione TEMPORANEA (24h): potrebbe tornare sano
            if _distribution_check(pair):
                exclude(c, a["chain"], a["contract_address"],
                        reason="distribuzione in corso (cascata di Sell)",
                        permanent=False, ttl_hours=24)
                excluded_n += 1
                continue

            # 3) QUALITÀ -> segnali per lo scoring
            _quality_signals(c, a["id"], pair)
            c.execute("UPDATE assets SET last_enriched_at=? WHERE id=?", (now, a["id"]))

    print(f"[enrichment] arricchiti={processed} esclusi={excluded_n}")
    return processed


if __name__ == "__main__":
    if "--once" in sys.argv:
        enrich_once()
    else:
        while True:
            try:
                enrich_once()
            except Exception as e:
                print(f"[enrichment] errore: {e}")
            time.sleep(60)
