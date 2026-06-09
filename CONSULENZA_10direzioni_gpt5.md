# Double Agent: 10 direzioni — gpt5

A) Dieci direzioni nuove/trascurate

1) Drift di distribuzione holder (Gini/entropia)
- Cos’è: entra solo su token dove la concentrazione tra top holder cala nel tempo (Gini in discesa, entropia in salita).
- Perché può funzionare gratis+lento: la redistribuzione è lenta (ore-giorni); segnala minore rischio rug e più “stickiness” della domanda.
- Implementazione:
  - Ogni ora: per mint M, scarica top N holder (Helius: getTokenAccountsByMint; se troppo costoso, limita a N=1000/2000 per capitalizzazione).
  - Calcola Gini_t e ΔGini_24h; oppure entropia H_t = -∑ p_i log p_i con p_i = balance_i/supply.
  - Regola d’ingresso: ΔGini_24h ≤ -0.02 e top10% ≤ 65% e supply_locked=true (mint authority revoked).
  - Stop: -30%; TP: trailing 25–35%.
- Probabilità EV+: bassa–media. Funziona solo su sopravvissuti e in regime risk-on.
- Insidia: API rate/completezza holder; molti DEX tool già filtrano; dataset rumoroso.

2) Anomalie LP (liquidity add/remove outsider)
- Cos’è: indicatori su grandi variazioni LP non accompagnate da pump (LP_add% alto con prezzo/piatta o drawdown contenuto).
- Perché: LP changes sono lente/visibili su timeframe orario; gli add “seri” (non ricicli) precedono marketing/onboarding.
- Implementazione:
  - DEXScreener: liquidity USD per pool ogni ora.
  - Signal long: ΔLP_1h ≥ +40% e |ΔPrice_1h| ≤ 5% e no deployer dump negli ultimi 2h (GeckoTerminal /trades net seller=deployer cluster < $X).
  - Exit: ΔLP_1h ≤ -30% o net_sell_1h by early holders > $Y.
- Probabilità: media come overlay risk; da solo non basta.
- Insidia: ricicli LP fra pool, spoof LP, Raydium routing.

3) Modello “stage transition” della vita del token
- Cos’è: tradare transizioni lente di stato (es. 100→1000 holder, CG trending→CGK listing, authority revocata→LP lock).
- Perché: i passaggi di stato richiedono ore-giorni; meno competizione di latenza.
- Implementazione:
  - Feature: holder_count, first_seen, authority flags (mint/freeze revoked), LP lock, TG followers delta.
  - Regola: entra solo su Stage2→3: holder 100→1000 in ≤48h, authority_revoked=true, Δvol_24h > 2x, top10% ≤60%.
  - Backtest su OHLCV DEXScreener con latenze realistiche (+10% slippage ingresso).
- Probabilità: bassa–media, ma concentrata in bull regime.
- Insidia: base rate bassissima; sopravvivenza crea overfitting.

4) Flussi per cluster di wallet (non singoli “smart”)
- Cos’è: costruisci community/cluster via grafo wallet–token e usa il net-flow del cluster come segnale.
- Perché: i cluster “coordinati” si muovono più lentamente del whale singolo; segnale più robusto su H1-H4.
- Implementazione:
  - Ogni 2h: da GeckoTerminal /trades raccogli buyers/sellers ultimi 24–48h; costruisci bipartito (wallet, token), proietta grafo wallet–wallet con similarità Jaccard; Louvain community.
  - Score cluster c su token k: flow_c,k = Σ trade_usd_buy - Σ sell, normalizzato per size storica del cluster.
  - Entra quando ≥2 cluster indipendenti iniziano accumulo (flow_zscore ≥ +2 su 6h) e holder_count_zscore ≥ +1.
- Probabilità: media. È l’unica “copy” che non collassa subito.
- Insidia: drift dei cluster, bot contamination; serve manutenzione etichette.

5) Reputazione sviluppatore (deployer lineage)
- Cos’è: collega il signer di mint/LP add a mints precedenti; reputazione = storico rug/survival/EV.
- Perché: i team “studio” ri-lanciano; reputazione si trasferisce e si evolve lentamente.
- Implementazione:
  - Helius: estrai signer/authority di mint, first LP add, early transfers; normalizza per relazioni (funding chain 1–2 hop).
  - Labela esiti passati (survival 7/30d, maxDD, rug flag); score_dev = P(survival30d|dev).
  - Entrate solo se score_dev ≥ soglia (es. top decile) e authority_revoked al T0+24h.
- Probabilità: media nelle fasi di mania; bassa in mercati freddi.
- Insidia: dev usano nuovi keypairs/proxy; falsi negativi/positivi.

6) Filtro di regime macro-chain (entri solo in risk-on)
- Cos’è: non un segnale d’ingresso, ma un kill-switch; trade solo quando Solana è in “risk-on”.
- Perché: il regime perdura su giorni; il grosso dell’EV viene da finestre ristrette.
- Implementazione:
  - Indicatori gratuiti orari: ΔUSDC_supply_solana (SPL mint supply), net bridge inflow (Wormhole API), DEX volume memecoin index (somma vol 100 top meme), SOL price/vol z-score.
  - Regole esempio: trade_enabled = (z(DEX_vol_24h) ≥ +1) AND (ΔUSDC_24h ≥ +1%) AND (SOL z_24h ≥ 0).
  - Se false: no nuove entrate, riduci risk 50% posizioni.
- Probabilità: media come miglioratore di Sharpe/EV.
- Insidia: dati bridge sporchi; definizione index; regime switch tardivo.

7) “Smart-exit” overlay (usa i “bravi” solo per uscire)
- Cos’è: non copi le entrate dei wallet “bravi”, usi le loro vendite come stop dinamico.
- Perché: l’informazione di uscita propaga più lento del pump; utile su timeframe orario per tagliare code di distribuzione.
- Implementazione:
  - Mantieni lista di wallet “early-and-green” per token T (entrati <10% dal listing e ancora in profitto).
  - Exit trigger: se net_sell_usd di questi wallet su T in 2h ≥ 20% del loro cost basis aggregato, chiudi.
  - Combina con trailing stop più stretto quando early cohort riduce exposure.
- Probabilità: media come riduttore di drawdown; EV marginale positivo in bull.
- Insidia: pochi wallet per token → rumore; vendite parziali.

8) Contrarian “dump-bounce” su sopravvissuti
- Cos’è: comprare flush estremi con liquidità intatta e nessun rug flag; orizzonte 12–48h.
- Perché: mean reversion lenta dopo -60/80% intraday su token che non rugga (LP intatto).
- Implementazione:
  - Scan orario: drawdown_6h ≤ -60%, LP_drop_6h ≤ 10%, holder_count stabile o ↑, no authority change negativa.
  - Entry: al primo close 1h sopra VWAP_6h; Exit: TP +20/35%, stop -15%.
- Probabilità: bassa–media; coda grassa ma bassa frequenza; EV dipende da filtri rug.
- Insidia: falling knives; false recovery; slippage alto su buchi di book.

9) Stagionalità intraday/day-of-week (risk scheduling)
- Cos’è: allochi rischio solo nelle finestre statisticamente favorevoli (es. UTC 14–22, weekend mania).
- Perché: ciclicità di retail/US session; sfruttabile senza latenza.
- Implementazione:
  - Backtest: R_t per ore/dow sui top 50 meme per liquidità; clusterizza finestre con μ/σ migliori.
  - Policy: apri nuove posizioni solo nelle ore top-quantile; forza riduzione 50–100% fuori finestra.
- Probabilità: bassa–media; piccoli edge ma gratis e combinabile.
- Insidia: regime drift forte; facile overfit.

10) Trade su eventi di authority/lock (renounce/lock event)
- Cos’è: comprare subito dopo la revoca di mint/freeze authority o lock LP se il prezzo non ha ancora prezzato.
- Perché: evento binario on-chain, spesso price-lag di ore lato retail.
- Implementazione:
  - Helius: monitora istruzioni SetAuthority/Revoke + lock LP tx (Raydium/lockers noti); polling orario.
  - Trigger: authority_revoked in t, ΔPrice_1h post-evento ≤ +5%, ΔHolder_6h > 0 → entra piccolo.
- Probabilità: media in mania; bassa in regime freddo.
- Insidia: dev fingono lock/renounce via proxy; spoof announcements.

B) Verdetto brutale
- Sì, stai rincorrendo un fantasma se l’obiettivo è “copiare smart-money su memecoin Solana” con vincoli: gratis, orario, no accesso privilegiato. Il meta è dominato da:
  - Latenza secondi–minuti (Jito/MEV/bot), canali Telegram interni, insider marketing.
  - Base rate: la maggior parte dei token → zero; i pochi vincitori richiedono anticipazione non ottenibile a cadenza oraria.
  - La tua evidenza: 0/27 wallet copiabili ex ante dopo +10% slippage e rigorosa statistica. Questo è conclusivo.
- Dove ha senso pivotare con stessi strumenti/skill:
  1) Prodotti dati/infra (non trading): risk scoring, dev reputation, cluster flow dashboards/alerts Telegram. Monetizzabili; non richiedono edge di mercato.
  2) Strategie cross-sectional lente su asset liquidi (no-meme): momentum/quality su top Solana ecosystem (SOL, Jito, JUP, PYTH, WIF ma solo >$50–100m liquidi). Timeframe giornaliero/orario; edge piccolo ma reale e testabile.
  3) Overlay/regime/factor timing: usare flussi USDC on-chain + DEX volume per attivare/disattivare rischio; applicabile a basket liquido (anche CEX per perps) con API gratuite.
  4) Airdrop/points farming sistematico e rivendita post-TGE (event-driven lento): edge operativo, non di prezzo intra-h.

C) Le 3 cose che farei ora (priorità)
1) Smetti di cercare “wallet copiabili”. Ricicla il modulo in “cluster flow + dev reputation” come filtri/overlay. In 2 settimane: pipeline stabile per
   - cluster net-flow per token (6–24h),
   - score dev (link mints precedenti),
   - regime filter (DEX vol + USDC inflow).
   Backtest combinato su 6–12 mesi con costi reali (+10–20% slippage meme), poi decidi go/no-go.

2) Costruisci un prodotto: “Solana Meme Risk/Intel Feed”
   - Feeds: authority/lock events, LP anomaly, holder dispersion drift, early-cohort net-sell alerts.
   - Output: Telegram bot/API. Pubblica report settimanale con metriche dure (false positive, precision @24h).
   - Monetizzazione > eventuale trading. Migliora dealflow/partnership, non richiede edge live.

3) Pivot parallelo su strategia lenta e liquida
   - Universo: top 30–50 Solana ecosystem tokens per liquidità (no microcap).
   - Modello: cross-sectional momentum 3–7d con regime filter; ribilanci orario solo per stop/exit, ingressi 1–2 volte/dì; sizing per volatilità target.
   - Metriche attese realistiche: Sharpe 0.6–1.0 lordi in bull, 0.2–0.4 medi; verifica con costi CEX/DEX free-tier.
   - Se Sharpe <0.4 dopo costi → stacca dalla parte “trading” e concentra sul prodotto dati.

Se cerchi PnL su memecoin Solana con polling orario e budget zero: lascia perdere come core alpha. Usa memecoin solo come sorgente di segnali lenti di rischio/comportamento, non per entrare “prima degli altri”.