"""
jobs/mainwallet.py — MAIN WALLET TRACKER (funding graph).

Risolve la disposabilita': i wallet di trading sono usa-e-getta, ma sono tutti finanziati
dallo stesso MAIN wallet (quello coi capitali, es. $27M). Il main NON sparisce.

  1) Dai wallet COPIABILI che troviamo -> risaliamo a CHI li ha finanziati (= candidato main).
  2) Se il main e' serio (capitale + genera piu' wallet, non un CEX) -> lo tracciamo.
  3) Ad ogni giro ricontrolliamo i main: ogni NUOVO wallet che generano = un tentacolo fresco,
     lo mettiamo in coda alla qualifica -> lo becchiamo dal minuto zero (early, non dopo).

CFO: bounded (poche risalite/controlli per giro). Senza Helius = no-op.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import MAIN
from db import (get_conn, init_db, already_traced, upsert_main, record_spawn,
                seed_wallet, get_mains_to_watch, set_main_checked)
import onchain


def _qualifies(stats):
    return stats and stats["balance_sol"] >= MAIN["min_balance_sol"] \
        and MAIN["min_funded"] <= stats["funded_count"] <= MAIN["max_funded_hub"]


def _ingest_spawns(c, main, stats):
    new = 0
    for child, (csol, cts) in stats["recipients"].items():
        if csol >= MAIN["spawn_min_sol"] and record_spawn(c, main, child, round(csol, 3), cts):
            seed_wallet(c, child)   # il tentacolo entra nella qualifica
            new += 1
    return new


def mainwallet_once():
    init_db()
    if not onchain.available():
        print("[mainwallet] Helius non configurato — no-op")
        return 0
    new_mains, new_spawns = 0, 0
    with get_conn() as c:
        # 1) RISALI ai main dai wallet copiabili non ancora tracciati
        whales = c.execute(
            "SELECT address FROM wallets WHERE verified=1 AND is_bot=0 AND copy_pnl>0").fetchall()
        traced = 0
        for w in whales:
            if traced >= MAIN["max_trace_per_cycle"]:
                break
            if already_traced(c, w["address"]):
                continue
            funder, _sol = onchain.funder_of(w["address"])
            traced += 1
            if not funder:
                continue
            stats = onchain.main_wallet_stats(funder)
            if _qualifies(stats):
                upsert_main(c, funder, stats["balance_sol"], stats["funded_count"], w["address"])
                new_spawns += _ingest_spawns(c, funder, stats)
                new_mains += 1

        # 2) RICONTROLLA i main tracciati per NUOVI spawn (tentacoli freschi)
        for main in get_mains_to_watch(c, MAIN["recheck_hours"] * 3600, MAIN["max_watch_per_cycle"]):
            stats = onchain.main_wallet_stats(main)
            if not stats:
                continue
            set_main_checked(c, main, stats["balance_sol"], stats["funded_count"])
            new_spawns += _ingest_spawns(c, main, stats)

    print(f"[mainwallet] nuovi_main={new_mains} nuovi_spawn_catturati={new_spawns}")
    return new_mains


if __name__ == "__main__":
    mainwallet_once()
