# Prompt A -> B -> C — deep search (2026-06-15)

## Evoluzione
- A (vecchio): "dammi le piu' twittate/hype ORA" -> token al PICCO, eta' mediana 24h. Entravamo tardi.
- B (anticipo): "dammi il PRE-PICCO, curva di menzioni che SALE" -> eta' 7h, 28/28 pre-picco. Becchiamo presto.
- C (questo): B risolveva il TIMING (quando), C risolve la PRECISIONE (quale). 7h e' gia' il limite (sotto
  e' rumore illeggibile): C non becca prima, becca MEGLIO — meta' spazzatura.

## La scoperta chiave: le balene SONO gia' su X (i proxy)
Le balene non si vedono su X direttamente, MA bot (GMGN, RayBot, Nansen...) postano in AUTOMATICO
"smart money bought X SOL" in tempo reale. Grok li puo' leggere -> intercettiamo l'ingresso balene
su X PRIMA di leggerlo on-chain. E' il ponte social->on-chain mancante.

## Implementato in C (gratis, zero costi aggiuntivi)
- Sezione "SEGNALI-PROXY DELLE BALENE": cerca i post dei tracker smart-money.
- Anti-rug 2026: curve_fill_speed (curva in minuti=bot/rug, in ore=sano), bundle, top10>40%.
- mention_curve_shape: stairstep (organico/BUONO) vs spike (coordinato/wash).
- confluence_type: independent (3 fonti scollegate=forte) vs echo (si retwittano).
- Campi nuovi: whale_proxy, smart_money_on_x, confluence_type, mention_curve_shape, curve_fill_speed.
- "Tripletta d'oro": accelerazione organica + proxy smart money + retail non ancora arrivato.

## Onesta'
X mostra il RACCONTO dell'on-chain, mai l'on-chain. whale_proxy su X = indizio (prior), NON prova.
La conferma resta Helius. C alza la probabilita' a priori, non sostituisce il filtro on-chain.
Stima: precisione da ~60% a ~75-80% (meta' spazzatura in meno). Da VALIDARE col backtest, non e' un fatto.

Fonti: coinedition (98.6% rug pump.fun), dextools GMGN, phemex/bitrue rug red flags, cryptonews find memecoins early.
