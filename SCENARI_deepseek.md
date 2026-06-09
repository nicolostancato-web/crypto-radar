# 10 Scenari — deepseek

## Roadmap: 10 Scenari per Sfruttare la Smart-Money su Solana Memecoin (Free, Polling 2h)

**Vincoli critici:** latenza elevata (2h), nessun insider, solo dati pubblici free (GeckoTerminal /trades, OHLCV; Helius RPC storia wallet/PnL; DexScreener). Ogni scenario va testato per 6-12h di trading simulato, con slippage minimo del 10% (come da fallimento copy-trading). Ordine dal più promettente al meno.

---

### 1. Smart‑Exit Overlay
- **IPOTESI:** I wallet profittevoli vendono in modo strutturato (grossi blocchi, pattern) che sopravvive alla latenza di 2h. Anche se entriamo dopo, uscire insieme a loro ci dà un edge netto.
- **METODO:**  
  - Seleziona 30 wallet con PnL realizzato > 5 SOL negli ultimi 7 giorni (Helius RPC `getSignaturesForAddress` + `getTransaction` per calcolare PnL aggregato).  
  - Per ogni nuovo token in top 50 volumi su GeckoTerminal, monitora gli *sell trades* aggregati di questi wallet ogni 2h.  
  - **Entry:** Compra al prezzo OHLCV di apertura della candela 2h quando il volume di acquisto di questi wallet nelle 2h precedenti è > 500 USD e il prezzo è entro +20% dal loro prezzo medio di acquisto (estratta da trade history).  
  - **Exit:** Vendi alla candela successiva (2h dopo) *se* il volume di vendita aggregato dei wallet è > 30% del loro volume di acquisto medio nelle 2h oppure se il prezzo scende sotto una trailing stop loss del 15%. Altrimenti tieni per max 5 candele.
- **SUCCESSO:** EV netto >+3% su almeno 30 paper trade, slippage simulato 10% su entry+exit.  
- **PARK:** Se dopo 50 trade l'EV è <0 e la varianza non scende, o se la frequenza di segnali è <1 ogni 10 token (mancanza di dati).  
- **TEMPO:** 3-5 giorni di accumulo (6-10 iterazioni 2h).  
- **PROBABILITÀ:** Media – l'effetto “uscita in blocco” è osservabile, ma la latenza potrebbe farci perdere i movimenti rapidi.

---

### 2. Deployer Reputation Score
- **IPOTESI:** Il deployer di un token ha un track record: se ha sempre creato pump‑and‑dumps, il token è da evitare; se ha progetti con chart decenti e profitti per early buyer, è un segnale long.
- **METODO:**  
  - Usa Helius RPC per trovare il deployer: per ogni token nella top 50 volumi, recupera la signature di `createAccount` + istruzione di creazione pool (DexScreener fornisce `pairCreatedAt` ma non ancora deployer). Alternativa: GeckoTerminal non dà deployer. Quindi via Helius: recupera tutte le transazioni del token (primo mint) e trova l'address che ha inviato la prima fee.  
  - Calcola score su 3 fattori: (a) numero di token creati > 5, (b) rapporto di sopravvivenza (token ancora sopra $0.00001 dopo 7 giorni) > 30%, (c) PnL medio dei primi 10 acquirenti (Helius RPC per wallet che hanno comprato entro 10 blocchi dalla creazione) > 0.  
  - **Entry:** Compra solo se lo score > 50 (normalizzato 0-100) e il token ha volume > 500 SOL nelle prime 2h.  
  - **Exit:** Trailing stop loss 20% dal massimo storico toccato, oppure take profit 50% se la candela 2h successiva ha volume < 30% della media mobile (7 candele).  
- **SUCCESSO:** EV netto >+5% su 20 paper trade (perché segnali rari).  
- **PARK:** Se in 10 token con score alto nessuno ha EV+ (probabile se i buoni deployer sono rari o i dati di PnL early sono inaccessibili).  
- **TEMPO:** 7-10 giorni per raccogliere abbastanza deployer con dati storici.  
- **PROBABILITÀ:** Bassa – la qualità dei dati deployer è scarsa su script free (spesso il deployer è un contratto factory), e i veri “bravi” non riutilizzano wallet.

---

### 3. Cluster Coordinato (Copy‑Trading di Gruppo)
- **IPOTESI:** Un gruppo di wallet che compra gli stessi token nello stesso blocco ha potere di segnalazione. Anche con 2h di ritardo, se il cluster accumula lentamente per ore, possiamo inserirci.
- **METODO:**  
  - Estrai da GeckoTerminal /trades una lista di 100 wallet con almeno 20 trades ciascuno. Per ogni coppia di wallet, calcola co‑occorrenza (stesso token, stesso blocco o entro 5 minuti). Usa una soglia di similarità > 0.3. Cluster gli wallet con algoritmo di community detection (es. label propagation).  
  - Per ogni token nuovo, controlla se almeno 2 wallet dello stesso cluster hanno comprato nelle ultime 2h per un totale > 1000 USD.  
  - **Entry:** Compra quando il prezzo è ancora entro +15% dal prezzo medio di acquisto del cluster (estratto dai trades).  
  - **Exit:** Vendi quando il totale delle vendite del cluster nelle ultime 2h supera il 40% del loro totale acquistato per il token, oppure dopo 48h se ancora in posizione.  
- **SUCCESSO:** EV netto >+2% su 20 paper trade, con drawdown massimo <20%.  
- **PARK:** Se il segnale è troppo raro (<1 ogni 30 token) o i cluster sono instabili (cambi ogni giorno).  
- **TEMPO:** 4-6 giorni di raccolta storica + 3 giorni di test live.  
- **PROBABILITÀ:** Medio‑bassa – la latenza 2h spesso perde la finestra di ingresso, ma i cluster lenti possono funzionare.

---

### 4. Regime Filter (Risk‑On/Off)
- **IPOTESI:** I memecoin prosperano solo in fasi di mercato bullish. Un filtro basato su volume aggregato e trend SOL separa periodi di alta probabilità.
- **METODO:**  
  - Calcola su base rolling 24h: (a) volume totale su tutti i memecoin (top 100 su DexScreener) > $50M, (b) prezzo SOL trend rialzista (> -5% ultimi 3 giorni), (c) numero di nuovi token lanciati > 200 nelle ultime 24h.  
  - Se tutte le condizioni sono vere → regime “risk‑on”. Altrimenti astieniti.  
  - Applica questo filtro a qualsiasi altra strategia (es. smart‑exit o cluster). Testa prima su un semplice “buy at first 2h candle and hold 48h”.  
  - **Entry/Exit:** solo quando regime è on.  
- **SUCCESSO:** La stessa strategia base con filtro ha Sharpe > 0.5 e EV >+2% netto, mentre senza filtro è negativa (baseline).  
- **PARK:** Se il regime non discrimina (es. Sharpe migliora <0.1) o il segnale è sempre on (nessuna variabilità).  
- **TEMPO:** 5-7 giorni per vedere fasi sufficienti (almeno 2 periodi off).  
- **PROBABILITÀ:** Media – facile da implementare, ma i dati volume di DexScreener potrebbero non essere gratuiti illimitatamente.

---

### 5. Elite Wallet Momentum Following
- **IPOTESI:** I migliori trader (top 5% per Sharpe ratio) hanno un vantaggio informativo. Se comprano un token e lo tengono per più di 2h, possiamo copiarli con ritardo e vendere con loro o prima.
- **METODO:**  
  - Identifica i 20 wallet con Sharpe ratio > 1.5 sui trades degli ultimi 7 giorni (Helius PnL + GeckoTerminal trade data).  
  - Per ogni wallet, monitora i suoi acquirenti di token su GeckoTerminal (endpoint `/trades` con address filter).  
  - **Entry:** Se un wallet elite acquista un token per >1000 USD e lo tiene ancora dopo la prossima candela 2h (controlla che non abbia venduto), allora compra quando il prezzo è entro +10% dal suo prezzo medio di acquisto.  
  - **Exit:** Vendi quando lo stesso wallet vende (dato di candela successiva) o dopo 4 candele (8h) se non vende.  
- **SUCCESSO:** EV netto >+1% su almeno 20 trade con slippage 10%.  
- **PARK:** Se i wallet elite cambiano rapidamente o i segnali sono <1 ogni 5 giorni.  
- **TEMPO:** 5-8 giorni.  
- **PROBABILITÀ:** Bassa – il wallet elite potrebbe non essere affatto “elite” su memecoin (noise), e la latenza ci fa perdere il prezzo migliore.

---

### 6. Smart Accumulation Detection (Dip Buying)
- **IPOTESI:** Quando wallet con PnL positivo accumulano un token mentre il prezzo scende, è un segnale di raccolta. Possiamo entrare con loro dopo 2h.
- **METODO:**  
  - Per ogni token, usa Helius RPC per ottenere tutti i wallet che hanno PnL positivo su quel token (o globalmente). Filtra quelli con >5 SOL di guadagno.  
  - Calcola il flusso netto (acquisti - vendite) di questi wallet nelle ultime 2h. Se netto positivo > 500 USD, e il prezzo (OHLCV close) è sceso di almeno 5% nelle ultime 2h, è un segnale di accumulo.  
  - **Entry:** Compra alla prossima candela 2h (quindi dopo 2-4h dall'accumulo).  
  - **Exit:** Trailing stop loss 10% oppure vendi quando il flusso netto diventa negativo per 2h consecutive.  
- **SUCCESSO:** EV netto >+3% su 15 trade.  
- **PARK:** Se la frequenza di segnali è <1 ogni 50 token (dati troppo rari) o il segnale è sempre falso (dip buying non esiste su memecoin).  
- **TEMPO:** 6-8 giorni.  
- **PROBABILITÀ:** Bassa – il “dip” su memecoin è spesso una trappola, e i wallet smart potrebbero essere bot.

---

### 7. Liquidity Analysis (LP Lock & Risk)
- **IPOTESI:** I token con LP bloccato o con un profilo di liquidità stabile hanno meno rischio di rug pull e quindi EV positivo.
- **METODO:**  
  - Usa DexScreener per ogni token: recupera `liquidityUSD`, `liquidity` (reserve), `pairCreatedAt`. Verifica se la liquidità è aumentata o diminuita nelle ultime 24h.  
  - Calcola score: (a) liquidità bloccata? (non free, ma possiamo vedere se la riserva è cambiata – se stabile, probabile lock? Approssimazione). (b) rapporto volume/liquidità < 10 (evita wash trading). (c) LP provider top 2 wallet hanno meno del 60% della liquidità totale (decentramento).  
  - **Entry:** Compra solo se score > 70 (su 100).  
  - **Exit:** Vendi se la liquidità scende del 20% in 2h o se il prezzo supera +100% (profit taking).  
- **SUCCESSO:** EV netto >+1% su 20 trade, con drawdown <15%.  
- **PARK:** Impossibile verificare LP lock gratis; i dati riserve di DexScreener possono essere manipolati (rug pull).  
- **TEMPO:** 4-6 giorni.  
- **PROBABILITÀ:** Molto bassa – i veri rug pull hanno LP simulato, i dati non bastano.

---

### 8. Cross‑DEX Price Arbitrage (Latency Killer)
- **IPOTESI:** A volte lo stesso token ha prezzi diversi su Raydium, Orca, Meteora per pochi secondi/minuti. Con 2h di polling è inutile, ma forse alcune discrepanze persistono per ore (es. su token illiquidi).
- **METODO:**  
  - Con DexScreener, confronta il prezzo dello stesso token su due DEX (cerca `marketId` diversi).  
  - Se la differenza percentuale > 15% e il volume su entrambi è > 500 SOL, esegui una simulazione: compra su DEX più economico, vendi sull'altro. Slippage simulato al 10% per lato.  
  - **Entry/Exit:** esegui ogni 2h.  
  - **SUCCESSO:** Profitto netto medio per trade > 0 dopo slippage.  
  - **PARK:** Dopo 20 tentativi, nessun trade profittevole (la latenza uccide).  
- **TEMPO:** 3 giorni.  
- **PROBABILITÀ:** Quasi zero – non esiste free lunch persistente con 2h di ritardo.

---

### 9. Social Signal Proxy (DexScreener Trending)
- **IPOTESI:** I token “trending” su DexScreener attirano volume e smart money. Possiamo entrare all'inizio della tendenza.
- **METODO:**  
  - Usa l'API DexScreener (gratis ma limitata) per ottenere i token top trend (sconosciuto se esiste endpoint; in alternativa, possiamo ordinare per volume 24h).  
  - **Entry:** Compra i primi 5 token per volume nelle ultime 2h, ma solo se il volume è aumentato > 2x rispetto alla candela precedente.  
  - **Exit:** Vendi dopo 2h (hold per 2h) o se il volume crolla del 50%.  
- **SUCCESSO:** EV netto >+0.5% su 50 trade (molto basso perché è rumoroso).  
- **PARK:** Se dopo 100 trade l'EV è negativo o nullo.  
- **TEMPO:** 3-4 giorni.  
- **PROBABILITÀ:** Molto bassa – è sostanzialmente momentum retail, già battuto.

---

### 10. Baseline: Buy First Candle Hold 48h (Futility Check)
- **IPOTESI:** Serve come controllo negativo. Comprando ogni token al lancio (prima candela 2h) e tenendo 48h, perdiamo soldi. Confermiamo che il sistema funziona e che i filtri servono.
- **METODO:**  
  - Per ogni nuovo token che appare su DexScreener con volume > 100 SOL nella prima 2h, compra a market (prezzo close).  
  - **Exit:** Vendi alla close della candela 48h.  
- **SUCCESSO:** Nessuno – lo scenario deve fallire per validare la metodologia.  
- **PARK:** Se per miracolo EV > 0 (allora tutto il resto è inutile).  
- **TEMPO:** 2 giorni (24-48h di trading).  
- **PROBABILITÀ:** Zero di profitto, ma necessario per avere un baseline.

---

## Ordine di Test Raccomandato

1. **Scenario 10** (Baseline) – per assicurarsi che l'ambiente di paper trading e i dati funzionino, e per confermare il fallimento naive.
2. **Scenario 4** (Regime Filter) – applicabile a tutte le successive, va calibrato per primo.
3. **Scenario 1** (Smart‑Exit Overlay) – più promettente di tutti, da testare subito dopo il regime.
4. **Scenario 2** (Deployer Reputation) – richiede più setup ma ha segnali indipendenti.
5. **Scenario 3** (Cluster Coordinato) – simile al 1 ma più complesso; dopo aver visto i risultati del 1 si decide se procedere.
6. **Scenario 5** (Elite Wallet Following) – probabilità bassa, ma veloce da testare.
7. **Scenario 6** (Smart Accumulation) – può essere fuso col 1, test separato se tempo.
8. **Scenario 7** (Liquidity Analysis) – bassissima probabilità, ma se i primi funzionano si può ignorare.
9. **Scenario 8** (Cross‑DEX Arbitrage) – test rapido per escludere formalmente.
10. **Scenario 9** (Social Trend) – ultimo, quasi sicuramente inutile.

**Nota brutale:** 7 su 10 falliranno. L'unico con possibilità realistica di EV positivo è lo Smart‑Exit Overlay (scen. 1), ma solo se la latenza 2h non distrugge il segnale. I cluster (3) e il deployer (2) sono secondi con probabilità media. Altri sono pura speculazione – vanno testati per avere evidenza solida da presentare, non per profitto.