"""
telegram_source.py — l'ORECCHIO MIGLIORE (Telegram), versione SENZA login.

I 5 canali seri sono PUBBLICI: Telegram ne espone i messaggi recenti via web preview
(https://t.me/s/<canale>). Li leggiamo cosi', a COSTO ZERO e SENZA credenziali/login.
~16-20 messaggi recenti per canale: per canali ad alto traffico = finestra recente buona.

La velocita' di menzione di un ticker su questi canali e' il segnale di attenzione piu'
anticipato che abbiamo gratis. Misuriamo, non seguiamo le "call".

UPGRADE futuro (opzionale): con api_id/api_hash in .env si puo' passare a Telethon per
storia piu' profonda. Non serve ora: il web preview basta per il segnale.
"""
import re
import html
import requests
from config import TELEGRAM, LIMITS

UA = {"User-Agent": "Mozilla/5.0 (crypto-radar; research; paper-trading only)"}
_MSG_RE = re.compile(
    r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', re.S
)
_TAG_RE = re.compile(r"<[^>]+>")


def _fetch_channel(ch):
    """Messaggi recenti di un canale pubblico via web preview. Lista di stringhe."""
    try:
        r = requests.get(f"https://t.me/s/{ch}", headers=UA,
                         timeout=LIMITS["http_timeout"])
        r.raise_for_status()
    except requests.RequestException:
        return []
    out = []
    for m in _MSG_RE.findall(r.text):
        txt = html.unescape(_TAG_RE.sub(" ", m)).strip()
        if txt:
            out.append(txt)
    return out


def available():
    """Sempre disponibile: il web preview non richiede credenziali."""
    return True


def get_telegram_corpus():
    """Blob di testo coi messaggi recenti di tutti i canali configurati. '' se tutto fallisce."""
    parts = []
    per_channel = {}
    for ch in TELEGRAM["channels"]:
        msgs = _fetch_channel(ch)
        per_channel[ch] = len(msgs)
        parts.extend(msgs)
    corpus = " ".join(parts)
    # diagnostica leggera (non rompe nulla se un canale e' a 0)
    get_telegram_corpus.last_per_channel = per_channel
    return corpus


get_telegram_corpus.last_per_channel = {}


if __name__ == "__main__":
    corpus = get_telegram_corpus()
    print(f"[telegram] corpus: {len(corpus)} char dai {len(TELEGRAM['channels'])} canali seri")
    print(f"[telegram] messaggi per canale: {get_telegram_corpus.last_per_channel}")
    from social import count_mentions
    for s in ["BTC", "ETH", "BONK", "SOL", "WLD"]:
        print(f"  {s}: {count_mentions(corpus, s)} menzioni")
