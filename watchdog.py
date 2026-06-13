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
TRACK = os.path.join(HERE, "data", "track.jsonl")
CANDS = os.path.join(HERE, "data", "candidates.jsonl")
PIPE = os.path.join(HERE, "web", "pipeline.json")

MAX_SCAN_GAP_H = 9.0    # scan ogni 4h; oltre 9h = fermo (margine per i cron saltati di GitHub)

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


def _read(path):
    if not os.path.exists(path):
        return []
    out = []
    for l in open(path):
        l = l.strip()
        if l:
            try:
                out.append(json.loads(l))
            except Exception:
                pass
    return out


def _trigger(workflow):
    """AUTO-RECOVERY: ri-lancia un workflow fermo via API GitHub (serve WORKFLOW_PAT con actions:write)."""
    pat = os.getenv("WORKFLOW_PAT")
    if not pat:
        return False
    url = "https://api.github.com/repos/nicolostancato-web/crypto-radar/actions/workflows/%s/dispatches" % workflow
    data = json.dumps({"ref": "main"}).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", "token " + pat)
    req.add_header("Accept", "application/vnd.github+json")
    try:
        urllib.request.urlopen(req, timeout=15)
        print("[watchdog] AUTO-RECOVERY: ri-lanciato %s" % workflow)
        return True
    except Exception as e:
        print("[watchdog] auto-recovery fallita su %s: %s" % (workflow, str(e)[:100]))
        return False


def _data_quality(now):
    """Controlla che stiamo accumulando dati BUONI (non solo che il sistema e' acceso). Ritorna (problemi, fix_fatti)."""
    problems, fixes = [], []

    # 1) SCAN fresco e produttivo
    trends = _read(TRENDS)
    if not trends:
        problems.append("trends.jsonl vuoto: nessuno scan.")
    else:
        gap = (now - trends[-1].get("ts", 0)) / 3600
        if gap > MAX_SCAN_GAP_H:
            problems.append("Scan X fermo da %.1fh." % gap)
            if _trigger("trends.yml"):
                fixes.append("ri-lanciato lo scan")
        recent = [t for t in trends if now - t.get("ts", 0) < 24 * 3600]
        if recent and sum(t.get("n", 0) for t in recent) == 0:
            problems.append("Gli scan delle ultime 24h non trovano NESSUN token (Grok a vuoto?).")

    # 2) TRACKING che cresce e con prezzi validi
    track = _read(TRACK)
    recent_obs = [o for o in track if now - o.get("obs_ts", 0) < 6 * 3600]
    if len(recent_obs) < 3:
        problems.append("Tracking quasi fermo: solo %d osservazioni in 6h." % len(recent_obs))
        if _trigger("track.yml"):
            fixes.append("ri-lanciato il tracking")
    if recent_obs:
        valid = [o for o in recent_obs if o.get("price")]
        if len(valid) / len(recent_obs) < 0.6:
            problems.append("Dati sporchi: %d%% delle osservazioni recenti senza prezzo valido." % round(100 * (1 - len(valid) / len(recent_obs))))

    # 3) Stiamo costruendo SERIE (non punti singoli)?
    by_ca = {}
    for o in track:
        by_ca.setdefault(o.get("ca"), 0)
        by_ca[o.get("ca")] += 1
    if by_ca and not any(c >= 3 for c in by_ca.values()):
        problems.append("Nessun token ha una serie ≥3 punti: non stiamo costruendo storia, solo singoli scatti.")

    # 4) Il filtro fa passare delle PERLE? (le perle sono rare 1-5%: allarme solo se 0 su un campione ampio in 48h)
    cands = _read(CANDS)
    recent_c = [c for c in cands if now - c.get("ts", 0) < 48 * 3600]
    if len(recent_c) >= 30 and not any(c.get("pass") for c in recent_c):
        problems.append("0 perle in 48h su %d valutati: lo scout pesca male (vecchi/rug) o il filtro e' troppo stretto — da rivedere." % len(recent_c))

    return problems, fixes


def run():
    now = time.time()
    problems, fixes = _data_quality(now)
    if not os.path.exists(PIPE):
        problems.append("web/pipeline.json mancante: la dashboard non si aggiorna.")

    when = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(now))
    if problems:
        fix_txt = ("\n\n🔧 Auto-recovery: " + ", ".join(fixes) + ".") if fixes else ""
        msg = ("🛑 CRYPTO-RADAR — controllo dati %s\nProblemi nella RACCOLTA:\n%s%s\n\n"
               "(Se l'auto-recovery non basta, serve un occhio umano.)" %
               (when, "\n".join("• " + p for p in problems), fix_txt))
        print(msg)
        alert("🛑 Crypto-radar: problema nella raccolta dati", msg)
        return 1
    print("[watchdog] %s — raccolta dati sana." % when)
    return 0


if __name__ == "__main__":
    run()
