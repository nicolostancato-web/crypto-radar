# 10 Scenari — gpt5

1) Cluster Accumulation (co-buy coordinato)
1. Ipotesi: quando 3+ wallet storicamente profittevoli accumulano lo stesso token entro 60 minuti con size aggregata rilevante, c’è follow-through tradabile anche con polling orario.
2. Metodo di test:
   - Discovery pool: DEXScreener /latest/dex/search?q=solana (top pairs) -> pairs/solana/{pairAddress} per volumeUsd, txns, buyers/sellers, liquidityUsd, fdv, age.
   - Trades: GeckoTerminal /api/v2/networks/solana/pools/{pool}/trades?limit=500 (wallet, side, sizeUsd, price, ts).
   - “Smart set”: per gli ultimi 30 giorni, via Helius enriched tx (GET /v0/addresses/{address}/transactions?api-key=..., o batch by pool signer) ricostruisci swap buy/sell in USD e realizza PnL per wallet (FIFO semplice per ogni mint). Smart = realized PnL tot > $5k, winrate > 55%, N trade chiusi ≥ 20.
   - Cluster event per token: in finestra T=60m, unique smart wallet ≥ 3 e net buy USD ≥ $10k; feature: uniqueSmart, netSmartBuy, timeSinceCreation, buyers/sellers h1 (DEXScreener).
3. Regole ingresso/exit:
   - Ingresso: al primo poll dopo evento cluster se: uniqueSmart ≥ 3, netSmartBuy ≥ $10k, buyers/sellers h1 ≥ 1.2, liquidityUsd $30k–$500k, age ≤ 3d, prezzo ≤ +5% dal max 1h.
   - Size paper: 1% NAV max o $500 fissi (coerente col rischio).
   - Exit: TP +40%, SL -20%, time stop 24h; exit immediato se netSmartFlow(last 2h) ≤ -$5k.
4. Criterio di successo: EV netto (slippage 10% + fee 0.25%) ≥ +8% su ≥ 40 trade; Sharpe 6h-24h ≥ 0.5; maxDD ≤ 35%.
5. Criterio di park: < 0.5 segnali/giorno dopo 5 gg; EV ≤ 0 dopo 80 trade; delay mediano evento→ingresso > 60m; mixer/CEX offuscano i top wallet (match rate < 60%).
6. Tempo al verdetto: 4–7 giorni (8–14 run da 6–12h).
7. Probabilità EV+: medio-alta. La coordinazione esiste; il limite è la latenza ma i trend spesso durano ore.

2) Smart-EXIT overlay (uscire sui sell dei bravi)
1. Ipotesi: applicare un overlay di uscita basato sulle vendite dei wallet profittevoli migliora EV e DD di un momentum entry banale.
2. Metodo di test:
   - Base entries: Momentum 15m su DEXScreener/Gecko OHLCV: buy quando close > max(ultime 20 candele 15m) di ≥ 2%, buyers/sellers h1 ≥ 1.5, liquidityUsd $40k–$600k, age < 7d.
   - Monitor smart-sell: GeckoTerminal trades filtrati su smart set (come scen.1).
   - A/B: per ogni entry, ramo A senza overlay, ramo B con overlay; metriche PnL, MDD, winrate.
3. Regole ingresso/exit:
   - Ingresso (per entrambi): come sopra.
   - Exit overlay (B): vendi 100% se in 1h 2+ smart wallet vendono tot ≥ $5k OPPURE cumulative smart sells delle ultime 2h ≥ 30% dei loro cumulative buys sul token. Fallback: SL -25%, trailing stop 20%, time stop 24h.
4. Criterio di successo: overlay migliora mediana PnL trade di ≥ +5% assoluti e riduce 95% drawdown ≥ 30% vs controllo, N trade abbinati ≥ 60; EV netto ≥ +5%.
5. Criterio di park: precisione dei segnali di sell < 55% nel predire top locali (±1h); < 30 trigger/5gg; overlay esce troppo tardi (lag mediano > 2h dal top).
6. Tempo al verdetto: 3–5 giorni.
7. Probabilità EV+: media. Uscite dei bravi spesso anticipano la fine del move; latenza accettabile per l’EXIT.

3) Deployer/Dev reputation + hygiene gate
1. Ipotesi: token da deployer con storico “pulito” e con hygiene on-chain (mint/freeze revocati presto) hanno base-rate migliore e meno rug.
2. Metodo di test:
   - Nuove pair: DEXScreener (age < 24h).
   - Metadata: Helius token-metadata (mintAuthority, freezeAuthority, supply, decimals).
   - Deployer: Helius enriched tx sul primo add-liquidity -> signer primario; storico 90gg: #token creati, %rug (drawdown -90% in 48h), median ATHx, % con revoke entro 2h.
   - Hygiene: mintAuthority=None + freezeAuthority=None entro 2h; liquidityUsd ≥ $40k; nessun LP removal > 40% nelle prime 6h (Helius: istruzioni Raydium/Orca remove).
3. Regole ingresso/exit:
   - Score deployer 0–1: 1 - (rugRate) * 0.5 + (revokeRate entro 2h)*0.3 + (medianATHx normalized)*0.2. Ingresso se score ≥ 0.6, hygiene OK, age 30–180m, m15 vol > $20k, buyers/sellers ≥ 1.2, prezzo ∈ [VWAP1h -10%, VWAP1h +15%].
   - Exit: SL -20%, TP +50%, exit se LP removal > 20% in 1h o se deployer riceve > 20% supply indietro in 1h.
4. Criterio di successo: EV netto ≥ +7% su ≥ 50 trade; rug rate ≤ 5% (vs baseline > 15%).
5. Criterio di park: deployer sempre nuovi (no reputazione riusabile), metadata incompleti, filtri troppo restrittivi (< 1 segnale/giorno dopo 5gg), nessun miglioramento rug-rate.
6. Tempo al verdetto: 5–10 giorni.
7. Probabilità EV+: media. Hygiene aiuta, ma dev “usa-e-getta” riducono la trasferibilità della reputazione.

4) Regime filter overlay (risk-on Solana)
1. Ipotesi: filtrare ingressi solo in regime risk-on (macro/breadth/volume) aumenta winrate e riduce code losers.
2. Metodo di test:
   - SOL regime: DEXScreener SOL/USDC 4h OHLCV -> regime ON se close > SMA20(4h) e RSI14(4h) > 55.
   - Breadth: top 200 pairs Solana (DEXScreener) -> % con h1 change > +5% e buyers>sellers; ON se > 55%.
   - Volume: somma vol1h top 200; ON se > 70° percentile di 30d per quella fascia oraria.
   - Applica overlay su una base-strategy (es. scen.1 o momentum base).
3. Regole ingresso/exit:
   - Ingresso: permetti segnali base solo se regime=ON nell’ultimo poll.
   - Exit: come base; opzionale hard exit se regime passa OFF e PnL < +10%.
4. Criterio di successo: +10 pp winrate e EV ≥ +6% vs unfiltered su ≥ 80 trade; maxDD ridotto ≥ 25%.
5. Criterio di park: regime ON < 20% del tempo (sample insufficiente), nessun delta EV ≥ +3%, ritardi > 4h nel catturare svolte.
6. Tempo al verdetto: 4–7 giorni.
7. Probabilità EV+: media. Il regime conta; semplice da implementare e riusabile come overlay.

5) LP fee harvest su churn di cluster (DeFi yield arbitrage)
1. Ipotesi: durante churn elevato indotto da cluster, le fee LP nelle 6h successive superano l’IL su orizzonte breve.
2. Metodo di test:
   - Trigger: evento cluster (scen.1) con txns h1 ≥ 300 e volume1h ≥ $200k (DEXScreener).
   - Fee model: assume AMM 0.25% (Raydium). Fees6h ≈ volume6h * 0.25% * (quotaPool). quotaPool ≈ L / (liquidityUsd + L).
   - IL: usa prezzo inizio/fine 6h (Gecko OHLCV 5m/15m) su x*y=k; IL% = 2*sqrt(r)/(1+r) - 1 con r = P_end/P_start (assumi quote bilanciate).
   - Paper-LP: L tale che quotaPool ≤ 1%.
3. Regole ingresso/exit:
   - Ingresso LP se stima (Fees6h - IL) ≥ +1.0% e liquidityUsd $50k–$500k.
   - Exit: a 6h o se nuova stima (ad ogni poll) scende < 0% per due poll consecutivi.
4. Criterio di successo: PnL medio per “deposito 6h” ≥ +0.5% su ≥ 30 simulazioni; share di casi negativi ≤ 35%.
5. Criterio di park: pool CLMM (range) prevalenti (modello errato), fee tier ignoto -> errore stima > 30%, segnale raro (< 1/gg) o PnL mediano ≤ 0.
6. Tempo al verdetto: 5–8 giorni.
7. Probabilità EV+: medio-bassa. Può funzionare solo su vol/flat; IL spesso mangia le fee.

6) Coordinated rotation (uscita A → ingresso B)
1. Ipotesi: i cluster spostano capitale in blocco; comprare il “successore” entro 2h dall’uscita dal precedente dà edge.
2. Metodo di test:
   - Con Helius, stima posizioni per cluster per token. Evento “exit A”: net sell cluster > $10k e riduzione posizione > 50% in 3h.
   - Cerca “entry B”: entro 2h, net buy cluster ≥ $8k su altro token; seleziona quello con net buy max; conferma buyers/sellers ≥ 1 (DEXScreener).
3. Regole ingresso/exit:
   - Ingresso: al primo poll con entry B confermata, prezzo sopra VWAP15m e ≤ +2% dal max 1h.
   - Exit: TP +35%, SL -18%, oppure se cluster torna net seller > $4k in 2h.
4. Criterio di successo: EV netto ≥ +8% su ≥ 30 trade; rank mediano del ritorno 6h ≥ 60° percentile vs universo.
5. Criterio di park: < 10 rotazioni/settimana, cluster instabili, EV ≤ 0 dopo 40 trade.
6. Tempo al verdetto: 5–8 giorni.
7. Probabilità EV+: medio-bassa. Rotazioni esistono ma sono rumorose/spezzate.

7) Post-renounce momentum (SetAuthority→None)
1. Ipotesi: il revoke di mint/freeze è uno shock di fiducia che genera drift positivo nelle ore successive.
2. Metodo di test:
   - Event detection: Helius enriched tx -> istruzioni SetAuthority(Mint/Freeze) con newAuthority=None per mint del token.
   - Misura: pre/post returns con Gecko/DEXScreener OHLCV; filtra age < 7d, liquidityUsd $30k–$500k, no LP removal > 20% ultime 2h.
3. Regole ingresso/exit:
   - Ingresso: alla prima chiusura 15m ≥ VWAP15m dopo l’evento, volume1h ≥ $15k.
   - Exit: TP +25%, SL -15%, time stop 12h.
4. Criterio di successo: EV netto ≥ +5% su ≥ 40 eventi; share ritorni 6h > 0 almeno 55%.
5. Criterio di park: eventi rari (< 1/gg), reazione già esaurita (median + >10% entro 2h dall’evento), manipolazioni frequenti.
6. Tempo al verdetto: 4–10 giorni.
7. Probabilità EV+: medio-bassa. Segnale pulito ma spesso tardivo.

8) First-retrace buy (dip “pulito” con pressione acquisti)
1. Ipotesi: il primo ritraccio 20–35% dopo un raddoppio iniziale rimbalza se il flusso acquirente rimane netto.
2. Metodo di test:
   - OHLCV (Gecko/DEXScreener) per rilevare +100% dal listing e poi drawdown 20–35%; ultima ora: buyers ≥ sellers e net inflow USD > 0 (Gecko trades).
3. Regole ingresso/exit:
   - Ingresso: prezzo ∈ [0.62, 0.77]*max1h (zona 23.6–38.2% retrace), close 15m verde, age < 3d, hygiene OK se disponibile.
   - Exit: TP +30%, SL -12% sotto swing low, time stop 8h.
4. Criterio di successo: EV netto ≥ +6% su ≥ 60 trade; stop-out rate ≤ 65%.
5. Criterio di park: gap/slippage rendono SL inefficace; sample scarso.
6. Tempo al verdetto: 3–6 giorni.
7. Probabilità EV+: medio-bassa. TA pura rumorosa; filtro flussi migliora ma non risolve.

9) Secondary LP add (liquidity spike follow)
1. Ipotesi: un +50% di liquidità senza dump di prezzo indica domanda organica e supporta un leg up.
2. Metodo di test:
   - Helius: detect add-liquidity (Raydium/Orca program IDs), somma incremento riserve in 2h; contare unique LP adders ≥ 3.
   - DEXScreener: conferma jump liquidityUsd +50%, txns up, price near VWAP.
3. Regole ingresso/exit:
   - Ingresso: dopo conferma spike, prezzo entro ±10% di VWAP2h, buyers/sellers h1 > 1, age < 5d.
   - Exit: TP +20%, SL -12%, exit su LP removal > 20%.
4. Criterio di successo: EV netto ≥ +4% su ≥ 40 trade.
5. Criterio di park: eventi rari/rumorosi o usati come bait (mediana < 0% post-event), difficoltà nel parsing LP per CLMM.
6. Tempo al verdetto: 5–10 giorni.
7. Probabilità EV+: bassa-media. Segnale concreto ma spesso già “priced in”.

10) Prodotto dati/alert (SNR e latenza)
1. Ipotesi: anche senza EV diretto, alert ad alto SNR (cluster, renounce, LP spike) con lead time utile sono monetizzabili.
2. Metodo di test:
   - Genera alert per top 3 segnali (scen.1,7,9). Logga: t_event (on-chain), t_alert (prossimo poll), latenza, r+1h, r+6h.
   - Simula utente: ingresso alla prossima close 15m, exit +20%/-15%.
3. Regole ingresso/exit: solo per valutazione (come sopra).
4. Criterio di successo: top 20% alert per score interno (intensità segnale) con EV ≥ +7%, maxDD < 20%, latenza mediana ≤ 20m; AUC ≥ 0.6 vs random.
5. Criterio di park: nessun tipo supera EV +3% nel top quintile; latenza mediana > 60m; N<100 alert/7gg.
6. Tempo al verdetto: 5–7 giorni.
7. Probabilità EV+: media (come prodotto, non come trading). SNR > trading live grazie all’uso “umano” del contesto, ma la latenza free è il collo di bottiglia.

Note implementative comuni (per tutti gli scenari):
- Slippage simulata: 10% sull’ingresso e 10% sull’uscita per stress-test (o 10% solo ingresso se vuoi riprodurre il tuo test precedente); fee 0.25%; gas Solana trascurabile.
- Universe: limita a top 300 pair Solana per volume nelle ultime 24h (DEXScreener) per rimanere nei limiti free.
- Clustering wallet: grafo di co-trade; arco tra due wallet se hanno co-buyato lo stesso token in finestra ≤ 2h su ≥ 3 token negli ultimi 7d; cluster = componenti con degree medio ≥ 2. Ricalcolo giornaliero.

Ordine di test consigliato (e perché):
1) Cluster Accumulation — massima leva sugli angoli “coordinati”; segnale forte, chiaro, misurabile.
2) Smart-EXIT overlay — quick win potenziale: migliora qualunque entry, costo implementativo basso.
3) Regime filter overlay — overlay trasversale che evita periodi tossici; migliora SNR dei test successivi.
4) Deployer/Dev reputation + hygiene — riduce tail-risk (rug); utile come gate per tutti gli altri.
5) LP fee harvest su churn — unico vero “arbitraggio” DeFi testabile con polling; o funziona o si parcheggia.
6) Coordinated rotation — sfrutta il comportamento dei cluster già identificati; complessità media.
7) Post-renounce momentum — evento netto, facile da automatizzare; frequenza variabile.
8) First-retrace buy — TA condizionale: utile come baseline “market-structure”.
9) Secondary LP add — evento meno predittivo, ma semplice da escludere sistematicamente.
10) Prodotto dati/alert — fallback monetizzabile se gli edge di trading restano borderline; misura SNR/latency.

Brutalità finale:
- Se scen.1–4 falliscono (EV ≤ 0 dopo campione adeguato), l’edge orario free su memecoin Solana è strutturalmente eroso: passa a prodotto/alert (scen.10) o LP fee opportunistico (scen.5) nei soli momenti di churn estremo.