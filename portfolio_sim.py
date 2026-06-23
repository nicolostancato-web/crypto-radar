"""
portfolio_sim.py — PAPER PORTFOLIO da 100 EUR (onesto, no look-ahead).

Simula: parti da 100 EUR, per ogni segnale (in ordine di tempo) apri un paper-trade con una frazione
fissa del capitale, esegui entrata+uscita REALISTICHE (slippage su entrambe, uscita trailing causale
che cammina le candele 5-min se disponibili, altrimenti la serie oraria), aggiorna il capitale.

Output: web/portfolio.json -> lista trade + curva del capitale + statistiche, mostrato sul dashboard.
Onesto fino in fondo: se la strategia perde, il portafoglio scende. Niente numeri gonfiati.
"""
import os, json, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
SLIP = 0.06          # slippage 6% su entrata E uscita (micro-cap)
TRAIL = 0.30         # esci se il prezzo scende 30% dal picco
BET_FRAC = 0.15      # rischio 15% del capitale per trade
START = 100.0


def _load_candles():
    """ohlcv 5-min per token (ascendente). {ca: [(ts,open,high,low,close)]}"""
    out = {}
    p = os.path.join(HERE, "data", "ohlcv.jsonl")
    if not os.path.exists(p):
        return out
    for l in open(p):
        try:
            r = json.loads(l); c = r.get("candles") or []
            if c:
                out[r["ca"]] = sorted([(int(x[0]), x[1], x[2], x[3], x[4]) for x in c], key=lambda t: t[0])
        except Exception:
            pass
    return out


def _hourly_series():
    """fallback: serie oraria (ts, price) dal tracking."""
    obs = {}
    for l in open(os.path.join(HERE, "data", "track.jsonl")):
        o = json.loads(l)
        if o.get("price"):
            obs.setdefault(o["ca"], []).append((o["obs_ts"], o["price"], o.get("signal_ts", 0)))
    return {ca: sorted(v, key=lambda t: t[0]) for ca, v in obs.items()}


def _trade_return(ca, signal_ts, candles, hourly):
    """ritorno realistico del trade: entry+slip dopo il segnale, uscita trailing causale, exit-slip."""
    # serie (ts, high, low/close) point-in-time DOPO il segnale
    fine = candles.get(ca)
    if fine:
        seq = [(ts, hi, cl) for (ts, op, hi, lo, cl) in fine if ts >= signal_ts]
        src = "5m"
    else:
        h = hourly.get(ca)
        if not h:
            return None
        seq = [(ts, pr, pr) for (ts, pr, _s) in h if ts >= (signal_ts or 0)]
        src = "1h"
    seq = [(ts, hi, cl) for (ts, hi, cl) in seq if hi and cl]
    if len(seq) < 2:
        return None
    # DEGLITCH: togli candele con prezzi assurdi (polvere/glitch) rispetto alla mediana
    med = st.median([cl for _, _, cl in seq])
    seq = [(ts, hi, cl) for (ts, hi, cl) in seq if med / 15 <= cl <= med * 15 and hi <= med * 20]
    if len(seq) < 2:
        return None
    entry = seq[0][2] * (1 + SLIP)        # compro al close del primo periodo, peggiorato
    peak = seq[0][1]
    for ts, hi, cl in seq[1:]:
        peak = max(peak, hi)
        if cl <= peak * (1 - TRAIL):       # trailing stop scattato
            return max(cl * (1 - SLIP) / entry - 1, -0.95), src, ts
    return max(min(seq[-1][2] * (1 - SLIP) / entry - 1, 10.0), -0.95), src, seq[-1][0]


def run(strategy="bs>=1.5"):
    candles = _load_candles()
    hourly = _hourly_series()
    # segnali con bs e signal_ts
    sigs = {}
    for l in open(os.path.join(HERE, "data", "candidates.jsonl")):
        c = json.loads(l); ca = c.get("ca"); m = c.get("metrics", {})
        if ca and ca not in sigs:
            sigs[ca] = {"ticker": c.get("ticker") or m.get("name") or ca[:6],
                        "bs": m.get("bs_ratio_1h"), "ts": hourly.get(ca, [(0,)])[0][0] if ca in hourly else 0}

    def keep(s):
        if strategy == "bs>=1.5":
            return (s["bs"] or 0) >= 1.5
        if strategy == "bs>=2.0":
            return (s["bs"] or 0) >= 2.0
        return True  # buy_all

    picks = [(ca, s) for ca, s in sigs.items() if keep(s) and ca in hourly]
    picks.sort(key=lambda x: x[1]["ts"])   # ordine cronologico di entrata

    bal = START
    trades = []
    equity = [[picks[0][1]["ts"], START]] if picks else []
    for ca, s in picks:
        tr = _trade_return(ca, s["ts"], candles, hourly)
        if not tr:
            continue
        ret, src, exit_ts = tr
        bet = bal * BET_FRAC
        pnl = bet * ret
        bal += pnl
        trades.append({"ticker": s["ticker"], "ca": ca, "bs": s["bs"], "entry_ts": s["ts"],
                       "exit_ts": exit_ts, "ret_pct": round(ret * 100, 1), "pnl_eur": round(pnl, 2),
                       "balance": round(bal, 2), "src": src})
        equity.append([exit_ts, round(bal, 2)])

    wins = [t for t in trades if t["ret_pct"] > 0]
    out = {"start": START, "final": round(bal, 2), "strategy": strategy,
           "rules": f"entry+{int(SLIP*100)}% slip, trailing {int(TRAIL*100)}% exit, bet {int(BET_FRAC*100)}%/trade",
           "n_trades": len(trades), "win_rate": round(len(wins) / len(trades) * 100) if trades else 0,
           "best": max((t["ret_pct"] for t in trades), default=0),
           "worst": min((t["ret_pct"] for t in trades), default=0),
           "n_5m": sum(1 for t in trades if t["src"] == "5m"),
           "equity": equity, "trades": sorted(trades, key=lambda t: t["entry_ts"], reverse=True)}
    with open(os.path.join(HERE, "web", "portfolio.json"), "w") as f:
        json.dump(out, f)
    print(f"[portfolio] {strategy}: 100 EUR -> {bal:.2f} EUR | {len(trades)} trade | win {out['win_rate']}% | "
          f"candele 5m su {out['n_5m']}/{len(trades)} trade")
    return out


if __name__ == "__main__":
    import sys
    run(sys.argv[1] if len(sys.argv) > 1 else "bs>=1.5")
