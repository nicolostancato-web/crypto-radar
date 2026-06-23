# Audit dati per l'edge — deepseek

**Risposta brutale:** Il database è incompleto, distorto e l'approccio è sbagliato. Ecco perché:

1. **Dati critici mancanti** (da Helius/CoinGecko):  
   - **Slippage e prezzi reali eseguiti** (non stimati dalla liquidità). Calcola da `swap` tx il prezzo effettivo e confrontalo con il prezzo pool.  
   - **Fonte dei fondi del wallet**: se il wallet è finanziato direttamente da un exchange centrale o da un altro memecoin pump, è un segnale di insider/coordinator.  
   - **Grafo di coordinazione**: chi ha *mandato SOL* a questo wallet? Chi è stato *primo acquirente* del token? Gli insiders si finanziano a catena.  
   - **Token deployer wallet** e sue azioni (rimozioni LP, mint, freeze).  
   - **Variazione della concentrazione holder** nei primi minuti dopo il buy (non solo snapshot statico).  
   - **MeV/pacchetti Jito**: i trade profitabili spesso usano bundle per evitare frontrunning.

2. **Problemi di qualità/bias**:  
   - **Selection bias**: stai osservando wallet con PnL passato positivo, ma la performance è temporanea (mean reversion).  
   - **Look-ahead nelle label**: `copy_net` usa prezzo futuro fino a exit; se exit è triggerata da condizioni future, hai leakage. Usa solo info disponibili al momento del buy.  
   - **Sopravvivenza**: token rugpullati subito potrebbero non apparire se lo swap non è stato registrato (ma Helius dovrebbe includerli).  
   - **Bassa numerosità campione**: 150 wallet non bastano per generalizzare; molti sono probabilmente bot o test.

3. **Quantità dati**:  
   - Non è il numero di eventi (5.600) il problema, ma la **densità di segnale**. Per un edge statistico su memecoin (variance altissima) servono **>50k eventi** e **>500 wallet** indipendenti per avere confidenza. Stai crescendo, ma manca ancora potenza.

4. **Cosa aggiungere ORA**:  
   - **Costruisci un indice di “insiderness”**: per ogni evento, calcola la distanza dal deployer wallet (es. funding chain ≤ 2 hop) e la presenza di acquisti in bundle Jito. Questa è la feature #1 per edge su memecoin.

5. **Approccio sbagliato**:  
   - Copiare wallet *tutti* i loro trade è rumoroso. L’edge è **token-centrico e temporale**:  
     - Nuovi pool su Pump.fun / Raydium con **insider clustering** (primi acquirenti che si ripetono).  
     - **Timing**: acquistare nei primi 30 secondi dopo la creazione del pool, basato su pattern di liquidità e holders.  
     - **Sentiment on-chain**: rapporto buy/sell dei wallet “freschi” (fundati da exchange).  
   - Brutalmente: il copy-trading è un mercato efficiente. L’edge è trovare **token che diventeranno memecoin viral**, non copiare chi li compra.