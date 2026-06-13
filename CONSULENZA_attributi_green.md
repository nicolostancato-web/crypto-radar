# Grok — attributi da loggare per le GREEN (2026-06-13)

**1. I 5-6 ATTRIBUTI NON-NEGOZIABILI**

Questi sono gli unici su cui non si transige: senza di questi il dataset è cieco sul timing.

1. **Buy/Sell ratio 1h + unique buyers 1h** (helius) — misura la forza reale del flusso retail/whale. Predittivo altissimo sia entry che exit.
2. **Whale netflow 1h** (helius — wallet >0.5% supply) — il segnale più pulito di accumulo o dump istituzionale.
3. **Posts/ora su X (velocity)** (grok) — l’unico social metric che anticipa il volume di 1-3 ore.
4. **Top10% supply concentration delta 1h** (helius) — quando sale velocemente = whale dentro; quando scende = distribuzione.
5. **Holder growth rate 1h** (helius) — nuovi holder netti / ora. Entry forte solo se > +8-12% con buy ratio >1.4.
6. **Volume 1h / Volume 1h precedente (momentum)** (derived) — l’accelerazione del volume è il trigger di breakout o reversal.

**2. LISTA COMPLETA PER CATEGORIA**

**Prezzo / Volatilità**  
- Price change 1h/4h/12h (derived) — high entry, high exit  
- Realized volatility 1h (std dev returns) (derived) — med entry, high exit  

**Volume e derivata**  
- Volume 1h momentum (derived) — high both  
- Volume / FDV ratio (derived) — med entry, low exit  

**Flusso**  
- Buy/Sell ratio 1h (helius) — high both  
- Unique buyers 1h (helius) — high both  
- Avg buy size 1h (helius) — med entry, low exit  
- Unique sellers 1h (helius) — med exit  

**Whale / Holder**  
- Top10% supply delta 1h (helius) — high both  
- Whale netflow 1h (helius) — high both  
- New holders / hour (helius) — high entry, med exit  
- Holder churn (new - left) 1h (helius) — med both  
- Top1 wallet % change (helius) — med exit  

**Liquidità**  
- Liquidity absolute + delta 1h (dexscreener) — med entry, high exit  
- LP burn/lock status (dexscreener snapshot) — low both (solo se cambia)  

**Social / X**  
- Posts/ora (velocity) (grok) — high both  
- KOL mentions count 1h (grok) — med entry, low exit  
- Follower reach weighted (grok) — low both  

**Derivati temporali**  
- Volume acceleration (vol1h / avg last 3h) (derived) — high both  
- Holder acceleration (derived) — high entry  
- Buy ratio acceleration (derived) — high both  

**3. RUMORE DA SCARTARE**

- Total holders absolute (solo il delta conta)  
- Any single-tweet sentiment score (troppo noisy)  
- FDV absolute (già loggato)  
- Market cap rank o trending position  
- Any metric >24h senza normalizzazione oraria  
- Telegram/Discord member count  
- Generic “hype score” non basato su velocity

**4. JSON FINALE**

```json
{
  "must_have": [
    {"attr":"Buy/Sell ratio 1h","why":"misura forza flusso reale","source":"helius","predictive":"both"},
    {"attr":"Whale netflow 1h","why":"accumulo/dump istituzionale","source":"helius","predictive":"both"},
    {"attr":"Posts per hour (velocity)","why":"anticipa volume 1-3h","source":"grok","predictive":"both"},
    {"attr":"Top10% supply delta 1h","why":"concentrazione whale","source":"helius","predictive":"both"},
    {"attr":"Holder growth rate 1h","why":"inflow retail netto","source":"helius","predictive":"both"},
    {"attr":"Volume 1h momentum","why":"trigger breakout/reversal","source":"derived","predictive":"both"}
  ],
  "full_list": [
    {"attr":"Price change 1h/4h/12h","source":"derived","predictive_entry":"high","predictive_exit":"high"},
    {"attr":"Realized volatility 1h","source":"derived","predictive_entry":"med","predictive_exit":"high"},
    {"attr":"Volume 1h momentum","source":"derived","predictive_entry":"high","predictive_exit":"high"},
    {"attr":"Buy/Sell ratio 1h","source":"helius","predictive_entry":"high","predictive_exit":"high"},
    {"attr":"Unique buyers 1h","source":"helius","predictive_entry":"high","predictive_exit":"high"},
    {"attr":"Avg buy size 1h","source":"helius","predictive_entry":"med","predictive_exit":"low"},
    {"attr":"Unique sellers 1h","source":"helius","predictive_entry":"med","predictive_exit":"med"},
    {"attr":"Top10% supply delta 1h","source":"helius","predictive_entry":"high","predictive_exit":"high"},
    {"attr":"Whale netflow 1h","source":"helius","predictive_entry":"high","predictive_exit":"high"},
    {"attr":"New holders / hour","source":"helius","predictive_entry":"high","predictive_exit":"med"},
    {"attr":"Holder churn 1h","source":"helius","predictive_entry":"med","predictive_exit":"med"},
    {"attr":"Liquidity delta 1h","source":"dexscreener","predictive_entry":"med","predictive_exit":"high"},
    {"attr":"Posts per hour","source":"grok","predictive_entry":"high","predictive_exit":"high"},
    {"attr":"KOL mentions 1h","source":"grok","predictive_entry":"med","predictive_exit":"low"},
    {"attr":"Volume acceleration","source":"derived","predictive_entry":"high","predictive_exit":"high"},
    {"attr":"Holder acceleration","source":"derived","predictive_entry":"high","predictive_exit":"med"},
    {"attr":"Buy ratio acceleration","source":"derived","predictive_entry":"high","predictive_exit":"high"}
  ],
  "noise": [
    "total holders absolute",
    "single-tweet sentiment",
    "FDV absolute",
    "market cap rank",
    "telegram members",
    "generic hype score"
  ]
}
```