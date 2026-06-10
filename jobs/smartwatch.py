"""
jobs/smartwatch.py — IL PIVOT: monitora DIRETTAMENTE i wallet smart noti (Helius).

Invece di campionare pool a caso sperando di incrociare i bravi, guardiamo cosa fanno
i ~20 wallet gia' verificati: i loro BUY alimentano i cluster (S3), i loro SELL il segnale
d'uscita (S2). Cosi' S2/S3 hanno finalmente i dati per un verdetto onesto.

CFO: ~wallets_per_cycle x recent_tx chiamate Helius/giro (free tier 1M/mese). DEXScreener gratis
per prezzo/liquidita'/pool del token. Helius assente = no-op pulito.
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from config import SMARTWATCH
from db import get_conn, init_db, record_spike_buy, record_wallet_sell
import onchain

WSOL = "So11111111111111111111111111111111111111112"
DEX = "https://api.dexscreener.com/latest/dex/tokens/"


def _dex_info(mint, cache):
    """(price_usd, liquidity_usd, pool_addr, name) del pair Solana piu' liquido. Cache per giro."""
    if mint in cache:
        return cache[mint]
    info = (None, None, None, None)
    try:
        r = requests.get(DEX + mint, timeout=10)
        if r.ok:
            pairs = [p for p in (r.json().get("pairs") or []) if p.get("chainId") == "solana"]
            if pairs:
                p = max(pairs, key=lambda x: (x.get("liquidity") or {}).get("usd") or 0)
                price = float(p["priceUsd"]) if p.get("priceUsd") else None
                liq = (p.get("liquidity") or {}).get("usd") or 0
                name = ((p.get("baseToken") or {}).get("symbol") or mint[:6])
                info = (price, liq, p.get("pairAddress"), name)
    except Exception:
        pass
    cache[mint] = info
    return info


def _smart_wallets(c, limit):
    """Wallet smart da monitorare: verificati-profittevoli + boss early ricorrenti. Rotazione casuale."""
    rows = c.execute(
        """SELECT address FROM (
               SELECT address FROM wallets WHERE verified=1 AND is_bot=0 AND pnl_sol>0
               UNION
               SELECT wallet AS address FROM spike_buys WHERE is_early=1
                      GROUP BY wallet HAVING COUNT(DISTINCT mint)>=2
           ) ORDER BY RANDOM() LIMIT ?""", (limit,)).fetchall()
    return [r[0] for r in rows]


def smartwatch_once():
    init_db()
    if not onchain.available():
        print("[smartwatch] Helius assente — skip")
        return 0
    now = time.time()
    lookback = SMARTWATCH["lookback_s"]
    cache = {}
    sol_price = _dex_info(WSOL, cache)[0] or 150.0   # SOL/USD per stimare i $
    buys_n = sells_n = 0
    with get_conn() as c:
        wallets = _smart_wallets(c, SMARTWATCH["wallets_per_cycle"])
        for w in wallets:
            for t in onchain.wallet_recent_activity(w, SMARTWATCH["recent_tx"]):
                if not t.get("ts") or t["ts"] < now - lookback:
                    continue
                usd = (t["sol"] or 0) * sol_price
                price, liq, pool, name = _dex_info(t["mint"], cache)
                if not pool:
                    continue   # senza pool non possiamo simulare l'uscita
                if t["side"] == "buy" and usd >= SMARTWATCH["min_buy_usd"]:
                    if record_spike_buy(c, w, t["mint"], name, round(usd), t["ts"],
                                        price=price, liquidity=liq, pool_addr=pool, is_early=0):
                        buys_n += 1
                elif t["side"] == "sell" and usd >= SMARTWATCH["min_sell_usd"]:
                    if record_wallet_sell(c, w, t["mint"], pool, round(usd), price, t["ts"]):
                        sells_n += 1
    print(f"[smartwatch] wallet={len(wallets)} buy_smart={buys_n} sell_smart={sells_n}")
    return buys_n + sells_n


if __name__ == "__main__":
    smartwatch_once()
