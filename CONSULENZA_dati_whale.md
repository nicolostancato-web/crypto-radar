# Possiamo estrarre più dati WHALE allo stesso prezzo? — deep search verificato (2026-06-15)

## Verdetto: siamo al ~60%, gratis si arriva a ~90%.
Oggi usiamo SOLO `getTokenLargestAccounts` (foto top-20 holder ogni ora). E' un'istantanea aggregata:
vediamo "la fetta dei grossi cresce/cala", ma NON le singole transazioni, NON chi compra/vende, NON il timing.

## Cosa NON sfruttiamo di Helius (gia' nel FREE tier, 1M crediti/mese)
- `getSignaturesForAddress` (1 credito) -> lista di tutte le tx di un pool o wallet.
- Enhanced Transactions API `POST /v0/transactions` (100 crediti, ma batch di 100 swap = ~1 credito/swap)
  -> ogni swap PARSATO: chi, side buy/sell, importo, programma (Raydium/Jupiter/Pump), timestamp.
- Webhook (1 gratis, 1 credito/evento) -> push in tempo reale quando un wallet top-20 si muove.
- Trappola: `getTransactionsForAddress`/`getTransfersByAddress` sono BLOCCATI nel free (a pagamento).
  La strada free: getSignaturesForAddress -> batch 100 a Enhanced. Stesso risultato, zero costo extra.

## CFO crediti (free 1M/mese)
- ~101 crediti per snapshot di 100 swap di un token.
- Polling ORARIO su 50 token = ~3.6M/mese -> SFORA. Ogni 2-4h su 20-30 token -> dentro 1M.
- Webhook = 1 credito/evento -> piu' economico del polling cieco.
- Superato 1M: Helius RATE-LIMITA/blocca, NON fattura a sorpresa. Zero rischio addebito.

## Cosa DERIVIAMO in piu' (che la foto top-20 non da')
- whale netflow REALE per singolo wallet (accumulo vs distribuzione)
- wallet NUOVI che entrano vs chi esce
- SMART MONEY: profilare lo storico di un wallet -> win rate sui token passati
- EARLY BUYERS: i primi N compratori ordinati per timestamp

## Alternative gratis da AGGIUNGERE (mirate, free tier stretti)
- Birdeye (30k CU/mese): endpoint top_traders -> top trader gia' rankati per token.
- Vybe (12k crediti, 4 req/min): LABELED wallets -> sai se una whale e' un exchange o smart money vero.
- Scartare: Bitquery (free solo 1 mese), Moralis/GeckoTerminal/Solscan (ridondanti).

## LE 3 AZIONI (da 60% a ~90%, gratis)
1. [+20%] Pipeline SWAP parsate: per ogni token, getSignaturesForAddress(pool) -> Enhanced batch 100 ->
   salva ogni swap (wallet, side, importo, ts). Refresh ogni 2-4h (non ogni ora) per stare sotto 1M crediti.
   Da qui: netflow per-wallet, early buyers, accumulo vs distribuzione.
2. [+7%] Webhook real-time sui top-20 address -> evento push quando una whale si muove (event-driven, non polling).
3. [+3%] Labeling Vybe + top-traders Birdeye, solo sui token caldi (rispettando i rate limit stretti).

Fonti: helius.dev/docs (plans, credits, enhanced-transactions), docs.birdeye.so, docs.vybenetwork.com
