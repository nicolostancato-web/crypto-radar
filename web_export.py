"""
web_export.py — produce web/data.json per la dashboard.

La dashboard è statica (Vercel) e legge questo JSON. Il bot lo riscrive ad ogni giro,
così la dashboard è sempre aggiornata. Mostriamo TUTTI i candidati con score (non solo
quelli sopra soglia export): l'utente vuole VEDERE chi c'è sul radar, anche i deboli.
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import SCORING, OUTCOMES
from db import get_conn, init_db

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
OUT_PATH = os.path.join(OUT_DIR, "data.json")


def _score_10(raw):
    ref = SCORING.get("score_reference", 12.0)
    return round(min(10.0, max(0.0, (raw or 0) / ref * 10.0)), 1)


def build():
    init_db()
    now = time.time()
    with get_conn() as c:
        rows = c.execute(
            """SELECT a.ticker, a.name, a.chain, a.contract_address, a.pair_address,
                      a.discovered_at, a.discovery_source,
                      s.current_score, s.price_at_score, s.breakdown, s.updated_at,
                      b.avg_liquidity
               FROM scores s
               JOIN assets a ON a.id = s.asset_id
               LEFT JOIN baselines b ON b.asset_id = a.id
               WHERE a.status='active'
               ORDER BY s.current_score DESC
               LIMIT 60""",
        ).fetchall()

        picks = []
        for r in rows:
            bd = json.loads(r["breakdown"] or "{}")
            signals = [{"k": k, "v": round(v, 2)} for k, v in
                       sorted(bd.items(), key=lambda x: -x[1])]
            chain = r["chain"]
            ref = r["pair_address"] or r["contract_address"]
            picks.append({
                "ticker": r["ticker"] or "?",
                "name": r["name"] or "",
                "chain": chain,
                "score10": _score_10(r["current_score"]),
                "score_raw": round(r["current_score"] or 0, 2),
                "price": r["price_at_score"],
                "liquidity": round(r["avg_liquidity"]) if r["avg_liquidity"] else None,
                "age_h": round((now - r["discovered_at"]) / 3600, 1),
                "updated_min": round((now - r["updated_at"]) / 60, 1),
                "source": r["discovery_source"],
                "signals": signals,
                "above_threshold": (r["current_score"] or 0) >= SCORING["min_score_for_export"],
                "dexscreener": f"https://dexscreener.com/{chain}/{ref}" if ref else None,
                "contract": r["contract_address"],
            })

        # validazione (outcomes)
        oc = c.execute("SELECT * FROM outcomes").fetchall()
        validation = []
        for h in OUTCOMES["horizons"]:
            nets = [o[f"ret_{h}h_net"] for o in oc if o[f"ret_{h}h_net"] is not None]
            if nets:
                validation.append({
                    "horizon": f"{h}h",
                    "n": len(nets),
                    "avg_net": round(sum(nets) / len(nets), 4),
                    "win_rate": round(sum(1 for x in nets if x > 0) / len(nets), 3),
                })
            else:
                validation.append({"horizon": f"{h}h", "n": 0, "avg_net": None, "win_rate": None})

        stats = {
            "candidates": len(picks),
            "above_threshold": sum(1 for p in picks if p["above_threshold"]),
            "watching": c.execute("SELECT COUNT(*) FROM assets WHERE status='active'").fetchone()[0],
            "excluded": c.execute("SELECT COUNT(*) FROM exclusions").fetchone()[0],
            "outcomes_open": c.execute("SELECT COUNT(*) FROM outcomes WHERE status='open'").fetchone()[0],
        }

        # ripartizione per chain (per la "rotazione di chain")
        by_chain = {}
        for p in picks:
            by_chain[p["chain"]] = by_chain.get(p["chain"], 0) + 1

    # cosa sta imparando il sistema (per-segnale: netto + peso APPRESO applicato).
    try:
        from jobs.outcomes import learning_signals
        learning = learning_signals(72)
        with get_conn() as c2:
            mults = {r["signal"]: r["multiplier"] for r in
                     c2.execute("SELECT signal, multiplier FROM learned_weights").fetchall()}
        for l in learning:
            l["multiplier"] = round(mults.get(l["signal"], 1.0), 2)
    except Exception:
        learning = []

    data = {
        "updated_at": now,
        "updated_iso": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(now)),
        "threshold": SCORING["min_score_for_export"],
        "stats": stats,
        "by_chain": by_chain,
        "picks": picks,
        "validation": validation,
        "learning": learning,
    }

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[web] data.json scritto: {len(picks)} candidati")
    return OUT_PATH


if __name__ == "__main__":
    build()
