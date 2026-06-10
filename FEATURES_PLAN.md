# Feature Plan — i dati GIUSTI per trovare l'edge

> Sintesi: DeepSeek (deep search, troncato a 26) + completamento Fable 5. Obiettivo: estrarre
> 1 riga per evento "wallet compra token" con questi attributi, accumulare migliaia di righe,
> poi SEGMENTARE per trovare la combinazione con EV positivo (l'edge). Tutto da fonti gratis.
>
> Legenda: ✅ già estratto · 🟡 da aggiungere (gratis, stessa chiamata) · 🔶 da aggiungere (1 chiamata extra)

## 1. WALLET (chi compra)
| Feature | Predice | Fonte | Stato |
|---|---|---|---|
| w_pnl, w_winrate, w_closed | skill del wallet | Helius (storia) | ✅ |
| w_avg_hold_minutes | orizzonte (copy con latenza vuole hold brevi) | Helius | 🔶 |
| w_profit_factor, w_sharpe | qualità risk-adjusted | Helius | 🔶 |
| w_median_buy_usd, w_std_buy_usd | taglia tipica (calibra il copy) | Helius | 🔶 |
| w_rug_buy_rate | % token comprati che poi ruggano (filtro anti-rug del wallet) | Helius+DEX | 🔶 |
| w_coordination_score | quanto opera in gruppo (insider?) | storia overlap | 🟡 |
| w_balance / w_whale_score | capitale / potere | Helius getBalance | ✅ |
| w_unique_tokens_30d | rotazione (alta = rumoroso) | Helius | 🔶 |

## 2. TOKEN (cosa compra), al momento del buy
| Feature | Predice | Fonte | Stato |
|---|---|---|---|
| token_age_minutes | giovane = incertezza+upside; >24h edge decade | DEXScreener pairCreatedAt | 🟡 |
| liquidity | impact + rischio rug | DEXScreener | ✅ |
| volume_24h, volume_1h/24h | hype + accelerazione | DEXScreener | 🟡 |
| price_change_1h, runup_before | momento (upswing vs fomo tardivo) | DEX/OHLCV | ✅🟡 |
| price_change_since_first_smart | già salito troppo? (fomo) | calcolo | 🔶 |
| holders_total, holder_concentration_top10 | centralizzazione → rischio rug | Helius getTokenLargestAccounts | 🔶 |
| txn_buy_sell_ratio_1h | pressione d'acquisto (>1.5 = continuazione) | DEXScreener txns | 🟡 |
| fdv / market_cap | dimensione | DEXScreener | 🟡 |
| pool_type (Raydium/Pump.fun/…) | rischio rug per venue | DEXScreener dexId | 🟡 |

## 3. SICUREZZA / RUG (Fable 5)
| Feature | Predice | Fonte | Stato |
|---|---|---|---|
| mint_authority_revoked | non possono coniare altra supply | Helius mint info | 🔶 |
| freeze_authority_revoked | non possono congelarti | Helius mint info | 🔶 |
| lp_burned_or_locked | liquidità non ritirabile (anti-rug) | Helius/DEX | 🔶 |
| top_holder_pct | 1 wallet può scaricarti addosso | Helius | 🔶 |

## 4. TIMING / COORDINAZIONE (Fable 5)
| Feature | Predice | Fonte | Stato |
|---|---|---|---|
| smart_coord_1h | quanti smart wallet entro ±1h (cluster) | nostro DB | ✅ |
| is_first_smart_buyer / rank | primo o ultimo della fila? | calcolo | 🔶 |
| minutes_since_first_smart_buy | quanto sei in ritardo | calcolo | 🔶 |
| buy_pct_liquidity | price impact del buy | calcolo | ✅ |

## 5. ESITO / LABEL (la verità da predire)
| Label | Stato |
|---|---|
| copy_net (entrata +10%, uscita meccanica) ← target primario | ✅ |
| hold_net (benchmark: tieni 24h) | ✅ |
| max_gain_24h, max_drawdown_24h | ✅🟡 |
| return_1h / 6h / 24h | 🟡 |
| did_rug (liquidità crollata) | 🔶 |
| profitable_copy = copy_net > 0 (label binaria) | calcolo |

---

## TOP-10 da avere SUBITO (massimo potere predittivo)
1. **w_winrate** · 2. **w_pnl** · 3. **w_rug_buy_rate** · 4. **w_coordination_score** ·
5. **token_age_minutes** · 6. **holder_concentration_top10** · 7. **txn_buy_sell_ratio_1h** ·
8. **price_change_since_first_smart** · 9. **buy_pct_liquidity** · 10. **mint/freeze_authority_revoked**

## SEGMENTAZIONI da testare per prime (dove si nasconde l'edge)
1. Solo wallet con **winrate > 60%** + **rug_buy_rate basso**
2. Solo token **early** (age < 60min) **E** liquidità $20k-200k
3. Solo **coordinati** (smart_coord_1h ≥ 2)
4. Solo token **sicuri** (authority revocata + top10 < 60%)
5. Solo **non-fomo** (price_change_since_first_smart < +30%)
6. **Combinazioni** AND dei sopra (qui si trova l'edge, se c'è)

## TARGET da predire
- Primario: **copy_net** (continuo) e **profitable_copy** (binario)
- Per ogni segmento: **mediana copy_net** + **win-rate** + **batte hold?** → se un segmento ha mediana >+5% e batte il hold su 30+ trade → **EDGE TROVATO**

---

## ⚠️ QUALI WALLET TRACCIARE (input Nicolò — pilastro "dati giusti" applicato ai wallet)

Problema reale: i bravi usano wallet **usa-e-getta** finanziati da main/exchange (Binance/Coinbase
cold wallet con milioni), accumulano per settimane, poi svuotano. Non siamo dentro un exchange con
visibilità totale → solo on-chain. Scegliere i wallet SBAGLIATi = perdere tempo.

**Criteri del wallet GIUSTO da tracciare (filtri di selezione):**
- ✅ **Persistente**: attivo da settimane/mesi (span_days alto), NON creato in giornata
- ✅ **Umano**: cadenza normale (no bot: tx_per_day sotto soglia)
- ✅ **NON hub/exchange**: pochi counterparty rispetto al volume (gli hub Binance hanno 100+ counterparty/ora → ESCLUDI, lezione caso Binance-hub)
- ✅ **Track record reale**: abbastanza trade chiusi (closed_count) per non confondere skill e fortuna
- ✅ **Profittevole su campione vero** (non 1-2 trade fortunati)

**Nota strategica (Nicolò):** si potrebbe partire dai wallet "importanti" (es. chi riceve da exchange
e POI tradeggia bene) con un tracciamento diverso — ma attenzione: il funding-graph porta agli hub CEX
(già provato, abbandonato). Conta il COMPORTAMENTO del wallet che tradeggia, non chi lo finanzia.
