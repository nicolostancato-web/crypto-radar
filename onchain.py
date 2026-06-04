"""
onchain.py — accesso Solana on-chain via Helius (free tier).

Una sola cosa: dato un token (mint), trova CHI lo sta comprando (i wallet).
Serve a scoprire la smart money "dal basso": quando il radar entra su un token,
fotografiamo chi altro sta comprando; se il token poi pompa, quei wallet che
RICORRONO sui vincitori sono gli smart da seguire.

CFO: ~n chiamate per token (n piccolo), solo sui pochi token su cui il radar entra.
Senza chiave Helius = no-op pulito (il sistema gira lo stesso).
"""
import os
import json
import time
import urllib.request

def _key():
    return os.getenv("HELIUS_API_KEY", "")


def available():
    return bool(_key())


def _rpc(method, params, tries=2):
    url = f"https://mainnet.helius-rpc.com/?api-key={_key()}"
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
            return json.load(urllib.request.urlopen(req, timeout=25)).get("result")
        except Exception:
            time.sleep(0.4)
    return None


def recent_buyers(mint, n=50):
    """
    Ritorna i wallet che hanno COMPRATO il token nelle ultime ~n transazioni.
    Compratore = il FIRMATARIO della tx il cui saldo del token è AUMENTATO (no pool, no sell).
    Lista di (wallet, timestamp). [] se manca la chiave o nessun dato.
    """
    if not available():
        return []
    sigs = _rpc("getSignaturesForAddress", [mint, {"limit": n}])
    if not sigs:
        return []
    buyers = []
    for s in sigs:
        if s.get("err"):
            continue
        tx = _rpc("getTransaction", [s["signature"],
                  {"maxSupportedTransactionVersion": 0, "encoding": "jsonParsed"}])
        if not tx:
            continue
        meta = tx.get("meta") or {}
        keys = tx.get("transaction", {}).get("message", {}).get("accountKeys", [])
        signer = keys[0]["pubkey"] if keys and isinstance(keys[0], dict) else None
        if not signer:
            continue
        pre = {b["owner"]: (b["uiTokenAmount"]["uiAmount"] or 0)
               for b in meta.get("preTokenBalances", []) if b.get("mint") == mint and b.get("owner")}
        post = {b["owner"]: (b["uiTokenAmount"]["uiAmount"] or 0)
                for b in meta.get("postTokenBalances", []) if b.get("mint") == mint and b.get("owner")}
        delta = post.get(signer, 0) - pre.get(signer, 0)
        if delta > 0:   # il firmatario ha RICEVUTO il token => compra
            buyers.append((signer, s.get("blockTime")))
    return buyers


WSOL = "So11111111111111111111111111111111111111112"


def wallet_pnl(address, max_tx=25):
    """
    QUALIFICA un wallet: PnL realizzato (in SOL) e win-rate sui suoi swap recenti.
    Per ogni swap: il token che entra/esce + la variazione di SOL nativo del wallet.
    PnL su un token = SOL incassato (vendite) - SOL speso (acquisti). Win = token chiusi in utile.
    Proxy onesto (ignora token ancora in mano e coppie non-SOL). [] se manca la chiave.
    """
    if not available():
        return None
    sigs = _rpc("getSignaturesForAddress", [address, {"limit": max_tx}])
    if not sigs:
        return None
    per = {}
    for s in sigs:
        if s.get("err"):
            continue
        tx = _rpc("getTransaction", [s["signature"],
                  {"maxSupportedTransactionVersion": 0, "encoding": "jsonParsed"}])
        if not tx:
            continue
        meta = tx.get("meta") or {}
        keys = tx.get("transaction", {}).get("message", {}).get("accountKeys", [])
        idx = next((i for i, k in enumerate(keys)
                    if (k.get("pubkey") if isinstance(k, dict) else k) == address), None)
        if idx is None:
            continue
        pre, post = meta.get("preBalances", []), meta.get("postBalances", [])
        if idx >= len(pre) or idx >= len(post):
            continue
        sol_delta = (post[idx] - pre[idx]) / 1e9
        preT = {b["mint"]: (b["uiTokenAmount"]["uiAmount"] or 0)
                for b in meta.get("preTokenBalances", []) if b.get("owner") == address}
        postT = {b["mint"]: (b["uiTokenAmount"]["uiAmount"] or 0)
                 for b in meta.get("postTokenBalances", []) if b.get("owner") == address}
        for m in set(preT) | set(postT):
            if m == WSOL:
                continue
            d = postT.get(m, 0) - preT.get(m, 0)
            if d == 0:
                continue
            rec = per.setdefault(m, {"in": 0.0, "out": 0.0, "buys": 0, "sells": 0})
            if d > 0 and sol_delta < 0:
                rec["in"] += -sol_delta; rec["buys"] += 1
            elif d < 0 and sol_delta > 0:
                rec["out"] += sol_delta; rec["sells"] += 1
    closed = [v["out"] - v["in"] for v in per.values() if v["sells"] > 0 and v["in"] > 0]
    if not closed:
        return {"tokens": len(per), "closed": 0, "realized_sol": 0.0, "win_rate": None}
    return {"tokens": len(per), "closed": len(closed),
            "realized_sol": round(sum(closed), 3),
            "win_rate": round(sum(1 for x in closed if x > 0) / len(closed), 2)}


def wallet_deep(address, max_tx=200):
    """
    ANALISI PROFONDA di un wallet: track record vero su molte tx.
    Ritorna PnL realizzato totale, win-rate, n. posizioni, frequenza (per rilevare i BOT),
    e i MINT VINCENTI (per lo snowball: chi altro li ha comprati = la rete).
    None se manca la chiave.
    """
    if not available():
        return None
    sigs = _rpc("getSignaturesForAddress", [address, {"limit": min(max_tx, 1000)}])
    if not sigs:
        return None
    per = {}
    times = []
    for s in sigs:
        if s.get("err"):
            continue
        if s.get("blockTime"):
            times.append(s["blockTime"])
        tx = _rpc("getTransaction", [s["signature"],
                  {"maxSupportedTransactionVersion": 0, "encoding": "jsonParsed"}])
        if not tx:
            continue
        meta = tx.get("meta") or {}
        keys = tx.get("transaction", {}).get("message", {}).get("accountKeys", [])
        idx = next((i for i, k in enumerate(keys)
                    if (k.get("pubkey") if isinstance(k, dict) else k) == address), None)
        if idx is None or idx >= len(meta.get("preBalances", [])):
            continue
        sol = (meta["postBalances"][idx] - meta["preBalances"][idx]) / 1e9
        preT = {b["mint"]: (b["uiTokenAmount"]["uiAmount"] or 0)
                for b in meta.get("preTokenBalances", []) if b.get("owner") == address}
        postT = {b["mint"]: (b["uiTokenAmount"]["uiAmount"] or 0)
                 for b in meta.get("postTokenBalances", []) if b.get("owner") == address}
        for m in set(preT) | set(postT):
            if m == WSOL:
                continue
            d = postT.get(m, 0) - preT.get(m, 0)
            if d == 0:
                continue
            r = per.setdefault(m, {"in": 0.0, "out": 0.0, "sells": 0})
            if d > 0 and sol < 0:
                r["in"] += -sol
            elif d < 0 and sol > 0:
                r["out"] += sol; r["sells"] += 1
    closed = [(m, v["out"] - v["in"]) for m, v in per.items() if v["sells"] > 0 and v["in"] > 0]
    pnls = [x[1] for x in closed]
    span_days = ((max(times) - min(times)) / 86400.0) if len(times) >= 2 else 0.0
    txc = len(sigs)
    tx_per_day = txc / span_days if span_days > 0.05 else float(txc)
    top_wins = sorted([c for c in closed if c[1] > 0], key=lambda x: -x[1])[:5]
    return {
        "realized_sol": round(sum(pnls), 3) if pnls else 0.0,
        "win_rate": round(sum(1 for x in pnls if x > 0) / len(pnls), 2) if pnls else None,
        "closed": len(pnls),
        "tokens": len(per),
        "tx_count": txc,
        "span_days": round(span_days, 2),
        "tx_per_day": round(tx_per_day, 1),
        "top_wins": [m for m, _ in top_wins],   # mint dei vincenti, per lo snowball
    }


if __name__ == "__main__":
    if not available():
        print("[onchain] HELIUS_API_KEY assente — no-op. Vedi SETUP.md.")
    else:
        import sys
        mint = sys.argv[1] if len(sys.argv) > 1 else None
        if mint:
            b = recent_buyers(mint, 30)
            print(f"[onchain] compratori recenti: {len(b)}")
            for w, ts in b[:15]:
                print(" ", time.strftime("%m-%d %H:%M", time.gmtime(ts or 0)), w)
