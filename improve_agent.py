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

LA DOMANDA: dato lo stato e i dati di OGGI, **cosa miglioreresti ADESSO?** Dammi 3-5 modifiche CONCRETE,
implementabili coi miei vincoli (gratis/low-cost, retail lento), ordinate per impatto. Per ognuna: cosa,
perche', come (passi concreti), e che dato mi aspetto migliori. Sii brutale e specifico, niente fuffa.
Se i dati sono ancora troppo pochi per concludere qualcosa, DILLO chiaramente e di' solo cosa accumulare.
Chiudi con: la SINGOLA cosa piu' importante da fare adesso."""


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
    watchdog._email(
        f"🔁 Crypto-radar — cosa migliorare ({day})",
        f"STATO:\n{state_txt}{prob_txt}\n\n--- FEEDBACK DEEPSEEK ---\n\n{fb}\n\n"
        f"(Loop: leggi, decidi cosa implementare, poi accumula 24h e si ripete.)"
    )
    return fb


if __name__ == "__main__":
    run()
