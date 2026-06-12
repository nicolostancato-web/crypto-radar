"""
learner.py — PIPELINE X-FIRST, step 5: l'APPRENDIMENTO COSTANTE.

Ogni ciclo (gira insieme allo scan orario) analizza i TRADE CONCLUSI: incrocia l'esito (track.jsonl —
quanto ha corso il token dopo il segnale) con le CONDIZIONI AL SEGNALE (candidates.jsonl — volume,
voliq, eta', concentrazione, buy/sell, heat di Grok). Impara quali condizioni separano i RUNNER dai MORTI.

Onesta' statistica (principio del progetto): con pochi dati NON conclude — lo dichiara e continua ad
accumulare. Appena il campione e' sufficiente, estrae le regole vere e suggerisce come tarare config.FILTER.
NON tocca il filtro da solo: propone, decide l'umano.

Free: solo lettura di file locali + statistica (nessuna API). Output: data/learnings.json per la dashboard.
"""
import os, json, time

HERE = os.path.dirname(os.path.abspath(__file__))
TRACK = os.path.join(HERE, "data", "track.jsonl")
CANDS = os.path.join(HERE, "data", "candidates.jsonl")
OUT = os.path.join(HERE, "data", "learnings.json")

RUNNER_PCT = 0.5      # un token "ha corso" se ha fatto almeno +50% dall'entrata ipotetica
PRELIM = 8            # da qui mostriamo numeri PRELIMINARI (con disclaimer)
READY = 25           # da qui le lezioni diventano statisticamente credibili

# feature al segnale da analizzare (nome interno -> etichetta leggibile)
FEATURES = [
    ("vol_1h", "volume 1h"),
    ("vol_24h", "volume 24h"),
    ("voliq", "volume/liquidità"),
    ("liq", "liquidità"),
    ("age_h", "età (h)"),
    ("top10_pct", "top 10 wallet"),
    ("bs_ratio_1h", "buy/sell 1h"),
    ("grok_heat", "heat di Grok"),
]


def _read_jsonl(path):
    if not os.path.exists(path):
        return []
    out = []
    for l in open(path):
        l = l.strip()
        if l:
            try:
                out.append(json.loads(l))
            except Exception:
                pass
    return out


def _median(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def _outcomes():
    """ret_max per ca dai dati del tracker (entry = prima osservazione dopo il segnale)."""
    obs = {}
    for o in _read_jsonl(TRACK):
        obs.setdefault(o.get("ca"), []).append(o)
    res = {}
    for ca, series in obs.items():
        series = sorted(series, key=lambda x: x.get("obs_ts") or 0)
        prices = [s.get("price") for s in series if s.get("price")]
        entry = series[0].get("price")
        if not entry or len(prices) < 2:
            continue   # serve almeno un secondo punto per misurare un movimento
        hours = ((series[-1].get("obs_ts") or 0) - (series[0].get("obs_ts") or 0)) / 3600
        if hours < 2:
            continue   # almeno 2h di storia
        res[ca] = {"ret_max": max(prices) / entry - 1, "hours": hours, "n_obs": len(series)}
    return res


def _signal_features():
    """condizioni AL SEGNALE per ca (primo record in candidates.jsonl)."""
    feat = {}
    for c in _read_jsonl(CANDS):
        ca = c.get("ca")
        if not ca or ca in feat:
            continue
        m = c.get("metrics", {})
        feat[ca] = {
            "vol_1h": m.get("vol_1h"), "vol_24h": m.get("vol_24h"), "voliq": m.get("voliq"),
            "liq": m.get("liq"), "age_h": m.get("age_h"), "top10_pct": m.get("top10_pct"),
            "bs_ratio_1h": m.get("bs_ratio_1h"), "grok_heat": c.get("grok_heat"),
            "ticker": c.get("ticker"), "pass": bool(c.get("pass")),
        }
    return feat


def run():
    outcomes = _outcomes()
    feats = _signal_features()
    trades = []
    for ca, o in outcomes.items():
        f = feats.get(ca)
        if not f:
            continue
        trades.append({"ca": ca, "ticker": f.get("ticker"), "pass": f.get("pass"),
                       "ret_max": o["ret_max"], "runner": o["ret_max"] >= RUNNER_PCT, "feat": f})

    settled = len(trades)
    runners = [t for t in trades if t["runner"]]
    deads = [t for t in trades if not t["runner"]]

    lessons = []
    if settled >= PRELIM and runners and deads:
        for key, label in FEATURES:
            rm = _median([t["feat"].get(key) for t in runners])
            dm = _median([t["feat"].get(key) for t in deads])
            if rm is None or dm is None:
                continue
            # quanto discrimina: rapporto tra le due mediane
            ratio = (rm / dm) if dm else None
            lessons.append({
                "feature": key, "label": label,
                "runner_median": round(rm, 3), "dead_median": round(dm, 3),
                "ratio": round(ratio, 2) if ratio else None,
            })
        # ordina per potere discriminante (mediane piu' divergenti prima)
        lessons.sort(key=lambda x: abs((x["ratio"] or 1) - 1), reverse=True)

    data = {
        "updated_utc": time.strftime("%Y-%m-%d %H:%M", time.gmtime()),
        "runner_pct": int(RUNNER_PCT * 100),
        "settled": settled, "runners": len(runners), "deads": len(deads),
        "prelim_at": PRELIM, "ready_at": READY,
        "status": "ready" if settled >= READY else ("prelim" if settled >= PRELIM else "accumulo"),
        "lessons": lessons,
        "best_runners": sorted(
            [{"ticker": t["ticker"], "ret_max": round(t["ret_max"], 2), "pass": t["pass"],
              "vol_1h": t["feat"].get("vol_1h"), "voliq": t["feat"].get("voliq")}
             for t in runners], key=lambda x: x["ret_max"], reverse=True)[:8],
    }
    with open(OUT, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    msg = {"accumulo": f"in accumulo ({settled}/{PRELIM} trade conclusi)",
           "prelim": f"PRELIMINARE ({settled} trade, {len(runners)} runner)",
           "ready": f"PRONTO ({settled} trade, {len(runners)} runner)"}[data["status"]]
    print(f"[learner] {msg} -> data/learnings.json")
    return data


if __name__ == "__main__":
    run()
