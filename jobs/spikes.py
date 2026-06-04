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
    new_events, seeded, coordinated = 0, 0, 0
    with get_conn() as c:
        for mint, addr, name in pools:
            for wallet, usd, ts in spikes.get_big_buys(addr):
                if record_spike_buy(c, wallet, mint, name, usd, ts):
                    new_events += 1
                    seed_wallet(c, wallet)   # il boss entra nella qualifica PnL
                    seeded += 1
            # coordinazione: piu' wallet sullo stesso token nella stessa finestra?
            if mint:
                recent = c.execute(
                    "SELECT bought_at FROM spike_buys WHERE mint=? ORDER BY bought_at DESC LIMIT 1",
                    (mint,)).fetchone()
                if recent and coordination_count(c, mint, recent[0], SPIKES["coordination_window_s"]) >= 3:
                    coordinated += 1
    print(f"[spikes] pool={len(pools)} big_buy_nuovi={new_events} wallet_nuovi={seeded} "
          f"token_coordinati={coordinated}")
    return new_events


if __name__ == "__main__":
    spikes_once()
