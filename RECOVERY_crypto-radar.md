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

## FATTO dopo (sessione 2026-06-03, parte 3) — DEPLOY 24/7
- Telegram attivato SENZA login: telegram_source.py legge i 5 canali via web preview
  (t.me/s/<canale>), zero credenziali. Integrato nel social. .env con api_id/api_hash
  salvato (permessi 600, gitignored) per upgrade Telethon futuro.
- CFO check: Railway NON e' piu' gratis ($5/mese). Scelto GitHub Actions (free su repo privato).
- DB: deciso SQLite separato (radar.db). Niente Supabase (limite free tier 2 progetti raggiunto;
  e comunque mixarlo col DB clienti WhatsApp = rischio). Migrazione futura = solo get_conn.
- REPO PRIVATO creato e pushato: github.com/nicolostancato-web/crypto-radar
- GitHub Actions .github/workflows/radar.yml: cron ORARIO (min 7) + workflow_dispatch.
  Gira run.py --once nel cloud, checkpoint WAL, ricommitta radar.db + top_scores.xlsx.
- VERIFICATO: primo run cloud success in 43s, bot ha committato "radar run ...". GIRA 24/7, Mac spento.

## Stato: IL RADAR E' ONLINE E AUTONOMO (gira ogni ora, gratis)
- Output: scaricare top_scores.xlsx da github.com/nicolostancato-web/crypto-radar
- ATTENZIONE SVILUPPO: il bot aggiorna radar.db nel cloud ogni ora. Prima di modificare
  codice in locale: git pull. Non committare modifiche locali a radar.db (lo possiede il bot);
  per test locali usare un DB separato o git checkout radar.db prima del push.

## FATTO dopo (sessione 2026-06-03, parte 4) — VALIDAZIONE
- Tabella outcomes (db.py schema + helper). config OUTCOMES (soglia 3.0, orizzonti 24/72/168h,
  slippage simulato = taglia/liquidita + fee, andata+ritorno). jobs/outcomes.py apre entrate
  ipotetiche quando score>=soglia e le matura nel tempo. Integrato in run.py.
- export_excel: 2a scheda "Validazione" = valore atteso NETTO + win rate per orizzonte.
- VERIFICATO nel cloud: bot ha creato tabella outcomes, aperto 2 entrate (Magpie, three),
  Excel con schede [Top Scores, Validazione]. Gira tutto hourly, autonomo.

## Prossimo step previsto
- Lasciar maturare gli outcomes (24/72/168h) -> la scheda Validazione si riempie da sola.
- Notifica Telegram dei top pick (chat ID 5182348358) — comodita' + watchdog.
- Dopo settimane di dati: leggere il valore atteso netto = l'edge c'e' o no (onesto).

## BLOCCHI: nessuno. Sistema completo e autonomo. (opz: CoinGecko demo key per stabilita')

## File modificati di recente
- crypto-radar/PLAN.md (nuovo), sources.py (nuovo), probe_sources.py (nuovo),
  jobs/discovery.py (modificato: usa get_candidates), RECOVERY_crypto-radar.md (questo).
- DB locale: crypto-radar/radar.db (SQLite, generato dai run di test).

## Costi finora: 0 EUR (solo GET pubbliche gratis, nessuna API a pagamento).

## Come riprendere
"Apri il progetto crypto-radar, leggi RECOVERY_crypto-radar.md e PLAN.md, riprendi dal
prossimo step (Stage 3 social no-cred)." Stack: SQLite locale per test, ./venv per girare.
