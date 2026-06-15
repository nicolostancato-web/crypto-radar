# Webhook real-time — il 100% (PRONTO, da accendere quando serve)

Questo è l'ultimo 10%: vedere le **balene vincenti muoversi al secondo** invece che ogni 4h.
È **pronto come codice ma SPENTO**, per non pagare prima del tempo.

## Quando accenderlo (NON prima)
Solo quando `data/smart_wallets.json` ha **3-5 wallet con winrate ≥ 50%** (balene che vincono davvero).
Finché winrate = 0, non c'è nessuno da seguire → accenderlo = pagare $5/mese per monitorare il vuoto.
Controlla la sezione "balene" sulla dashboard: quando compaiono wallet smart, è il momento.

## Cosa fa, una volta acceso
1. `server.py` gira su Railway (sempre acceso) ed espone `/helius`.
2. `register.py` dice a Helius: "notifica quel server ogni volta che queste balene fanno uno swap".
3. Quando una balena vincente COMPRA un token → ti arriva un'**email all'istante**:
   *"🐋 Balena X ha comprato Y adesso"* → puoi copiarla in tempo reale.

## Come si accende (5 min, ~$5/mese Railway)
1. **Deploy server**: crea un progetto Railway, collega questa cartella `webhook/`, start command:
   `uvicorn server:app --host 0.0.0.0 --port $PORT`
   Dipendenze: `fastapi`, `uvicorn`. Env: `GMAIL_APP_PASSWORD` (per gli alert email).
   Railway ti dà un URL tipo `https://crypto-radar-whale.up.railway.app`.
2. **Registra il webhook**:
   `WEBHOOK_URL=https://...up.railway.app/helius HELIUS_API_KEY=<key> python webhook/register.py`
   (rilancialo ogni tanto: quando lo smart-money trova nuove balene, gli address da seguire cambiano).
3. Fatto. Da quel momento ricevi gli alert in tempo reale.

## CFO
- Railway Hobby: ~$5/mese (primo costo fisso del progetto). Verificato 2026-06-15.
- Helius webhook: 1 credito per evento consegnato → dentro il free tier 1M/mese.
- Si spegne in 1 click su Railway quando vuoi.
