# PLAN — crypto-radar v2 (radar di confluenza)

## Concept (bloccato con Nicolò, 2026-06-03)

Un **analista AI che fa il lavoro di studio di un degen disciplinato, 24/7, su centinaia
di coin insieme**. Non stampa soldi mentre dormi: fa la *fatica della ricerca* al posto
tuo e te la serve pronta in un Excel ordinato per score 1-10. **Tu decidi**, simuli
l'entrata (paper), il sistema misura l'esito onestamente.

> Il vantaggio NON è un edge segreto sui prezzi. È **velocità e copertura di ricerca**:
> facciamo a macchina, su scala, quello che chi guadagna fa a mano su 2-3 coin.
> Solo ~5% usa l'AI così. Quello è il gap che sfruttiamo.

### La tesi: CONFLUENZA
Non UN segnale (= rumore). **Tutti i segnali allineati** (= storia):
**volume + holder + attenzione social + catalizzatore.** Chi fa soldi entra quando
4 cose convergono, mette poco (€100-1000), ed **esce quando arrivano i polli**.

## Principio di costo: leva sul lavoro altrui (CFO mode)
Non costruiamo infrastruttura, non paghiamo firehose. Ci appoggiamo a chi raccoglie già
i dati e li regala. Noi **concateniamo + analizziamo + rankiamo**.

| Segnale | Fonte gratis | Key? | Stato |
|---|---|---|---|
| Prezzo/volume/liquidità/txns | **DEXScreener** | no | già nel codice |
| Trending + market + community score | **CoinGecko** (Demo free) | sì, free | da aggiungere |
| Pool on-chain + trending per network | **GeckoTerminal** (free) | no | da aggiungere |
| Attenzione social aggregata (Twitter+Reddit) | **LunarCrush** | ⚠️ | VERIFICARE pricing oggi prima di usare |
| Attenzione precoce / narrativa | **Telegram** (Telethon) | no* | da aggiungere |
| Narrativa degen ancora più precoce | **4chan /biz/** (JSON) | no | da aggiungere |
| "I polli si informano" | **Google Trends** (pytrends) | no | da aggiungere |
| Holder count / on-chain | **The Graph** / RPC free tier | sì, free | park (v3) |

*Telegram: serve creare un'app gratis su my.telegram.org (api_id/api_hash). €0.

Twitter/X API ufficiale = **FUORI** finché i gratis non dimostrano segnale.
Anthropic (Haiku) per estrarre catalizzatori dal testo = **v2.1**, con stima costi + OK.

## La pipeline (parole di Nicolò): Discovery → Filtro → Validazione → Ranking → Entry → Monitor

```
   [DISCOVERY]        [SAFETY]         [SOCIAL VALID.]      [SCORING]        [EXPORT]         [OUTCOMES]
   multi-fonte   →   kill-switch   →   conferma social  →   confluenza   →   Excel 1-10   →   misura esito
   largo, gratis     anti-rug          Telegram/biz/Trends  decay+bonus      "perché"         valore atteso
                     anti-distrib.                                           price_at_score   netto slippage
```

### Stage 1 — DISCOVERY (largo, gratis)
- Candidati da: DEXScreener boosts + **CoinGecko trending** + **GeckoTerminal trending pools**.
- Dedup (UNIQUE chain+contract, `upsert_asset`).
- Filtri hard (liquidità, età, vol/liq) — già in `discovery.py`.
- Consulta blacklist PRIMA di ogni chiamata.
- Segnali precoci pesati (liquidità↑, accel volume) — già presenti, da estendere con holder↑.

### Stage 2 — SAFETY (kill-switch, non punteggio)
- Anti-rug: liquidità non bloccata, impersonazione brand → **esclusione permanente**.
- Anti-distribuzione: cascata di Sell mentre prezzo alto → **esclusione 24h**.
- Concentrazione wallet → richiede on-chain (RPC/The Graph) → park v3, oggi "non disponibile".

### Stage 3 — SOCIAL VALIDATION (il layer che mancava!)
Per ogni candidato sopravvissuto, **conferma l'attenzione** (gratis):
- **Telegram**: velocità di menzione del ticker/contract in N canali pubblici (la *derivata*,
  non il livello: menzioni che ACCELERANO).
- **CoinGecko community/social score**.
- **4chan /biz/**: presenza/accelerazione menzioni.
- **Google Trends**: pendenza dell'interesse di ricerca.
- (LunarCrush social volume — solo se free tier confermato.)
→ scrive segnali grezzi in `signals`, NON giudica (lo fa lo scoring).

### Stage 4 — SCORING (confluenza → voto 1-10)
- Somma pesata dei segnali (market + social), con **decay** (i vecchi pesano meno).
- **Bonus di confluenza** quando ≥3 dimensioni diverse si allineano (è la confluenza che conta).
- Normalizza a scala **0-10**.
- Breakdown JSON trasparente: ogni voto ricostruibile ("perché score 9").
- Salva `price_at_score` = entry ipotetica.

### Stage 5 — EXPORT (la vetrina)
- `top_scores.xlsx` ordinato per score (codice già pronto, da estendere con colonne social).
- Colonne: Ticker, Score/10, Prezzo_al_voto, **Perché** (breakdown), Social, Catalizzatore,
  Chain, Età, Contract + colonne paper trading da compilare/auto.
- v2: dashboard web (dopo che l'Excel dimostra valore).

### Stage 6 — OUTCOMES (l'onestà nel sistema)
- Tabella `outcomes`: N giorni dopo ogni score registra il prezzo.
- Calcola **valore atteso al netto di slippage simulato** (non la % di colpi giusti).
- È la metrica che dopo 2 mesi dice: il metodo funziona o no?

## Decisioni prese (2026-06-03)
- **DB**: nuovo progetto Supabase dedicato "crypto-radar" (isolato da WhatsApp/Craftlabs).
- **Hosting**: Railway 24/7 (tuo standard "tutto online"). Token/progetto già disponibili.
- **Output**: Excel prima (`top_scores.xlsx`), dashboard web dopo.
- **Chain**: NON fissa. **Si segue l'attenzione.** Monitoriamo tutte le major
  (solana, ethereum, base, bsc...) e aggiungiamo una **metrica di rotazione di chain**:
  se l'attenzione/volume si sposta su una chain, il sistema la segue ("oggi nessuno su
  Solana, domani tutti" → le masse si muovono, noi le seguiamo). Vedi nota chain-rotation.

### Chain-rotation (nuovo segnale)
A livello di CHAIN, non solo di token: misurare dove sta crescendo volume/attenzione
aggregata. Bonus di score ai token che stanno sulla chain "calda" del momento.

## Dove gira / DB
- **Sviluppo/test v1**: SQLite locale (zero setup, €0) per iterare veloce a costo nullo.
- **Produzione**: Railway 24/7 + nuovo progetto Supabase. Migrazione = solo `get_conn`.
- Output Excel leggibile mentre il loop gira (WAL già attivo).

## Cost check (CFO mode)
- v1: **€0** — tutte fonti free tier, hosting locale, nessuna LLM call.
- LunarCrush: ⚠️ verificare pricing ufficiale prima di integrarlo.
- v2.1 (Haiku per estrarre catalizzatori da testo): stima costi + OK Nicolò prima.
- Cap obbligatori quando si va su cloud: Railway hobby free, Supabase free 500MB.

## Ordine di costruzione (incrementale, ogni step testabile a €0)
1. **Stage 1 esteso**: aggiungere CoinGecko + GeckoTerminal al discovery. Test `--once`.
2. **Stage 3 — Google Trends + 4chan**: i due social gratis senza setup. Test.
3. **Stage 3 — Telegram**: setup api_id/api_hash, listener menzioni. Test.
4. **Stage 4**: scoring confluenza 0-10 con dimensione social. Test.
5. **Stage 5**: Excel esteso con colonne social/catalizzatore.
6. **Stage 6**: tabella outcomes + calcolo valore atteso netto.
7. **Solo dopo dati onesti**: dashboard, Railway, eventuale LunarCrush/Twitter.

## Onestà (non si tocca)
- L'aspettativa di default resta: un edge facile probabilmente non c'è. Lo Stage 6 serve
  a DIMOSTRARLO coi dati, non a crederci. Paper trading = ottimista (no slippage/emozioni).
- Servono CENTINAIA di osservazioni in regimi diversi prima di credere a un edge.
- Il sistema ti tiene FUORI dalle trappole (anti-distrib/rug), non ti ci butta dentro.
