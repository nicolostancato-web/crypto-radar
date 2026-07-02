"""
webhook/server.py — RICEVITORE REAL-TIME delle balene + FEED per il dashboard.

Helius manda un POST ogni volta che una balena vincente fa uno swap. Il server riconosce gli ACQUISTI,
li salva in memoria (ultimi 100) e li espone su GET /events -> il dashboard li mostra in diretta
("🐋 movimenti balene"). Cosi' apri il sito e vedi cosa hanno comprato le balene, senza email.
(L'email resta opzionale in background se GMAIL_APP_PASSWORD e' impostata.)

Dipendenze: fastapi, uvicorn.
"""
import os, json, time, smtplib, threading
from email.mime.text import MIMEText
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
ALERT_TO = os.getenv("ALERT_EMAIL", "nicolostancato@gmail.com")

EVENTS = []          # ultimi movimenti balene (in memoria)
MAX_EVENTS = 100


def _email(subject, body):
    pw = os.getenv("GMAIL_APP_PASSWORD")
    if not pw:
        return
    try:
        user = os.getenv("GMAIL_USER", "nicolostancato@gmail.com")
        m = MIMEText(body); m["Subject"] = subject; m["From"] = user; m["To"] = ALERT_TO
        s = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15)
        s.login(user, pw.replace(" ", "")); s.sendmail(user, [ALERT_TO], m.as_string()); s.quit()
    except Exception as e:
        print("[webhook] errore email:", str(e)[:120])


@app.get("/")
def health():
    return {"ok": True, "service": "crypto-radar whale webhook", "events_seen": len(EVENTS)}


@app.get("/events")
def events():
    """Il dashboard legge da qui: i movimenti recenti delle balene (piu' nuovi in cima)."""
    return {"count": len(EVENTS), "events": list(reversed(EVENTS))[:50]}


@app.post("/helius")
async def helius(req: Request):
    """Riceve gli eventi Helius. Per ogni tx, se una balena ha COMPRATO un token -> salva + (email)."""
    try:
        data = await req.json()
    except Exception:
        return {"ok": False}
    events = data if isinstance(data, list) else [data]
    for tx in events:
        fee = tx.get("feePayer")
        if not fee:
            continue
        bought = None
        for tt in (tx.get("tokenTransfers") or []):
            if tt.get("toUserAccount") == fee and tt.get("mint"):
                bought = tt.get("mint"); break
        if bought:
            ev = {"ts": int(time.time()), "wallet": fee, "token": bought,
                  "solscan": f"https://solscan.io/account/{fee}",
                  "dex": f"https://dexscreener.com/solana/{bought}"}
            EVENTS.append(ev)
            del EVENTS[:-MAX_EVENTS]
            print("[webhook] BUY:", fee[:6], "->", bought[:8])
            msg = f"🐋 Balena {fee[:6]}… ha comprato {bought[:8]}…\n{ev['dex']}"
            threading.Thread(target=_email, args=(f"🐋 Balena ha comprato {bought[:6]}", msg), daemon=True).start()
    return {"ok": True, "n": len(events)}
