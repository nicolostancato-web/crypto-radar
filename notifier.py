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
import smtplib
import urllib.parse
import urllib.request
from email.mime.text import MIMEText

from config import TELEGRAM, EMAIL, SCORING
from db import get_conn, init_db, is_notified, mark_notified


def _tg_ok():
    return bool(TELEGRAM.get("bot_token") and TELEGRAM.get("chat_id"))


def _email_ok():
    return bool(EMAIL.get("gmail_app_password") and EMAIL.get("to"))


def available():
    return _tg_ok() or _email_ok()


def _send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM['bot_token']}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": TELEGRAM["chat_id"], "text": text,
        "parse_mode": "HTML", "disable_web_page_preview": "true",
    }).encode()
    with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=12) as r:
        return r.status == 200


def _send_email(subject, text):
    msg = MIMEText(text, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = EMAIL["gmail_user"]
    msg["To"] = EMAIL["to"]
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as s:
        s.login(EMAIL["gmail_user"], EMAIL["gmail_app_password"])
        s.sendmail(EMAIL["gmail_user"], [EMAIL["to"]], msg.as_string())
    return True


def send(subject, text):
    """Manda su tutti i canali configurati (Telegram e/o email). True se almeno uno parte."""
    ok = False
    if _tg_ok():
        try:
            ok = _send_telegram(text) or ok
        except Exception as e:
            print(f"[notifier] telegram fallito: {e}")
    if _email_ok():
        try:
            ok = _send_email(subject, text) or ok
        except Exception as e:
            print(f"[notifier] email fallita: {e}")
    return ok


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
            subject = f"🟢 Crypto Radar — {r['ticker']} {score10}/10 ({r['chain']})"
            text = (f"Nuovo candidato sul radar\n\n"
                    f"{r['ticker']} · {score10}/10 · {r['chain']}\n"
                    f"segnali: {sigs}\n\n"
                    f"grafico: {link}\n\n"
                    f"— crypto-radar (paper trading, non è consulenza)")
            if send(subject, text):
                mark_notified(c, r["contract_address"], r["ticker"], r["current_score"])
                sent += 1
    if sent:
        print(f"[notifier] inviati {sent} nuovi pick")
    return sent


def notify_errors(errors):
    """WATCHDOG: alert immediato se uno stage è fallito."""
    if not errors or not available():
        return
    body = "\n".join(f"- {e}" for e in errors)
    send("⚠️ Crypto Radar — problema", f"Uno o più stage sono falliti:\n\n{body}")


if __name__ == "__main__":
    if not available():
        print("[notifier] non configurato (manca email/bot). No-op. Vedi SETUP.md.")
    elif "--test" in __import__("sys").argv:
        ok = send("✅ Crypto Radar — test", "Notifiche attive. Se leggi questa, funziona.")
        print("[notifier] test inviato:", ok)
    else:
        notify_new_picks()
