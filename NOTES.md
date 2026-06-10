# NOTES — idee parcheggiate (da tirare fuori al momento giusto)

> Idee strategiche di Nicolò da NON eseguire ora, ma da ricordare. Ognuna con un trigger.

---

## 1. Allargare oltre Solana memecoin (chain/mercati diversi) — input Nicolò 2026-06-10

**L'idea:** stiamo focalizzando MOLTO su Solana memecoin. Erano il "tetto del mondo" 2-3 anni fa,
ma il mercato si sposta. Forse adesso "accadono più cose in background" altrove — **BNB**, altre
chain, o altri tipi di asset. Stiamo su Solana memecoin perché è **più facile da analizzare**, ma
potrebbe non esserci l'edge: magari l'azione vera è altrove.

**Stato attuale (fatto reale):** il sistema è **Solana-only** — DEXScreener, GeckoTerminal/CoinGecko
e Helius li usiamo tutti scoped su Solana. CoinGecko API però tira fuori **tutte le chain** (BNB,
Base, ETH, ecc.) → si potrebbe esplorare dove c'è più volume/attività adesso.

**NON fare ora.** Restiamo focalizzati su Solana per non disperdere il focus.

**TRIGGER per tirarla fuori:**
- Se dopo i test (backtest + dataset segmentato) **Solana memecoin NON dà edge**, allora PRIMA di
  passare al Piano B (tool), valutare se ripuntare il sistema su un'altra chain/mercato (es. BNB) o
  un altro tipo di asset dove magari l'inefficienza è ancora sfruttabile.
- Oppure: una volta che il sistema funziona, fare un giro veloce su CoinGecko "dove sta il volume
  adesso" per decidere se vale la pena espandere.
