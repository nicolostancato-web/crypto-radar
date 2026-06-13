# Roadmap Stato — Scenari (consenso GPT-5 + DeepSeek)

> Stato vivo. Aggiornato a ogni auto-analisi (ogni ~6h). Legenda stato:
> 🔵 ATTIVO · ⏳ DA TESTARE · 🅿️ PARK (vicolo cieco, col motivo) · 🟢 FUNZIONA (avvisare Nick)

**Scenario attivo:** S3_cluster (fail-fast: parto dai due ad alta conviction)
**Loop auto-analisi:** 🟢 LIVE — gira in cloud ogni 6h (auto_analysis.py)
**Slippage simulato:** 10% entry + 10% exit · fee 0.25% (stress test, come il fallimento copy-trading)

---

## Ordine di test (consenso dei due modelli)

| # | Scenario | Conviction | Stato | Verdetto |
|---|----------|-----------|-------|----------|
| S0 | **Baseline futility** — compra ogni token al lancio, hold 48h | controllo (deve perdere) | ⏳ | — |
| S1 | **Regime Filter** — entra solo in risk-on (vol memecoin + trend SOL) | media · overlay trasversale | 🔵 | — |
| S2 | **Smart-EXIT Overlay** — entry momentum, ESCI sui sell dei bravi | **alta (entrambi top)** | ⏳ | — |
| S3 | **Cluster Accumulation** — 3+ wallet profittevoli co-comprano <60min | **medio-alta (GPT-5 #1)** | ⏳ | — |
| S4 | **Deployer Reputation** — score storico del dev + hygiene (revoke authority) | media | ⏳ | — |
| S5 | **LP Fee Harvest** — provider LP durante churn da cluster (unico vero arbitraggio DeFi) | medio-bassa | ⏳ | — |
| S6 | **Coordinated Rotation** — cluster esce da A → entra in B entro 2h | medio-bassa | ⏳ | — |
| S7 | **Elite Momentum** — copia wallet top-Sharpe se tengono >2h | bassa | ⏳ | — |
| S8 | **Smart Dip-Buy** — accumulo di wallet in profitto mentre prezzo scende | bassa | ⏳ | — |
| S9 | **Post-Renounce / LP-Spike** — drift dopo revoke authority o +50% liquidità | bassa | ⏳ | — |
| S10 | **Prodotto Dati/Alert** — non-trading, monetizza alert ad alto SNR | media (come prodotto) | ⏳ | — |

---

## Criteri per scenario (sintesi)

**S0 — Baseline futility (controllo)**
- TEST: ogni nuovo token con vol >100 SOL nella prima candela → compra, vendi a 48h.
- SUCCESSO: nessuno (deve perdere). Se per miracolo EV>0 → tutto il resto è inutile.
- PARK: n/a (è il controllo). TEMPO: 2 giorni.

**S1 — Regime Filter** 🔵 ATTIVO
- TEST: risk-on = vol totale memecoin top100 >$50M (24h) AND trend SOL > -5% (3g) AND nuovi token >200/24h. Applica a una base-strategy (buy-first-candle-hold-48h) e confronta ON vs OFF.
- SUCCESSO: la base CON filtro ha Sharpe >0.5 e EV >+2% netto, mentre senza è negativa.
- PARK: il regime non discrimina (ΔSharpe <0.1) o è sempre ON (nessuna variabilità). TEMPO: 5-7 giorni.

**S2 — Smart-EXIT Overlay** (top conviction)
- TEST: entry momentum banale; A/B con/senza overlay. Overlay: esci 100% se in 1h 2+ smart-wallet vendono ≥$5k OPPURE sell cumulati 2h ≥30% dei loro buy. Smart = PnL realizzato >$5k, winrate >55%, ≥20 trade chiusi.
- SUCCESSO: overlay migliora mediana PnL ≥+5% assoluti e riduce DD ≥30% vs controllo, N≥60.
- PARK: precisione sell <55% nel predire top locali (±1h); lag mediano >2h dal top. TEMPO: 3-5 giorni.

**S3 — Cluster Accumulation** (GPT-5 #1)
- TEST: cluster = wallet che co-comprano stessi token in finestra ≤2h. Evento: ≥3 smart-wallet, net buy ≥$10k in 60min. Entry se prezzo ≤+5% dal max 1h, liq $30k-500k, age ≤3d.
- SUCCESSO: EV netto ≥+8% su ≥40 trade; Sharpe ≥0.5; maxDD ≤35%.
- PARK: <0.5 segnali/giorno dopo 5g; EV≤0 dopo 80 trade; match-rate wallet <60% (mixer/CEX). TEMPO: 4-7 giorni.

**S4 — Deployer Reputation**: score dev (rug-rate, ATHx, revoke-rate) + hygiene. SUCCESSO: EV ≥+7% su ≥50, rug-rate ≤5%. PARK: dev usa-e-getta (no reputazione riusabile). TEMPO: 5-10g.

**S5 — LP Fee Harvest**: provider LP durante churn, se Fees6h − IL ≥+1%. SUCCESSO: PnL medio ≥+0.5% su ≥30. PARK: IL mangia le fee / pool CLMM. TEMPO: 5-8g.

**S6 — Coordinated Rotation**: cluster esce da A (net sell >$10k, −50% pos) → compra B (net buy ≥$8k entro 2h). SUCCESSO: EV ≥+8% su ≥30. PARK: <10 rotazioni/sett, cluster instabili. TEMPO: 5-8g.

**S7 — Elite Momentum**: copia top-Sharpe (>1.5) se tengono >2h. SUCCESSO: EV ≥+1% su ≥20. PARK: wallet "elite" cambiano / sono bot. TEMPO: 5-8g. (Bassa.)

**S8 — Smart Dip-Buy**: wallet in profitto accumulano mentre prezzo −5% in 2h. SUCCESSO: EV ≥+3% su ≥15. PARK: dip = trappola. TEMPO: 6-8g. (Bassa.)

**S9 — Post-Renounce / LP-Spike**: drift dopo revoke mint/freeze o +50% liquidità senza dump. SUCCESSO: EV ≥+5% su ≥40. PARK: eventi rari / già prezzati. TEMPO: 4-10g. (Bassa.)

**S10 — Prodotto Dati/Alert**: logga alert (cluster/renounce/LP-spike) con latenza + ritorno +1h/+6h. SUCCESSO: top-quintile alert con EV ≥+7%, latenza ≤20min, AUC ≥0.6. PARK: nessun tipo supera +3% nel top quintile. (Fallback monetizzabile, no edge di trading.)

---

## Verdetto onesto dei due modelli
**7 su 10 falliranno.** Le uniche con probabilità realistica di EV+ sono **Smart-EXIT (S2)** e **Cluster Accumulation (S3)**, con **Regime Filter (S1)** come overlay che migliora tutto. Se S1-S4 falliscono dopo campione adeguato → l'edge orario free su memecoin è strutturalmente eroso → pivot su **Prodotto Dati (S10)** o **LP Fee (S5)**. Gli altri si testano per **escluderli sistematicamente** con evidenza solida, non per profitto.

---

## Log auto-analisi
_(ogni run del loop autonomo appende qui: data, scenario, # trade accumulati, EV corrente, decisione presa)_
- **2026-06-09 07:44 UTC** · S3_cluster it1 · n=0 EV=— aperti=0 · **CONTINUA**
  - 🤖 Double Agent:
    **deepseek:** (1) Zero trades significa che nessun segnale ha soddisfatto i parametri: troppo restrittivi o assenza di smart-money attivo nel timeframe orario. Con max_runup 0.3 (30% di rialzo pre-entry) e finestra 3600s si escludono quasi tutte le entry.
    
    (2) Abbassa **max_runup_at_entry** a **0.1** (10%) – così catturi movimenti più precoci prima che il run-up escluda l’entry. In alternativa, riduci **smart_min_wallets** a 1 (ma degrada qualità). Proverei prima il runup.
    
    (3) Non è un vicolo cieco, ma il paper-trading su memecoin Solana richiede parametri più aggressivi. Se dopo l’aggiustamento ancora zero trade, allora switcha a finestra più lunga (7200s) o cambia asset.
- **2026-06-09 07:57 UTC** · S3_cluster it1 · n=0 EV=— aperti=0 · **CONTINUA**
- **2026-06-09 07:58 UTC** · S3_cluster it1 · n=0 EV=— aperti=0 · **CONTINUA**
  - 🤖 Double Agent:
    **deepseek:** (1) **Brutale**: Zero trades eseguiti. Nessun segnale ha superato i filtri. `smart_min_wallets=2` blocca tutto – o non trovi abbastanza wallet "smart" nell’ora, o il `max_runup_at_entry=0.3` è troppo stretto. Strategia paralizzata.
    
    (2) **Un aggiustamento**: Abbassa `smart_min_wallets` a **1**. Una sola smart wallet basti per entrare. Se ancora zero, prova `max_runup_at_entry=0.5`.
    
    (3) **Vicolo cieco?** No, ma se dopo questo cambio non hai trade in 24h, il dataset di smart wallet è inesistente o la definizione "soft" è troppo morbida – allora abbandona.
- **2026-06-09 15:31 UTC** · S3_cluster it1 · n=0 EV=— aperti=0 · **CONTINUA**
- **2026-06-09 15:31 UTC** · S2_smartexit it1 · n=0 EV=— aperti=1 · **CONTINUA**
  - 🤖 Double Agent:
    **deepseek:** (1) Lettura brutale: **S3_cluster** con n=0 e aperti=0 significa che non hai ancora generato alcun segnale: stai monitorando nel vuoto. **S2_smartexit** ha una posizione aperta ma n=0 e EV=n/d: sei in trade senza alcun dato per decidere l’exit, affidato al caso.
    
    (2) Aggiustamenti concreti:
    - **S3_cluster**: riduci la soglia di cluster da, esempio, 5 a 2 transazioni ravvicinate per forzare segnali anche su volumi minimi.
    - **S2_smartexit**: imposta un trailing stop loss fisso al 15% dal prezzo d’ingresso, dato che non hai EV per calcolare uscite ottimali.
    
    (3) **S2_smartexit** è più vicino a un vicolo cieco: hai già capitale allocato senza alcun framework decisionale per chiudere la posizione. Senza dati, rischi di tenere trade morti o esplodere in perdita. S3_cluster almeno è a rischio zero.
- **2026-06-09 20:22 UTC** · S3_cluster it2 · n=0 EV=— aperti=0 · **CONTINUA**
- **2026-06-09 20:22 UTC** · S2_smartexit it2 · n=1 EV=+31.27% · meccanica +31.27% aperti=0 · **CONTINUA**
  - 🤖 Double Agent:
    **deepseek:** **Lettura brutale:** S3_cluster è vuoto: zero trade, nessun EV. Continuare è autolesionismo. S2_smartexit ha un solo trade (+31%) — è rumore, non conferma. Entrambe le scelte "CONTINUA" sono pretestuose.
    
    **Aggiustamenti concreti:**  
    - **S3_cluster:** Imposta soglia minima n≥5 per abilitare decisioni. Con n=0, stop immediato.  
    - **S2_smartexit:** Richiedi n≥30 campioni con EV>0 per proseguire; altrimenti pausa.
    
    **Vicolo cieco:** S3_cluster. Nessun dato, nessuna opportunità — è un buco nero. S2_smartexit almeno ha un segnale (seppur debole).
- **2026-06-10 04:53 UTC** · S3_cluster it3 · n=0 EV=— aperti=0 · **RARO: 0 segnali in 3 giri -> finestra 3600s->5400s**
- **2026-06-10 04:53 UTC** · S2_smartexit it3 · n=2 EV=+1193.71% · meccanica +383.35% aperti=0 · **CONTINUA**
  - 🤖 Double Agent:
    **deepseek:** (1) Lettura brutale: S3_cluster è clinicamente morto – zero segnali su 3 test, finestra ridicola. S2_smartexit ha EV droga (1194%) ma solo n=2, aperti=0: o coda di distribuzione o fortuna cieca.
    
    (2) Aggiustamenti concreti:
    - S3_cluster: allarga finestra a 7200s→10800s, oppure taglia soglia di attivazione del 50%.
    - S2_smartexit: esigi n≥10 per CONTINUA, imposta trailing stop loss dinamico (es. 30% dal picco).
    
    (3) Vicolo cieco: S3_cluster. Zero segnali su 3 giri con finestra già estesa indica pattern inesistente o overfit. S2 almeno ha EV positivo, ma serve campione reale.
- **2026-06-10 10:37 UTC** · S3_cluster it4 · n=0 EV=— aperti=0 · **RARO: 0 segnali in 4 giri -> finestra 5400s->8100s**
- **2026-06-10 10:37 UTC** · S2_smartexit it4 · n=4 EV=+575.22% · meccanica +601.13% aperti=3 · **CONTINUA**
  - 🤖 Double Agent:
    **deepseek:** (1) S3_cluster: morto — zero segnali in 4 round su finestra 5400-8100s, il filtro cluster è troppo stretto o il mercato non si adatta. S2_smartexit: EV +575% su n=4 è irrealistico su memecoin, probabile outlier; 3 posizioni aperte rischiano un crollo.
    
    (2) S3: ridurre soglia cluster minima da 2 a 1 evento. S2: aggiungere trailing stop-loss al 20% del massimo di profitto non realizzato.
    
    (3) S3 è più vicino a vicolo cieco — zero segnali ripetuti indicano assenza di opportunità nel pattern, non solo parametri sbagliati.
- **2026-06-10 16:12 UTC** · S3_cluster it5 · n=0 EV=— aperti=0 · **RARO: 0 segnali in 5 giri -> finestra 8100s->10800s**
- **2026-06-10 16:12 UTC** · S2_smartexit it5 · n=5 EV=+453.31% · meccanica +489.83% aperti=7 · **CONTINUA**
  - 🤖 Double Agent:
    **gpt5:** (1) Lettura brutale
    - S3_cluster: zero segnali in 5 giri = filtro troppo stretto + polling orario che perde i burst tipici (minuti) delle memecoin. Allargare solo la finestra (8100→10800s) è inutile: state guardando nel posto sbagliato al ritmo sbagliato.
    - S2_smartexit: EV +453% con n=5 e 7 posizioni aperte puzza di bias (fill irreali, slippage/MEV/fee sottostimate). Rischio di over-exposure e drawdown non visto.
    
    (2) Un aggiustamento concreto
    - S3_cluster: riduci detection_window a 1200s rolling (valutata a ogni poll), mantenendo gli altri filtri invariati. Obiettivo: catturare micro-cluster senza snaturare la precisione.
    - S2_smartexit: imposta max_hold_time = 6 ore; alla scadenza chiudi a mercato. Taglia code e realizza PnL, riducendo l’EV gonfiato da posizioni “zombie”.
    
    (3) Più vicino al vicolo cieco
    - S3_cluster, finché resti su polling orario gratuito: i segnali veri vivono su scale di minuti. Senza feed/event-driven o polling più denso, l’approccio cluster è strutturalmente castrato. S2 è migliorabile con risk/exit policy realistiche.
    
    **deepseek:** (1) S3_cluster: 0 segnali in 5 giri, finestra enorme (8100-10800s) → strategia paralizzata, nessun dato su cui valutare. S2_smartexit: EV +453% su 5 chiusi ma 7 aperti → performance gonfiata da pochi trade, alta concentrazione di rischio e possibile overfitting su campione piccolo.
    
    (2) S3: ridurre finestra a 3600s (1h) per forzare più tentativi e capire se il cluster esiste. S2: imporre max 2 posizioni aperte contemporaneamente per limitare drawdown e testare robustezza.
    
    (3) S3 è il vicolo cieco: zero segnali = nessuna opportunità di trading, mentre S2 almeno produce segnali e va disciplinato.
- **2026-06-10 21:04 UTC** · S3_cluster it6 · n=0 EV_med=— aperti=0 · **CONTINUA**
- **2026-06-10 21:04 UTC** · S2_smartexit it6 · n=8 EV_med=-32.73% · hold -31.14% aperti=6 · **CONTINUA**
- **2026-06-11 05:03 UTC** · S3_cluster it7 · n=0 EV_med=— aperti=0 · **CONTINUA**
- **2026-06-11 05:03 UTC** · S2_smartexit it7 · n=9 EV_med=-31.32% · hold +100.85% aperti=6 · **CONTINUA**
- **2026-06-11 11:03 UTC** · S3_cluster it8 · n=0 EV_med=— aperti=0 · **CONTINUA**
- **2026-06-11 11:03 UTC** · S2_smartexit it8 · n=10 EV_med=-32.82% · hold +100.85% aperti=6 · **CONTINUA**
- **2026-06-11 16:32 UTC** · S3_cluster it9 · n=0 EV_med=— aperti=0 · **CONTINUA**
- **2026-06-11 16:32 UTC** · S2_smartexit it9 · n=10 EV_med=-32.82% · hold -31.55% aperti=12 · **CONTINUA**
- **2026-06-11 20:39 UTC** · S3_cluster it10 · n=0 EV_med=— aperti=0 · **CONTINUA**
- **2026-06-11 20:39 UTC** · S2_smartexit it10 · n=13 EV_med=-31.32% · hold +45.59% aperti=11 · **CONTINUA**
- **2026-06-12 05:11 UTC** · S3_cluster it11 · n=0 EV_med=— aperti=0 · **CONTINUA**
- **2026-06-12 05:11 UTC** · S2_smartexit it11 · n=17 EV_med=-31.32% · hold +103.43% aperti=10 · **CONTINUA**
- **2026-06-12 10:44 UTC** · S3_cluster it12 · n=0 EV_med=— aperti=0 · **CONTINUA**
- **2026-06-12 10:44 UTC** · S2_smartexit it12 · n=18 EV_med=-0.03% · hold +168.23% aperti=13 · **CONTINUA**
- **2026-06-12 15:44 UTC** · S3_cluster it13 · n=0 EV_med=— aperti=3 · **CONTINUA**
- **2026-06-12 15:44 UTC** · S2_smartexit it13 · n=19 EV_med=-31.32% · hold +103.43% aperti=15 · **CONTINUA**
- **2026-06-12 20:31 UTC** · S3_cluster it14 · n=1 EV_med=+73.71% · hold +151.23% aperti=2 · **CONTINUA**
- **2026-06-12 20:31 UTC** · S2_smartexit it14 · n=22 EV_med=-32.82% · hold +103.43% aperti=14 · **CONTINUA**
- **2026-06-13 04:55 UTC** · S3_cluster it15 · n=1 EV_med=+73.71% · hold +151.23% aperti=6 · **CONTINUA**
- **2026-06-13 04:55 UTC** · S2_smartexit it15 · n=23 EV_med=-31.37% · hold +74.51% aperti=16 · **CONTINUA**
- **2026-06-13 09:40 UTC** · S3_cluster it16 · n=1 EV_med=+73.71% · hold +151.23% aperti=6 · **CONTINUA**
- **2026-06-13 09:40 UTC** · S2_smartexit it16 · n=25 EV_med=-31.37% · hold +103.43% aperti=17 · **CONTINUA**
- **2026-06-13 14:33 UTC** · S3_cluster it17 · n=1 EV_med=+73.71% · hold +151.23% aperti=8 · **CONTINUA**
- **2026-06-13 14:33 UTC** · S2_smartexit it17 · n=28 EV_med=-31.35% · hold +127.33% aperti=23 · **CONTINUA**
- **2026-06-13 19:57 UTC** · S3_cluster it18 · n=1 EV_med=+73.71% · hold +151.23% aperti=10 · **CONTINUA**
- **2026-06-13 19:57 UTC** · S2_smartexit it18 · n=29 EV_med=-31.37% · hold +151.23% aperti=30 · **CONTINUA**
