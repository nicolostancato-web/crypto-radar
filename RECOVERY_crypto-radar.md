# RECOVERY — crypto-radar

## Cosa stiamo facendo (1 frase)
Costruiamo un "radar di confluenza" crypto: un analista AI che studia 24/7 su dati gratis
(DEXScreener, GeckoTerminal, CoinGecko, Telegram, 4chan), trova la confluenza di segnali
(volume+holder+attenzione social+catalizzatore), produce un Excel ordinato per score 1-10
che Nicolò rivede e usa per paper trading. NON è un bot automatico. Vedi PLAN.md e CLAUDE.md.

## Decisioni prese (2026-06-03)
- DB: nuovo progetto Supabase dedicato "crypto-radar" (serve crearlo, vedi blocchi).
- Hosting: Railway 24/7.
- Output: Excel prima, dashboard dopo.
- Chain: NON fissa, si segue l'attenzione (chain-rotation). Oggi ~73% candidati su Solana.

## Ultimi step fatti
1. Estratto progetto base in ~/n8n builder/crypto-radar (da Downloads/files/crypto-radar.zip).
2. Letto tutto, scritto PLAN.md (architettura v2 a 6 stadi + sorgenti gratis).
3. venv + deps installate (requests, pandas, openpyxl, pytrends). €0.
4. probe_sources.py: 4/5 fonti gratis OK (Google Trends 429, flaky). €0.
5. sources.py: discovery multi-fonte (DEXScreener boosts + GeckoTerminal trending), dedup,
   multi-chain. Testato: 46-47 candidati. Collegato a jobs/discovery.py.
6. run.py --once gira end-to-end su SQLite: discovery 2 confermati, enrichment 3 esclusi,
   scoring 6, export vuoto (atteso: niente baseline al 1o giro + manca layer social).

## FATTO dopo (sessione 2026-06-03, parte 2)
- Stage 3 SOCIAL no-cred: social.py (/biz/ + CoinGecko trending) + jobs/social.py, integrato in run.py. OK.
- Fix BUG inflazione score (scoring usa la misura PIU' RECENTE per tipo, non la somma). OK.
- Modulo Telegram: telegram_source.py (Telethon, no-op senza api_id/api_hash), 5 canali
  SERI verificati pre-configurati in config.TELEGRAM. Integrato in jobs/social.py.
- Canali verificati: @binance_announcements (4.07M), @WatcherGuru (627K), @cointelegraph
  (370K), @lookonchain (38K), @whale_alert_io (313K). NIENTE gruppi pump/scam (veleno).
- Score 0-10 (export _score_10, config score_reference=12). Colonna Score_su_10.
- Fix Excel stale (scrive avviso datato se niente sopra soglia).
- Fix impersonazione su NOME+TICKER (SPCX ora escluso, verificato).
- telethon aggiunto a requirements.txt (NON ancora pip-installato).

## Prossimo step previsto
- ATTIVARE Telegram: pip install telethon + Nicolò da' api_id/api_hash -> il segnale forte.
- Tabella outcomes (misura esito netto slippage) = la metrica di verita'.
- Infra: nuovo Supabase + deploy Railway (per girare 24/7).

## BLOCCHI (servono da Nicolò) — il solo vero blocco ora e' Telegram
1. **Telegram api_id + api_hash** da my.telegram.org (canali GIA' scelti). Sblocca il segnale migliore.
2. Supabase: progetto "crypto-radar" (URL+service key) o Management token. Serve per 24/7.
3. (opz) CoinGecko demo key per stabilita'.

## File modificati di recente
- crypto-radar/PLAN.md (nuovo), sources.py (nuovo), probe_sources.py (nuovo),
  jobs/discovery.py (modificato: usa get_candidates), RECOVERY_crypto-radar.md (questo).
- DB locale: crypto-radar/radar.db (SQLite, generato dai run di test).

## Costi finora: 0 EUR (solo GET pubbliche gratis, nessuna API a pagamento).

## Come riprendere
"Apri il progetto crypto-radar, leggi RECOVERY_crypto-radar.md e PLAN.md, riprendi dal
prossimo step (Stage 3 social no-cred)." Stack: SQLite locale per test, ./venv per girare.
