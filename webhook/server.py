"""
webhook/server.py — RICEVITORE REAL-TIME (mossa #2, il 100%). PRONTO MA SPENTO.

Quando lo accendi (deploy su Railway, ~$5/mese), Helius gli manda un POST OGNI VOLTA che un wallet
monitorato (le balene vincenti trovate da smart_money) fa una transazione. Il server riconosce se ha
COMPRATO un token e ti manda un alert email IMMEDIATO: "🐋 La balena X ha appena comprato Y".
E' il copy-trading in tempo reale: vedi le balene vincenti muoversi al secondo, non ogni 4h.

NON deployare finche' smart_wallets.json non ha wallet con winrate alto (vedi webhook/README.md).
Dipendenze: fastapi, uvicorn. Email via Gmail (GMAIL_APP_PASSWORD), opzionale.
"""
import os, json, smtplib
from email.mime.text import MIMEText
from fastapi import FastAPI, Request

app = FastAPI()
ALERT_TO = os.getenv("ALERT_EMAIL", "nicolostancato@gmail.com")


def _email(subject, body):
    user = os.getenv("GMAIL_USER", "nicolostancato@gmail.com")
    pw = os.getenv("GMAIL_APP_PASSWORD")
    if not pw:
        print("[webhook] no GMAIL_APP_PASSWORD — alert solo nei log:", subject)
        return
    try:
        m = MIMEText(body); m["Subject"] = subject; m["From"] = user; m["To"] = ALERT_TO
        s = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15)
        s.login(user, pw.replace(" ", "")); s.sendmail(user, [ALERT_TO], m.as_string()); s.quit()
        print("[webhook] alert email inviato")
    except Exception as e:
        print("[webhook] errore email:", str(e)[:120])


@app.get("/")
def health():
    return {"ok": True, "service": "crypto-radar whale webhook"}


@app.post("/helius")
async def helius(req: Request):
    """Riceve gli eventi Helius. Per ogni tx, se un wallet monitorato ha COMPRATO un token → alert."""
    try:
        events = await req.json()
    except Exception:
        return {"ok": False}
    if not isinstance(events, list):
        events = [events]
    for tx in events:
        fee = tx.get("feePayer")
        if not fee:
            continue
        # capisce quale token ha ricevuto (= comprato) il wallet che ha pagato la fee
        bought = None
        for tt in (tx.get("tokenTransfers") or []):
            if tt.get("toUserAccount") == fee and tt.get("mint"):
                bought = tt.get("mint")
                break
        if bought:
            short = fee[:6] + "…"
            msg = f"🐋 Balena {short} ha COMPRATO il token {bought[:8]}…\nSolscan: https://solscan.io/account/{fee}\nToken: https://dexscreener.com/solana/{bought}"
            print("[webhook] BUY:", short, "->", bought[:8])
            _email(f"🐋 Balena {short} ha comprato {bought[:6]}", msg)
    return {"ok": True, "n": len(events)}
