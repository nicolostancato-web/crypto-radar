# SETUP — cosa deve fare Nicolò (passi manuali)

Tutto gratis. Quando hai i valori, incollameli in chat (o mettili in un file `.env`
nella cartella crypto-radar — NON committarlo, è già protetto da .gitignore).

---

## 1. SUPABASE — nuovo progetto "crypto-radar" (~5 min)

Serve perché la chiave che ho ora accede solo al progetto WhatsApp/Craftlabs.
Ne creiamo uno dedicato così i dati crypto restano isolati.

1. Vai su **https://supabase.com** → **Sign in** (il tuo account `nicolostancato@gmail.com`, login GitHub).
2. In alto a destra: **New project**.
3. Compila:
   - **Name:** `crypto-radar`
   - **Database Password:** generane una forte e **SALVALA** (ti serve dopo). Es. usa il
     bottone "Generate a password" e copiala.
   - **Region:** `West EU (Ireland) / eu-west-1` (il tuo standard).
   - Piano: **Free**.
4. Premi **Create new project** e aspetta ~2 minuti (sta creando il DB).
5. Quando è pronto: menu a sinistra → **Project Settings** (icona ingranaggio) → **API**.
6. Copiami questi 3 valori:
   - **Project URL** (es. `https://xxxxxxxx.supabase.co`)
   - **`service_role` key** (sezione "Project API keys" → è quella **secret**, NON l'anon)
   - La **Database Password** del punto 3.

> ⚠️ La `service_role` key è un segreto totale (bypassa la sicurezza). Non la mettere mai
> in un repo pubblico. Io la userò solo via variabile d'ambiente / .env.

### (Alternativa più veloce, se preferisci che lo crei IO)
Invece dei passi sopra, dammi un **Management API token**:
- Vai su **https://supabase.com/dashboard/account/tokens** → **Generate new token** →
  nome "crypto-radar-claude" → copialo e dammelo.
- Con quello creo il progetto via API io, e tu non fai altro.

---

## 2. TELEGRAM — api_id + api_hash (~5 min)

È il segnale social più prezioso: dove nasce la narrativa prima di Twitter.

1. Vai su **https://my.telegram.org** e fai login col tuo **numero di telefono**
   (ti arriva un codice su Telegram).
2. Clicca **API development tools**.
3. Compila il form "Create new application":
   - **App title:** `crypto-radar`
   - **Short name:** `cryptoradar`
   - **Platform:** Other (o Desktop)
   - URL/descrizione: lascia vuoto o metti qualsiasi cosa.
4. Premi **Create application**.
5. Copiami:
   - **api_id** (un numero)
   - **api_hash** (una stringa lunga)

### Canali seed — GIÀ SCELTI E VERIFICATI (2026-06-03)
Lista SERIA pre-configurata in `config.py` (TELEGRAM["channels"]). Niente gruppi pump/scam:
quelli iniettano attenzione finta e ci farebbero surfacing dei token da EVITARE.
Tutti pubblici e verificati (checkmark Telegram):

| # | Canale | @username | Funzione | Iscritti |
|---|--------|-----------|----------|----------|
| 1 | Binance Announcements | `@binance_announcements` | Listing = catalizzatori forti | 4.07M |
| 2 | Watcher Guru | `@WatcherGuru` | News veloci / narrativa (rimbalza X) | 627K |
| 3 | Cointelegraph | `@cointelegraph` | News / mercato | 370K |
| 4 | Lookonchain | `@lookonchain` | Money flow on-chain (smart money PRIMA del prezzo) | 38K |
| 5 | Whale Alert | `@whale_alert_io` | Transazioni grosse on-chain | 313K |

> Sono pubblici → bastano gli @username, NESSUN login al tuo account serve per leggerli.
> Il sistema misurerà la *velocità di menzione* dei ticker su questi canali, non seguirà
> le loro "call". Dopo 2 settimane teniamo quelli che anticipano i movimenti, buttiamo gli altri.

Se vuoi aggiungere canali tuoi (X-equivalenti che segui), dimmeli e li metto.

---

## 3. (OPZIONALE) COINGECKO — demo API key (~2 min)

Keyless funziona ma è rate-limitato. Con la key gratis è più stabile.

1. Vai su **https://www.coingecko.com** → crea account gratis.
2. Vai su **https://www.coingecko.com/en/developers/dashboard**.
3. **Create new API key** → tipo **Demo** (gratis, ~30 chiamate/min, 10k/mese).
4. Copiami la **API key**.

---

## Priorità
1. **Telegram** (api_id/api_hash + canali) → sblocca il segnale migliore.
2. **Supabase** → quando vogliamo andare 24/7 (per ora testo in locale, non urgente).
3. **CoinGecko key** → opzionale, quando vuoi più stabilità.

Intanto io vado avanti col layer social gratis (4chan + CoinGecko keyless): non blocca nulla.
