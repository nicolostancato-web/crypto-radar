# RECOVERY — crypto-radar

## Cosa stiamo facendo (1 frase)
Sistema X-first per trovare un edge sulle memecoin/AI-agent: Grok scova su X -> filtro on-chain (green/red) ->
tracking ricco ora-per-ora -> impara entry/exit. Stiamo implementando le osservazioni della review DeepSeek, a BLOCCHI.

## Stato sistema (tutto LIVE in cloud, gira da solo)
- SCAN Grok ogni 4h (trends.yml): memecoin Solana + AI-agent, output ricco.
- FILTRO on-chain (filter_tokens.py): green/red. **Blocco 1 fatto: corsia EARLY** (token <8h soglie volume morbide).
- TRACKING ogni 1h (track.yml, gratis): prezzo, vol, buy/sell, whale (top10/top1/holders).
- SOCIAL green ogni 4h (green_social.yml, a pagamento): posts/h, trend, KOL, sentiment.
- LEARNER (ogni 1h) + SIMULATORE uscite (vol-fade vs fissi) + dip-entry test.
- WATCHDOG ogni 4h (alert email Gmail, secret GMAIL_APP_PASSWORD su GitHub).

## Dati/lezioni chiave (APPUNTI_TRADING.md, METODO_ENTRATA_USCITA.md)
- Entry TARDIVO: perle -26% al segnale vs scartati -1.7%. Causa (DeepSeek): latenza + filtro che escludeva i giovani.
- Dip-entry: aspettare correzione -15% rende +2% vs -16% al segnale (n piccolo, direzione coerente).
- 31 trade = troppo pochi. Serve sample size (Blocco 2).

## PIANO A BLOCCHI (review DeepSeek) — dove siamo
- [x] Blocco 1 — Fix filtro EARLY (corsia <8h) + dip-entry test. FATTO.
- [ ] Blocco 2 — Backtester STORICO su 500-1000 token (fonte: CoinGecko Pro o GeckoTerminal) per sample size vero. PROSSIMO.
- [ ] Blocco 3 — Derivati nel learner: accelerazione volume, whale netflow, top10 delta, buy-ratio accel.
- [ ] Blocco 4 — Pulizia rumore + slippage 2% nel P&L + feature (deployer age, buyers unici).
- [ ] Blocco 5 — Regressione logistica (sklearn): quali feature al segnale predicono +50%/6h.
- [ ] Blocco 6 (DA DECIDERE) — Ridurre latenza scan (streaming/event-driven). Serve infrastruttura, valutare CFO.

## Note
- Fable 5 = il modello Claude top, e' quello usato in questa sessione Claude Code (gratis Max). Doppia-voce esterna = DeepSeek/Grok (altra famiglia).
- CFO xAI: saldo ~$9.2, auto top-up OFF (tetto blindato). Consumo ~$0.7/giorno.
- Repo: nicolostancato-web/crypto-radar (privato). Dashboard: nicolostancato-web.github.io/crypto-radar-dashboard
- Credenziali: secret su GitHub (XAI_API_KEY, HELIUS_API_KEY, GMAIL_APP_PASSWORD, PAGES_PAT, COINGECKO_DEMO_KEY) + .env locale.

## Come riprendere
"Leggi RECOVERY_crypto_radar.md, riprendi dal Blocco 2 (backtester storico)."
