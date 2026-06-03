"""
sources.py — le FONTI GRATIS del discovery.

Filosofia (CFO): non costruiamo infrastruttura, ci appoggiamo a chi raccoglie gia'
i dati e li regala. Qui raccogliamo CANDIDATI (chain + token address) da piu' fonti
gratuite e li uniamo deduplicati. Il discovery poi li filtra e li pesa.

Tutte le fonti qui sono gratuite e SENZA chiave. Nessun costo.

  - DEXScreener boosts : token "spinti"/trending (proxy di attenzione+spesa)
  - GeckoTerminal trending pools : pool di tendenza GLOBALI (tutte le chain) ->
        supporta la "rotazione di chain": seguiamo l'attenzione dove si sposta,
        non una chain fissa.
"""
from net import RateLimiter, get_json
from config import LIMITS

DEX_BASE = "https://api.dexscreener.com"
GT_BASE = "https://api.geckoterminal.com/api/v2"

# GeckoTerminal usa id-rete diversi da DEXScreener. Mappa GT -> DEXScreener chainId.
GT_TO_DEX_CHAIN = {
    "eth": "ethereum",
    "ethereum": "ethereum",
    "solana": "solana",
    "base": "base",
    "bsc": "bsc",
    "polygon_pos": "polygon",
    "arbitrum": "arbitrum",
}

_limiter = RateLimiter(LIMITS["dexscreener_max_calls_per_min"])


def _dexscreener_boosts():
    """Token boosted/trending da DEXScreener. Ritorna [(chain, token), ...]."""
    data = get_json(f"{DEX_BASE}/token-boosts/latest/v1", _limiter)
    out = []
    if not data:
        return out
    items = data if isinstance(data, list) else data.get("pairs", [])
    for it in items:
        chain = it.get("chainId")
        token = it.get("tokenAddress") or it.get("address")
        if chain and token:
            out.append((chain, token, "dexscreener_boosts"))
    return out


def _geckoterminal_trending():
    """Pool di tendenza GLOBALI (tutte le chain). Ritorna [(chain, token), ...]."""
    data = get_json(f"{GT_BASE}/networks/trending_pools?include=base_token", _limiter)
    out = []
    if not data:
        return out
    for pool in data.get("data", []):
        rel = pool.get("relationships", {})
        net = (rel.get("network", {}).get("data") or {}).get("id")
        bt_id = (rel.get("base_token", {}).get("data") or {}).get("id", "")
        # bt_id ha formato "<network>_<address>"; l'address e' dopo il primo "_"
        if "_" in bt_id:
            token = bt_id.split("_", 1)[1]
        else:
            token = bt_id
        chain = GT_TO_DEX_CHAIN.get(net, net)
        if chain and token:
            out.append((chain, token, "geckoterminal_trending"))
    return out


def get_candidates():
    """
    Unisce tutte le fonti gratis e deduplica su (chain, token).
    Ritorna lista di dict: {chain, token, source}.
    La sorgente piu' "forte" vince in caso di duplicato (trending pool > boost).
    """
    raw = _geckoterminal_trending() + _dexscreener_boosts()
    seen = {}
    for chain, token, source in raw:
        key = (chain, token.lower())
        if key not in seen:
            seen[key] = {"chain": chain, "token": token, "source": source}
    return list(seen.values())


if __name__ == "__main__":
    c = get_candidates()
    print(f"[sources] candidati totali (dedup): {len(c)}")
    from collections import Counter
    by_chain = Counter(x["chain"] for x in c)
    by_src = Counter(x["source"] for x in c)
    print(f"[sources] per chain: {dict(by_chain)}")
    print(f"[sources] per fonte: {dict(by_src)}")
    for x in c[:8]:
        print("  ", x["chain"], x["source"], x["token"][:16] + "...")
