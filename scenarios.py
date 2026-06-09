"""
scenarios.py — il MOTORE A ELIMINAZIONE SISTEMATICA.

Testiamo UN'ipotesi (scenario) alla volta. Ogni scenario ha le SUE regole d'ingresso e
apre paper-trade taggati col suo nome in `outcomes`. L'exitsim meccanico esistente
(jobs/outcomes.simulate_exits) calcola il ritorno NETTO di ognuno. Il loop auto-analisi
(ogni 6h) legge scenario_stats(), aggiusta i parametri in config.SCENARIOS, e decide
PARK / CONTINUA / FUNZIONA.

NIENTE soldi veri: solo paper trading. Vincolo: gratis, polling orario.

Scenari implementati: S0 baseline (controllo), S1 regime filter, S3 cluster accumulation.
S2/S4+ arrivano quando il loop avanza (richiedono cattura dei SELL / metadata deployer).
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import SCENARIOS
from db import (get_conn, init_db, upsert_asset, ensure_scenario,
                has_open_scenario_outcome, open_scenario_outcome, scenario_stats)
from jobs.outcomes import _price_and_liq


# --- SMART WALLET SET (per S3) --------------------------------------------

def _smart_wallets(c, definition):
    """Insieme dei wallet 'smart'. soft = verificati-profittevoli UNION boss early ricorrenti;
    strict = solo verificati profittevoli con track record solido (>=10 chiusi)."""
    if definition == "strict":
        rows = c.execute(
            """SELECT address FROM wallets
               WHERE verified=1 AND is_bot=0 AND pnl_sol>0 AND closed_count>=10""").fetchall()
        return {r["address"] for r in rows}
    # soft
    verified = c.execute(
        "SELECT address FROM wallets WHERE verified=1 AND is_bot=0 AND pnl_sol>0").fetchall()
    bosses = c.execute(
        """SELECT wallet FROM spike_buys WHERE is_early=1
           GROUP BY wallet HAVING COUNT(DISTINCT mint) >= 2""").fetchall()
    return {r["address"] for r in verified} | {r["wallet"] for r in bosses}


# --- SCENARI ---------------------------------------------------------------

def s3_cluster(c, cfg, max_entries):
    """S3 — Cluster Accumulation: >=N wallet SMART distinti comprano lo stesso token entro
    una finestra, e non stanno inseguendo (runup contenuto). Entra al loro prezzo recente."""
    smart = _smart_wallets(c, cfg["smart_def"])
    if not smart:
        print("[S3] nessun wallet smart ancora (set vuoto) — niente cluster da rilevare")
        return 0
    now = time.time()
    window = cfg["window_s"]
    placeholders = ",".join("?" * len(smart))
    # mint con >= N smart-wallet distinti che hanno comprato entro la finestra
    rows = c.execute(
        f"""SELECT mint,
                   COUNT(DISTINCT wallet) AS n_smart,
                   AVG(runup_pct)         AS avg_runup,
                   MAX(bought_at)         AS last_buy,
                   AVG(price)             AS px,
                   AVG(liquidity)         AS liq,
                   MAX(pool_addr)         AS pool,
                   MAX(pool_name)         AS name
            FROM spike_buys
            WHERE wallet IN ({placeholders}) AND bought_at >= ?
            GROUP BY mint
            HAVING n_smart >= ?""",
        (*smart, now - window, cfg["smart_min_wallets"])).fetchall()

    opened = 0
    for r in rows:
        if opened >= max_entries:
            break
        if r["avg_runup"] is not None and r["avg_runup"] > cfg["max_runup_at_entry"]:
            continue  # stanno inseguendo: non entriamo
        if not r["px"] or not r["pool"]:
            continue
        asset_id = upsert_asset(c, "solana", r["mint"], (r["mint"] or "")[:6],
                                r["name"], r["pool"], "S3_cluster")
        if not asset_id:
            continue  # escluso (rugpull noto, ecc.)
        if has_open_scenario_outcome(c, asset_id, "S3_cluster"):
            continue
        open_scenario_outcome(c, "S3_cluster", asset_id, "solana", r["mint"],
                              (r["mint"] or "")[:6], r["px"], r["liq"],
                              signals='{"cluster":1}')
        opened += 1
        print(f"[S3] CLUSTER: {r['name']} — {r['n_smart']} smart wallet, runup~{(r['avg_runup'] or 0):.0%}")
    return opened


def _baseline_entries(c, cfg, max_entries, scenario):
    """Apre entrate su asset attivi con volume minimo (usato da S0 e, sotto regime, da S1)."""
    rows = c.execute(
        """SELECT a.id, a.chain, a.contract_address, a.ticker, b.avg_volume
           FROM assets a JOIN baselines b ON b.asset_id = a.id
           WHERE a.status='active' AND b.avg_volume >= ?
           ORDER BY b.avg_volume DESC LIMIT ?""",
        (cfg["min_vol_usd"], max_entries * 3)).fetchall()
    opened = 0
    for r in rows:
        if opened >= max_entries:
            break
        if has_open_scenario_outcome(c, r["id"], scenario):
            continue
        price, liq = _price_and_liq(r["contract_address"])
        if price is None:
            continue
        open_scenario_outcome(c, scenario, r["id"], r["chain"], r["contract_address"],
                              r["ticker"], price, liq, signals='{"baseline":1}')
        opened += 1
    return opened


def s0_baseline(c, cfg, max_entries):
    """S0 — Baseline futility (controllo): compra ogni asset attivo con volume. Deve perdere."""
    return _baseline_entries(c, cfg, max_entries, "S0_baseline")


def _regime_on(c, cfg):
    """Proxy risk-on: abbastanza token vivi nel radar (breadth). (Il loop puo' raffinarlo.)"""
    n = c.execute("SELECT COUNT(*) FROM assets WHERE status='active'").fetchone()[0]
    return n >= cfg["min_active_candidates"], n


def s1_regime(c, cfg, max_entries):
    """S1 — Regime Filter: apre entrate baseline SOLO quando il regime e' risk-on.
    Il verdetto confronta S1 (filtrato) vs S0 (non filtrato): il filtro aggiunge valore?"""
    on, n = _regime_on(c, cfg)
    if not on:
        print(f"[S1] regime OFF (solo {n} token attivi) — nessuna entrata")
        return 0
    merged = {"min_vol_usd": SCENARIOS["S0_baseline"]["min_vol_usd"]}
    return _baseline_entries(c, merged, max_entries, "S1_regime")


REGISTRY = {
    "S0_baseline": s0_baseline,
    "S1_regime": s1_regime,
    "S3_cluster": s3_cluster,
}


def run_active_scenario():
    """Stadio della pipeline: esegue SOLO lo scenario attivo. Apre paper-trade taggati."""
    init_db()
    active = SCENARIOS["active"]
    fn = REGISTRY.get(active)
    if not fn:
        print(f"[scenari] scenario attivo '{active}' non implementato (ancora) — skip")
        return 0
    cfg = SCENARIOS.get(active, {})
    with get_conn() as c:
        ensure_scenario(c, active)
        opened = fn(c, cfg, SCENARIOS["max_entries_per_cycle"])
    print(f"[scenari] attivo={active} nuovi_paper_trade={opened}")
    return opened


def report():
    """Verdetto coi dati per ogni scenario con almeno un trade. Per il loop auto-analisi."""
    init_db()
    out = []
    with get_conn() as c:
        names = [r["scenario"] for r in c.execute(
            "SELECT DISTINCT scenario FROM outcomes WHERE scenario IS NOT NULL").fetchall()]
        for name in names:
            for h in (24, 72):
                st = scenario_stats(c, name, horizon=h)
                if st["n"] > 0:
                    out.append({**st, "horizon": h})
    return out


if __name__ == "__main__":
    if "--report" in sys.argv:
        for r in report():
            ev = f"{r['ev_net']:+.2%}" if r["ev_net"] is not None else "—"
            wr = f"{r['win_rate']:.0%}" if r["win_rate"] is not None else "—"
            print(f"  {r['scenario']:14} @{r['horizon']}h  n={r['n']:3}  EV_netto={ev}  win={wr}  aperti={r['open']}")
    else:
        run_active_scenario()
