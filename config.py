"""
config.py — TUTTE le manopole del sistema in un posto solo.

Filosofia: nessun numero "magico" sparso nel codice. Tutto quello che vorrai
tarare guardando i dati veri sta qui. Cambi un valore qui, riparte tutto.

I pesi e le soglie iniziali sono CONSERVATIVI di proposito. Partono "stretti"
(pochi candidati, pochi falsi positivi) e li allarghi tu se vedi che ti perdi
roba. È molto più facile allargare che ripulire un Excel pieno di spazzatura.
"""

# ---------------------------------------------------------------------------
# DATABASE
# ---------------------------------------------------------------------------
DB_PATH = "radar.db"            # SQLite: zero setup. Per Postgres cambi solo db.py
EXPORT_PATH = "top_scores.xlsx"  # il file che apri tu

# ---------------------------------------------------------------------------
# DISCOVERY — il "buttafuori". Largo ed economico. Solo fonti gratuite.
# ---------------------------------------------------------------------------
DISCOVERY = {
    # Catene da monitorare su DEXScreener (free API). Aggiungi/togli a piacere.
    "chains": ["solana", "ethereum", "base", "bsc"],

    # FILTRI DI ESCLUSIONE (scartano spazzatura PRIMA di sprecare enrichment)
    "min_liquidity_usd": 30_000,      # sotto questo non entri/esci senza distruggere il prezzo
    "max_vol_liq_ratio": 8.0,         # vol/liq troppo alto = wash trading / instabilità
    "min_vol_liq_ratio": 0.05,        # vol/liq troppo basso = token morto
    "min_age_hours": 6,               # troppo giovane = pump.fun appena nato, troppo rischio
    "max_age_days": 90,               # troppo vecchio e piatto = non sta succedendo niente

    # SEGNALI DI INGRESSO (pesati per PRECOCITÀ: precoce > tardivo)
    # La liquidità che cresce mentre prezzo/volume sono ancora piatti è il
    # segnale più anticipato sui dati di mercato puri. Lo spike di volume
    # assoluto è TARDIVO: lo teniamo basso, vale come conferma, non come trigger.
    "weight_liquidity_growth": 3.0,   # variazione liquidità (PRECOCE)
    "weight_volume_accel": 2.0,       # accelerazione volume = derivata (medio-alto)
    "weight_volume_spike": 0.5,       # spike assoluto (TARDIVO, quasi conferma)
    "weight_young_with_volume": 1.5,  # pool giovane che già si muove

    # Soglia: somma dei segnali sopra cui un token diventa "candidato"
    "candidate_threshold": 2.5,

    "poll_seconds": 180,              # ogni quanto gira il discovery (3 min)
}

# ---------------------------------------------------------------------------
# ENRICHMENT — l'"investigatore". Costoso. Gira SOLO sui candidati attivi.
# ---------------------------------------------------------------------------
ENRICHMENT = {
    # RPC pubblici / free tier. Mettine uno per catena. Lasciali vuoti per ora:
    # il sistema gira lo stesso e marca i segnali on-chain come "non disponibili".
    "rpc": {
        "ethereum": "",   # es. https://eth-mainnet.g.alchemy.com/v2/LA_TUA_KEY (free tier)
        "base": "",
        "bsc": "",
        "solana": "",
    },

    # FILTRI DI SICUREZZA (KILLER ASSOLUTI -> esclusione permanente, non punteggio)
    "max_top_holder_pct": 0.50,       # se 1 wallet ha >50% può scaricarti addosso
    "max_top10_holder_pct": 0.85,     # top 10 wallet > 85% = concentrazione pericolosa
    "require_liquidity_locked": True, # liquidità non bloccata = rischio rugpull

    # RILEVAMENTO DISTRIBUZIONE (il filtro anti-"exit liquidity")
    # Se nelle ultime transazioni dominano vendite grosse di pochi wallet mentre
    # il prezzo è in alto, è distribuzione in corso: TENERSI FUORI. Penalità forte
    # o esclusione temporanea, NON un candidato.
    "distribution_sell_ratio": 0.70,  # >70% del volume recente sono Sell -> distribuzione
    "distribution_lookback": 30,      # quante trade recenti guardare

    # SEGNALI DI QUALITÀ (graduali -> diventano punteggio, NON sì/no)
    "weight_exchange_netflow_out": 3.0,  # prelievi netti da exchange = accumulo (PRECOCE)
    "weight_holder_growth": 2.0,         # numero holder in crescita
    "weight_buy_pressure": 1.5,          # più buy che sell nelle trade recenti

    # Frequenza decrescente: i nuovi candidati si arricchiscono spesso,
    # i vecchi sempre meno, finché si archiviano.
    "refresh_fresh_minutes": 5,       # asset scoperti < 6h
    "refresh_warm_minutes": 30,       # asset 6h–48h
    "refresh_cold_minutes": 720,      # asset > 48h (12h)
    "archive_after_days": 7,          # niente movimento da 7 giorni -> archivia
    "max_active_assets": 80,          # tetto duro sugli asset arricchiti in parallelo (COSTI)
}

# ---------------------------------------------------------------------------
# SOCIAL — l'"orecchio". Attenzione gratis e SENZA chiave. Gira sui candidati attivi.
# È il layer che dà vita alla CONFLUENZA: mercato + attenzione, non solo mercato.
# ---------------------------------------------------------------------------
SOCIAL = {
    # 4chan /biz/ — narrativa degen precoce. Segnale SOTTILE (catalog limitato): peso basso.
    "biz_mentions_full": 6,        # n. menzioni che vale "attenzione piena" (per normalizzare 0..1)
    "weight_biz_mentions": 1.5,    # peso del segnale /biz/

    # CoinGecko trending — attenzione già aggregata su milioni di utenti: segnale forte.
    "weight_coingecko_trending": 2.5,

    # Telegram (quando avremo api_id/api_hash) — il segnale migliore. Pronto, peso alto.
    "weight_telegram_velocity": 3.0,
}

# ---------------------------------------------------------------------------
# TELEGRAM — il segnale di attenzione più prezioso. Credenziali da .env (NON in codice).
# Senza api_id/api_hash il modulo gira a vuoto (no-op), come i punti [RPC]: niente si rompe.
# ---------------------------------------------------------------------------
import os

TELEGRAM = {
    "api_id": os.getenv("TELEGRAM_API_ID", ""),      # da my.telegram.org (vedi SETUP.md)
    "api_hash": os.getenv("TELEGRAM_API_HASH", ""),

    # NOTIFICHE in uscita (bot) — il bot token viene da @BotFather (vedi SETUP.md).
    "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
    "chat_id": os.getenv("TELEGRAM_CHAT_ID", "5182348358"),  # chat di Nicolò
    "session": "crypto_radar_tg",                     # file sessione Telethon (locale)
    "lookback_minutes": 180,                          # finestra di messaggi recenti da leggere
    "mentions_full": 8,                               # n. menzioni che vale "attenzione piena" (norm 0..1)

    # Canali SERI pre-verificati (pubblici, checkmark). NIENTE pump/scam: iniettano
    # attenzione finta. Misuriamo la velocità di menzione, non seguiamo le call.
    "channels": [
        "binance_announcements",   # listing/catalizzatori (4.07M)
        "WatcherGuru",             # news veloci / narrativa, rimbalza X (627K)
        "cointelegraph",           # news / mercato (370K)
        "lookonchain",             # money flow on-chain, smart money (38K)
        "whale_alert_io",          # transazioni grosse on-chain (313K)
    ],
}

# ---------------------------------------------------------------------------
# SCORING — somma pesata dei segnali di qualità. Decide il voto dell'Excel.
# ---------------------------------------------------------------------------
SCORING = {
    "confluence_bonus": 1.5,          # bonus se >=3 segnali positivi si allineano
    "min_signals_for_bonus": 3,
    "score_decay_hours": 24,          # i segnali vecchi pesano meno (mercato si muove)
    "min_score_for_export": 4.0,      # sotto questo (score GREZZO) non finisce nell'Excel
    "top_n_export": 25,               # quanti top mostrare
    # Scala di visualizzazione 0-10 (lo score grezzo resta la verità nel breakdown).
    # 'score_reference' = score grezzo che mappa a 10/10 (confluenza forte ma realistica).
    "score_reference": 12.0,
}

# ---------------------------------------------------------------------------
# OUTCOMES — la METRICA DI VERITÀ. Misura se gli score alti si muovono DAVVERO,
# al netto di slippage+fee simulati. Non la % di colpi giusti (mente): il VALORE ATTESO.
# ---------------------------------------------------------------------------
OUTCOMES = {
    "tracking_threshold": 3.0,    # score grezzo minimo per aprire un'entrata da validare
    "horizons": [24, 72, 168],    # ore: misura a 1g / 3g / 7g (3g = colonna Excel "dopo 3g")
    "paper_trade_usd": 500.0,     # taglia ipotetica del trade (per stimare lo slippage)
    "swap_fee_pct": 0.003,        # fee DEX per lato (0.3% tipico)
    "slippage_cap_pct": 0.15,     # tetto allo slippage stimato (15%) per non esagerare
    "max_open_assets": 100,       # tetto entrate aperte in parallelo (controllo chiamate)
}

# ---------------------------------------------------------------------------
# COSTI / RETE — paletti per non bruciare i rate limit gratuiti
# ---------------------------------------------------------------------------
LIMITS = {
    "http_timeout": 12,
    "max_retries": 3,
    "dexscreener_max_calls_per_min": 50,  # DEXScreener free: resta sotto
    "rpc_max_calls_per_min": 60,          # adatta al tuo free tier
    "user_agent": "crypto-radar/1.0 (research; paper-trading only)",
}
