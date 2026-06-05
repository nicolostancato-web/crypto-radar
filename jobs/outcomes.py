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

from config import OUTCOMES, EXIT, LIMITS
from db import (get_conn, init_db, has_open_outcome, open_outcome,
                get_open_outcomes, set_outcome_point, close_outcome)
from net import RateLimiter, get_json
import spikes

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
            """SELECT a.id, a.chain, a.contract_address, a.ticker,
                      s.current_score, s.breakdown
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
                         r["current_score"], price, liq, signals=r["breakdown"])
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


def _simulate_exit(candles, entered_at, entry_price, liquidity):
    """Simula TP scalari + trailing + stop sul path di prezzo. Ritorna (net_return, motivo)."""
    if not candles or not entry_price or entry_price <= 0:
        return None, None
    end = entered_at + EXIT["hard_hours"] * 3600
    path = [c for c in candles if entered_at <= c[0] <= end]
    if not path:
        return None, None
    pos, proceeds, peak = 1.0, 0.0, entry_price
    tp1 = entry_price * (1 + EXIT["tp1_gain"])
    tp2 = entry_price * (1 + EXIT["tp2_gain"])
    stop = entry_price * (1 - EXIT["stop_loss"])
    arm = entry_price * (1 + EXIT["trailing_arm"])
    t1, t2, reason = False, False, "hard_24h"
    for ts, o, hi, lo, cl in path:
        peak = max(peak, hi)
        # stop loss prima (pessimista)
        if lo <= stop:
            proceeds += pos * stop; pos = 0; reason = "stop_loss"; break
        if not t1 and hi >= tp1:
            proceeds += EXIT["tp1_sell"] * tp1; pos -= EXIT["tp1_sell"]; t1 = True
        if not t2 and hi >= tp2:
            proceeds += EXIT["tp2_sell"] * tp2; pos -= EXIT["tp2_sell"]; t2 = True
        trail = peak * (1 - EXIT["trailing"])
        if peak >= arm and lo <= trail and pos > 0:
            proceeds += pos * trail; pos = 0; reason = "trailing"; break
    if pos > 0:
        proceeds += pos * path[-1][4]   # resto liquidato all'ultima candela
    gross = proceeds / entry_price - 1
    slip = min(OUTCOMES["paper_trade_usd"] / max(liquidity or 1, 1), OUTCOMES["slippage_cap_pct"])
    net = gross - 2 * (slip + OUTCOMES["swap_fee_pct"])
    return round(net, 4), reason


def simulate_exits():
    """Per ogni paper trade, simula la strategia d'uscita meccanica sul path reale (OHLCV)."""
    init_db()
    now, done = time.time(), 0
    with get_conn() as c:
        rows = c.execute(
            """SELECT o.id, o.entered_at, o.price_at_entry, o.liquidity_at_entry,
                      a.chain, a.pair_address, a.contract_address
               FROM outcomes o JOIN assets a ON a.id = o.asset_id""").fetchall()
        for o in rows:
            pool = o["pair_address"] or o["contract_address"]
            if not pool or not o["price_at_entry"]:
                continue
            candles = spikes.get_ohlcv(o["chain"], pool, EXIT["ohlcv_aggregate_min"])
            net, reason = _simulate_exit(candles, o["entered_at"], o["price_at_entry"], o["liquidity_at_entry"])
            if net is not None:
                c.execute("UPDATE outcomes SET sim_return=?, sim_reason=?, sim_at=? WHERE id=?",
                          (net, reason, now, o["id"]))
                done += 1
    print(f"[exitsim] paper trade simulati con exit meccaniche: {done}")
    return done


def learning_signals(horizon=72):
    """
    COSA STA IMPARANDO IL SISTEMA: per ogni segnale, qual è il rendimento netto medio
    delle entrate in cui era acceso. È la base dell'apprendimento — ma ONESTA: con pochi
    dati è rumore, quindi riportiamo anche N e una 'confidenza'. Si tara SOLO con N alto.
    """
    import json as _json
    init_db()
    col = f"ret_{horizon}h_net"
    with get_conn() as c:
        rows = c.execute(
            f"SELECT signals_at_entry, {col} AS ret FROM outcomes WHERE {col} IS NOT NULL"
        ).fetchall()

    agg = {}  # signal -> list[net]
    for r in rows:
        try:
            sigs = _json.loads(r["signals_at_entry"] or "{}")
        except (TypeError, ValueError):
            sigs = {}
        for k in sigs:
            agg.setdefault(k, []).append(r["ret"])

    out = []
    for k, nets in sorted(agg.items(), key=lambda x: -(sum(x[1]) / len(x[1]))):
        n = len(nets)
        avg = sum(nets) / n
        # confidenza grezza: serve volume per crederci (curve-fitting su pochi = morte)
        conf = "alta" if n >= 30 else "media" if n >= 10 else "bassa"
        out.append({"signal": k, "n": n, "avg_net": round(avg, 4), "confidence": conf})
    return out


if __name__ == "__main__":
    if "--summary" in sys.argv:
        outcomes_summary()
    elif "--learning" in sys.argv:
        for s in learning_signals():
            print(f"  {s['signal']:22} n={s['n']:3} netto_medio={s['avg_net']:+.2%} conf={s['confidence']}")
    else:
        outcomes_once()
        outcomes_summary()
