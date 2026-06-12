"""
filter_tokens.py — PIPELINE X-FIRST, step 2: il FILTRO.

Prende i token che Grok ha flaggato su X (data/trends.jsonl), e per ognuno con contract address
scarica DexScreener (liquidita', volume, eta', txns) + Helius (holders, concentrazione, authority),
e applica i filtri FORTI (config.FILTER) per scartare rug/dud e tenere solo le perle vere.

Output: data/candidates.jsonl — 1 riga per token valutato (con metriche, pass/fail, motivi).
Quelle che PASSANO sono le "entrate ipotetiche" da tracciare (step 4) e su cui calibrare (step 5).

Free: DexScreener (no key) + Helius (1M/mese). Idempotente: dedup per (ca, snapshot_ts).
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except Exception:
    pass

import requests
from config import FILTER
import onchain

TRENDS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "trends.jsonl")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "candidates.jsonl")


def _dex(ca):
    """Metriche DexScreener del pair piu' liquido (Solana o Base) per un contract address."""
    try:
        r = requests.get("https://api.dexscreener.com/latest/dex/tokens/" + ca, timeout=10)
        pairs = [p for p in (r.json().get("pairs") or []) if p.get("chainId") in ("solana", "base")]
        if not pairs:
            return None
        p = max(pairs, key=lambda x: (x.get("liquidity") or {}).get("usd") or 0)
        tx1 = (p.get("txns") or {}).get("h1") or {}
        return {
            "name": (p.get("baseToken") or {}).get("symbol"),
            "chain": p.get("chainId"),
            "liq": (p.get("liquidity") or {}).get("usd") or 0,
            "vol_24h": (p.get("volume") or {}).get("h24") or 0,
            "vol_1h": (p.get("volume") or {}).get("h1") or 0,
            "pc_24h": (p.get("priceChange") or {}).get("h24"),
            "buys_1h": tx1.get("buys") or 0, "sells_1h": tx1.get("sells") or 0,
            "fdv": p.get("fdv"), "venue": p.get("dexId"),
            "created_ms": p.get("pairCreatedAt"),
        }
    except Exception:
        return None


def evaluate(ca):
    """Valuta un token contro i filtri. Ritorna dict con metriche + pass + motivi del fallimento."""
    d = _dex(ca)
    if not d:
        return {"pass": False, "fails": ["no_pool"], "metrics": {}}
    # i check di sicurezza Helius (concentrazione/authority) sono Solana-only; su Base si saltano
    s = (onchain.token_safety(ca) or {}) if d.get("chain") == "solana" else {}
    now = time.time()
    age_h = ((now - d["created_ms"] / 1000) / 3600) if d.get("created_ms") else None
    voliq = (d["vol_24h"] / d["liq"]) if d["liq"] else None
    bs1 = (d["buys_1h"] / d["sells_1h"]) if d["sells_1h"] else (d["buys_1h"] or 0)
    m = {"name": d["name"], "liq": round(d["liq"]), "vol_24h": round(d["vol_24h"]),
         "vol_1h": round(d["vol_1h"]), "voliq": round(voliq, 2) if voliq else None,
         "age_h": round(age_h, 1) if age_h is not None else None, "bs_ratio_1h": round(bs1, 2),
         "holders": s.get("holders"), "top10_pct": s.get("top10_pct"), "top1_pct": s.get("top1_pct"),
         "mint_revoked": s.get("mint_revoked"), "freeze_revoked": s.get("freeze_revoked"),
         "fdv": d.get("fdv"), "venue": d.get("venue"), "pc_24h": d.get("pc_24h"), "chain": d.get("chain")}

    f = FILTER
    fails = []
    if d["liq"] < f["min_liquidity"]: fails.append("liq_bassa")
    if d["liq"] > f["max_liquidity"]: fails.append("liq_troppo_alta")
    if voliq is not None and (voliq < f["voliq_min"] or voliq > f["voliq_max"]): fails.append("voliq_anomalo")
    if d["vol_24h"] < f["min_vol_24h"]: fails.append("vol24_basso")
    if d["vol_1h"] < f["min_vol_1h"]: fails.append("vol1h_basso")
    if age_h is not None and (age_h < f["age_min_hours"] or age_h > f["age_max_hours"]): fails.append("eta_fuori")
    if s.get("holders") is not None and s["holders"] < f["min_holders"]: fails.append("pochi_holder")
    if s.get("top10_pct") is not None and s["top10_pct"] > f["max_top10_pct"]: fails.append("top10_concentrato")
    if s.get("top1_pct") is not None and s["top1_pct"] > f["max_top1_pct"]: fails.append("top1_balena")
    if bs1 < f["min_bs_ratio_1h"]: fails.append("bs_ratio_basso")
    # authority verificabile solo su Solana (Helius); su Base (s vuoto) il check si salta
    if f["require_authority_revoked"] and s and not (s.get("mint_revoked") and s.get("freeze_revoked")):
        fails.append("authority_attiva")
    return {"pass": len(fails) == 0, "fails": fails, "metrics": m}


def run(lookback_snapshots=2):
    if not os.path.exists(TRENDS):
        print("[filter] niente trends.jsonl — prima gira l'agente trend"); return
    rows = [json.loads(l) for l in open(TRENDS)][-lookback_snapshots:]
    seen = set()
    if os.path.exists(OUT):
        for l in open(OUT):
            try:
                r = json.loads(l); seen.add((r["ca"], r["snapshot_ts"]))
            except Exception:
                pass
    onchain_ok = onchain.available()
    f = open(OUT, "a")
    passed = evaluated = 0
    for snap in rows:
        for t in snap.get("tokens", []):
            ca = (t.get("ca") or "").split("|")[0].strip()
            if not ca or len(ca) < 30:
                continue
            key = (ca, snap["ts"])
            if key in seen:
                continue
            seen.add(key)
            res = evaluate(ca)
            evaluated += 1
            row = {"ts": int(time.time()), "snapshot_ts": snap["ts"], "ticker": t.get("ticker"),
                   "ca": ca, "arena": t.get("arena") or "memecoin",
                   "chain": t.get("chain") or res["metrics"].get("chain"),
                   "grok_heat": t.get("heat"), "grok_velocity": t.get("velocity"),
                   "pass": res["pass"], "fails": res["fails"], "metrics": res["metrics"]}
            f.write(json.dumps(row) + "\n")
            mark = "✅ PASSA" if res["pass"] else "❌ " + ",".join(res["fails"][:3])
            print(f"  {str(t.get('ticker')):14} {mark}  liq=${res['metrics'].get('liq','?')} "
                  f"vol1h=${res['metrics'].get('vol_1h','?')} age={res['metrics'].get('age_h','?')}h "
                  f"top10={res['metrics'].get('top10_pct','?')}")
            if res["pass"]:
                passed += 1
    f.close()
    print(f"\n[filter] valutati={evaluated} PASSATI={passed} (le perle vere) -> data/candidates.jsonl")
    if not onchain_ok:
        print("[filter] NB: Helius assente -> holders/authority non valutati")
    return passed


if __name__ == "__main__":
    run(lookback_snapshots=int(sys.argv[1]) if len(sys.argv) > 1 else 3)
