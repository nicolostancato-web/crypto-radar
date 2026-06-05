# Consulenza GPT (quant/on-chain) — 2026-06-05

Fonte: risposta di ChatGPT al prompt PROMPT_CHATGPT.txt. Qui i punti azionabili.

## L'INTUIZIONE CHIAVE (reframe)
NON chiedersi "il wallet è bravo?" ma: **"copiarlo QUANDO LO VEDO IO (1-5 min dopo, a prezzo
+5-10% peggiore, col MIO slippage) produce EV netto positivo?"** → si valuta la COPIABILITÀ,
non il PnL assoluto. Un wallet che fa milioni vendendo in 40s NON è copiabile.

## VERDETTO
- Edge esiste, ma NON nella forma semplice "vedo smart wallet comprare → compro". Troppo
  affollato/arbitrato/sensibile alla latenza. I pro hanno streaming gRPC, priority fee,
  liste curate, gruppi privati, insider. Con polling orario NON siamo nel gioco sniping.
- Edge POSSIBILE per noi: wallet copiabili (hold >30min) + conferma di CLUSTER (non singolo
  buy) + exit meccaniche + paper trading onesto. NIENTE soldi veri finché EV netto non provato.
- Stato attuale dati = ZERO validità statistica (n=2 outcomes).

## DOVE FALLISCONO SISTEMI COME IL NOSTRO
Catturano buyer tardivi; confondono whale con smart; niente exit; backtest su wallet scelti
DOPO il pump (look-ahead); ignorano slippage; non simulano latenza; non distinguono bot/dev/
insider/copiabile; si innamorano di 1 caso; cambiano pesi troppo presto; token illiquidi.

## 1. EARLY vs LATE (distinguere big-buy informato da pollo del top)
Per ogni big-buy calcolare: token_age_at_entry; price_runup_before_entry; buy_usd/liquidity;
forward returns r_5m/r_15m/r_1h/r_6h/r_24h; MFE_1h; MAE_1h.
- Early possibile: age<120min, runup<+80%, buy/liq 0.3%-5%, r_15m>+10% o MFE_1h>+25%, MAE_1h>-20%.
- Late/pollo: runup>+200%, già trending, compra dopo spike verticale, MFE piccolo/MAE grande.
- entry_worked_score = 0.25*clamp(r_15m/0.25) + 0.25*clamp(r_1h/0.5) + 0.20*clamp(MFE_1h/0.75,0,1)
  - 0.15*clamp(|MAE_1h|/0.3,0,1) - 0.15*late_chase_penalty
  (late_chase_penalty: 1 se runup>200%, 0.5 se 100-200%, 0 altrimenti)

## 2. SCOPERTA EARLY (la priorità #1)
Spostare da "trending → chi compra" a "NEW POOL → entra capitale anomalo prima del trend".
- Ogni ~5 min: GeckoTerminal /networks/solana/new_pools + DEXScreener latest profiles/boosts.
- Per ogni nuovo pool salvare: created_at, initial_liquidity, fdv, price, tx/vol/buyers 5m, largest_buy_5m.
- Candidate early token: age<180min; liq $10k-$300k; vol_5m/liq>0.10; >=5 buyer unici/10min;
  largest_buy > max($500, 1% liq); non già pumpato >300%.
- early_big_buy: buy_usd >= max($500, 0.5%*liq) AND age<120min AND runup_before<100%.
- Token a 60k+ tx: NON paginare tutto. Snapshot incrementali dei trade ogni 5 min, dedup.

## 3. CLUSTER COORDINATI
Grafo wallet-wallet. coord_score(w1,w2)=log(1+co_buy)*exp(-median_dt_min/10)*avg_fwd_return*min(1,avg_usd/1000).
- Coppia coordinata: co_buy>=3 token, median_dt<=10min, jaccard>=0.15, age medio<=180min.
- Cluster: >=3 wallet, >=3 token condivisi, comprano entro 10min su >=2 token, size>=3% liq early.
- Community detection (Louvain/Leiden/connected components). Entry: 3 wallet stesso cluster
  comprano stesso token <10min, age<3h, runup<150%, liq>$20k → paper-enter.
- Insidia: cluster = spesso bot dello stesso operatore (non copiabili) o follower di call pubblici.

## 4. WALLET-SWITCHING (funding graph) — fase 2
funder→trading wallet→next. Fingerprint: median_buy_usd, hold_time, age_at_entry, priority_fee,
router preferito, ore attive UTC, stile vendita. link_score=0.35*funding+0.25*behavior+0.20*token_overlap
+0.10*timing+0.10*size. linked se >=0.70. NON collegare via hub CEX (falsi positivi).

## 5. SMART SCORE (EV, non win-rate)
profit_factor=gross_profit/|gross_loss|; payoff=avg_win/|avg_loss|; expectancy=(wr*avg_win)-((1-wr)*|avg_loss|);
net_expectancy = expectancy - slippage - fee - latency_penalty.
entry_earliness (age<30min=1, 30-120=0.7, 120-360=0.4, >360=0.1). exit_quality=realized/max_possible.
copyability: simula entrata a buy_price*1.05/1.10/1.20 → regge ancora? hold_time_score (>7d=0.5, 1h-24h=1, <2min=0).
- Ignora: closed<20, hold<2min, tx/day>60, profit_factor<1.3, net_EV<=0.
- Watchlist: closed>=20, PF>=1.5, net_EV>+10%, hold>10min, copy-sim ok a +10% peggiore.
- Boss: closed>=50, PF>=2, net_EV>+20%, positivo su 3 regimi/30gg, regge slippage+5-10min ritardo.

## 6. VALIDITÀ STATISTICA
EV=mean(net_return); SE=std/sqrt(n); bootstrap CI. Minimi: 100 trade per osservare, 300 per
prima lettura seria, 500+ su settimane diverse per soldi veri. Wallet copy: >=30 closed, >=20 copy-sim.
Anti-bias: discover gg1-14 → CONGELA lista gg15-30 → testa solo FORWARD gg31-60. Usa EV netto,
non win-rate. Mediana non deve essere profondamente negativa.

## 7. EXIT (il più importante)
Copy-sell da solo NON basta (vedi la vendita tardi; vendono OTC/altri pool/wallet collegati).
Testare 4 exit in parallelo: A) copy-sell; B) TP scalare (+50% vendi40%, +100% vendi25%, runner trailing,
stop -30%); C) trailing su MFE; D) time-decay. Base memecoin: stop -25/-35%, TP1 +50% (40%),
TP2 +100% (30%), resto trailing 30%, hard exit 24h, emergency se liq -30% o dev/holder scarica.

## 8. FONTI MANCANTI
Dune (SQL gratis su trade Solana storici → backtest senza crediti RPC) ⭐. Allium free tier.
Birdeye Lite $39/mese (solo se serio). Solscan paid solo a validazione. Paper "MemeTrans"
(40k launch, dataset pubblico). NON costruire su scraping Cloudflare (GMGN). Non pagare prima
di avere una domanda statistica chiara.

## LE 3 COSE DA FARE (priorità GPT, coincidono coi nostri dubbi)
1. Spostare da "trending buyers" → "NEW POOL early-flow watcher" (ogni 5 min).
2. Copy-simulation realistica con EXIT meccaniche (non solo outcome 24/72/168h).
3. Valutare wallet su COPIABILITÀ (regge +5-10% entrata peggiore + 1-5min ritardo), non PnL assoluto.
