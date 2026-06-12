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
    return data


if __name__ == "__main__":
    d = build()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"[pipeline_export] scan={d['scans_total']} valutati={d['evaluated']} "
          f"PASSATI={d['passed_count']} -> web/pipeline.json")
