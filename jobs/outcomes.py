"""
jobs/outcomes.py — la METRICA DI VERITA'.

Una sola domanda onesta: "gli score alti si muovono DAVVERO?"

Quando uno score supera la soglia di tracking, apriamo un'ENTRATA IPOTETICA (paper trade):
registriamo prezzo+liquidita' di partenza. Poi, a 24h/72h/168h, misuriamo il prezzo e
calcoliamo il rendimento NETTO di slippage+fee simulati. Non la % di colpi giusti (mente):
il VALORE ATTESO netto. Una % alta puo' comunque perdere soldi.

Slippage simulato (onesto, pessimista): impatto ~ taglia_trade / liquidita', + fee per lato,
andata E ritorno. Su token illiquidi mangia i guadagni "sulla carta" — ed e' giusto cosi'.
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import OUTCOMES, LIMITS
from db import (get_conn, init_db, has_open_outcome, open_outcome,
                get_open_outcomes, set_outcome_point, close_outcome)
from net import RateLimiter, get_json

DEX_BASE = "https://api.dexscreener.com"
limiter = RateLimiter(LIMITS["dexscreener_max_calls_per_min"])


def _price_and_liq(contract):
    """Ritorna (prezzo_usd, liquidita_usd) del pair piu' liquido, o (None, None)."""
    pd = get_json(f"{DEX_BASE}/latest/dex/tokens/{contract}", limiter)
    pairs = (pd or {}).get("pairs") or []
    if not pairs:
        return None, None
    pair = max(pairs, key=lambda p: (p.get("liquidity") or {}).get("usd") or 0)
    try:
        price = float(pair.get("priceUsd"))
    except (TypeError, ValueError):
        price = None
    liq = (pair.get("liquidity") or {}).get("usd") or 0
    return price, liq


def _net_return(p_entry, p_now, liq_entry):
    """Rendimento lordo e NETTO (slippage+fee, andata+ritorno). Onesto e pessimista."""
    if not p_entry or not p_now:
        return None, None
    gross = (p_now - p_entry) / p_entry
    slip = min(OUTCOMES["paper_trade_usd"] / max(liq_entry or 1.0, 1.0),
               OUTCOMES["slippage_cap_pct"])
    round_trip_cost = 2 * (slip + OUTCOMES["swap_fee_pct"])
    net = gross - round_trip_cost
    return round(gross, 4), round(net, 4)


def outcomes_once():
    init_db()
    now = time.time()
    opened, matured, closed = 0, 0, 0

    with get_conn() as c:
        # 1) APRI nuove entrate: score >= soglia, asset attivo, nessuna entrata gia' aperta
        rows = c.execute(
            """SELECT a.id, a.chain, a.contract_address, a.ticker, s.current_score
               FROM scores s JOIN assets a ON a.id = s.asset_id
               WHERE a.status='active' AND s.current_score >= ?
               ORDER BY s.current_score DESC
               LIMIT ?""",
            (OUTCOMES["tracking_threshold"], OUTCOMES["max_open_assets"]),
        ).fetchall()

        for r in rows:
            if has_open_outcome(c, r["id"]):
                continue
            price, liq = _price_and_liq(r["contract_address"])
            if price is None:
                continue
            open_outcome(c, r["id"], r["chain"], r["contract_address"], r["ticker"],
                         r["current_score"], price, liq)
            opened += 1

        # 2) MATURA le entrate aperte: riempi gli orizzonti scaduti, poi chiudi
        horizons = OUTCOMES["horizons"]
        max_h = max(horizons)
        for o in get_open_outcomes(c):
            age_h = (now - o["entered_at"]) / 3600.0
            due = [h for h in horizons if age_h >= h and o[f"price_{h}h"] is None]
            if due:
                price_now, _ = _price_and_liq(o["contract_address"])
                if price_now is not None:
                    for h in due:
                        g, n = _net_return(o["price_at_entry"], price_now, o["liquidity_at_entry"])
                        set_outcome_point(c, o["id"], h, price_now, g, n)
                    matured += 1
            # chiudi se l'orizzonte massimo e' passato (i punti mancanti restano NULL)
            if age_h >= max_h:
                close_outcome(c, o["id"])
                closed += 1

    print(f"[outcomes] aperte={opened} maturate={matured} chiuse={closed}")
    return opened


def outcomes_summary():
    """Stampa il VERDETTO coi dati: valore atteso netto per orizzonte. Onesto."""
    init_db()
    with get_conn() as c:
        rows = c.execute("SELECT * FROM outcomes").fetchall()
    n = len(rows)
    print(f"[outcomes] entrate totali tracciate: {n}")
    for h in OUTCOMES["horizons"]:
        nets = [r[f"ret_{h}h_net"] for r in rows if r[f"ret_{h}h_net"] is not None]
        if not nets:
            print(f"  {h}h: nessun dato maturo ancora")
            continue
        avg = sum(nets) / len(nets)
        win = sum(1 for x in nets if x > 0) / len(nets)
        print(f"  {h}h: n={len(nets)}  valore_atteso_netto={avg:+.2%}  win_rate={win:.0%}")


if __name__ == "__main__":
    if "--summary" in sys.argv:
        outcomes_summary()
    else:
        outcomes_once()
        outcomes_summary()
