"""
analyze.py — L'AGENTE ANALISTA. Studia il dataset e produce un REPORT con l'edge (se c'e').

Non traccia wallet: cerca il SETUP. Segmenta gli eventi storici per combinazioni di fattori
(qualita' wallet, eta' token, coordinazione, ingresso flat/fomo, liquidita', size) e per ogni
segmento calcola: n, mediana copy_net, win-rate, batte-il-hold. Un segmento con mediana >+5% che
batte il hold su >=20 casi = EDGE CANDIDATO. Robusto ai dati mancanti e al dataset che cresce.

Output: stampa + data/analysis_report.md (committabile su GitHub). Free, nessuna API (legge il file).
"""
import sys, os, json, statistics

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "dataset.jsonl")
REPORT = os.path.join(ROOT, "data", "analysis_report.md")
MIN_N = 20            # sotto questo, un segmento e' rumore
EDGE_MEDIAN = 0.05    # mediana copy_net per essere "edge"


def _load():
    rows = []
    if os.path.exists(DATA):
        for line in open(DATA):
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def _g(r, k):
    v = r.get(k)
    return v if isinstance(v, (int, float)) else None


def _stats(rows):
    nets = [r["copy_net"] for r in rows if isinstance(r.get("copy_net"), (int, float))]
    holds = [r["hold_net"] for r in rows if isinstance(r.get("hold_net"), (int, float))]
    if not nets:
        return None
    med = statistics.median(nets)
    medh = statistics.median(holds) if holds else None
    return {
        "n": len(nets),
        "median": med,
        "mean": statistics.mean(nets),
        "win": sum(1 for x in nets if x > 0) / len(nets),
        "hold_median": medh,
        "beats_hold": (med > medh) if medh is not None else None,
    }


# SEGMENTI = combinazioni di fattori da testare (dal FEATURES_PLAN). (nome, filtro)
SEGMENTS = [
    ("TUTTO (baseline)", lambda r: True),
    ("wallet provato (closed>=10)", lambda r: (_g(r, "w_closed") or 0) >= 10),
    ("wallet winrate>=60%", lambda r: (_g(r, "w_winrate") or 0) >= 0.6),
    ("ingresso FLAT (runup<10%)", lambda r: (_g(r, "runup_before") is not None and r["runup_before"] < 0.10)),
    ("coordinato (>=1 altro smart 1h)", lambda r: (_g(r, "smart_coord_1h") or 0) >= 1),
    ("coordinato forte (>=2)", lambda r: (_g(r, "smart_coord_1h") or 0) >= 2),
    ("liquidita' 20k-200k", lambda r: (_g(r, "liquidity") or 0) >= 20000 and (_g(r, "liquidity") or 0) <= 200000),
    ("buy grosso (>=$1000)", lambda r: (_g(r, "buy_usd") or 0) >= 1000),
    ("token early (<60min)", lambda r: (_g(r, "token_age_min") is not None and r["token_age_min"] < 60)),
    ("pressione buy (bs_ratio>1.5)", lambda r: (_g(r, "txn_bs_ratio_1h") or 0) > 1.5),
    # COMBINAZIONI (qui si nasconde l'edge)
    ("provato + FLAT", lambda r: (_g(r, "w_closed") or 0) >= 10 and (_g(r, "runup_before") is not None and r["runup_before"] < 0.10)),
    ("provato + coordinato", lambda r: (_g(r, "w_closed") or 0) >= 10 and (_g(r, "smart_coord_1h") or 0) >= 1),
    ("FLAT + coordinato", lambda r: (_g(r, "runup_before") is not None and r["runup_before"] < 0.10) and (_g(r, "smart_coord_1h") or 0) >= 1),
    ("winrate>=60% + FLAT", lambda r: (_g(r, "w_winrate") or 0) >= 0.6 and (_g(r, "runup_before") is not None and r["runup_before"] < 0.10)),
]


def analyze():
    rows = _load()
    lines = [f"# Analisi dataset — {len(rows)} eventi\n"]
    print(f"[analyze] {len(rows)} eventi nel dataset")
    if len(rows) < MIN_N:
        msg = f"Solo {len(rows)} eventi: troppo pochi per concludere (servono migliaia). Continua ad accumulare."
        print("[analyze]", msg); lines.append(f"> {msg}\n")
        open(REPORT, "w").write("\n".join(lines)); return

    results = []
    for name, f in SEGMENTS:
        seg = [r for r in rows if f(r)]
        st = _stats(seg)
        if st and st["n"] >= MIN_N:
            results.append((name, st))
    results.sort(key=lambda x: -(x[1]["median"]))

    lines.append("| Segmento | n | mediana copy | win | hold | batte hold? | EDGE? |")
    lines.append("|---|---|---|---|---|---|---|")
    edges = []
    for name, st in results:
        edge = st["median"] >= EDGE_MEDIAN and st["beats_hold"]
        if edge:
            edges.append((name, st))
        hold = f"{st['hold_median']:+.1%}" if st["hold_median"] is not None else "—"
        lines.append(f"| {name} | {st['n']} | **{st['median']:+.1%}** | {st['win']:.0%} | {hold} | "
                     f"{'SI' if st['beats_hold'] else 'no'} | {'🟢 SI' if edge else ''} |")

    lines.append("")
    if edges:
        lines.append(f"## 🟢 EDGE CANDIDATI ({len(edges)})")
        for name, st in edges:
            lines.append(f"- **{name}**: mediana {st['median']:+.1%} su {st['n']} eventi, batte il hold. → da validare con piu' dati.")
    else:
        lines.append("## ❌ Nessun edge ancora")
        best = results[0] if results else None
        if best:
            lines.append(f"Miglior segmento: **{best[0]}** (mediana {best[1]['median']:+.1%}) — ma sotto soglia o non batte il hold.")
        lines.append("Servono piu' dati / piu' feature (token_age, holders, authority) per segmenti piu' fini.")

    out = "\n".join(lines)
    open(REPORT, "w").write(out)
    print("\n" + out)
    print(f"\n[analyze] report -> {REPORT}")


if __name__ == "__main__":
    analyze()
