"""
run.py — orchestratore.

Fa girare i quattro stadi in pipeline, in loop, rispettando le frequenze.
Per sviluppo in Claude Code puoi anche lanciare ogni job a mano con --once.

  python run.py            # loop continuo (uso normale)
  python run.py --once     # un solo giro completo (utile per test)

Ordine: discovery -> enrichment -> scoring -> export.
Ogni stadio è isolato in try/except: se uno fallisce, gli altri continuano.
"""
import sys, time
from db import init_db
from jobs import discovery, enrichment, social, scoring, export_excel


def one_cycle():
    for name, fn in [
        ("discovery", discovery.discover_once),
        ("enrichment", enrichment.enrich_once),
        ("social", social.social_once),
        ("scoring", scoring.score_once),
        ("export", export_excel.export),
    ]:
        try:
            fn()
        except Exception as e:
            print(f"[run] stadio {name} fallito: {e}")


def main():
    init_db()
    if "--once" in sys.argv:
        one_cycle()
        return
    print("[run] avvio loop. Ctrl-C per fermare.")
    while True:
        one_cycle()
        time.sleep(180)  # un ciclo completo ogni 3 minuti


if __name__ == "__main__":
    main()
