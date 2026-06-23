# Dati per rilevare i token virali — deepseek

**1. ON-CHAIN (precoce)**  
- **Holder velocity**: >50 new holders in first 2 min (accelerating).  
- **Deployer fingerprint**: no previous rug, low initial supply concentration (<5% in deployer wallet after bundle).  
- **Bundle analysis**: Jito tip >0.01 SOL per tx → sniping activity.  
- **Inflow netto**: >$10k net buy into LP in first 30s.  
- **Smart-money clustering**: wallets that bought previously viral tokens now co-buying.  
- **Pool age + locked liquidity**: liquidity locked >1h (fake) vs. unlocked (high risk).  
- **Volume acceleration**: >$50k volume in 1st minute, with increasing tick frequency.

**2. SOCIAL (nuovo)**  
- **X/Twitter**: mentions/sec of CA/ticker in first 5 min. **Most predictive**. Access via Nitter (free, fragile) or paid API ($100/mo for basic). Alternative: scrape public lists from DexScreener mentions (free, delayed).  
- **Telegram**: reaction speed in Pump.fun chat, KOL channel messages. Use Telethon (free).  
- **TikTok**: less predictable, but viral short videos pre-pump. Scrape via unofficial API (e.g., TikTokAPI, rate-limited).  
- **Discord**: early alerts from server bots (e.g., GMGN). Free via webhooks.

**3. COMBINAZIONE (ordine)**  
1. **Pool created** with deployer pattern + liquidity unlocked.  
2. **Jito bundle detected** → first buys.  
3. **Holder count >10** in 1 min + volume >$10k.  
4. **X mentions >5 unique accounts** in 2 min (topic: ticker or CA).  
5. **Telegram reaction speed** <5s to first post.  

Seen historically: tokens that hit steps 1-4 within 3 min tend to 2x in 10 min.

**4. FONTE #1 ORA**  
**X/Twitter real-time mentions** – non-negotiable. Use a free scraper (e.g., `snscrape` + rotating proxies, or `twint` fork) despite instability; it’s the only source that captures KOL calls before price moves. If banned, add Telegram (Pump.fun chat) as backup.

**5. BRUTAL VERITÀ**  
Sì, si può rilevare, ma il **vero edge** è nel **lag di 5-30 secondi** tra primo segnale social e ampia adozione on-chain. L’inefficienza sfruttabile: la maggior parte dei retail vede il token dopo 1-2 minuti, mentre i wallet smart comprano al 1° blocco. Se riesci a sottrarre 10 secondi usando on-chain sniping + social in tempo reale, sei sopra. Ma il mercato è spietato: **le memecoin virali spesso sono già pumpate da bot MEV prima che tu possa eseguire**. L’unico vero edge è **intelligente selezione del deployer** (es. token con narrative “meme di giorno” su X) + **entrata al secondo 0 con slippage alto**. Non è illusione, ma richiede latenza <500ms e capitale per slippage.