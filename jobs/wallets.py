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
                set_wallet_score, wallets_to_qualify, set_wallet_pnl)
import onchain


def _qualify_batch(c):
    """Qualifica (PnL reale via Helius) un lotto di wallet NON ancora qualificati. Bounded + cache."""
    addrs = wallets_to_qualify(c, WALLETS["requalify_days"] * 86400, WALLETS["max_qualify_per_cycle"])
    done = 0
    for a in addrs:
        p = onchain.wallet_pnl(a, WALLETS["qualify_tx"])
        if p is None:
            continue
        set_wallet_pnl(c, a, p["realized_sol"], p["win_rate"], p["closed"])
        done += 1
    return done


def _smart_score(c):
    """smart_score = PnL reale x win-rate x credibilità + bonus ricorrenza sui nostri token."""
    scored = 0
    for w in c.execute("SELECT address, pnl_sol, win_rate, closed_count, buys_count FROM wallets").fetchall():
        buys = w["buys_count"] or 0
        pnl, win, closed = w["pnl_sol"], w["win_rate"], w["closed_count"] or 0
        if pnl is not None and closed >= WALLETS["min_closed_for_proven"]:
            cred = min(closed / 3.0, 1.0)
            score = round(pnl * (win or 0) * cred + 0.1 * buys, 3)
        else:
            score = round(0.05 * buys, 3)   # solo un filo di ricorrenza finché non è qualificato
        set_wallet_score(c, w["address"], score, win)
        if score > 0:
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
        qualified = _qualify_batch(c)   # accumulo qualificato, bounded
        scored = _smart_score(c)
    print(f"[wallets] fotografati={captured} qualificati={qualified} con_score={scored}")
    return captured


if __name__ == "__main__":
    capture_once()
