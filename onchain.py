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
