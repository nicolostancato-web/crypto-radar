"""
jobs/social.py — l'ORECCHIO.

Una sola domanda: "di questo token si sta PARLANDO (attenzione che cresce)?"
Gira sui candidati attivi e aggiunge segnali di ATTENZIONE allo storico `signals`,
che lo scoring poi somma agli altri per fare la CONFLUENZA.

Costo: 2 chiamate per CICLO (non per token). Tutto gratis, nessuna chiave.

NB: misura e basta, NON giudica (principio: misurare != giudicare). I valori sono
normalizzati 0..1 prima di applicare il peso, cosi' nessun segnale "esplode" e
domina lo score.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SOCIAL, TELEGRAM
from db import get_conn, init_db, add_signal
from social import get_biz_corpus, count_mentions, get_cg_trending_symbols
from telegram_source import get_telegram_corpus, available as tg_available


def social_once():
    init_db()
    # scarica le fonti UNA volta per ciclo (controllo costi)
    biz_corpus = get_biz_corpus()
    cg_trending = get_cg_trending_symbols()
    tg_corpus = get_telegram_corpus()   # "" se Telegram non configurato (no-op pulito)

    tagged = 0
    with get_conn() as c:
        assets = c.execute(
            "SELECT id, ticker FROM assets WHERE status='active'"
        ).fetchall()

        for a in assets:
            sym = (a["ticker"] or "").strip()
            if not sym:
                continue

            # 1) /biz/ — menzioni normalizzate 0..1 (segnale sottile, peso basso)
            mentions = count_mentions(biz_corpus, sym)
            if mentions > 0:
                val = min(mentions / SOCIAL["biz_mentions_full"], 1.0)
                add_signal(c, a["id"], "social", "biz_mentions",
                           round(val, 3), SOCIAL["weight_biz_mentions"])
                tagged += 1

            # 2) CoinGecko trending — appartenenza alla lista (segnale forte)
            if sym.upper() in cg_trending:
                add_signal(c, a["id"], "social", "coingecko_trending",
                           1.0, SOCIAL["weight_coingecko_trending"])
                tagged += 1

            # 3) TELEGRAM — il segnale migliore (canali seri). Menzioni normalizzate 0..1.
            if tg_corpus:
                tg_m = count_mentions(tg_corpus, sym)
                if tg_m > 0:
                    val = min(tg_m / TELEGRAM["mentions_full"], 1.0)
                    add_signal(c, a["id"], "social", "telegram_velocity",
                               round(val, 3), SOCIAL["weight_telegram_velocity"])
                    tagged += 1

    tg_state = f"{len(tg_corpus)}char" if tg_corpus else "OFF(no-cred)"
    print(f"[social] /biz/={len(biz_corpus)}char cg_trending={len(cg_trending)} "
          f"telegram={tg_state} segnali_aggiunti={tagged}")
    return tagged


if __name__ == "__main__":
    social_once()
