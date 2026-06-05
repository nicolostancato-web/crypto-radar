"""
jobs/spikes.py — accumulo "Who Knows More Than Me".

Ogni giro: pesca i pool Solana con volume, estrae i BIG-BUY (gli spike), li registra.
I wallet che fanno big-buy entrano anche nella pipeline di qualifica (deep-dive PnL):
cosi' un boss e' un wallet che (a) muove spike su piu' vincitori E (b) guadagna davvero.

Gratis (GeckoTerminal). Bounded dal rate limit.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SPIKES
from db import get_conn, init_db, record_spike_buy, seed_wallet, coordination_count
import spikes


def spikes_once():
    init_db()
    pools = spikes.get_solana_pools(SPIKES["max_pools_per_cycle"])
    new_events, seeded, early_n = 0, 0, 0
    with get_conn() as c:
        for mint, addr, name, created, liq in pools:
            for b in spikes.get_big_buys(addr, created, liq):
                if record_spike_buy(c, b["wallet"], mint, name, b["usd"], b["ts"],
                                    price=b["price"], token_age_min=b["age_min"],
                                    runup_pct=b["runup"], liquidity=liq, is_early=b["is_early"]):
                    new_events += 1
                    if b["is_early"]:
                        early_n += 1
                        seed_wallet(c, b["wallet"])   # solo gli EARLY entrano nella qualifica (non i polli)
                        seeded += 1
    print(f"[spikes] pool={len(pools)} big_buy_nuovi={new_events} EARLY={early_n} wallet_nuovi={seeded}")
    return new_events


if __name__ == "__main__":
    spikes_once()
