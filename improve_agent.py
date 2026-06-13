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
    state = _state()
    if not state:
        print("[improve] pipeline.json assente — niente stato da analizzare."); return
    prompt = _prompt(state)
    print("[improve] chiedo a DeepSeek cosa migliorare...")
    try:
        fb = da.ask_deepseek(prompt, max_tokens=4000, timeout=300)
    except Exception as e:
        print(f"[improve] DeepSeek errore: {str(e)[:150]}"); return
    if not fb:
        print("[improve] nessuna risposta da DeepSeek"); return
    os.makedirs(OUTDIR, exist_ok=True)
    day = time.strftime("%Y-%m-%d", time.gmtime())
    path = os.path.join(OUTDIR, f"improve_{day}.md")
    with open(path, "w") as f:
        f.write(f"# Cosa migliorare — {day} (DeepSeek)\n\n## Stato di oggi\n{state}\n\n## Feedback\n{fb}\n")
    print(f"[improve] feedback salvato -> data/improvements/improve_{day}.md")
    # manda l'email col feedback (decide l'umano)
    watchdog._email(
        f"🔁 Crypto-radar — cosa migliorare oggi ({day})",
        f"STATO DI OGGI:\n{state}\n\n--- FEEDBACK DEEPSEEK ---\n\n{fb}\n\n"
        f"(Loop del miglioramento: leggi, decidi cosa implementare, poi accumula 24h e si ripete.)"
    )
    return fb


if __name__ == "__main__":
    run()
