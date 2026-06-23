"""
trade_learner.py — TAB 3 che IMPARA. Ogni giorno cerca la strategia di uscita/sizing meno peggiore.

Prova una griglia (filtro segnale x tipo uscita x trailing) sul campione maturo con esecuzione
realistica (slippage, candele 5-min dove ci sono, no look-ahead), classifica per P&L mediano, e
scrive la VINCENTE in data/trade_config.json (che portfolio_sim legge). Appende a data/trade_learnings.jsonl
lo storico: cosi' vediamo se il Trader migliora col tempo. Onesto: se tutte perdono, sceglie la meno
peggiore e lo dichiara.
"""
import os, json, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
SLIP = 0.06


def _candles():
    out = {}
    p = os.path.join(HERE, "data", "ohlcv.jsonl")
    if os.path.exists(p):
        for l in open(p):
            try:
                r = json.loads(l); c = r.get("candles") or []
                if c:
                    out[r["ca"]] = sorted([(int(x[0]), x[2], x[4]) for x in c], key=lambda t: t[0])  # ts,high,close
            except Exception:
                pass
    return out


def _series():
    obs = {}
    for l in open(os.path.join(HERE, "data", "track.jsonl")):
        o = json.loads(l)
        if o.get("price"):
            obs.setdefault(o["ca"], []).append((o["obs_ts"], o["price"]))
    bs = {}
    for l in open(os.path.join(HERE, "data", "candidates.jsonl")):
        c = json.loads(l); ca = c.get("ca")
        if ca and ca not in bs:
            bs[ca] = (c.get("metrics") or {}).get("bs_ratio_1h")
    return {ca: sorted(v) for ca, v in obs.items()}, bs


def _ret(ca, candles, hourly, exit_type, trail):
    if ca in candles:
        seq = [(ts, hi, cl) for ts, hi, cl in candles[ca]]
    else:
        h = hourly.get(ca)
        if not h:
            return None
        seq = [(ts, pr, pr) for ts, pr in h]
    if len(seq) < 2:
        return None
    med = st.median([cl for _, _, cl in seq])
    seq = [(ts, hi, cl) for ts, hi, cl in seq if med / 15 <= cl <= med * 15 and hi <= med * 20]
    if len(seq) < 2:
        return None
    entry = seq[0][2] * (1 + SLIP); peak = seq[0][1]
    for ts, hi, cl in seq[1:]:
        peak = max(peak, hi)
        if exit_type == "trail" and cl <= peak * (1 - trail):
            return max(cl * (1 - SLIP) / entry - 1, -0.95)
        if exit_type == "tp_sl":
            if cl >= entry * (1 + trail * 3):      # take-profit a 3x il trail
                return cl * (1 - SLIP) / entry - 1
            if cl <= entry * (1 - trail - 0.1):    # stop
                return max(cl * (1 - SLIP) / entry - 1, -0.95)
    return max(min(seq[-1][2] * (1 - SLIP) / entry - 1, 10.0), -0.95)


def run():
    candles = _candles(); hourly, bs = _series()
    nobs = {ca: len(v) for ca, v in hourly.items()}
    mature = [ca for ca in hourly if nobs[ca] >= 6]
    filters = {"buy_all": lambda ca: True, "bs>=1.5": lambda ca: (bs.get(ca) or 0) >= 1.5,
               "bs>=2.0": lambda ca: (bs.get(ca) or 0) >= 2.0, "bs>=3.0": lambda ca: (bs.get(ca) or 0) >= 3.0}
    grid = []
    for fname, fpred in filters.items():
        sel = [ca for ca in mature if fpred(ca)]
        for etype in ("trail", "tp_sl"):
            for trail in (0.20, 0.30, 0.40):
                rs = [_ret(ca, candles, hourly, etype, trail) for ca in sel]
                rs = [r for r in rs if r is not None]
                if len(rs) < 15:
                    continue
                grid.append({"filter": fname, "exit": etype, "trail": trail, "n": len(rs),
                             "median_pnl": round(st.median(rs) * 100, 1), "mean_pnl": round(st.mean(rs) * 100, 1),
                             "win": round(sum(1 for r in rs if r > 0) / len(rs) * 100)})
    if not grid:
        print("[trade_learner] dati insufficienti"); return
    grid.sort(key=lambda g: (g["median_pnl"], g["mean_pnl"]), reverse=True)
    best = grid[0]
    best["bet_frac"] = 0.10 if best["median_pnl"] < 0 else 0.15   # se perde, rischia meno
    best["profitable"] = best["median_pnl"] > 0
    with open(os.path.join(HERE, "data", "trade_config.json"), "w") as f:
        json.dump(best, f)
    hist = os.path.join(HERE, "data", "trade_learnings.jsonl")
    prev = [json.loads(l) for l in open(hist)] if os.path.exists(hist) else []
    date_ts = max((v[-1][0] for v in hourly.values()), default=0)
    if not prev or prev[-1].get("n") != best["n"]:
        with open(hist, "a") as f:
            f.write(json.dumps({"date_ts": date_ts, **best, "top3": grid[:3]}) + "\n")
    tag = "PROFITTEVOLE" if best["profitable"] else "MENO PEGGIORE (tutte perdono)"
    print(f"[trade_learner] migliore: {best['filter']} + {best['exit']}{int(best['trail']*100)}% "
          f"-> mediana {best['median_pnl']}% win {best['win']}% [{tag}]")
    return best


if __name__ == "__main__":
    run()
