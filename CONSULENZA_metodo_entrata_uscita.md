# Consulenza Grok — metodo entrata/uscita (2026-06-13)

**DIAGNOSI**  
Entri tardi perché il tuo segnale parte dopo il primo spike di volume (27-55h) e il filtro on-chain non cattura l’accelerazione iniziale. Per anticipare devi entrare sul primo derivato positivo del volume + whale buy fresco + X con <150 post/ora, prima che fdv superi 800k.

**REGOLA D’INGRESSO**  
Trigger ON:  
- età token < 8h  
- volume 1h accelera ≥ +80% vs ora precedente (non livello assoluto)  
- buy/sell ratio 1h ≥ 2.8  
- whale (top10) net buy > 0.8% supply nelle ultime 2h  
- X: menzioni < 120/h + sentiment ratio buy:sell ≥ 3:1 (ultime 2h)  
- fdv < 650k e liquidità > 45k  

Se 4 su 5 condizioni vere → entra al prossimo candle 5m.

**REGOLE D’USCITA (su segnale)**  
1. Volume svanisce: volume 1h < 35% del picco assoluto → esci  
2. Distribuzione whale: top10% holders sale ≥ +1.8% supply in 2h consecutive → esci  
3. Buy/sell inversione: buy/sell ratio 1h scende sotto 1.2 per 2 ore consecutive → esci

**PARAMETRI DA LOGGARE**  
On-chain (ogni ora): prezzo, fdv, liq, vol1h, vol24h, buys1h, sells1h, top1% supply, top10% supply, holders totali, whale netflow 1h/2h.  
Social (ogni ora): post/h su X (query token), sentiment ratio, KOL mentions count.  
Scarta: total market cap, holder count grezzo, tweet totali lifetime, prezzo su Dexscreener senza context.

**JSON FINALE**
```json
{
  "entry_rule": {
    "conditions": [
      "age_h < 8",
      "vol1h_accel >= 80",
      "buy_sell_ratio_1h >= 2.8",
      "whale_net_buy_2h > 0.8",
      "x_mentions_2h < 120",
      "x_sentiment >= 3",
      "fdv < 650000",
      "liq > 45000"
    ],
    "thresholds": {"min_conditions": 4}
  },
  "exit_rules": [
    {"name": "volume_death", "signal": "vol1h < 35% peak", "threshold": "35%"},
    {"name": "whale_distrib", "signal": "top10%_supply_up_2h", "threshold": "+1.8%"},
    {"name": "flow_inversion", "signal": "buy_sell_ratio_1h < 1.2 for 2h", "threshold": "1.2"}
  ],
  "log_params": [
    "price","fdv","liq","vol1h","vol24h","buys1h","sells1h",
    "top1_supply","top10_supply","holders","whale_netflow_1h","whale_netflow_2h",
    "x_posts_h","x_sentiment_ratio","x_kol_mentions"
  ],
  "drop_params": ["total_mc","raw_holders","lifetime_tweets","dex_price_raw"],
  "backtest_note": "usa solo dati fino all'ora t per decidere entry/exit a t+1; nessun forward fill su peak volume o whale flow"
}
```