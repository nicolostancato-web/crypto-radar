"""
jobs/wallets.py — scoperta SMART MONEY dal basso.

Quando il radar ENTRA su un token (apre un outcome), fotografiamo chi altro lo sta
comprando in quel momento (onchain.recent_buyers via Helius). Li accumuliamo. Su TANTI
token, i wallet che RICORRONO sui token che poi PERFORMANO prendono smart_score alto:
sono la smart money da seguire (i loro buy = entrata, i loro sell = uscita).

CFO: solo token Solana, solo quelli su cui entriamo, tetto max_capture_per_cycle.
Senza chiave Helius = no-op (il sistema gira lo stesso).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import WALLETS
from db import (get_conn, init_db, asset_has_wallet_capture, record_wallet_buy,
                set_wallet_score)
import onchain


def _score_wallets(c):
    """smart_score = rendimento netto medio dei suoi token x ricorrenza. Solo con dati."""
    scored = 0
    for w in c.execute("SELECT address FROM wallets").fetchall():
        nets = [r[0] for r in c.execute(
            """SELECT o.ret_72h_net FROM wallet_buys wb
               JOIN outcomes o ON o.asset_id = wb.asset_id
               WHERE wb.address=? AND o.ret_72h_net IS NOT NULL""", (w["address"],)).fetchall()]
        if len(nets) >= WALLETS["min_buys_for_smart"]:
            avg = sum(nets) / len(nets)
            set_wallet_score(c, w["address"], round(avg * len(nets), 4), round(avg, 4))
            scored += 1
    return scored


def capture_once():
    init_db()
    if not onchain.available():
        print("[wallets] Helius non configurato — no-op")
        return 0
    captured = 0
    with get_conn() as c:
        rows = c.execute(
            """SELECT o.asset_id, o.contract_address, o.ticker
               FROM outcomes o JOIN assets a ON a.id = o.asset_id
               WHERE o.status='open' AND a.chain='solana'
               ORDER BY o.entered_at DESC""").fetchall()
        todo = [r for r in rows if not asset_has_wallet_capture(c, r["asset_id"])][:WALLETS["max_capture_per_cycle"]]
        for r in todo:
            buyers = onchain.recent_buyers(r["contract_address"], WALLETS["capture_recent_n"])
            for w, ts in buyers:
                record_wallet_buy(c, w, r["asset_id"], r["contract_address"], r["ticker"], ts)
            if buyers:
                captured += 1
        scored = _score_wallets(c)
    print(f"[wallets] token fotografati={captured} wallet_smart_valutati={scored}")
    return captured


if __name__ == "__main__":
    capture_once()
