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

# Ordine di avanzamento: i due ad alta conviction prima, poi gli altri implementati.
ADVANCE_ORDER = ["S3_cluster", "S2_smartexit", "S1_regime", "S0_baseline"]
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


def _next_scenario(state, running):
    """Prossimo scenario da attivare: primo nell'ordine non già running e non parcheggiato/promosso."""
    for name in ADVANCE_ORDER:
        if name in running:
            continue
        st = state.get(name, {})
        if st.get("status") in (None, "active", "idle"):
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


def _evaluate(c, name, ov, state, ts):
    """Valuta UNO scenario running: decide FUNZIONA/PARK/RARO/CONTINUA, aggiorna stato e running."""
    params = dict(SCENARIOS.get(name, {}))
    min_trades = SCENARIOS["min_trades_for_verdict"]
    park_thr, succ_thr = SCENARIOS["park_ev_threshold"], SCENARIOS["success_ev_threshold"]
    running = ov.setdefault("running", list(SCENARIOS.get("running", [])))

    sstate = state.setdefault(name, {"status": "active", "iteration": 0, "verdict": None})
    sstate["iteration"] += 1
    it = sstate["iteration"]
    st = scenario_stats(c, name, horizon=HORIZON)
    # VERDETTO sulla MEDIANA (robusta agli outlier) + deve BATTERE il buy-and-hold.
    n, ev, total = st["n"], st["ev_median"], st["n"] + st["open"]
    beats = st.get("beats_hold")
    hold = st.get("ev_hold_median")
    decision, verdict = "CONTINUA", None

    if n >= min_trades and ev is not None and ev >= succ_thr and beats:
        decision, verdict = "FUNZIONA", f"EV mediano {ev:+.2%} su {n} trade, batte il hold ({hold:+.2%})"
        sstate["status"], sstate["verdict"] = "works", verdict
        _telegram(f"🟢 CRYPTO-RADAR: {name} FUNZIONA! {verdict}. Guarda la dashboard.")
    elif n >= min_trades and ev is not None and (ev <= park_thr or beats is False):
        why = f"EV mediano {ev:+.2%}" + ("" if beats is not False else f" NON batte il hold ({hold:+.2%})")
        verdict = f"{why} su {n} trade -> vicolo cieco"
        sstate["status"], sstate["verdict"] = "parked", verdict
        if name in running:
            running.remove(name)
        nxt = _next_scenario(state, running)
        if nxt:
            running.append(nxt)
            state.setdefault(nxt, {"status": "active", "iteration": 0, "verdict": None})
            decision = f"PARK -> avanzo a {nxt}"
        else:
            decision = "PARK -> scenari implementati esauriti"
            _telegram("⚠️ CRYPTO-RADAR: scenari esauriti. Servono S4+ o Piano B (tool alert).")
    elif total == 0 and it >= 3 and name == "S3_cluster":
        cur_w = params.get("window_s", 3600)
        new_w = min(int(cur_w * 1.5), 10800)
        if new_w != cur_w:
            ov.setdefault("S3_cluster", {})["window_s"] = new_w
            decision = f"RARO: 0 segnali in {it} giri -> finestra {cur_w}s->{new_w}s"

    ev_s = f"{ev:+.2%}" if ev is not None else "—"
    extra = f" · hold {hold:+.2%}" if hold is not None else ""
    _append_log(f"- **{ts}** · {name} it{it} · n={n} EV_med={ev_s}{extra} aperti={st['open']} · **{decision}**"
                + (f" · {verdict}" if verdict else ""))
    print(f"[auto] {name} it{it} n={n} EV_med={ev_s} hold={extra} -> {decision}")
    return st, decision


def run():
    init_db()
    ov = _load_overrides()
    state = ov.setdefault("_state", {})
    running = list(SCENARIOS.get("running", [SCENARIOS.get("active", "S3_cluster")]))
    ts = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    print(f"[auto] {ts} running={running}")

    results = []
    with get_conn() as c:
        for name in running:
            st, dec = _evaluate(c, name, ov, state, ts)
            results.append((name, st, dec))

    # Double Agent (PAGAMENTO ~$0.11): solo quando c'e' una DECISIONE vera (park/avanza/funziona/raro),
    # NON sui giri di routine "CONTINUA". CFO: il deep-think di routine lo fa il modello free.
    decisione_vera = any(not d.startswith("CONTINUA") for _, _, d in results)
    if decisione_vera:
        ai = _combined_consult(results)
        if ai:
            _append_log("  - 🤖 Double Agent:\n    " + ai.replace("\n", "\n    "))
            print("[auto] Double Agent consultato (decisione vera)")
    else:
        print("[auto] nessuna decisione -> Double Agent NON chiamato (risparmio)")

    _save_overrides(ov)
    return [d for _, _, d in results]


def _combined_consult(results):
    """Una sola chiamata al Double Agent con i numeri di tutti gli scenari running. Cost-bounded."""
    try:
        import double_agent as da
    except Exception:
        return ""
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")):
        return ""
    lines = []
    for name, st, dec in results:
        ev = f"{st['ev_net']:+.2%}" if st["ev_net"] is not None else "n/d"
        lines.append(f"- {name}: n={st['n']} EV={ev} aperti={st['open']} decisione={dec}")
    body = "\n".join(lines)
    prompt = (
        "Quant on-chain brutalmente onesto. Sto testando in paper-trading (gratis, polling orario) "
        "strategie per sfruttare la smart-money su memecoin Solana. Stato scenari:\n\n" + body +
        "\n\nIn <=180 parole: (1) lettura brutale, (2) per ognuno UN aggiustamento concreto di parametro, "
        "(3) quale è più vicino a essere un vicolo cieco. Niente fronzoli."
    )
    out = []
    for nm in ("gpt5", "deepseek"):
        try:
            fn = da.ask_gpt5 if nm == "gpt5" else da.ask_deepseek
            txt = fn(prompt, max_tokens=1400, timeout=180)
            if txt:
                out.append(f"**{nm}:** {txt.strip()}")
        except Exception as e:
            print(f"[auto] {nm} errore: {str(e)[:120]}")
    return "\n\n".join(out)


if __name__ == "__main__":
    run()
