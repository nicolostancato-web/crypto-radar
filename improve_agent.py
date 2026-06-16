"""
improve_agent.py — IL LOOP DEL MIGLIORAMENTO automatizzato (punto 1). Vedi LOOP_MIGLIORAMENTO.md.

Ogni 24h: raccoglie lo STATO REALE del sistema (n. trade, entry timing, performance strategie, confronto
arene, lezioni, config attuale), compone un PROMPT MASSIVO e chiede a un'AI esterna (DeepSeek) "cosa
miglioreresti ADESSO dato questi dati?". Salva il feedback e lo manda via EMAIL a Nicolo, che decide cosa
implementare. Il resto del loop (implementa → accumula → analizza) resta umano-nel-loop, di proposito.

Free-ish: 1 query DeepSeek/giorno (~$0.01). Email gratis (Gmail). No key -> no-op pulito.
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except Exception:
    pass

import double_agent as da
import watchdog

HERE = os.path.dirname(os.path.abspath(__file__))
PIPE = os.path.join(HERE, "web", "pipeline.json")
OUTDIR = os.path.join(HERE, "data", "improvements")
STATE = os.path.join(HERE, "data", "improve_state.json")

# --- GATE: quando fare l'analisi critica vs quando solo accumulare ---
MIN_TRADES = 30        # soglia PRELIMINARE ragionevole (non perfezionista: evita il loop di rinvio infinito)
MIN_RUNNERS = 3        # servono dei vincitori, altrimenti non c'e' niente da cui imparare il pattern
MAX_SKIP_DAYS = 4      # dopo 4 giorni di solo-accumulo, FORZA comunque un'analisi (paura #1: mai bloccarsi)


def _load_state():
    try:
        return json.load(open(STATE))
    except Exception:
        return {"settled": 0, "skip_days": 0, "last_date": None}


def _save_state(s):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(s, open(STATE, "w"), indent=2)


def _readiness(d, prev):
    """Decide se i dati bastano E sono sensati. Ritorna (decision, reasons, metrics).
    decision: 'analyze' | 'skip' | 'force'. Protegge da: loop di rinvio (MAX_SKIP_DAYS) e trash (check qualita')."""
    les = d.get("lessons", {}) or {}
    L = d.get("learning", {}) or {}
    settled = les.get("settled") or 0
    runners = les.get("runners") or 0
    green = d.get("passed_count") or 0
    evaluated = d.get("evaluated") or 0
    delta = settled - (prev.get("settled") or 0)
    skip_days = prev.get("skip_days") or 0

    # --- check QUALITA' dei dati (paura #2: non accumulare trash) ---
    problems = []
    if prev.get("last_date") and delta <= 0:
        problems.append(f"RACCOLTA FERMA: i trade conclusi non crescono da ieri ({settled}, +{delta}). Problema nella pipeline?")
    if settled >= 50 and runners == 0:
        problems.append(f"DATASET SENZA VINCITORI: {settled} trade ma 0 runner. Filtro troppo severo o mercato morto — rivedere.")
    if evaluated >= 40 and green == 0:
        problems.append(f"ZERO PERLE su {evaluated} valutati: il filtro non fa passare nulla — troppo stretto.")

    ready = settled >= MIN_TRADES and runners >= MIN_RUNNERS
    if ready:
        decision = "analyze"
    elif skip_days >= MAX_SKIP_DAYS:
        decision = "force"   # troppi giorni fermi: analizza coi dati che ci sono, ma dillo
    else:
        decision = "skip"
    metrics = {"settled": settled, "runners": runners, "green": green, "evaluated": evaluated,
               "delta": delta, "skip_days": skip_days, "min_trades": MIN_TRADES, "min_runners": MIN_RUNNERS}
    return decision, problems, metrics


def _state():
    """Riassunto numerico dello stato reale, dal pipeline.json."""
    if not os.path.exists(PIPE):
        return None
    d = json.load(open(PIPE))
    L = d.get("learning", {})
    S = d.get("simulation", {})
    les = d.get("lessons", {})
    et = S.get("entry_timing", {})
    lines = []
    lines.append(f"- Token valutati: {d.get('evaluated')}, perle (green): {d.get('passed_count')}, tracciati: {L.get('tracked_tokens')}")
    lines.append(f"- Trade conclusi: {les.get('settled')}, runner (≥+50%): {les.get('runners')}, status learner: {les.get('status')}")
    lines.append(f"- Confronto arene (runner rate): " + ", ".join(f"{a}={v.get('runner_rate')}" for a, v in (L.get('by_arena') or {}).items()))
    lines.append(f"- Entry tardivo: perle mediana {S.get('pass_median')} vs scartati {S.get('fail_median')} (con trailing -25%)")
    if et:
        lines.append("- Timing d'ingresso (perle): " + ", ".join(f"{k}={v.get('median')}" for k, v in et.items()))
    if S.get("strategies"):
        best = S["strategies"][0]
        lines.append(f"- Miglior uscita: {best['label']} (mediana {best['median']}, win {best['win_rate']})")
    return "\n".join(lines)


def _prompt(state):
    return f"""Sei un trader-quant senior di memecoin + data scientist. Mi aiuti a migliorare un sistema, a CICLI.
Il sistema (crypto-radar, X-first): Grok scova su X memecoin Solana + AI-agent freschi -> filtro on-chain
(green/red) -> traccia ogni ora prezzo/volume/buy-sell/whale -> simula entrate/uscite -> impara. Retail LENTO
(finestra ore), paper trading, budget quasi zero (tool gratis). Scan ogni 4h, tracking ogni 1h.

STATO REALE OGGI (dati accumulati finora):
{state}

Gia' implementato dalle review precedenti: corsia 'early' nel filtro (token <8h con soglie volume morbide),
uscite su segnale-volume, test dip-entry (aspettare correzione invece del top), tracking whale ora-per-ora,
engagement X per le green.

LA RICHIESTA: aiutami a migliorare, da COACH che costruisce — non da giudice che demolisce. Sii onesto e
concreto (niente fuffa, niente false promesse), ma anche INCORAGGIANTE e motivante. Stiamo costruendo a cicli,
con pazienza: e' normale che i dati siano ancora pochi. Struttura la risposta COSI':

1. ✅ COSA STA ANDANDO BENE: 2-3 progressi reali e concreti (cosa funziona, cosa e' migliorato, i segnali
   positivi anche piccoli). Parti SEMPRE da qui — riconosci i passi avanti.
2. 🎯 LE 2-3 MOSSE PIU' UTILI ADESSO: modifiche concrete e a basso costo (cosa, perche', come), ordinate per
   impatto. Inquadrale come "il prossimo passo per crescere", non come "stai sbagliando".
3. 📊 ONESTA' SUI DATI: se il campione e' ancora piccolo dillo con serenita' (e' parte del processo), e di'
   quanti dati servono e cosa accumulare. Senza drammi: e' un cantiere, non un fallimento.
4. 💪 CHIUSURA MOTIVANTE: la SINGOLA cosa piu' importante adesso + una frase che ricorda che siamo sulla
   strada giusta e che il metodo (implementa->accumula->impara) sta funzionando.

Tono: come un mentore che crede nel progetto e ti spinge a migliorare, non come un critico che ti scoraggia."""


def run():
    if not os.path.exists(PIPE):
        print("[improve] pipeline.json assente — niente stato da analizzare."); return
    d = json.load(open(PIPE))
    state_txt = _state()
    prev = _load_state()
    decision, problems, m = _readiness(d, prev)
    day = time.strftime("%Y-%m-%d", time.gmtime())
    prob_txt = ("\n⚠️ PROBLEMI DI RACCOLTA:\n" + "\n".join("• " + p for p in problems)) if problems else ""

    # --- GATE: se i dati non bastano e non siamo bloccati da troppo, ACCUMULA (no analisi, no costo) ---
    if decision == "skip":
        new_state = {"settled": m["settled"], "skip_days": m["skip_days"] + 1, "last_date": day}
        _save_state(new_state)
        msg = (f"Giorno di ACCUMULO ({day}). Dati ancora insufficienti per un'analisi critica onesta.\n"
               f"Trade conclusi: {m['settled']}/{m['min_trades']} (+{m['delta']} da ieri) · runner: {m['runners']}/{m['min_runners']} · "
               f"perle: {m['green']}/{m['evaluated']}.\nSalto l'analisi (giorno {m['skip_days']+1}/{MAX_SKIP_DAYS} di attesa). "
               f"Forzero' comunque un'analisi al giorno {MAX_SKIP_DAYS}.{prob_txt}\n\n"
               f"(Gate del loop: niente ottimizzazione su pochi dati, ma niente attesa cieca: se la raccolta e' "
               f"ferma o senza vincitori, lo vedi sopra.)")
        print("[improve] SKIP — " + msg.replace("\n", " ")[:160])
        watchdog._email(f"⏳ Crypto-radar — accumulo, {m['settled']}/{m['min_trades']} trade ({day})", msg)
        return

    # --- ANALYZE o FORCE: abbastanza dati (o troppi giorni fermi) -> chiedo a DeepSeek ---
    note = ""
    if decision == "force":
        note = (f"\n[NB: forzo l'analisi dopo {m['skip_days']} giorni di attesa, anche se i dati sono ancora "
                f"pochi ({m['settled']} trade). Pesa le conclusioni come PRELIMINARI.]")
    print(f"[improve] {decision.upper()} — chiedo a DeepSeek ({m['settled']} trade, {m['runners']} runner)...")
    try:
        fb = da.ask_deepseek(_prompt(state_txt) + note, max_tokens=4000, timeout=300)
    except Exception as e:
        print(f"[improve] DeepSeek errore: {str(e)[:150]}"); return
    if not fb:
        print("[improve] nessuna risposta da DeepSeek"); return
    os.makedirs(OUTDIR, exist_ok=True)
    path = os.path.join(OUTDIR, f"improve_{day}.md")
    with open(path, "w") as f:
        f.write(f"# Cosa migliorare — {day} (DeepSeek, {decision})\n\n## Stato\n{state_txt}\n{prob_txt}\n\n## Feedback\n{fb}\n")
    print(f"[improve] feedback salvato -> data/improvements/improve_{day}.md")
    _save_state({"settled": m["settled"], "skip_days": 0, "last_date": day})   # reset contatore skip
    grow = f" (+{m['delta']} da ieri)" if m.get("delta", 0) > 0 else ""
    intro = (f"Ciao Nicolò 👋\n\nIl sistema sta crescendo e gira da solo: {m['settled']} trade conclusi{grow}, "
             f"{m['runners']} runner, {m['green']} perle. Tutto funziona, non devi fare nulla.\n\n"
             f"Qui sotto: i progressi di oggi e il prossimo passo per crescere. È un cantiere che avanza un "
             f"mattone alla volta — non un voto. Stiamo costruendo l'edge col metodo giusto (implementa → "
             f"accumula → impara), e sta funzionando.\n")
    watchdog._email(
        f"📈 Crypto-radar — progressi e prossimo passo ({day})",
        f"{intro}\n--- ANALISI DI OGGI ---\n\n{fb}\n\n"
        f"— Il tuo sistema. Domani si accumula ancora e si ripete. 🐋"
    )
    return fb


if __name__ == "__main__":
    run()
