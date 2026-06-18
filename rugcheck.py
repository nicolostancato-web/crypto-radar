"""
rugcheck.py — i predittori #1 di RUG, storicizzati (gratis, no API key).

Per ogni token Solana attivo chiama il report pubblico di RugCheck e salva i segnali che l'on-chain RPC non
da' facilmente e che sono IRRECUPERABILI (informazione del blocco 0): rischio rug, % insider/sniper (wallet
che comprano coordinati al lancio), LP lockata/bruciata, dev holdings, creator address, authority. Sono i
predittori piu' forti di sopravvivenza vs rug su memecoin — e se il token muore RugCheck smette di servirli.

Free: endpoint pubblico read, nessuna key. Rate limit conservativo (1 req/1.2s). Append-only su data/rugcheck.jsonl.
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except Exception:
    pass

import requests
import whale_flow   # riuso _active_tokens (token Solana attivi)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "rugcheck.jsonl")
API = "https://api.rugcheck.xyz/v1/tokens/%s/report"


def _report(mint):
    try:
        r = requests.get(API % mint, timeout=20, headers={"User-Agent": "crypto-radar/1.0"})
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def _extract(d):
    tok = d.get("token") or {}
    markets = d.get("markets") or []
    lp = (markets[0].get("lp") if markets else {}) or {}
    top = d.get("topHolders") or []
    insiders = d.get("insiderNetworks") or []
    insider_pct = None
    try:
        insider_pct = round(sum((n.get("activeAccounts") or 0) for n in insiders), 0) if insiders else None
    except Exception:
        insider_pct = None
    return {
        "risk_score": d.get("score_normalised") if d.get("score_normalised") is not None else d.get("score"),
        "rugged": d.get("rugged"),
        "mint_auth_active": bool(tok.get("mintAuthority")),
        "freeze_auth_active": bool(tok.get("freezeAuthority")),
        "lp_locked_pct": lp.get("lpLockedPct"),
        "creator": d.get("creator"),
        "total_holders": d.get("totalHolders"),
        "top10_pct_rc": round(sum((h.get("pct") or 0) for h in top[:10]), 2) if top else None,
        "insider_accounts": insider_pct,
        "n_risks": len(d.get("risks") or []),
    }


def _all_tokens():
    """TUTTI i token storici (per il backfill una-tantum), non solo gli attivi."""
    seen, out = set(), []
    if not os.path.exists(os.path.join(HERE, "data", "candidates.jsonl")):
        return []
    for l in open(os.path.join(HERE, "data", "candidates.jsonl")):
        try:
            c = json.loads(l)
        except Exception:
            continue
        ca = c.get("ca")
        if ca and ca not in seen and c.get("chain") in (None, "solana"):
            seen.add(ca)
            out.append({"ca": ca, "ticker": c.get("ticker")})
    return out


def run(backfill=False):
    toks = _all_tokens() if backfill else whale_flow._active_tokens()
    if not toks:
        print("[rugcheck] nessun token."); return 0
    f = open(OUT, "a")
    n = 0
    for t in toks:
        if t.get("chain") not in (None, "solana"):
            continue
        d = _report(t["ca"])
        if not d:
            continue
        row = {"ca": t["ca"], "ticker": t.get("ticker"), "obs_ts": int(time.time()), **_extract(d)}
        f.write(json.dumps(row) + "\n")
        n += 1
        print(f"   {str(t.get('ticker')):14} risk={row['risk_score']} lp_lock={row['lp_locked_pct']} "
              f"top10={row['top10_pct_rc']} mint_auth={row['mint_auth_active']} rugged={row['rugged']}")
        time.sleep(1.2)   # rate limit conservativo
    f.close()
    print(f"[rugcheck] {n} token -> data/rugcheck.jsonl")
    return n


if __name__ == "__main__":
    run(backfill=(len(sys.argv) > 1 and sys.argv[1] == "all"))
