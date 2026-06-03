"""
notifier.py — NOTIFICHE Telegram + WATCHDOG.

Due lavori:
  1) ti manda sul telefono i NUOVI pick caldi (sopra soglia), una volta sola per token;
  2) WATCHDOG: se un giro fallisce (stage in errore) ti manda un alert subito.

Usa un BOT Telegram (token da @BotFather, vedi SETUP.md). Senza token = no-op pulito:
il sistema gira lo stesso, semplicemente non manda nulla.

Niente librerie extra: chiamata HTTP diretta all'API di Telegram (gratis).
"""
import json
import urllib.parse
import urllib.request

from config import TELEGRAM, SCORING
from db import get_conn, init_db, is_notified, mark_notified


def available():
    return bool(TELEGRAM.get("bot_token") and TELEGRAM.get("chat_id"))


def send(text):
    """Manda un messaggio Telegram. Ritorna True/False. No-op se non configurato."""
    if not available():
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM['bot_token']}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": TELEGRAM["chat_id"],
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=12) as r:
            return r.status == 200
    except Exception as e:
        print(f"[notifier] invio fallito: {e}")
        return False


def notify_new_picks():
    """Manda i NUOVI token sopra soglia (mai notificati prima). Anti-spam via tabella notified."""
    if not available():
        return 0
    init_db()
    sent = 0
    with get_conn() as c:
        rows = c.execute(
            """SELECT a.ticker, a.chain, a.contract_address, a.pair_address,
                      s.current_score, s.breakdown
               FROM scores s JOIN assets a ON a.id = s.asset_id
               WHERE a.status='active' AND s.current_score >= ?
               ORDER BY s.current_score DESC""",
            (SCORING["min_score_for_export"],),
        ).fetchall()
        for r in rows:
            if is_notified(c, r["contract_address"]):
                continue
            bd = json.loads(r["breakdown"] or "{}")
            sigs = ", ".join(sorted(bd, key=lambda k: -bd[k]))
            ref = r["pair_address"] or r["contract_address"]
            link = f"https://dexscreener.com/{r['chain']}/{ref}"
            score10 = round(min(10.0, (r["current_score"] or 0) / SCORING.get("score_reference", 12.0) * 10), 1)
            msg = (f"🟢 <b>Nuovo sul radar</b>\n"
                   f"<b>{r['ticker']}</b> · {score10}/10 · {r['chain']}\n"
                   f"segnali: {sigs}\n"
                   f'<a href="{link}">grafico DEXScreener</a>')
            if send(msg):
                mark_notified(c, r["contract_address"], r["ticker"], r["current_score"])
                sent += 1
    if sent:
        print(f"[notifier] inviati {sent} nuovi pick")
    return sent


def notify_errors(errors):
    """WATCHDOG: alert immediato se uno stage è fallito."""
    if not errors or not available():
        return
    body = "\n".join(f"• {e}" for e in errors)
    send(f"⚠️ <b>crypto-radar — problema</b>\n{body}")


if __name__ == "__main__":
    if not available():
        print("[notifier] non configurato (manca TELEGRAM_BOT_TOKEN). No-op. Vedi SETUP.md.")
    else:
        send("✅ crypto-radar: test notifica OK")
        notify_new_picks()
