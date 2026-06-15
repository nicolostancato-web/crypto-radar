"""
webhook/register.py — registra/aggiorna il webhook Helius sui WALLET VINCENTI (le balene da copiare).

Legge data/smart_wallets.json (prodotto da smart_money.py), prende i wallet con winrate alto, e dice a
Helius di notificare il nostro server (server.py su Railway) ogni volta che uno di loro fa una transazione.
Da rilanciare quando lo smart-money trova nuove balene (i wallet da seguire cambiano).

Uso: WEBHOOK_URL=https://...railway.app/helius HELIUS_API_KEY=... python webhook/register.py
"""
import os, json, sys, requests

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SMART = os.path.join(HERE, "data", "smart_wallets.json")
MIN_WINRATE = 0.5     # segui solo le balene che vincono almeno la metà delle volte
MAX_WALLETS = 100     # Helius accetta molti address; ne teniamo i migliori


def main():
    key = os.getenv("HELIUS_API_KEY")
    url = os.getenv("WEBHOOK_URL")
    if not key or not url:
        print("Servono HELIUS_API_KEY e WEBHOOK_URL (es. https://tuo-app.up.railway.app/helius)"); sys.exit(1)
    if not os.path.exists(SMART):
        print("smart_wallets.json assente — gira prima smart_money.py (servono balene identificate)."); sys.exit(1)
    smart = json.load(open(SMART)).get("smart", [])
    wallets = [w["wallet"] for w in smart if w.get("winrate", 0) >= MIN_WINRATE][:MAX_WALLETS]
    if not wallets:
        print(f"Nessuna balena con winrate >= {MIN_WINRATE} ancora. Accumula altri dati prima di accendere il webhook.")
        sys.exit(0)

    body = {"webhookURL": url, "transactionTypes": ["SWAP"], "accountAddresses": wallets, "webhookType": "enhanced"}
    r = requests.post(f"https://api.helius.xyz/v0/webhooks?api-key={key}", json=body, timeout=30)
    if r.status_code in (200, 201):
        print(f"✅ Webhook registrato su {len(wallets)} balene vincenti. Helius notifichera' {url} ad ogni loro swap.")
    else:
        print(f"❌ Errore {r.status_code}: {r.text[:200]}")


if __name__ == "__main__":
    main()
