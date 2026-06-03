"""
jobs/scoring.py — il GIUDICE.

Una sola domanda: "quanto valgono, INSIEME, i segnali di qualità di questo asset?"
- somma i pesi dei segnali recenti (con DECAY: i vecchi pesano meno)
- BONUS DI CONFLUENZA se >=3 segnali positivi si allineano (è la confluenza che
  funziona, non il singolo segnale)
- salva score + PREZZO AL MOMENTO (serve a verificare l'edge dopo, onestamente)

Lo score è sempre RICOSTRUIBILE dal breakdown JSON: quando guardi l'Excel sai
PERCHÉ un token ha quel voto.
"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SCORING, LIMITS
from db import get_conn, init_db
from net import RateLimiter, get_json

DEX_BASE = "https://api.dexscreener.com"
limiter = RateLimiter(LIMITS["dexscreener_max_calls_per_min"])


def _current_price(contract):
    pd = get_json(f"{DEX_BASE}/latest/dex/tokens/{contract}", limiter)
    pairs = (pd or {}).get("pairs") or []
    if not pairs:
        return None
    pair = max(pairs, key=lambda p: (p.get("liquidity") or {}).get("usd") or 0)
    try:
        return float(pair.get("priceUsd"))
    except (TypeError, ValueError):
        return None


def score_once():
    init_db()
    now = time.time()
    decay_window = SCORING["score_decay_hours"] * 3600
    scored = 0
    with get_conn() as c:
        assets = c.execute("SELECT * FROM assets WHERE status='active'").fetchall()
        for a in assets:
            sigs = c.execute(
                """SELECT signal_type, value, weight, detected_at FROM signals
                   WHERE asset_id=? AND detected_at > ?""",
                (a["id"], now - decay_window),
            ).fetchall()
            if not sigs:
                continue

            # Per ogni TIPO di segnale tieni solo la misura PIÙ RECENTE: lo score è la
            # "confluenza attuale", non la somma di tutte le volte che l'abbiamo misurato.
            # (Il design append-only di `signals` resta per audit; qui non si gonfia.)
            latest = {}  # signal_type -> (detected_at, value, weight)
            for s in sigs:
                st = s["signal_type"]
                if st not in latest or s["detected_at"] > latest[st][0]:
                    latest[st] = (s["detected_at"], s["value"] or 0, s["weight"] or 1.0)

            total = 0.0
            breakdown = {}
            positive_count = 0
            for st, (ts, val, w) in latest.items():
                decay = max(0.0, 1.0 - (now - ts) / decay_window)   # lineare: 1 -> 0 su 24h
                contrib = val * w * decay
                total += contrib
                breakdown[st] = round(contrib, 3)
                if contrib > 0:
                    positive_count += 1

            # bonus di confluenza
            if positive_count >= SCORING["min_signals_for_bonus"]:
                total += SCORING["confluence_bonus"]
                breakdown["confluence_bonus"] = SCORING["confluence_bonus"]

            price = _current_price(a["contract_address"])
            c.execute(
                """INSERT INTO scores (asset_id, current_score, breakdown, price_at_score, updated_at)
                   VALUES (?,?,?,?,?)
                   ON CONFLICT(asset_id) DO UPDATE SET
                     current_score=excluded.current_score, breakdown=excluded.breakdown,
                     price_at_score=excluded.price_at_score, updated_at=excluded.updated_at""",
                (a["id"], round(total, 3), json.dumps(breakdown), price, now),
            )
            scored += 1
    print(f"[scoring] asset valutati={scored}")
    return scored


if __name__ == "__main__":
    if "--once" in sys.argv:
        score_once()
    else:
        while True:
            try:
                score_once()
            except Exception as e:
                print(f"[scoring] errore: {e}")
            time.sleep(120)
