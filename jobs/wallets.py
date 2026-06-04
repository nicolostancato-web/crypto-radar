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

import json
from config import WALLETS
from db import (get_conn, init_db, asset_has_wallet_capture, record_wallet_buy,
                set_wallet_score, wallets_to_qualify, set_wallet_pnl,
                wallets_to_deepdive, set_wallet_deep, whales_to_snowball,
                mark_snowballed, seed_wallet)
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


def _deepdive_batch(c):
    """LIVELLO 2: scava in profondità chi ha passato lo screen. Verità + rileva i bot."""
    done, bots = 0, 0
    for a in wallets_to_deepdive(c, WALLETS["max_deep_per_cycle"]):
        d = onchain.wallet_deep(a, WALLETS["deep_tx"])
        if d is None:
            continue
        is_bot = d["tx_per_day"] > WALLETS["bot_tx_per_day"]
        set_wallet_deep(c, a, d["realized_sol"], d["win_rate"], d["closed"],
                        d["tx_per_day"], is_bot, d["top_wins"], d["tokens"], d["open"])
        done += 1
        if is_bot:
            bots += 1
    return done, bots


def _snowball(c):
    """Dalle whale VERIFICATE, scopri la rete: chi compra i loro token vincenti = nuovi candidati."""
    seeded = 0
    for w in whales_to_snowball(c, WALLETS["max_snowball_per_cycle"]):
        try:
            mints = json.loads(w["top_wins"] or "[]")[:WALLETS["snowball_tokens"]]
        except (TypeError, ValueError):
            mints = []
        for mint in mints:
            for buyer, _ts in onchain.recent_buyers(mint, WALLETS["snowball_buyers_tx"]):
                seed_wallet(c, buyer)
                seeded += 1
        mark_snowballed(c, w["address"])
    return seeded


def _smart_score(c):
    """smart_score: privilegia le whale VERIFICATE (deep) e profittevoli. I bot vanno a zero."""
    scored = 0
    for w in c.execute("""SELECT address, pnl_sol, win_rate, closed_count, buys_count,
                                 verified, is_bot FROM wallets""").fetchall():
        buys = w["buys_count"] or 0
        pnl, win, closed = w["pnl_sol"], w["win_rate"], w["closed_count"] or 0
        if w["is_bot"]:
            score = 0.0                                   # bot/HFT: fuori
        elif w["verified"] and pnl is not None and closed >= WALLETS["min_closed_for_proven"]:
            cred = min(closed / 5.0, 1.0)
            score = round(pnl * (win or 0) * cred + 0.1 * buys, 3)   # whale provata
        elif pnl is not None and closed >= WALLETS["min_closed_for_proven"]:
            score = round(0.3 * pnl * (win or 0) + 0.05 * buys, 3)   # promettente (screen) ma non verificata
        else:
            score = round(0.03 * buys, 3)
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
        qualified = _qualify_batch(c)        # LIVELLO 1: screen veloce
        deep, bots = _deepdive_batch(c)      # LIVELLO 2: deep-dive (verità + anti-bot)
        seeded = _snowball(c)                # RETE: espandi dalle whale verificate
        scored = _smart_score(c)
    print(f"[wallets] foto={captured} screen={qualified} deep={deep}(bot:{bots}) "
          f"snowball+{seeded} score={scored}")
    return captured


if __name__ == "__main__":
    capture_once()
