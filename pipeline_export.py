"""
pipeline_export.py — genera web/pipeline.json per la dashboard pubblica.

Traduce lo stato della PIPELINE X-FIRST (data/trends.jsonl + data/candidates.jsonl) in un
JSON che il sito mostra in modo che un umano capisca, SOLO guardando la dashboard, cosa
stiamo facendo: Grok legge X live -> trova token virali freschi -> filtriamo on-chain duro
-> teniamo solo le perle (non i rug) -> tracciamo -> calibriamo.

Free, idempotente, nessuna chiamata API: legge solo i file gia' prodotti dagli agenti.
"""
import os, json, time

HERE = os.path.dirname(os.path.abspath(__file__))
TRENDS = os.path.join(HERE, "data", "trends.jsonl")
CANDS = os.path.join(HERE, "data", "candidates.jsonl")
TRACK = os.path.join(HERE, "data", "track.jsonl")
LEARN = os.path.join(HERE, "data", "learnings.json")
OUT = os.path.join(HERE, "web", "pipeline.json")

# etichette in italiano per i motivi di scarto del filtro
FAIL_IT = {
    "no_pool": "nessun pool su DEX (token fantasma / non scambiabile)",
    "liq_bassa": "liquidità troppo bassa (esci e crolla)",
    "liq_troppo_alta": "già troppo grande (onda passata)",
    "voliq_anomalo": "rapporto volume/liquidità anomalo (volume finto o morto)",
    "vol24_basso": "volume 24h troppo basso (nessuno scambia)",
    "vol1h_basso": "volume 1h troppo basso (non scalda ora)",
    "eta_fuori": "età fuori finestra (troppo nuovo o troppo vecchio)",
    "pochi_holder": "troppo pochi holder",
    "top10_concentrato": "i primi 10 wallet tengono troppo (rug pronto)",
    "top1_balena": "un solo wallet domina (balena che ti scarica addosso)",
    "bs_ratio_basso": "più vendite che acquisti (già in distribuzione)",
    "authority_attiva": "il creatore può ancora coniare/congelare (non sicuro)",
}


def _read_jsonl(path):
    if not os.path.exists(path):
        return []
    out = []
    for l in open(path):
        l = l.strip()
        if not l:
            continue
        try:
            out.append(json.loads(l))
        except Exception:
            pass
    return out


def _clean_series(series):
    """Scarta osservazioni con prezzo glitch (outlier oltre 15x dalla mediana): dati sporchi DexScreener."""
    ps = sorted(s.get("price") for s in series if s.get("price"))
    if len(ps) < 3:
        return series
    med = ps[len(ps) // 2]
    if not med:
        return series
    cleaned = [s for s in series if not s.get("price") or (med / 15 <= s["price"] <= med * 15)]
    return cleaned or series


def build_outcomes():
    """Dalle osservazioni del tracker (track.jsonl), simula entrata/uscita per ogni token.

    Entrata ONESTA = primo prezzo osservato DOPO il segnale (non si entra prima del segnale).
    Calcola: picco, ritorno attuale, ritorno a +1h/+6h/+24h, max gain, se ha fatto 2x, se e' ruggato.
    Mostra anche le condizioni AL SEGNALE (vol_1h, eta) per imparare cosa separa i runner dai morti.
    """
    obs = _read_jsonl(TRACK)
    by_ca = {}
    for o in obs:
        by_ca.setdefault(o.get("ca"), []).append(o)

    def ret_at(series, target_min):
        """ritorno % piu' vicino a target_min minuti dall'entrata (entry = prima obs)."""
        if not series:
            return None
        entry = series[0].get("price")
        if not entry:
            return None
        best = min(series, key=lambda x: abs((x.get("age_min") or 0) - target_min))
        if abs((best.get("age_min") or 0) - target_min) > 180:   # tolleranza 3h, altrimenti non ancora
            return None
        p = best.get("price")
        return round(p / entry - 1, 3) if p else None

    out = []
    for ca, series in by_ca.items():
        series = _clean_series(sorted(series, key=lambda x: x.get("obs_ts") or 0))
        if not series:
            continue
        entry = series[0]
        last = series[-1]
        ep = entry.get("price")
        prices = [s.get("price") for s in series if s.get("price")]
        peak = max(prices) if prices else None
        ret_now = round(last["price"] / ep - 1, 3) if (ep and last.get("price")) else None
        ret_max = round(peak / ep - 1, 3) if (ep and peak) else None
        dd_from_peak = round(last["price"] / peak - 1, 3) if (peak and last.get("price")) else None
        rugged = bool(last.get("liq") is not None and entry.get("liq") and last["liq"] < entry["liq"] * 0.3)
        out.append({
            "ca": ca, "ticker": entry.get("ticker"), "pass": entry.get("pass"),
            "arena": entry.get("arena") or "memecoin", "chain": entry.get("chain"),
            "entry_fdv": entry.get("fdv"), "last_fdv": last.get("fdv"),
            "sig_vol_1h": entry.get("vol_1h"), "sig_liq": entry.get("liq"),
            "ret_now": ret_now, "ret_max": ret_max, "dd_from_peak": dd_from_peak,
            "ret_1h": ret_at(series, 60), "ret_6h": ret_at(series, 360), "ret_24h": ret_at(series, 1440),
            "hit_2x": bool(ret_max is not None and ret_max >= 1.0),
            "rugged": rugged, "n_obs": len(series),
            "hours_tracked": round(((last.get("obs_ts") or 0) - (entry.get("obs_ts") or 0)) / 3600, 1),
        })
    # ordina per miglior picco raggiunto
    out.sort(key=lambda x: (x["ret_max"] is not None, x["ret_max"] or -9), reverse=True)
    return out


def _exit_strategies(pts):
    """pts = lista (age_min, price, vol_1h) dall'ENTRATA in poi. Simula regole d'uscita.
    Le strategie SU SEGNALE (volume) sono quelle giuste per le memecoin: non stop fissi, ma
    'tieni finche' l'hype/volume regge, esci quando svanisce'. Le fisse restano per CONFRONTO.
    Ritorna (ritorno%, minuti tenuti) per ogni strategia (paper, esecuzione ideale)."""
    entry = pts[0][1]
    end_age, end_p = pts[-1][0], pts[-1][1]

    def run(tp=None, sl=None, trail=None, tmax=None):
        peak = entry
        for age, p, v in pts[1:]:
            peak = max(peak, p)
            r = p / entry - 1
            if tp is not None and r >= tp:
                return tp, age
            if sl is not None and r <= sl:
                return r, age
            if trail is not None and peak > entry and p <= peak * (1 - trail):
                return r, age
            if tmax is not None and age >= tmax:
                return r, age
        return end_p / entry - 1, end_age

    def vol_fade(frac):
        """SEGNALE: tieni finche' il volume regge, esci quando vol_1h scende sotto frac del suo picco
        (= l'hype si sta spegnendo). Niente stop fisso: si segue lo stato del mercato."""
        peak_v = pts[0][2] or 0
        for age, p, v in pts[1:]:
            peak_v = max(peak_v, v or 0)
            if peak_v > 0 and (v or 0) < peak_v * frac:
                return p / entry - 1, age
        return end_p / entry - 1, end_age

    return {
        "vol_fade50": vol_fade(0.5),           # SEGNALE: esci quando il volume dimezza dal picco
        "vol_fade30": vol_fade(0.3),           # SEGNALE: piu' paziente, esci quando volume -70%
        "hodl24": run(),                       # tieni fino a fine finestra
        "trail25": run(trail=0.25),            # trailing stop -25% (fisso, per confronto)
        "tp100_sl30": run(tp=1.0, sl=-0.3),    # +100% o stop -30% (fisso, per confronto)
        "time6h": run(tmax=360),               # esci dopo 6h
    }


STRAT_LABEL = {
    "vol_fade50": "🔊 Esci quando il volume dimezza", "vol_fade30": "🔊 Esci quando il volume cala −70%",
    "hodl24": "Tieni fino a fine (24h)", "trail25": "Trailing stop −25% (fisso)",
    "tp100_sl30": "+100% o stop −30% (fisso)", "time6h": "Esci dopo 6h",
}


def build_simulation():
    """Paper trading: entra al segnale, prova diverse uscite, dice quale rende di più e quanto tenere."""
    obs = {}
    for o in _read_jsonl(TRACK):
        obs.setdefault(o.get("ca"), []).append(o)
    agg = {k: {"rets": [], "holds": []} for k in STRAT_LABEL}
    arena_rets = {}
    pass_rets, fail_rets = [], []      # per capire se entriamo tardi (perle vs scartati con la miglior uscita)
    n = 0
    for ca, series in obs.items():
        series = _clean_series(sorted(series, key=lambda x: x.get("obs_ts") or 0))
        pts = [(s.get("age_min") or 0, s.get("price"), s.get("vol_1h")) for s in series if s.get("price")]
        if len(pts) < 2:
            continue
        n += 1
        res = _exit_strategies(pts)
        for k, (r, hold) in res.items():
            agg[k]["rets"].append(r)
            agg[k]["holds"].append(hold)
        a = (series[0].get("arena") or "memecoin")
        arena_rets.setdefault(a, []).append(res["trail25"][0])
        (pass_rets if series[0].get("pass") else fail_rets).append(res["trail25"][0])

    def med(xs):
        xs = sorted(xs)
        return xs[len(xs) // 2] if xs else None

    strategies = []
    for k, v in agg.items():
        if not v["rets"]:
            continue
        strategies.append({
            "name": k, "label": STRAT_LABEL[k],
            "median": round(med(v["rets"]), 3), "avg": round(sum(v["rets"]) / len(v["rets"]), 3),
            "win_rate": round(sum(1 for r in v["rets"] if r > 0) / len(v["rets"]), 2),
            "avg_hold_min": round(sum(v["holds"]) / len(v["holds"])),
        })
    strategies.sort(key=lambda s: s["median"], reverse=True)
    return {
        "n_trades": n,
        "strategies": strategies,
        "best": strategies[0]["name"] if strategies else None,
        "by_arena": {a: round(med(rs), 3) for a, rs in arena_rets.items()},
        "pass_median": round(med(pass_rets), 3) if pass_rets else None,
        "fail_median": round(med(fail_rets), 3) if fail_rets else None,
    }


def build():
    trends = _read_jsonl(TRENDS)
    cands = _read_jsonl(CANDS)

    # --- ultimo scan Grok ---
    last_trend = trends[-1] if trends else None
    scans = len(trends)

    # --- candidate: tieni l'ultima valutazione per ogni token (ca) ---
    by_ca = {}
    for c in cands:
        by_ca[c.get("ca")] = c           # le righe sono in ordine cronologico -> vince l'ultima
    cand_list = list(by_ca.values())
    cand_list.sort(key=lambda c: (c.get("pass") is True, c.get("ts", 0)), reverse=True)

    passed = [c for c in cand_list if c.get("pass")]
    evaluated = len(cand_list)

    def card(c):
        m = c.get("metrics", {})
        return {
            "ticker": c.get("ticker") or m.get("name") or "?",
            "ca": c.get("ca"),
            "arena": c.get("arena") or "memecoin",
            "chain": c.get("chain") or m.get("chain"),
            "pass": bool(c.get("pass")),
            "grok_heat": c.get("grok_heat"),
            "fails": [FAIL_IT.get(f, f) for f in (c.get("fails") or [])],
            "liq": m.get("liq"),
            "vol_24h": m.get("vol_24h"),
            "vol_1h": m.get("vol_1h"),
            "age_h": m.get("age_h"),
            "top10_pct": m.get("top10_pct"),
            "top1_pct": m.get("top1_pct"),
            "bs_ratio_1h": m.get("bs_ratio_1h"),
            "mint_revoked": m.get("mint_revoked"),
            "freeze_revoked": m.get("freeze_revoked"),
            "pc_24h": m.get("pc_24h"),
        }

    data = {
        "updated_utc": time.strftime("%Y-%m-%d %H:%M", time.gmtime()),
        "scans_total": scans,
        "last_scan": {
            "utc": last_trend.get("utc") if last_trend else None,
            "n_tokens": last_trend.get("n") if last_trend else 0,
            "tokens": [
                {
                    "ticker": t.get("ticker"),
                    "arena": t.get("arena") or "memecoin",
                    "chain": t.get("chain"),
                    "narrative": t.get("narrative"),
                    "callers": t.get("callers"),
                    "distinct_callers": t.get("distinct_callers"),
                    "why_now": t.get("why_now"),
                    "entry_thesis": t.get("entry_thesis"),
                    "red_flags": t.get("red_flags"),
                    "sentiment": t.get("sentiment"),
                    "momentum": t.get("momentum"),
                    "heat": t.get("heat"),
                    "confidence": t.get("confidence"),
                    "velocity": t.get("velocity"),
                    "age_hours": t.get("age_hours"),
                }
                for t in (last_trend.get("tokens", []) if last_trend else [])
            ],
        },
        "evaluated": evaluated,
        "passed_count": len(passed),
        "candidates": [card(c) for c in cand_list],
    }

    # --- esiti simulati + apprendimento (perle vs scartati) ---
    outcomes = build_outcomes()
    data["outcomes"] = outcomes
    settled = [o for o in outcomes if o["ret_max"] is not None]
    pearls = [o for o in settled if o["pass"]]
    rejects = [o for o in settled if not o["pass"]]

    def hit2x_rate(group):
        return round(sum(1 for o in group if o["hit_2x"]) / len(group), 2) if group else None

    data["learning"] = {
        "tracked_tokens": len(outcomes),
        "settled": len(settled),
        "pearls_tracked": len(pearls),
        "rejects_tracked": len(rejects),
        "pearls_2x_rate": hit2x_rate(pearls),     # quante perle hanno fatto almeno 2x
        "rejects_2x_rate": hit2x_rate(rejects),   # quanti scartati hanno fatto 2x (= filtro troppo severo?)
        "best": outcomes[0] if outcomes and outcomes[0]["ret_max"] is not None else None,
    }

    # --- confronto PER ARENA (memecoin vs ai_agent): quale rende di piu' per noi ---
    arenas = {}
    for o in outcomes:
        a = o.get("arena") or "memecoin"
        ar = arenas.setdefault(a, {"tracked": 0, "settled": 0, "runners": 0, "best_ret": None})
        ar["tracked"] += 1
        if o["ret_max"] is not None:
            ar["settled"] += 1
            if o["hit_2x"]:
                ar["runners"] += 1
            if ar["best_ret"] is None or o["ret_max"] > ar["best_ret"]:
                ar["best_ret"] = o["ret_max"]
    for a, ar in arenas.items():
        ar["runner_rate"] = round(ar["runners"] / ar["settled"], 2) if ar["settled"] else None
    data["learning"]["by_arena"] = arenas

    # quante candidate per arena (anche non ancora tracciate)
    acount = {}
    for c in cand_list:
        a = c.get("arena") or "memecoin"
        acount[a] = acount.get(a, 0) + 1
    data["arena_counts"] = acount

    # --- simulazione entrate/uscite (paper trading) ---
    data["simulation"] = build_simulation()

    # --- lezioni apprese (step 5: learner.py) ---
    if os.path.exists(LEARN):
        try:
            data["lessons"] = json.load(open(LEARN))
        except Exception:
            data["lessons"] = None
    return data


if __name__ == "__main__":
    d = build()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"[pipeline_export] scan={d['scans_total']} valutati={d['evaluated']} "
          f"PASSATI={d['passed_count']} -> web/pipeline.json")
