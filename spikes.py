"""
spikes.py — "Who Knows More Than Me": trova CHI muove gli spike, PRESTO.

Punto 1 della consulenza GPT: spostare il radar da "token già caldi" a "NEW POOL +
flow anomalo PRIMA del trend". Su un token già pompato catturi i polli del top (exit
liquidity); su un pool giovane catturi chi entra prima del movimento.

Per ogni big-buy calcoliamo i dati EARLY:
  - token_age_min  = quanto è giovane il token al momento dell'acquisto
  - runup_pct      = quanto è già salito il prezzo PRIMA di questo acquisto (se basso = non insegue)
  - is_early       = entrato presto, prima del trend, con size significativa

Fonte: GeckoTerminal /trades (gratis) — wallet + USD + prezzo + timestamp di ogni trade.
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
    """NEW pool prima (giovani = early), poi trending per copertura.
    Ritorna [(mint, pool_addr, name, created_ts, liquidity)]."""
    out, seen = [], set()
    for ep in ("/networks/solana/new_pools", "/networks/solana/trending_pools"):
        d = _gt(ep)
        for p in (d or {}).get("data", []):
            a = p["attributes"]
            addr = a["address"]
            if addr in seen:
                continue
            seen.add(addr)
            bt = (p.get("relationships", {}).get("base_token", {}).get("data") or {}).get("id", "")
            mint = bt.split("_", 1)[1] if "_" in bt else bt
            created = _iso_to_ts(a.get("pool_created_at"))
            try:
                liq = float(a.get("reserve_in_usd") or 0)
            except (TypeError, ValueError):
                liq = 0
            out.append((mint, addr, a["name"], created, liq))
            if len(out) >= limit:
                return out
    return out


DEX_TO_GT_NET = {"solana": "solana", "base": "base", "ethereum": "eth",
                 "bsc": "bsc", "polygon": "polygon_pos", "arbitrum": "arbitrum", "ton": "ton"}


def get_ohlcv(chain, pool_addr, aggregate_min=15, limit=120):
    """Candele OHLCV (15min) di un pool. Ritorna [(ts,open,high,low,close)] crescente, o []."""
    net = DEX_TO_GT_NET.get(chain, chain)
    d = _gt(f"/networks/{net}/pools/{pool_addr}/ohlcv/minute?aggregate={aggregate_min}&limit={limit}")
    lst = (((d or {}).get("data") or {}).get("attributes") or {}).get("ohlcv_list") or []
    out = []
    for row in lst:
        try:
            out.append((int(row[0]), float(row[1]), float(row[2]), float(row[3]), float(row[4])))
        except (TypeError, ValueError, IndexError):
            continue
    out.sort(key=lambda x: x[0])
    return out


def get_big_buys(pool_addr, created_ts, liquidity):
    """Big-buy con dati EARLY. Ritorna lista di dict {wallet, usd, ts, price, age_min, runup, is_early}."""
    d = _gt(f"/networks/solana/pools/{pool_addr}/trades")
    trades = (d or {}).get("data", [])
    # ordina per tempo crescente per calcolare il run-up PRIMA di ogni acquisto
    rows = []
    for t in trades:
        a = t["attributes"]
        ts = _iso_to_ts(a.get("block_timestamp"))
        try:
            price = float(a.get("price_to_in_usd") or 0)
        except (TypeError, ValueError):
            price = 0
        try:
            usd = float(a.get("volume_in_usd") or 0)
        except (TypeError, ValueError):
            usd = 0
        rows.append((ts or 0, a.get("kind"), price, usd, a.get("tx_from_address")))
    rows.sort(key=lambda x: x[0])

    out = []
    min_price = None
    floor = max(SPIKES["min_usd"], SPIKES["early_min_liq_ratio"] * (liquidity or 0))
    for ts, kind, price, usd, wallet in rows:
        if price > 0:
            min_price = price if min_price is None else min(min_price, price)
        if kind != "buy" or usd < SPIKES["min_usd"] or not wallet or not ts:
            continue
        runup = (price / min_price - 1) if (min_price and price > 0) else None
        age_min = ((ts - created_ts) / 60.0) if created_ts else None
        is_early = bool(
            age_min is not None and age_min <= SPIKES["early_max_age_min"]
            and (runup is None or runup <= SPIKES["early_max_runup"])
            and usd >= floor
        )
        out.append({"wallet": wallet, "usd": round(usd), "ts": ts, "price": price,
                    "age_min": round(age_min, 1) if age_min is not None else None,
                    "runup": round(runup, 3) if runup is not None else None,
                    "is_early": is_early})
    return out
