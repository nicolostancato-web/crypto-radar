"""
team_standup.py — IL CTO. Coordina la squadra di 3 agenti, 1x al giorno.

Fa girare e legge i 3 agenti che imparano ogni giorno:
  TAB 1 Accumulatore  -> quanti dati nuovi, quali fonti rendono
  TAB 2 Analista(KPI) -> c'e' un segnale? regge nel tempo? (kpi_daily.py)
  TAB 3 Trader        -> quale strategia perde meno / guadagna (trade_learner.py + portfolio_sim.py)
Aggrega tutto in web/team.json (per il dashboard a 3 tab) e manda un report senior. Onesto: dice cosa
e' migliorato e cosa no, e qual e' la mossa. Niente entusiasmo finto.
"""
import os, json, time, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))


def _accumulo():
    cas = set(); runners = 0; obs = {}
    for l in open(os.path.join(HERE, "data", "track.jsonl")):
        o = json.loads(l); cas.add(o["ca"])
        if o.get("price"):
            obs.setdefault(o["ca"], []).append(o["price"])
    for ca, pr in obs.items():
        if len(pr) >= 2 and pr[0] and max(pr) / pr[0] - 1 >= 0.5:
            runners += 1
    candles = sum(1 for _ in open(os.path.join(HERE, "data", "ohlcv.jsonl"))) if os.path.exists(os.path.join(HERE, "data", "ohlcv.jsonl")) else 0
    # crescita giornaliera dallo storico KPI
    hist = os.path.join(HERE, "data", "kpi_history.jsonl")
    growth = None
    if os.path.exists(hist):
        h = [json.loads(l) for l in open(hist)]
        if len(h) >= 2:
            growth = h[-1]["n_tokens"] - h[-2]["n_tokens"]
    return {"token": len(cas), "runner": runners, "candele_5m": candles, "crescita_ultimo_ciclo": growth}


def _trend(hist_path, key):
    if not os.path.exists(hist_path):
        return None
    h = [json.loads(l) for l in open(hist_path)]
    if len(h) < 2:
        return "primo dato"
    a, b = h[-2].get(key), h[-1].get(key)
    if a is None or b is None:
        return None
    return "in miglioramento" if b > a else ("stabile" if b == a else "in calo")


def run():
    import kpi_daily, trade_learner, portfolio_sim
    acc = _accumulo()
    kpi = kpi_daily.run()
    trade = trade_learner.run()
    port = portfolio_sim.run()

    kpi_trend = _trend(os.path.join(HERE, "data", "kpi_history.jsonl"), "lift_pt")
    trade_trend = _trend(os.path.join(HERE, "data", "trade_learnings.jsonl"), "median_pnl")

    # nota del CTO (sintesi onesta)
    if kpi and kpi.get("survives") and trade and trade.get("profitable"):
        nota = "Segnale vivo E monetizzabile: prima volta. Pronti a un paper-trading serio sul config imparato."
    elif kpi and kpi.get("survives"):
        nota = (f"Il segnale bs regge (lift +{kpi['lift_pt']}pt, OOS {kpi['oos_win']}%) ma NON e' ancora monetizzabile "
                f"(miglior P&L mediano {trade['median_pnl']}%). Il collo di bottiglia resta l'esecuzione/slippage. "
                f"Accumulo continua, candele 5m a {acc['candele_5m']}/{acc['token']}.")
    else:
        nota = (f"Nessun edge monetizzabile oggi. Il sistema fa il suo lavoro: ce lo dice a costo zero. "
                f"Continuiamo ad accumulare ({acc['token']} token, {acc['runner']} runner) e a raffinare l'uscita.")

    out = {"ts": int(time.time()),
           "tab1_accumulo": {**acc, "trend": "in crescita" if (acc.get("crescita_ultimo_ciclo") or 0) > 0 else "fermo"},
           "tab2_kpi": {"base_win": kpi["base_win"], "bs15_win": kpi["bs15_win"], "lift_pt": kpi["lift_pt"],
                        "oos_win": kpi["oos_win"], "n": kpi["n_mature"], "verdict": kpi["verdict"],
                        "trend": kpi_trend, "survives": kpi["survives"]},
           "tab3_trading": {"strategy": f"{trade['filter']} + {trade['exit']}{int(trade['trail']*100)}%",
                            "median_pnl": trade["median_pnl"], "win": trade["win"], "profitable": trade["profitable"],
                            "portfolio_final": port["final"], "n_trades": port["n_trades"], "trend": trade_trend},
           "cto_note": nota}
    with open(os.path.join(HERE, "web", "team.json"), "w") as f:
        json.dump(out, f)
    print("\n===== STANDUP SQUADRA =====")
    print(f"TAB1 Accumulo : {acc['token']} token, {acc['runner']} runner, {acc['candele_5m']} candele 5m")
    print(f"TAB2 KPI      : base {kpi['base_win']}% -> bs>=1.5 {kpi['bs15_win']}% (lift +{kpi['lift_pt']}pt, {kpi_trend})")
    print(f"TAB3 Trading  : {out['tab3_trading']['strategy']} -> mediana {trade['median_pnl']}% ({trade_trend})")
    print(f"CTO           : {nota}")

    # report email (se configurato)
    try:
        import watchdog
        body = (f"STANDUP SQUADRA crypto-radar\n\nTAB1 Accumulo: {acc['token']} token, {acc['runner']} runner, "
                f"{acc['candele_5m']} candele 5m (crescita: {acc['crescita_ultimo_ciclo']})\n"
                f"TAB2 KPI: base {kpi['base_win']}% -> bs>=1.5 {kpi['bs15_win']}% (lift +{kpi['lift_pt']}pt, {kpi_trend}) | {kpi['verdict']}\n"
                f"TAB3 Trading: {out['tab3_trading']['strategy']} -> P&L mediano {trade['median_pnl']}%, "
                f"portafoglio 100->{port['final']} EUR ({trade_trend})\n\nCTO: {nota}")
        watchdog._email("crypto-radar — standup squadra", body)
        print("[standup] report inviato")
    except Exception as e:
        print(f"[standup] email non inviata: {str(e)[:80]}")
    return out


if __name__ == "__main__":
    run()
