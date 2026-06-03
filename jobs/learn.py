"""
jobs/learn.py — il MOTORE DI AUTO-MIGLIORAMENTO.

Chiude il cerchio: esiti reali -> ri-tara i pesi dei segnali -> lo scoring migliora.

Per ogni segnale guarda il rendimento NETTO medio delle entrate in cui era acceso e
sposta il suo moltiplicatore verso un target dato dai dati. Segnali che hanno portato
a guadagni salgono; quelli che hanno portato a ZERO scendono.

I FRENI (perché un senior non fa overfitting):
  - tocca un segnale SOLO con >= min_samples esiti (sotto = rumore, si lascia a 1.0);
  - si muove a piccoli passi (step), non salta;
  - resta dentro [floor, cap]: niente pesi azzerati o esplosi.

Idempotente: rigirarlo sugli stessi dati converge al target, poi si ferma.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import LEARN
from db import get_conn, init_db, set_learned_weight


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def calibrate_once():
    init_db()
    h = LEARN["horizon"]
    col = f"ret_{h}h_net"
    changes = []
    with get_conn() as c:
        rows = c.execute(
            f"SELECT signals_at_entry, {col} AS ret FROM outcomes WHERE {col} IS NOT NULL"
        ).fetchall()

        agg = {}
        for r in rows:
            try:
                sigs = json.loads(r["signals_at_entry"] or "{}")
            except (TypeError, ValueError):
                sigs = {}
            for k in sigs:
                agg.setdefault(k, []).append(r["ret"])

        current = {r["signal"]: r["multiplier"]
                   for r in c.execute("SELECT signal, multiplier FROM learned_weights").fetchall()}

        for signal, nets in agg.items():
            n = len(nets)
            if n < LEARN["min_samples"]:
                continue  # FRENO: pochi dati -> non si tocca
            avg = sum(nets) / n
            target = _clamp(1 + LEARN["k"] * avg, LEARN["floor"], LEARN["cap"])
            cur = current.get(signal, 1.0)
            new = cur + LEARN["step"] * (target - cur)   # passo graduale
            new = round(_clamp(new, LEARN["floor"], LEARN["cap"]), 3)
            if abs(new - cur) >= 0.001:
                set_learned_weight(c, signal, new, n, round(avg, 4))
                changes.append((signal, round(cur, 3), new, n, round(avg, 4)))

    if changes:
        print("[learn] pesi ritarati sugli esiti:")
        for s, old, new, n, avg in changes:
            print(f"  {s:22} {old} -> {new}  (n={n}, netto medio {avg:+.2%})")
    else:
        with get_conn() as c2:
            ready = c2.execute(f"SELECT COUNT(*) FROM outcomes WHERE {col} IS NOT NULL").fetchone()[0]
        print(f"[learn] nessuna modifica: servono >= {LEARN['min_samples']} esiti per segnale "
              f"(esiti maturi totali finora: {ready})")
    return len(changes)


if __name__ == "__main__":
    calibrate_once()
