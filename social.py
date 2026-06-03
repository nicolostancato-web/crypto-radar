"""
social.py — segnali di ATTENZIONE gratis e SENZA chiave.

Idea: l'edge (se c'e') sta nell'attenzione che nasce PRIMA del movimento di prezzo.
Qui misuriamo, a costo zero, due proxy di attenzione:

  - 4chan /biz/  : quante volte un ticker viene nominato (narrativa degen precoce).
                   Segnale SOTTILE (il catalog ha solo OP + ultime risposte) -> peso basso.
  - CoinGecko    : se il simbolo e' nella lista "trending" (attenzione gia' aggregata
                   da CoinGecko su milioni di utenti) -> segnale piu' forte.

COSTI: 2 chiamate per CICLO (non per token). Le fonti si scaricano una volta e si
confrontano in memoria con tutti i candidati. Nessun costo, nessuna chiave.
"""
import re
import requests
from net import RateLimiter, get_json
from config import LIMITS

UA = {"User-Agent": LIMITS["user_agent"]}
BIZ_CATALOG = "https://a.4cdn.org/biz/catalog.json"
CG_TRENDING = "https://api.coingecko.com/api/v3/search/trending"

_cg_limiter = RateLimiter(LIMITS["dexscreener_max_calls_per_min"])


def get_biz_corpus():
    """Scarica /biz/ una volta e ritorna un blob di testo (OP + ultime risposte)."""
    try:
        r = requests.get(BIZ_CATALOG, headers=UA, timeout=LIMITS["http_timeout"])
        r.raise_for_status()
        data = r.json()
    except (requests.RequestException, ValueError):
        return ""
    parts = []
    for page in data:
        for th in page.get("threads", []):
            parts.append(th.get("sub", "") or "")
            parts.append(th.get("com", "") or "")
            for rep in th.get("last_replies", []) or []:
                parts.append(rep.get("com", "") or "")
    return " ".join(parts)


def count_mentions(corpus, symbol):
    """
    Quante volte il ticker e' nominato. Ritorna un punteggio grezzo (>=0).
      - $SYMBOL  -> menzione FORTE (pattern tipico con cui /biz/ cita una coin): peso 2
      - SYMBOL   -> menzione debole, solo per ticker >=4 lettere (evita falsi positivi
                    su parole comuni tipo "LAB", "ETH" che matchano testo a caso): peso 1
    """
    if not corpus or not symbol or len(symbol) < 2:
        return 0
    sym = re.escape(symbol)
    strong = len(re.findall(rf"\${sym}\b", corpus, flags=re.IGNORECASE))
    weak = 0
    if len(symbol) >= 4:
        weak = len(re.findall(rf"\b{sym}\b", corpus, flags=re.IGNORECASE))
    return strong * 2 + weak


def get_cg_trending_symbols():
    """Set di simboli (UPPER) attualmente 'trending' su CoinGecko."""
    data = get_json(CG_TRENDING, _cg_limiter)
    out = set()
    if not data:
        return out
    for c in data.get("coins", []):
        sym = (c.get("item") or {}).get("symbol")
        if sym:
            out.add(sym.upper())
    return out


if __name__ == "__main__":
    corpus = get_biz_corpus()
    trending = get_cg_trending_symbols()
    print(f"[social] /biz/ corpus: {len(corpus)} char")
    print(f"[social] CoinGecko trending: {sorted(trending)}")
    for s in ["BONK", "WLD", "PEPE", "ETH"]:
        print(f"  {s}: biz={count_mentions(corpus, s)}  cg_trending={s in trending}")
