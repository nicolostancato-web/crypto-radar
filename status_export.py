"""
status_export.py — scrive web/status.json: un riassunto COMPATTO (solo numeri) dello stato
del crypto-radar, pubblicato sulla dashboard pubblica. Lo legge il bot WhatsApp ("/") per
rispondere alle domande di Nicolò sul progetto. NON espone strategia, solo metriche.
"""
import json, os, time
from db import get_conn, init_db, scenario_stats
from config import SCENARIOS


def build():
    init_db()
    out = {"updated_utc": time.strftime("%Y-%m-%d %H:%M", time.gmtime()), "scenarios": []}
    running = SCENARIOS.get("running") or [SCENARIOS.get("active", "S3_cluster")]
    with get_conn() as c:
        for name in running:
            for h in (24, 72):
                st = scenario_stats(c, name, horizon=h)
                if st["n"] > 0 or h == 24:
                    row = {"name": name, "horizon_h": h, "trades": st["n"],
                           "ev_net": st["ev_net"], "win_rate": st["win_rate"], "open": st["open"]}
                    if st.get("ev_mech") is not None:
                        row["ev_mech"] = st["ev_mech"]
                    out["scenarios"].append(row)
        def q(s):
            try: return c.execute(s).fetchone()[0]
            except Exception: return None
        out["totals"] = {
            "spike_buys": q("SELECT COUNT(*) FROM spike_buys"),
            "wallet_sells": q("SELECT COUNT(*) FROM wallet_sells"),
            "smart_wallets": q("SELECT COUNT(*) FROM wallets WHERE verified=1 AND is_bot=0 AND pnl_sol>0"),
            "best_real_copy_pnl": q("SELECT ROUND(MAX(copy_pnl),2) FROM wallets WHERE verified=1 AND closed_count>=10"),
        }
    os.makedirs("web", exist_ok=True)
    json.dump(out, open("web/status.json", "w"), indent=2)
    print(f"[status] web/status.json: {len(out['scenarios'])} scenari")
    return out


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
