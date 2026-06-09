"""
auto_analysis.py — IL CERVELLO DA 6 ORE (gira in cloud, GitHub Actions, Mac spento).

Ogni 6h, in autonomia:
  1. legge i risultati dello scenario attivo (paper-trade, EV netto, # trade)
  2. DECIDE da solo, con regole deterministiche e sicure:
       - FUNZIONA  -> EV netto >= soglia su campione adeguato -> alert Telegram a Nick
       - PARK      -> EV netto <= soglia dopo abbastanza trade -> avanza allo scenario dopo
       - CONTINUA  -> accumula ancora
       - RARO      -> se non genera segnali, allarga (entro limiti duri) la finestra
  3. chiama il DOUBLE AGENT (GPT-5 + DeepSeek, ~$0.11) per una lettura brutale + spunti
  4. scrive scenario_overrides.json (scenario attivo + parametri) e logga in ROADMAP_STATO.md

NIENTE soldi veri. Decisioni deterministiche; l'AI è consulente, non ha le mani sul volante.
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from config import SCENARIOS
from db import get_conn, init_db, scenario_stats
import scenarios

ROOT = os.path.dirname(os.path.abspath(__file__))
OVERRIDES = os.path.join(ROOT, "scenario_overrides.json")
ROADMAP = os.path.join(ROOT, "ROADMAP_STATO.md")

# Ordine di avanzamento: solo scenari IMPLEMENTATI. (S2/S4+ si aggiungono quando pronti.)
ADVANCE_ORDER = ["S3_cluster", "S1_regime", "S0_baseline"]
HORIZON = 24  # orizzonte di verdetto (ore)


def _load_overrides():
    if os.path.exists(OVERRIDES):
        try:
            return json.load(open(OVERRIDES))
        except Exception:
            return {}
    return {}


def _save_overrides(ov):
    json.dump(ov, open(OVERRIDES, "w"), indent=2)


def _telegram(msg):
    """Alert a Nick (best-effort). No-op se il bot non è configurato."""
    import urllib.request
    tok = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat = os.getenv("TELEGRAM_CHAT_ID", "5182348358")
    if not tok:
        print("[auto] (telegram non configurato, alert solo nel log)")
        return
    try:
        url = f"https://api.telegram.org/bot{tok}/sendMessage"
        data = json.dumps({"chat_id": chat, "text": msg}).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=15)
    except Exception as e:
        print(f"[auto] telegram errore: {str(e)[:120]}")


def _next_scenario(state, current):
    """Prossimo scenario non ancora parcheggiato/promosso nell'ordine (stato in JSON)."""
    try:
        idx = ADVANCE_ORDER.index(current)
    except ValueError:
        idx = -1
    for name in ADVANCE_ORDER[idx + 1:]:
        st = state.get(name, {})
        if st.get("status", "active") in ("idle", "active"):
            return name
    return None


def _ai_consult(active, st, params):
    """Double Agent: lettura brutale + spunti. Best-effort, costa centesimi. Ritorna testo o ''."""
    try:
        import double_agent as da
    except Exception:
        return ""
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")):
        return ""
    prompt = (
        "Sei un quant on-chain brutalmente onesto. Sto testando in paper-trading uno scenario "
        f"per copiare/sfruttare smart-money su memecoin Solana (gratis, polling orario).\n\n"
        f"SCENARIO ATTIVO: {active}\n"
        f"PARAMETRI: {json.dumps(params)}\n"
        f"RISULTATI: trade_con_esito={st['n']}, EV_netto_24h={st['ev_net']}, "
        f"win_rate={st['win_rate']}, trade_aperti={st['open']}\n\n"
        "In <=150 parole: (1) lettura brutale di questi numeri, (2) UN aggiustamento concreto "
        "di parametro che proveresti ora, (3) se è già un vicolo cieco dillo. Niente fronzoli."
    )
    out = []
    for name in ("gpt5", "deepseek"):
        try:
            fn = da.ask_gpt5 if name == "gpt5" else da.ask_deepseek
            txt = fn(prompt, max_tokens=1200, timeout=180)
            if txt:
                out.append(f"**{name}:** {txt.strip()}")
        except Exception as e:
            print(f"[auto] {name} errore: {str(e)[:120]}")
    return "\n\n".join(out)


def _append_log(line):
    try:
        with open(ROADMAP, "a") as f:
            f.write(line + "\n")
    except Exception as e:
        print(f"[auto] log errore: {e}")


def run():
    init_db()
    active = SCENARIOS["active"]
    params = dict(SCENARIOS.get(active, {}))
    min_trades = SCENARIOS["min_trades_for_verdict"]
    park_thr = SCENARIOS["park_ev_threshold"]
    succ_thr = SCENARIOS["success_ev_threshold"]

    # Stato del motore in JSON (mergeabile, niente conflitti binari su radar.db).
    ov = _load_overrides()
    state = ov.setdefault("_state", {})
    sstate = state.setdefault(active, {"status": "active", "iteration": 0, "verdict": None})
    sstate["iteration"] += 1
    iteration = sstate["iteration"]

    with get_conn() as c:   # SOLO lettura degli outcome (il radar orario possiede radar.db)
        st = scenario_stats(c, active, horizon=HORIZON)

    n, ev, total = st["n"], st["ev_net"], st["n"] + st["open"]
    ts = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    print(f"[auto] {ts} attivo={active} it={iteration} n={n} EV={ev} aperti={st['open']}")

    decision, verdict = "CONTINUA", None

    # 1) FUNZIONA?
    if n >= min_trades and ev is not None and ev >= succ_thr:
        decision = "FUNZIONA"
        verdict = f"EV netto {ev:+.2%} su {n} trade (>= +{succ_thr:.0%})"
        sstate["status"], sstate["verdict"] = "works", verdict
        _telegram(f"🟢 CRYPTO-RADAR: scenario {active} FUNZIONA! {verdict}. Controlla la dashboard.")
    # 2) PARK?
    elif n >= min_trades and ev is not None and ev <= park_thr:
        verdict = f"EV netto {ev:+.2%} su {n} trade (<= {park_thr:.0%}) -> vicolo cieco"
        sstate["status"], sstate["verdict"] = "parked", verdict
        nxt = _next_scenario(state, active)
        if nxt:
            ov["active"] = nxt
            state.setdefault(nxt, {"status": "active", "iteration": 0, "verdict": None})
            decision = f"PARK -> avanzo a {nxt}"
        else:
            decision = "PARK -> nessuno scenario rimasto (esauriti gli implementati)"
            _telegram("⚠️ CRYPTO-RADAR: scenari implementati esauriti. Servono S2/S4+ o Piano B (tool).")
    # 3) RARO: nessun segnale dopo abbastanza giri -> allarga la finestra (entro limiti duri)
    elif total == 0 and iteration >= 3 and active == "S3_cluster":
        cur_w = params.get("window_s", 3600)
        new_w = min(int(cur_w * 1.5), 10800)  # max 3h
        if new_w != cur_w:
            ov.setdefault("S3_cluster", {})["window_s"] = new_w
            decision = f"RARO: 0 segnali in {iteration} giri -> finestra {cur_w}s->{new_w}s"

    # Double Agent (consulente)
    ai = _ai_consult(active, st, params)

    _save_overrides(ov)
    ev_s = f"{ev:+.2%}" if ev is not None else "—"
    _append_log(f"- **{ts}** · {active} it{iteration} · n={n} EV={ev_s} aperti={st['open']} · **{decision}**"
                + (f" · {verdict}" if verdict else ""))
    if ai:
        _append_log(f"  - 🤖 Double Agent:\n    " + ai.replace("\n", "\n    "))

    print(f"[auto] decisione: {decision}")
    if ai:
        print("[auto] Double Agent consultato (loggato in ROADMAP_STATO.md)")
    return decision


if __name__ == "__main__":
    run()
