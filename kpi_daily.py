"""
kpi_daily.py — TAB 2: l'agente KPI giornaliero. "C'e' una strategia, si o no?"

Gira 1x al giorno. Misura sul campione MATURO: sopravvivenza del segnale bs (win-rate vs base),
P&L realistico mediano, test out-of-sample temporale. Salva web/kpi.json (per il dashboard) e
APPENDE a data/kpi_history.jsonl (cosi' vediamo il KPI EVOLVERE: il segnale regge mentre i dati
crescono, o svanisce?). Onesto: niente look-ahead, dichiara n e runner, distingue preliminare da solido.
"""
import os, json, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
SLIP = 0.06


def _load():
    obs = {}
    for l in open(os.path.join(HERE, "data", "track.jsonl")):
        o = json.loads(l)
        if o.get("price"):
            obs.setdefault(o["ca"], []).append((o["obs_ts"], o["price"]))
    bs = {}
    for l in open(os.path.join(HERE, "data", "candidates.jsonl")):
        c = json.loads(l); ca = c.get("ca"); m = c.get("metrics", {})
        if ca and ca not in bs:
            bs[ca] = m.get("bs_ratio_1h")
    rows = []
    for ca, s in obs.items():
        s = sorted(s); pr = [p for _, p in s]
        if len(pr) < 2 or not pr[0]:
            continue
        med = st.median(pr)
        prc = [p for p in pr if med / 15 <= p <= med * 15] or pr   # deglitch
        ret = max(prc) / prc[0] - 1
        rows.append({"ca": ca, "ret": ret, "run": int(ret >= 0.5), "nobs": len(pr),
                     "bs": bs.get(ca), "t0": s[0][0]})
    return rows


def _winrate(rows):
    return round(sum(r["run"] for r in rows) / len(rows) * 100) if rows else 0


def _pnl_median(rows, cap=3.0, capture=0.35):
    out = []
    for r in rows:
        ret = min(r["ret"], cap)
        out.append((ret * capture - SLIP) if r["run"] else (max(ret, -0.35) * 0.7 - SLIP))
    return round(st.median(out) * 100, 1) if out else 0


def run():
    rows = _load()
    mat = [r for r in rows if r["nobs"] >= 6]
    bsg = [r for r in mat if (r["bs"] or 0) >= 1.5]
    base = _winrate(mat); bsw = _winrate(bsg)
    # out-of-sample temporale (primi 60% vs ultimi 40%)
    order = sorted(mat, key=lambda r: r["t0"]); cut = int(len(order) * 0.6)
    oos = [r for r in order[cut:] if (r["bs"] or 0) >= 1.5]
    lift = bsw - base
    solid = len(bsg) >= 30 and sum(r["run"] for r in bsg) >= 5
    survives = lift >= 8 and _winrate(oos) >= base   # il segnale regge anche OOS
    if not solid:
        verdict = f"PRELIMINARE — campione piccolo (bs>=1.5: n={len(bsg)}). Serve accumulare."
    elif survives:
        verdict = f"SEGNALE VIVO — bs>=1.5 batte la base di +{lift}pt e regge out-of-sample. Da pressare (slippage/uscita)."
    else:
        verdict = f"NESSUN EDGE (per ora) — bs>=1.5 non separa abbastanza o non regge OOS. Continuo ad accumulare."
    out = {"date_ts": max((r["t0"] for r in rows), default=0),
           "n_tokens": len(rows), "n_runners": sum(r["run"] for r in rows), "n_mature": len(mat),
           "base_win": base, "bs15_n": len(bsg), "bs15_win": bsw, "lift_pt": lift,
           "bs15_pnl_median": _pnl_median(bsg), "all_pnl_median": _pnl_median(mat),
           "oos_n": len(oos), "oos_win": _winrate(oos),
           "solid": solid, "survives": survives, "verdict": verdict}
    with open(os.path.join(HERE, "web", "kpi.json"), "w") as f:
        json.dump(out, f)
    # storico: 1 riga al giorno (sovrascrive se gia' fatto oggi sullo stesso n_tokens)
    hist = os.path.join(HERE, "data", "kpi_history.jsonl")
    prev = [json.loads(l) for l in open(hist)] if os.path.exists(hist) else []
    if not prev or prev[-1].get("n_tokens") != out["n_tokens"]:
        with open(hist, "a") as f:
            f.write(json.dumps({k: out[k] for k in ("date_ts", "n_tokens", "n_runners", "base_win",
                                                    "bs15_n", "bs15_win", "lift_pt", "oos_win", "survives")}) + "\n")
    print(f"[kpi] n={out['n_tokens']} runner={out['n_runners']} | base={base}% bs>=1.5={bsw}% (lift +{lift}pt) "
          f"| OOS={out['oos_win']}% | {verdict}")
    return out


if __name__ == "__main__":
    run()
