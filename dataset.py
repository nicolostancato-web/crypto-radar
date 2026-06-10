"""
dataset.py — ESTRAZIONE DI MASSA dei dati GIUSTI per trovare l'edge.

Filosofia (Nicolo', 2026-06-10): non aspettare 5 trade/giorno. Estrarre MIGLIAIA di eventi
storici "wallet compra token" con TUTTI gli attributi che servono a capire QUANDO copiare rende.
Poi si segmenta il dataset e si cerca la combinazione di attributi con EV positivo = l'edge.

1 riga = 1 evento d'acquisto, con: profilo wallet + stato token all'ingresso + coordinazione +
esito (ritorno copia, hold, max gain). Salvato in data/dataset.jsonl (su GitHub, gratis, illimitato).
Accumula su piu' run (idempotente: dedup per (wallet,mint,ts)). Free-first (Helius/CoinGecko/DEX).
"""
import sys, os, json, time, statistics
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except Exception:
    pass

import onchain
import spikes
from jobs.outcomes import _simulate_exit, _hold_return
from jobs.smartwatch import _dex_info, _smart_wallets, WSOL
from config import EXIT
from db import get_conn, init_db

LATENCY = 1.10
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "dataset.jsonl")


def _load_seen():
    seen = set()
    if os.path.exists(OUT):
        for line in open(OUT):
            try:
                r = json.loads(line)
                seen.add((r["wallet"], r["mint"], r["ts"]))
            except Exception:
                continue
    return seen


def _wallet_profile(c):
    """Cache profilo dei wallet qualificati (dal DB): la 'qualita'' del wallet."""
    prof = {}
    for r in c.execute("""SELECT address,pnl_sol,win_rate,closed_count,balance_sol,
                                 span_days,is_bot,copy_pnl FROM wallets WHERE verified=1""").fetchall():
        prof[r["address"]] = dict(r)
    return prof


def extract(max_wallets=20, history_tx=120, max_rows=4000):
    init_db()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    seen = _load_seen()
    cache = {}
    sol_price = _dex_info(WSOL, cache)[0] or 150.0
    with get_conn() as c:
        wallets = _smart_wallets(c, max_wallets)
        prof = _wallet_profile(c)
        # coordinazione: tutti gli acquisti smart per mint (dal DB spike_buys)
        coord = {}
        for m, w, t in c.execute("SELECT mint,wallet,bought_at FROM spike_buys").fetchall():
            coord.setdefault(m, []).append((w, t))

    print(f"[dataset] {len(wallets)} wallet, fino a {history_tx} tx. Gia' nel dataset: {len(seen)} righe")
    new = 0
    f = open(OUT, "a")
    for wi, w in enumerate(wallets, 1):
        wp = prof.get(w, {})
        for t in onchain.wallet_recent_activity(w, history_tx):
            if new >= max_rows:
                break
            if t["side"] != "buy" or not t.get("ts"):
                continue
            key = (w, t["mint"], t["ts"])
            if key in seen:
                continue
            seen.add(key)
            price0, liq, pool, name = _dex_info(t["mint"], cache)
            if not pool:
                continue
            ts = t["ts"]
            candles = spikes.get_ohlcv("solana", pool, EXIT["ohlcv_aggregate_min"],
                                       limit=140, before=ts + EXIT["hard_hours"] * 3600 + 1800)
            after = [k for k in candles if k[0] >= ts]
            before_c = [k for k in candles if k[0] < ts]
            if not after:
                continue
            entry = after[0][4]
            # ESITO: copia (entrata +10%), hold, max gain nelle 24h
            net, reason = _simulate_exit(candles, ts, entry * LATENCY, liq)
            hold = _hold_return(candles, ts, entry * LATENCY, liq)
            window = [k for k in after if k[0] <= ts + EXIT["hard_hours"] * 3600]
            max_gain = (max(k[2] for k in window) / entry - 1) if window else None
            # ATTRIBUTI token all'ingresso
            runup = (entry / min(k[3] for k in before_c) - 1) if before_c else None
            usd = (t["sol"] or 0) * sol_price
            # COORDINAZIONE: altri smart wallet sullo stesso token entro +-1h
            others = len({ww for ww, tt in coord.get(t["mint"], []) if ww != w and abs((tt or 0) - ts) <= 3600})
            row = {
                "wallet": w, "mint": t["mint"], "ts": ts, "token": name,
                # profilo wallet
                "w_pnl": wp.get("pnl_sol"), "w_winrate": wp.get("win_rate"),
                "w_closed": wp.get("closed_count"), "w_balance": wp.get("balance_sol"),
                "w_span_days": wp.get("span_days"), "w_is_bot": wp.get("is_bot"),
                # token all'ingresso
                "buy_usd": round(usd), "runup_before": round(runup, 3) if runup is not None else None,
                "liquidity": round(liq) if liq else None,
                "buy_pct_liq": round(usd / liq, 4) if liq else None,
                # coordinazione
                "smart_coord_1h": others,
                # ESITO (la verita')
                "copy_net": net, "hold_net": hold,
                "max_gain_24h": round(max_gain, 3) if max_gain is not None else None,
                "exit_reason": reason,
            }
            f.write(json.dumps(row) + "\n")
            new += 1
        f.flush()
        print(f"  [{wi}/{len(wallets)}] {w[:8]}… righe nuove: {new}")
        if new >= max_rows:
            break
    f.close()
    total = len(seen)
    print(f"\n[dataset] righe nuove: {new} | TOTALE dataset: {total}")
    return new, total


if __name__ == "__main__":
    mw = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    extract(max_wallets=mw)
