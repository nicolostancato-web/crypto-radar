---
name: rug-pull-filter
description: Checklist on-chain per scartare rug-pull / honeypot / token-trappola Solana prima di tracciarli, usando DexScreener + Helius (free tier). USE WHEN si scrive o si modifica il filtro green/red, le soglie di config.FILTER, o si valuta la sicurezza on-chain di un token. SKIP WHEN si lavora su scan X, tracking prezzi o simulazione.
---

# Rug-Pull Filter — il gate anti-spazzatura

Il filtro decide GREEN (perla, si traccia a fondo) o RED (scartato, ma si tiene per imparare). Lo scopo NON
e' trovare exit-liquidity: e' TENERCI FUORI dalle trappole. Meglio scartare una buona che entrare in un rug.

## Hard-fail (uno solo basta per RED) — Solana via Helius
- **Mint authority ATTIVA** → il dev puo' coniare all'infinito → RED (killer).
- **Freeze authority ATTIVA** → il dev puo' congelare i tuoi token (honeypot) → RED (killer).
- **1 wallet (top1) > 30% supply** → una balena ti scarica addosso → RED.
- **Top10 > 50% supply** → distribuzione da pump-group → RED (calibrato: runner reali ~25%, rug 88-100%).
- **Liquidita' < soglia min** (token morto/rug) o **> max** su token giovane (possibile LP falso/wash) → RED.

## Soft-signal (pesa, non killer da soli)
- buy/sell ratio 1h basso (piu' vendite = distribuzione in corso).
- volume/liquidita' anomalo (troppo alto = wash trading; troppo basso = morto).
- eta' fuori finestra (troppo vecchio = onda passata; troppo nuovo = poco segnale — ma vedi corsia EARLY).

## Corsia EARLY (token < 8h) — non scartare i giovani per "vol basso"
Un token di 3h NON puo' avere vol24h alto: e' giovinezza, non difetto. Per i giovani usa soglie volume
PERMISSIVE (vol24h/vol1h morbidi), tieni invece TUTTI i check di sicurezza (authority, concentrazione).
Cosi' anticipiamo l'ignizione invece di beccare i token gia' pompati.

## Multi-chain
I check Helius (authority, top10) sono SOLO Solana. Su Base si saltano in sicurezza (None → non bloccano),
si tengono i check DexScreener (liquidita', volume, buy/sell). Mai far fallire un token Base per "authority".

## Principio
Misurare != giudicare: il filtro scrive metriche grezze + PASS/FAIL con il MOTIVO. Niente cancellazioni:
i RED restano nel dataset (servono a validare il filtro — se un RED esplode, il filtro era troppo severo).

## Reference (solo lettura)
DexScreener API (free, no key) · Helius RPC getAccountInfo + getTokenLargestAccounts (free 1M/mese).
