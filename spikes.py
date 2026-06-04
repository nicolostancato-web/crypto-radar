"""
spikes.py — "Who Knows More Than Me": trova CHI muove gli spike.

Fonte: GeckoTerminal trades (gratis) — ci dà wallet + size USD + timestamp di ogni trade.
Per ogni pool Solana di tendenza/nuovo, estraiamo i BIG-BUY (>= soglia): sono gli spike,
i wallet che mettono $$ grossi e muovono il mercato. Chi ricorre su piu' vincitori = boss.

Nessun muro di paginazione blockchain: GeckoTerminal ha gia' i trade con l'indirizzo.
"""
import time
import requests
from config import SPIKES

GT = "https://api.geckoterminal.com/api/v2"
UA = {"User-Agent": "crypto-radar (research; paper-trading)", "Accept": "application/json"}


def _gt(path):
    for _ in range(2):
        try:
            r = requests.get(f"{GT}{path}", headers=UA, timeout=15)
            if r.ok:
                return r.json()
        except requests.RequestException:
            pass
        time.sleep(1)
    return None


def _iso_to_ts(s):
    try:
        return time.mktime(time.strptime(s, "%Y-%m-%dT%H:%M:%SZ"))
    except (TypeError, ValueError):
        return None


def get_solana_pools(limit):
    """Pool Solana con volume (candidati vincitori): trending + nuovi. Ritorna [(mint, pool_addr, name)]."""
    out, seen = [], set()
    for ep in ("/networks/solana/trending_pools", "/networks/solana/new_pools"):
        d = _gt(ep)
        for p in (d or {}).get("data", []):
            addr = p["attributes"]["address"]
            if addr in seen:
                continue
            seen.add(addr)
            bt = (p.get("relationships", {}).get("base_token", {}).get("data") or {}).get("id", "")
            mint = bt.split("_", 1)[1] if "_" in bt else bt
            out.append((mint, addr, p["attributes"]["name"]))
            if len(out) >= limit:
                return out
    return out


def get_big_buys(pool_addr):
    """Big-buy (>= soglia USD) su un pool. Ritorna [(wallet, usd, ts)]."""
    d = _gt(f"/networks/solana/pools/{pool_addr}/trades")
    out = []
    for t in (d or {}).get("data", []):
        a = t["attributes"]
        if a.get("kind") != "buy":
            continue
        try:
            usd = float(a.get("volume_in_usd") or 0)
        except (TypeError, ValueError):
            usd = 0
        if usd >= SPIKES["min_usd"]:
            w = a.get("tx_from_address")
            ts = _iso_to_ts(a.get("block_timestamp"))
            if w and ts:
                out.append((w, round(usd), ts))
    return out
