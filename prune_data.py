"""
prune_data.py — AUTO-PRUNE: tiene i file dati sotto il limite GitHub (100MB), da solo, ad ogni ciclo.

Perche' esiste: il 2026-07-02 track.jsonl ha superato 100MB -> GitHub ha RIFIUTATO tutti i push -> la
raccolta dati si e' bloccata per 14h senza che nessuno se ne accorgesse. MAI PIU'. Questo gira nella
pipeline PRIMA del commit e garantisce che i file restino piccoli.

Strategia (append-only ma potato):
- track.jsonl: per i token CHIUSI (fuori finestra) tiene solo prima+picco+ultima osservazione (basta per
  l'outcome ret_max); per gli ATTIVI tiene tutto. Backup gzip locale (gitignored) prima di potare.
- ohlcv.jsonl: tiene le candele solo dei token ancora ATTIVI o recenti.
Soglia di intervento: potiamo solo se il file supera SOFT_MB (cosi' non lavora a vuoto ogni giro).
"""
import os, json, time, gzip
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SOFT_MB = 70          # sopra questa taglia, pota (margine sotto i 100MB di GitHub)
GREEN, RED = 120 * 3600, 96 * 3600


def _mb(path):
    return os.path.getsize(path) / 1e6 if os.path.exists(path) else 0


def _active_cas():
    """token ancora dentro la finestra di tracking (da candidates: signal_ts + pass)."""
    now = time.time(); active = set()
    p = os.path.join(HERE, "data", "candidates.jsonl")
    if not os.path.exists(p):
        return active
    seen = {}
    for l in open(p):
        try:
            c = json.loads(l); ca = c.get("ca"); sig = c.get("signal_ts") or c.get("ts")
            if ca and sig and ca not in seen:
                seen[ca] = (sig, bool(c.get("pass")))
        except Exception:
            pass
    for ca, (sig, passed) in seen.items():
        if now - sig <= (GREEN if passed else RED):
            active.add(ca)
    return active


def prune_track():
    p = os.path.join(HERE, "data", "track.jsonl")
    if _mb(p) < SOFT_MB:
        return f"track.jsonl {_mb(p):.0f}MB (ok, no prune)"
    with open(os.path.join(HERE, "data", "track_full_archive.jsonl.gz"), "ab") as g:
        pass  # l'archivio completo si accumula altrove; qui backup dello stato attuale
    gzip.open(os.path.join(HERE, "data", "track_prune_backup.jsonl.gz"), "wt").writelines(open(p))
    now = time.time(); by = defaultdict(list)
    for l in open(p):
        try:
            o = json.loads(l); by[o["ca"]].append(o)
        except Exception:
            pass
    keep = []
    for ca, rows in by.items():
        rows.sort(key=lambda x: x["obs_ts"])
        sig = rows[0].get("signal_ts") or rows[0]["obs_ts"]
        window = GREEN if rows[0].get("pass") else RED
        if (now - sig) > window and len(rows) > 3:
            prices = [(r.get("price") or 0) for r in rows]; mi = prices.index(max(prices))
            for i in sorted(set([0, mi, len(rows) - 1])):
                keep.append(rows[i])
        else:
            keep.extend(rows)
    keep.sort(key=lambda x: x["obs_ts"])
    with open(p, "w") as f:
        for r in keep:
            f.write(json.dumps(r) + "\n")
    return f"track.jsonl POTATO: {sum(len(v) for v in by.values())}->{len(keep)} righe, ora {_mb(p):.0f}MB"


def prune_ohlcv():
    p = os.path.join(HERE, "data", "ohlcv.jsonl")
    if _mb(p) < SOFT_MB:
        return f"ohlcv.jsonl {_mb(p):.0f}MB (ok)"
    active = _active_cas()
    gzip.open(os.path.join(HERE, "data", "ohlcv_prune_backup.jsonl.gz"), "wt").writelines(open(p))
    kept = 0; lines = []
    for l in open(p):
        try:
            if json.loads(l).get("ca") in active:
                lines.append(l); kept += 1
        except Exception:
            pass
    with open(p, "w") as f:
        f.writelines(lines)
    return f"ohlcv.jsonl POTATO: solo token attivi, {kept} righe, ora {_mb(p):.0f}MB"


def run():
    msgs = [prune_track(), prune_ohlcv()]
    for m in msgs:
        print("[prune]", m)
    return msgs


if __name__ == "__main__":
    run()
