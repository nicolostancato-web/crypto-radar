"""
deep_meeting.py — IL MEETING PROFONDO SETTIMANALE (non il daily di allineamento).

1x a settimana i 3 tab vanno A FONDO con l'AI cinese (GLM, analisi deep) + uno scan del mercato reale
(Grok live su X). Domanda guida, ripetuta come un mantra: COME ARRIVIAMO AL GOAL (mamma in pensione,
€1000/mese)? Come spingiamo di piu', come diventiamo profittevoli, come alziamo il win rate, cosa
dobbiamo estrarre/analizzare che non stiamo facendo. Output: una MAIL LUNGA e focalizzata.

CFO: ~3-4 chiamate AI (GLM + 1 Grok) ~ $0.30-0.40, una volta a settimana. GLM dai €10 prepagati.
"""
import os, json, statistics as st
import team_meeting as tm
import double_agent as da

HERE = os.path.dirname(os.path.abspath(__file__))


def _dossier():
    """Tutto quello che sappiamo e abbiamo, condensato per gli analisti."""
    rows, mature, candles, obs = tm.aligned_dataset()
    kpi = tm.analista(mature)
    trade = tm.trader(mature, candles, obs, kpi["recommends_to_trader"])
    runners = sum(r["run"] for r in rows)
    # storico mediana
    hist = os.path.join(HERE, "data", "meeting_history.jsonl")
    H = [json.loads(l) for l in open(hist)] if os.path.exists(hist) else []
    med_trend = " -> ".join(f"{h.get('best_median_pnl')}%" for h in H[-7:])
    # conto
    port = {}
    if os.path.exists(os.path.join(HERE, "web", "portfolio.json")):
        port = json.load(open(os.path.join(HERE, "web", "portfolio.json")))
    # ranking segnali (top)
    rank = "\n".join(f"  - {r['filter']}: win {r['win']}% (n={r['n']}, +{r['lift']}pt sulla base {kpi['base_win']}%)"
                     for r in kpi["ranking"][:6])
    # strategie di uscita testate
    exits_tested = "\n".join(f"  - {r['filter']} + {r['exit']}: media robusta {r.get('rmean','?')}%, media {r['mean']}%, mediana {r['median']}%, win {r['win']}%"
                             for r in (trade["all_tested"] if trade else [])[:6])
    d = f"""# DOSSIER crypto-radar (stato reale, niente fronzoli)

## MISSIONE (il perche')
Far smettere di lavorare la mamma di Nicolo (61 anni, lavora a 40 gradi). Servono ~1000 EUR/mese = 12.000/anno.
NON diventare ricchi: un edge piccolo, ripetibile, gestito con disciplina. Paper-trading finche' non e' provato.

## COSA ABBIAMO (Tab 1 - Dati)
- {len(rows)} token tracciati, {runners} "runner" (toccano +50%), {len(candles)} con candele 5-min
- Per ogni token: pressione buy/sell (5m/1h/6h/24h) + netta + accelerazione, liquidita', volume, eta',
  concentrazione top10, holders, authority, rugcheck (insider/lp), whale flow (swap grezzi), candele 5m
- Fonti: Grok (X live) + DexScreener + GeckoTerminal + Helius, tutte gratis o quasi

## COSA ABBIAMO IMPARATO (le scoperte dure)
1. "Toccare +50% != guadagnare": il segnale trova chi si muove, ma fare soldi e' tutto nell'USCITA.
   Un +42% "mediano" era il PICCO col senno di poi (look-ahead). Con uscita reale si perde.
2. Le balene erano look-ahead (compravano DURANTE il pump) -> inutili.
3. Unico segnale robusto: la pressione d'acquisto (bs ratio), sopravvive al crescere dei dati.
4. La coda lunga inganna: un conto a 148 EUR era 74 senza UN trade. Ora misuriamo "media robusta"
   (togliendo i piu' fortunati).
5. Le uscite A SCAGLIONI (vendi a +50%/2x/5x, lasci correre) hanno portato la media robusta da -13% a ~-1%.

## TAB 2 - KPI: classifica segnali ORA (base runner = {kpi['base_win']}%)
{rank}

## TAB 3 - TRADING: strategie di uscita testate (media robusta = quanto guadagni SENZA i colpi fortunati)
{exits_tested}
- Conto paper VIVO: stagione {port.get('season','?')}, saldo {port.get('final','?')} EUR (da 100),
  conti bruciati {port.get('blowups','?')}, fragile={port.get('fragile','?')}, win {port.get('win_rate','?')}%
- Mediana P&L giorno-su-giorno (ultimi 7): {med_trend}

## IL PROBLEMA CENTRALE
Sopravviviamo (il conto non si brucia piu') ma NON guadagniamo: media robusta ancora sotto zero (~-1%/-10%).
Il muro: per un retail LENTO su dati pubblici, lo slippage e la velocita' mangiano l'edge sottile.
"""
    return d, kpi, trade, len(rows), runners


def run():
    dossier, kpi, trade, n_tok, runners = _dossier()

    parti = {}

    # --- 0. SCAN DEL MERCATO REALE (Grok live su X) ---
    market_q = ("Sei un cacciatore di alpha sui memecoin Solana. Cerca su X in tempo reale: nel 2026, "
                "i trader che GUADAGNANO davvero sui memecoin Solana, COSA fanno di diverso? Quali segnali "
                "on-chain/sociali usano per entrare PRIMA della folla? Come gestiscono entrata e USCITA "
                "(scaglioni, trailing)? Cosa distingue chi cattura i 10x da chi perde? Concreto, niente ovvieta'.")
    try:
        parti["mercato"] = da.ask_grok(market_q, max_tokens=2500, timeout=240, live_x=True) or "(nessuna risposta)"
    except Exception as e:
        parti["mercato"] = f"(scan mercato non riuscito: {str(e)[:80]})"

    # --- 1-3. ANALISI PROFONDE con l'AI CINESE (GLM) ---
    base = dossier + "\n\nVai A FONDO. Niente frasi di circostanza. Numeri, ipotesi testabili, azioni concrete."
    prompts = {
        "dati_kpi": base + "\n\n# IL TUO COMPITO (Tab 1+2: Dati e Segnali)\n"
            "Analizza in profondita': quale e' il percorso PIU' FORTE verso un edge vero con i dati che abbiamo? "
            "Cosa dovremmo ESTRARRE o CALCOLARE che non stiamo facendo (nuove feature, derivate, combinazioni)? "
            "Quale segnale o COMBINAZIONE di segnali ha la miglior chance di alzare il win-rate sopra la base? "
            "Dove stiamo sprecando dati? Dammi 3-5 mosse concrete e testabili, in ordine di impatto.",
        "trading": base + "\n\n# IL TUO COMPITO (Tab 3: Trading)\n"
            "Come passiamo da media robusta negativa a POSITIVA? Analizza a fondo le uscite a scaglioni: "
            "quali livelli di take-profit e trailing massimizzano il guadagno robusto su questa coda lunga? "
            "Come alziamo il win-rate (oggi ~25-30%)? Conviene piu' selettivi (meno trade, migliori) o piu' larghi? "
            "Position sizing: frazione fissa, Kelly, o cosa, dato che vinciamo poche volte ma grosso? "
            "Dammi la strategia di uscita+sizing precisa da testare la prossima settimana.",
        "goal": base + "\n\n# IL TUO COMPITO (Sintesi - IL GOAL)\n"
            "RAGIONA COME UN SOCIO che vuole far smettere di lavorare la mamma di Nicolo. E' passato del tempo. "
            "Dato TUTTO lo stato sopra: quanto siamo REALMENTE vicini o lontani da 1000 EUR/mese? "
            "Qual e' il percorso piu' realistico e veloce - continuare su questo edge, o cambiare angolo? "
            "Se l'edge sui dati pubblici non basta, qual e' l'alternativa onesta? "
            "Dammi un PIANO prioritizzato per i prossimi 7 giorni: 3 cose da fare, brutali e concrete, "
            "per spingere verso il goal. Sii onesto se la strada e' lunga, ma indica la direzione.",
    }
    for k, p in prompts.items():
        try:
            parti[k] = da.ask_glm(p, max_tokens=4000, timeout=300) or "(nessuna risposta GLM)"
        except Exception as e:
            parti[k] = f"(GLM non riuscito: {str(e)[:80]})"

    # --- COMPONI LA MAIL LUNGA, FOCALIZZATA SUL GOAL ---
    email = f"""🎯 MEETING PROFONDO SETTIMANALE — crypto-radar

Ragazzi, e' passato del tempo. Ci ripetiamo la sola cosa che conta: DOBBIAMO ARRIVARE AL GOAL.
La mamma di Nicolo deve poter smettere di lavorare. 1000 EUR/mese. Non un sogno: un piano.

Stato oggi: {n_tok} token accumulati, {runners} runner. Sopravviviamo ma non guadagniamo ANCORA.
Oggi non ci alleniamo soltanto: andiamo NEL PROFONDO. Cosa abbiamo, come spingiamo, come diventiamo
profittevoli, come alziamo la percentuale di successo, come arriviamo al goal.

================================================================
🌍 COSA FUNZIONA NEL MERCATO REALE ADESSO (scan live su X)
================================================================
{parti['mercato']}

================================================================
📡🔬 TAB 1+2 — DATI & SEGNALI: dove possiamo migliorare (analisi profonda)
================================================================
{parti['dati_kpi']}

================================================================
💰 TAB 3 — TRADING: come diventiamo profittevoli (analisi profonda)
================================================================
{parti['trading']}

================================================================
🧠 LA SINTESI — IL PIANO PER ARRIVARE AL GOAL
================================================================
{parti['goal']}

================================================================
Dobbiamo arrivare al goal. Come spingiamo di piu', come ci miglioriamo, una settimana alla volta.
Prossimo meeting profondo: tra 7 giorni. Nel mezzo: il sistema accumula e si allena ogni giorno.
"""
    with open(os.path.join(HERE, "data", "deep_meeting_last.md"), "w") as f:
        f.write(email)
    try:
        import watchdog
        watchdog._email("crypto-radar — MEETING PROFONDO settimanale (come arriviamo al goal)", email)
        print("[deep] mail lunga inviata")
    except Exception as e:
        print(f"[deep] email non inviata: {str(e)[:80]}")
    print(f"[deep] meeting profondo fatto: {n_tok} token, {len(parti)} analisi (1 Grok + 3 GLM)")
    return email


if __name__ == "__main__":
    import sys, datetime
    if len(sys.argv) > 1 and sys.argv[1] == "weekly":
        # gira solo 1 volta ogni 7 giorni (l'investitore torna a settimana), anche se il cron e' ballerino
        marker = os.path.join(HERE, "data", "deep_meeting_last_date.txt")
        today = datetime.datetime.utcnow()
        last = None
        if os.path.exists(marker):
            try:
                last = datetime.datetime.strptime(open(marker).read().strip(), "%Y-%m-%d")
            except Exception:
                last = None
        if last and (today - last).days < 7:
            print(f"[deep] gia' fatto {(today-last).days}g fa, salto (settimanale)"); sys.exit(0)
        run()
        open(marker, "w").write(today.strftime("%Y-%m-%d"))
    else:
        run()
