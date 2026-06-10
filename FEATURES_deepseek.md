# Feature set per l'edge — deepseek

## Analisi del Problema

Copiare **tutti** gli acquisti di smart wallet è statisticamente perdente (EV mediano -19,5%, win rate 27%).  
L’edge **esiste** solo in un sottoinsieme definito da condizioni precise di wallet, token, timing e microstruttura.

Qui sotto il set **completo di feature** (40+), ordinato per categoria, con fonte, calcolo e potere predittivo atteso (basso/medio/alto).  
Sfrutto al massimo: **Helius RPC** (tx history, token accounts, mint info), **DEXScreener** (pool status, txn breakdown), **CoinGecko Free** (OHLCV 1min).

---

## 1. WALLET FEATURES (passato e comportamento)

| # | Feature | Cosa misura | Perché predittiva | Fonte / Calcolo | Potere |
|---|---------|-------------|-------------------|-----------------|--------|
| 1 | **w_pnl** | PnL storico chiuso del wallet (in SOL/USD) | Wallet con PnL positivo tendono a selezionare meglio i token | Da tutti i trade chiusi del wallet (Helius: swap tx, ricava prezzi) | **Alto** |
| 2 | **w_winrate** | % di trade chiusi in profitto | Indicatore di skill + risk management | Conta win/loss su trades chiusi | **Alto** |
| 3 | **w_avg_hold_minutes** | Tempo medio di detenzione (trades chiusi) | Svela orizzonte temporale; copy con latenza richiede hold brevi per non perdere coda | Da delta timestamps buy/sell su chain | **Alto** |
| 4 | **w_median_buy_usd** | Dimensione tipica di acquisto (mediana) | Aiuta a calibrare dimensione copy (evita eccessivo impact) | Distribuzione di `buy_usd` nello storico wallet | **Medio** |
| 5 | **w_std_buy_usd** | Variabilità della taglia di acquisto | Wallet che variano molto possono avere strategie più complesse (non replicabili) | Deviazione standard di buy_usd | **Medio** |
| 6 | **w_profit_factor** | ( Somma wins ) / ( | win/loss ratio | **Alto** |
| | | | | somma losses ) | |
| 7 | **w_sharpe** | Sharpe ratio approssimato sui trade chiusi | Misura risk-adjusted; wallet con Sharpe>1 hanno maggior probabilità di edge | Media(return) / std(return) su tutti i trade chiusi | **Alto** |
| 8 | **w_consecutive_wins** | Lunghezza media streak di win consecutivi | Alcuni wallet sono in fase calda; può indicare regime attuale | Media di win streak, ultima streak attiva | **Medio** |
| 9 | **w_time_since_last_trade_minutes** | Da quanto non compra | Wallet inattivi da molto potrebbero aver cambiato strategia | Ultimo timestamp di buy - now | **Basso** |
| 10 | **w_whale_score** | Quota di SOL/Token del wallet rispetto alla totalità osservata | Wallet grandi (top 5% balance) hanno più potere di mercato e informazioni | Percentile di balance SOL su tutti i wallet smart | **Medio** |
| 11 | **w_unique_tokens_30d** | Numero di token diversi scambiati negli ultimi 30 giorni | Wallet che cambiano spesso token (elevata rotazione) sono più rumorosi | Conta token distinti nei buy recenti | **Medio** |
| 12 | **w_rug_buy_rate** | % di token che poi hanno fatto rug (liquidity <10% after buy) | Rileva se il wallet ha un buon filtro anti-rug | Da rug check su ogni token comprato | **Alto** |
| 13 | **w_coordination_score** | Quante volte il wallet ha comprato lo **stesso token** di altri smart wallet entro 1h | Misura appartenenza a un gruppo di insider/coordinator | Overlap storico | **Alto** |
| 14 | **w_execution_slippage_avg** | Slippage medio subito nei buy passati | Wallet abile negozia con slippage basso, indica miglior execution | Da tx Helius: (price_expected - price_actual) / price_expected | **Medio** |

---

## 2. TOKEN FEATURES (caratteristiche del memecoin)

| # | Feature | Cosa misura | Perché predittiva | Fonte / Calcolo | Potere |
|---|---------|-------------|-------------------|-----------------|--------|
| 15 | **token_age_minutes** | Minuti da quando la pool è stata creata (pairCreatedAt) | Token molto giovani (<1h) hanno alta incertezza ma anche maggior upside; dopo 24h l’edge decade | DEXScreener `pairCreatedAt` | **Alto** |
| 16 | **liquidity** | Liquidità attuale della pool (USD) | Bassa liquidità → alto price impact, ma anche più probabile rug; liqu>50k$ meno volatilità ma meno alpha | DEXScreener `liquidity.usd` | **Alto** |
| 17 | **volume_24h** | Volume di scambio nelle ultime 24h | Indica hype e liquidità reale; volume/liquidity ratio >5 spesso pump&dump | DEXScreener `volume.h24` | **Medio** |
| 18 | **volume_1h / volume_24h** | % di volume concentrato nell’ultima ora | Segnale di accelerazione (wicks) | Volume 1h da DEXScreener txns buy/sell | **Alto** |
| 19 | **price_change_1h** | Variazione di prezzo ultima ora | Momento dell’acquisto (upswing vs downswing) | DEXScreener `priceChange.h1` | **Medio** |
| 20 | **price_change_since_first_smart** | Variazione da quando il primo smart wallet ha comprato | Se è già salito molto (>50%), probabile fomo tardivo | Calcolo con timestamp primo buy smart | **Alto** |
| 21 | **price_volatility_1h** | Deviazione std del prezzo su ultima ora (1min candles) | Alta volatilità → rischio ma anche gamma per copy | Da OHLCV CoinGecko (se disponibile) o da swap tx ogni minuto | **Medio** |
| 22 | **holders_total** | Numero totale di holder del token | Pochi holder (<100) = centralizzato, molti = distribuito | Helius `getTokenLargestAccounts` (size >0) | **Medio** |
| 23 | **holder_concentration_top10** | % di supply detenuta dai top 10 | Se >80% → rischio rug (pochi controllano) | Somma quantità top10 / token supply | **Alto** |
| 24 | **liquidity_to_supply_ratio** | Liquidità / Market Cap (se calcolabile) | Misura quanto è facile scaricare; ratio >20% = più sicuro | DEXScreener liquidity / (price * supply) | **Medio** |
| 25 | **txn_buy_sell_ratio_1h** | (Buy count / Sell count) o (Buy volume / Sell volume) nell’ultima ora | Se >1.5 → pressione acquisto, probabile continuazione | DEXScreener txns count by type | **Alto** |
| 26 | **pool_type** | Raydium, Orca, Meteora, Pump.fun? | Pool su AMM consolidati hanno meno rischi di rug; pump