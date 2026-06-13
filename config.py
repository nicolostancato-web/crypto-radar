"""
config.py — TUTTE le manopole del sistema in un posto solo.

Filosofia: nessun numero "magico" sparso nel codice. Tutto quello che vorrai
tarare guardando i dati veri sta qui. Cambi un valore qui, riparte tutto.

I pesi e le soglie iniziali sono CONSERVATIVI di proposito. Partono "stretti"
(pochi candidati, pochi falsi positivi) e li allarghi tu se vedi che ti perdi
roba. È molto più facile allargare che ripulire un Excel pieno di spazzatura.
"""

import os
# carica .env se presente (locale). Nel cloud le variabili arrivano dai secret -> no-op.
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

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

    # NOTIFICHE in uscita (bot) — opzionale, il bot token viene da @BotFather.
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
# EMAIL — canale di notifica opzionale (Gmail SMTP). Disattivo finché non si configura.
# ---------------------------------------------------------------------------
EMAIL = {
    "gmail_user": os.getenv("GMAIL_USER", "nicolostancato@gmail.com"),
    "gmail_app_password": os.getenv("GMAIL_APP_PASSWORD", ""),
    "to": os.getenv("EMAIL_TO", "nicolostancato@gmail.com"),
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
    "max_ohlcv_per_cycle": 6,     # CFO: tetto chiamate OHLCV/giro (free tier CoinGecko 10k/mese)
    "sim_recent_hours": 26,       # ri-simula solo i trade < 26h (oltre l'uscita è già definitiva)
}

# ---------------------------------------------------------------------------
# EXIT — copy-simulation con regole MECCANICHE (punto 2 consulenza). Non solo hold a 24h.
# Su ogni paper trade simula TP scalari + trailing + stop sul path di prezzo reale (OHLCV).
# ---------------------------------------------------------------------------
EXIT = {
    "stop_loss": 0.30,        # -30% -> esci tutto
    "tp1_gain": 0.50, "tp1_sell": 0.40,   # +50% -> vendi 40%
    "tp2_gain": 1.00, "tp2_sell": 0.30,   # +100% -> vendi 30%
    "trailing": 0.30,         # trailing stop 30% sul runner (resto 30%)
    "trailing_arm": 0.40,     # il trailing si attiva dopo +40%
    "hard_hours": 24,         # uscita dura dopo 24h
    "ohlcv_aggregate_min": 15,  # candele a 15 minuti
}

# ---------------------------------------------------------------------------
# LEARN — il motore di AUTO-MIGLIORAMENTO. Ritara i pesi dei segnali sugli esiti reali.
# Con i FRENI: si muove solo con abbastanza dati, a piccoli passi, dentro limiti.
# ---------------------------------------------------------------------------
LEARN = {
    "min_samples": 15,     # sotto N esiti, un segnale NON si tocca (no overfitting sul rumore)
    "horizon": 72,         # orizzonte di riferimento per imparare (3 giorni)
    "step": 0.25,          # quanto ci si muove verso il target a ogni calibrazione (graduale)
    "k": 3.0,              # sensibilità: target = 1 + k * rendimento_netto_medio
    "floor": 0.2,          # un segnale non scende sotto (non lo azzeriamo mai del tutto)
    "cap": 2.0,            # né sale sopra (non si fida ciecamente di un segnale)
}

# ---------------------------------------------------------------------------
# MAIN — Main Wallet Tracker (funding graph). Risale dai wallet bravi al MAIN coi capitali
# (es. $27M che genera 74 wallet). Tracciando il main becchiamo ogni nuovo spawn dal minuto zero.
# ---------------------------------------------------------------------------
MAIN = {
    "min_balance_sol": 30,        # un main "serio" tiene >=30 SOL
    "min_funded": 3,              # ha generato >=3 wallet di trading
    "max_funded_hub": 150,        # oltre = probabile CEX/servizio (non un operatore) -> scartato
    "max_trace_per_cycle": 2,     # quante whale risalire per giro (paging costoso)
    "max_watch_per_cycle": 3,     # quanti main ri-controllare per giro (nuovi spawn)
    "recheck_hours": 2,           # ogni 2h ricontrolla un main per nuovi tentacoli
    "spawn_min_sol": 0.1,         # finanziamento minimo per considerarlo uno spawn di trading
}

# ---------------------------------------------------------------------------
# WALLETS — scoperta smart-money DAL BASSO (Helius). CFO: solo sui token su cui entriamo.
# ---------------------------------------------------------------------------
WALLETS = {
    "capture_recent_n": 50,        # tx recenti da guardare per token (piccolo = pochi crediti)
    "max_capture_per_cycle": 8,    # max token fotografati per giro (ALZATO: Helius ha 1M/mese)
    "min_buys_for_smart": 3,       # un wallet è "smart" solo se ricorre su >= 3 token (no rumore)

    # QUALIFICA PnL (accumulo efficiente: ogni wallet si qualifica UNA volta, poi cache)
    "qualify_tx": 25,              # screen veloce: tx per il primo filtro
    "max_qualify_per_cycle": 18,   # max wallet screenati per giro (spinto: cresce la rete piu' in fretta)
    "requalify_days": 4,           # ri-qualifica un wallet solo dopo N giorni
    "min_closed_for_proven": 10,   # provato con >= 10 posizioni chiuse (stabilita': con poche, il
                                   # copy_pnl balla e mostra trappole. Meglio classifica corta ma vera)

    # WHALE = ricco + persistente + ancora attivo (oltre a profittevole+copiabile)
    "whale_min_balance_sol": 50,   # tiene >= 50 SOL (~$7.5k)
    "whale_min_biggest_buy": 8,    # ha fatto almeno un acquisto da >= 8 SOL (~$1.2k)
    "whale_min_span_days": 14,     # persistente: opera da >= 14 giorni
    "whale_max_inactive_days": 7,  # ancora attivo: ultima operazione entro 7 giorni

    # DEEP-DIVE (livello 2): solo su chi passa lo screen. Verità sul track record.
    "deep_tx": 300,                # tx per l'analisi profonda (piu' profonda = piu' stabile)
    "max_deep_per_cycle": 3,       # max deep-dive per giro (spinto da 2; ~300 call l'uno, ok 1M Helius)
    "bot_tx_per_day": 60,          # sopra questa frequenza = bot/HFT -> scartato (no deep value)

    # SNOWBALL: dalle whale verificate, scopri la rete (chi compra i loro vincenti)
    "max_snowball_per_cycle": 3,   # max whale da cui espandere per giro (ALZATO: rete cresce piu' in fretta)
    "snowball_tokens": 2,          # quanti token vincenti guardare per whale
    "snowball_buyers_tx": 30,      # tx recenti per token per trovare i co-compratori
}

# ---------------------------------------------------------------------------
# SMARTWATCH — IL PIVOT (2026-06-10): monitora DIRETTAMENTE i wallet smart noti via Helius.
# I loro buy alimentano i cluster (S3), i loro sell il segnale d'uscita (S2). Validato dal Double Agent.
# ---------------------------------------------------------------------------
SMARTWATCH = {
    "wallets_per_cycle": 20,   # TUTTI i wallet smart ogni giro (Helius ha 100x margine -> spingiamo)
    "recent_tx": 20,           # tx recenti per wallet (CFO: ~20x20=400 chiamate Helius/giro, ok 1M/mese)
    "min_buy_usd": 100,        # buy minimo (abbassato 2026-06-10: dare a S3 la max chance di
                               # vedere cluster - gli smart wallet comprano raramente insieme)
    "min_sell_usd": 20,        # sell minimo (sotto = dust/gas, non un'uscita vera)
    "lookback_s": 86400,       # solo attivita' delle ultime 24h
}

# ---------------------------------------------------------------------------
# SPIKES — "Who Knows More Than Me": i big-buy che muovono il mercato (GeckoTerminal, gratis).
# ---------------------------------------------------------------------------
SPIKES = {
    "min_usd": 400,               # soglia big-buy: via di mezzo (i $700 erano troppo stretti per
                                  # i pool piccoli; i $250 = rumore, warning del Double Agent 2026-06-10)
    "min_sell_usd": 100,          # soglia SELL piu' bassa: si vende in pezzi piccoli (diagnosi
                                  # 2026-06-10: 0 sell >$400, => S2 a secco di segnali d'uscita)
    "max_pools_per_cycle": 25,    # pool/giro ALZATO (CoinGecko Pro 100k/mese -> tanta capacita').
                                  # Piu' pool = piu' wallet scoperti = piu' dati da accumulare.
    "coordination_window_s": 600, # 10 min: big-buy sullo stesso token entro = COORDINATI
    "boss_min_tokens": 2,         # boss = big-buy su >= 2 token diversi (non casuale)

    # EARLY (punto 1 consulenza): distinguere chi entra PRIMA del trend dal pollo del top
    "early_max_age_min": 120,     # entrato entro 2h dalla nascita del pool
    "early_max_runup": 1.0,       # prezzo salito < +100% prima del suo ingresso (non insegue)
    "early_min_liq_ratio": 0.005, # buy >= 0.5% della liquidità (size significativa)
}

# ---------------------------------------------------------------------------
# SCENARIOS — il MOTORE A ELIMINAZIONE SISTEMATICA (vedi ROADMAP_STATO.md).
# Testiamo un'ipotesi alla volta: ogni scenario apre paper-trade taggati col suo nome,
# con le SUE regole d'ingresso. L'exitsim meccanico esistente calcola il ritorno netto.
# Il loop auto-analisi (ogni 6h) legge i risultati, aggiusta questi parametri da solo,
# e decide PARK / CONTINUA / FUNZIONA. "active" = lo scenario in test ora.
# ---------------------------------------------------------------------------
SCENARIOS = {
    "active": "S3_cluster",     # fallback se 'running' assente
    "running": ["S3_cluster", "S2_smartexit"],  # i due cavalli ad alta conviction, IN PARALLELO
    "min_trades_for_verdict": 30,   # sotto N paper-trade NON si dà verdetto (rumore)
    "park_ev_threshold": 0.0,       # se EV netto <= questo dopo abbastanza trade -> PARK
    "success_ev_threshold": 0.05,   # EV netto >= +5% su campione adeguato -> FUNZIONA (avvisa Nick)
    "max_entries_per_cycle": 6,     # tetto duro paper-trade aperti per giro (controllo)

    # --- S0 Baseline futility (controllo: deve perdere) ---
    "S0_baseline": {
        "min_vol_usd": 5_000,       # compra ogni asset attivo con volume minimo
    },
    # --- S1 Regime filter (entra solo in risk-on) ---
    "S1_regime": {
        "min_active_candidates": 8, # proxy risk-on: abbastanza token vivi nel radar
        "sol_trend_min": -0.05,     # SOL non in caduta (> -5% su 3g)
    },
    # --- S2 Smart-EXIT overlay (entry momentum, exit sui sell dei bravi) ---
    "S2_smartexit": {
        "momentum_lookback_s": 21600,  # entra su token con big-buy EARLY nelle ultime 6h
    },
    # --- S3 Cluster accumulation (>=N smart wallet co-comprano lo stesso token) ---
    "S3_cluster": {
        "smart_min_wallets": 2,     # >=2 wallet "smart" distinti sullo stesso token
        "window_s": 3600,           # entro 60 minuti
        "smart_def": "soft",        # soft = boss early O verificato ; strict = verificato+profittevole
        "max_runup_at_entry": 0.30, # non inseguire: prezzo salito < +30% rispetto al loro buy
    },
}

# Il loop auto-analisi (ogni 6h) scrive `scenario_overrides.json` per aggiustare i parametri
# e lo scenario attivo SENZA toccare il codice. Qui lo carichiamo e lo fondiamo (deep-merge).
def _apply_scenario_overrides():
    import json
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scenario_overrides.json")
    if not os.path.exists(path):
        return
    try:
        with open(path) as f:
            ov = json.load(f)
    except Exception:
        return
    for k, v in ov.items():
        if k.startswith("_"):      # _state = stato interno del loop, non un parametro
            continue
        if isinstance(v, dict) and isinstance(SCENARIOS.get(k), dict):
            SCENARIOS[k].update(v)
        else:
            SCENARIOS[k] = v

_apply_scenario_overrides()

# ---------------------------------------------------------------------------
# FILTER — pipeline X-FIRST step 2: filtri FORTI su DexScreener+Helius per scartare rug/dud.
# Soglie da deep search (DeepSeek 2026-06-12). CALIBRABILI: si stringono/allargano sui risultati.
# ---------------------------------------------------------------------------
FILTER = {
    "min_liquidity": 10_000,      # sotto = rug/morto (ROLL, GOOAL avevano $0)
    "max_liquidity": 2_000_000,   # sopra su token giovane = possibile wash/LP falso
    "voliq_min": 0.5,             # volume24h/liquidita': sotto = morto
    "voliq_max": 50,              # sopra = wash trading / pump artificiale
    "voliq_healthy_lo": 2, "voliq_healthy_hi": 15,  # range sano (bonus)
    "min_vol_24h": 50_000,
    "min_vol_1h": 3_000,          # momentum early (un filo sotto i $5k di DeepSeek per non perdere troppo)
    # CORSIA EARLY (review DeepSeek 13/06): un token <8h NON puo' avere vol24h alto — e' giovinezza, non difetto.
    # Per i giovani usiamo soglie volume permissive: cosi' NON cancelliamo i segnali precoci col nostro filtro.
    "early_age_hours": 8,         # sotto = "giovane": soglie volume morbide (catturiamo l'ignizione)
    "min_vol_24h_early": 5_000,
    "min_vol_1h_early": 800,
    "age_min_hours": 0,           # accettiamo anche <1h ora: gli altri filtri (liq, concentrazione) reggono i flash-rug
    "age_max_hours": 72,          # >72h = non piu' early (DeepSeek diceva 48; teniamo un filo largo)
    "min_holders": 0,             # OFF: il conteggio via Helius e' limitato a 20 (top accounts), non affidabile
    "max_top10_pct": 0.50,        # CALIBRATO 12/06: il runner BrimfableAI aveva 25%, i rug 88-100% -> 50% separa pulito
    "max_top1_pct": 0.30,         # 1 wallet >30% = allarme (era 10%, troppo stretto per gli early)
    "min_bs_ratio_1h": 1.2,       # pressione compratori (un filo sotto 1.5 per non essere troppo stretti)
    "require_authority_revoked": True,  # mint+freeze revocate = obbligatorio (KILLER)
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
