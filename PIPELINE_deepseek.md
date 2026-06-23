# Pipeline X-first + filtri DexScreener — deepseek

## Risposta Brutale e Concreta

### 1. FILTRI NUMERICI (DexScreener + Helius)

Applicati **in ordine rigoroso** (vedi punto 2). Ogni soglia è un **killer** se non rispettata.

#### 🔴 Liquidità (Liquidity.usd)
- **Minima: $10.000** – sotto è rug bait o token morto (es. ROLL, GOOAL).  
- **Massima: nessun cap** – ma attenzione: liquidità > $500k su token <1h può essere wash con LP falso.  
- **Rapporto Volume/Liquidità (24h)** :  
  - **Sano: 2x – 15x** (es. BrimfableAI ~ 233% pump => vol/liqui ~ 3x).  
  - **Wash trading** se <0.5x (nessuna attività reale) oppure >50x (pumping artificiale con bot).  

#### 📈 Volume (24h, 6h, 1h)
- **Minimo 24h: $50.000** – sotto è morto.  
- **Minimo 6h: $20.000** – per rilevare momentum precoce.  
- **Minimo 1h: $5.000** – per ingresso “early”.  

#### ⏳ Età del Pool (pairCreatedAt)
- **Finestra:** tra **1 ora** e **48 ore** dal momento dello scan.  
  - <1h: troppo rischioso (rug flash).  
  - >48h: non è più “early” (opportunità persa).  
- **Ottimale:** 2h – 24h (BrimfableAI era probabilmente 6-12h).  

#### 👥 Holder Count (holders)
- **Minimo: 50** – sotto è bundler o pochi wallet controllati.  
- **Top 10 concentration: max 25%** – sopra = cartello di rug.  
  - Se top1 >10% → allarme, scartare (anche se top10<25%).  

#### 🔄 Buy/Sell Ratio (txns buys / sells)
- **Per finestra 1h:** > **1.5** (pressione compratori).  
- **Per finestra 6h:** > **1.2** (tendenza sostenuta).  
- **Se sells > buys per 1h consecutivi** → dump imminente, non entrare.  

#### 🔐 Mint & Freeze Authority
- **Obbligatorio: entrambi revocati (null)** .  
  - Se ancora attivo → **KILLER** (dev può coniare/congelare).  

#### 🔒 Liquidità Lock / Burn
- **Locked** (es. via Team Finance,