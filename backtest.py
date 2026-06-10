"""
backtest.py — IMPARA DALLA STORIA, non aspettare i trade live.

Problema: dal vivo accumuliamo 3-5 trade/giorno -> mai abbastanza per un verdetto.
Soluzione: per ogni wallet smart prendiamo i suoi acquisti PASSATI e simuliamo "se avessimo
copiato (entrata +10% peggiore per latenza, uscita meccanica), quanto avremmo fatto?" sullo
storico OHLCV. Centinaia di paper-trade SUBITO -> mediana, win-rate, batte-il-hold = verdetto vero.

CFO: ~1 chiamata OHLCV per acquisto storico (gratis CoinGecko/Helius). Run on-demand, non nel loop.
"""
import sys, os, statistics
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

LATENCY = 1.10   # copiamo a +10% peggiore (latenza + slippage d'ingresso, test onesto)


def backtest(max_wallets=12, history_tx=80):
    init_db()
    cache = {}
    sol_price = _dex_info(WSOL, cache)[0] or 150.0
    with get_conn() as c:
        wallets = _smart_wallets(c, max_wallets)
    print(f"[backtest] {len(wallets)} wallet smart, fino a {history_tx} tx ciascuno...")

    nets, holds = [], []
    seen = set()
    n_buys = n_sim = 0
    for wi, w in enumerate(wallets, 1):
        for t in onchain.wallet_recent_activity(w, history_tx):
            if t["side"] != "buy" or not t.get("ts"):
                continue
            n_buys += 1
            key = (w, t["mint"], t["ts"])
            if key in seen:
                continue
            seen.add(key)
            price, liq, pool, name = _dex_info(t["mint"], cache)
            if not pool:
                continue
            ts = t["ts"]
            # candele storiche attorno al loro acquisto: da ~ts a ts+24h
            candles = spikes.get_ohlcv("solana", pool, EXIT["ohlcv_aggregate_min"],
                                       limit=130, before=ts + EXIT["hard_hours"] * 3600 + 1800)
            path = [k for k in candles if k[0] >= ts]
            if not path:
                continue
            entry = path[0][4] * LATENCY     # entrata: close della candela al loro acquisto, +10%
            net, reason = _simulate_exit(candles, ts, entry, liq)
            hold = _hold_return(candles, ts, entry, liq)
            if net is not None:
                nets.append(net)
                if hold is not None:
                    holds.append(hold)
                n_sim += 1
        print(f"  [{wi}/{len(wallets)}] {w[:8]}… trade simulati finora: {n_sim}")

    print(f"\n[backtest] acquisti storici visti: {n_buys} | paper-trade simulati: {n_sim}")
    if not nets:
        print("[backtest] nessun trade simulabile (storico OHLCV mancante).")
        return
    med = statistics.median(nets)
    mean = statistics.mean(nets)
    win = sum(1 for x in nets if x > 0) / len(nets)
    med_hold = statistics.median(holds) if holds else None
    beats = (med > med_hold) if med_hold is not None else None
    print("\n========= VERDETTO BACKTEST (copy-trade su storico) =========")
    print(f"  paper-trade:        {len(nets)}")
    print(f"  EV MEDIANO (netto): {med:+.2%}   <- la metrica che conta")
    print(f"  EV medio (netto):   {mean:+.2%}   (gonfiato dagli outlier)")
    print(f"  win-rate:           {win:.0%}")
    if med_hold is not None:
        print(f"  buy-and-hold med:   {med_hold:+.2%}")
        print(f"  BATTE il hold?      {'SI ✅' if beats else 'NO ❌'}")
    print("=============================================================")
    verdict = ("EDGE PLAUSIBILE: mediana positiva e batte il hold" if (med > 0.05 and beats)
               else "NESSUN EDGE: copiare questi wallet non rende (mediana <=0 o non batte il hold)")
    print(f"  -> {verdict}")
    return {"n": len(nets), "median": round(med, 4), "mean": round(mean, 4),
            "win_rate": round(win, 3), "hold_median": round(med_hold, 4) if med_hold else None,
            "beats_hold": beats}


if __name__ == "__main__":
    mw = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    backtest(max_wallets=mw)
