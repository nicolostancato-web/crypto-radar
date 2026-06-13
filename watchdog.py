"""
watchdog.py — L'AGENTE GUARDIANO (regola WATCHDOG, obbligatoria per ogni sistema in produzione).

Gira da solo ogni 4h, separato da tutto il resto. Controlla che il sistema sia VIVO e stabile:
- lo scan di X sta ancora girando? (freschezza di trends.jsonl)
- i file di stato esistono e sono coerenti?
Se trova un problema, manda un ALERT su Telegram al founder. Se tutto e' ok, sta zitto (niente spam).

Free: solo lettura file locali + 1 chiamata Telegram in caso di allarme. Nessun costo se tutto va bene.
"""
import os, json, time, smtplib, urllib.parse, urllib.request
from email.mime.text import MIMEText

HERE = os.path.dirname(os.path.abspath(__file__))
TRENDS = os.path.join(HERE, "data", "trends.jsonl")
PIPE = os.path.join(HERE, "web", "pipeline.json")

MAX_SCAN_GAP_H = 5.0    # lo scan dovrebbe girare ogni ~1-3h; oltre 5h = qualcosa e' fermo

ALERT_TO = os.getenv("ALERT_EMAIL", "nicolostancato@gmail.com")


def _email(subject, body):
    """Alert via Gmail SMTP (canale primario: credenziali gia' esistenti)."""
    user = os.getenv("GMAIL_USER", "nicolostancato@gmail.com")
    pw = os.getenv("GMAIL_APP_PASSWORD")
    if not pw:
        return False
    try:
        m = MIMEText(body)
        m["Subject"] = subject
        m["From"] = user
        m["To"] = ALERT_TO
        s = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20)
        s.login(user, pw.replace(" ", ""))
        s.sendmail(user, [ALERT_TO], m.as_string())
        s.quit()
        print("[watchdog] alert email inviato a %s" % ALERT_TO)
        return True
    except Exception as e:
        print("[watchdog] errore invio email: %s" % str(e)[:120])
        return False


def _telegram(msg):
    """Alert via Telegram (fallback, se configurato)."""
    tok = os.getenv("TELEGRAM_BOT_TOKEN")
    chat = os.getenv("TELEGRAM_CHAT_ID")
    if not tok or not chat:
        return False
    url = "https://api.telegram.org/bot%s/sendMessage" % tok
    data = urllib.parse.urlencode({"chat_id": chat, "text": msg}).encode()
    try:
        urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=15)
        print("[watchdog] alert Telegram inviato")
        return True
    except Exception as e:
        print("[watchdog] errore invio Telegram: %s" % str(e)[:120])
        return False


def alert(subject, body):
    sent = _email(subject, body)
    sent = _telegram(subject + "\n" + body) or sent
    if not sent:
        print("[watchdog] NESSUN canale di alert configurato (manca GMAIL_APP_PASSWORD e Telegram) — alert solo nei log")


def run():
    problems = []
    now = time.time()

    # 1) lo scan di X sta girando?
    if os.path.exists(TRENDS):
        rows = [json.loads(l) for l in open(TRENDS) if l.strip()]
        if rows:
            gap = (now - rows[-1].get("ts", 0)) / 3600
            if gap > MAX_SCAN_GAP_H:
                problems.append("Scan X fermo da %.1fh (atteso < %.0fh). Il radar potrebbe essere bloccato." % (gap, MAX_SCAN_GAP_H))
        else:
            problems.append("trends.jsonl vuoto: nessuno scan registrato.")
    else:
        problems.append("trends.jsonl mancante.")

    # 2) i file di stato ci sono?
    if not os.path.exists(PIPE):
        problems.append("web/pipeline.json mancante: la dashboard non si aggiorna.")

    when = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(now))
    if problems:
        msg = "🛑 CRYPTO-RADAR WATCHDOG — %s\nProblemi rilevati:\n%s" % (when, "\n".join("• " + p for p in problems))
        print(msg)
        tg(msg)
        return 1
    print("[watchdog] %s — tutto stabile, nessun problema." % when)
    return 0


if __name__ == "__main__":
    run()
