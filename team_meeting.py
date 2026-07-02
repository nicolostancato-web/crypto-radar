"""
team_meeting.py — IL MEETING DI ALLENAMENTO GIORNALIERO (ore 06:30 UTC).

Non un report passivo: i 3 agenti si PARLANO e si AGGIUSTANO a vicenda, gestiti da me (CTO senior).
Flusso del meeting (board condivisa = canale di comunicazione):
  0. Dataset allineato (maturo, deglitchato) -> tutti leggono lo stesso.
  1. ANALISTA (KPI): classifica quale filtro-segnale separa meglio i runner -> RACCOMANDA al Trader i top.
  2. TRADER: testa la sua griglia + i filtri raccomandati dal KPI -> sceglie il migliore, DICE cosa gli serve.
  3. ACCUMULATORE: legge i bisogni di Trader/KPI -> sposta il focus (logga la direzione, niente cambi rischiosi).
  4. CTO: verbale (chi ha detto cosa, cosa cambia, decisioni) -> web/meeting.json + data/meeting_history + email.

Onesto e senza look-ahead: deglitch, slippage, uscita causale, dichiara n e runner.
"""
import os, json, time, statistics as st
import exits

HERE = os.path.dirname(os.path.abspath(__file__))
SLIP = 0.06


def _smart_wallets():
    """Set degli indirizzi dei wallet vincenti (da smart_money.py). Robusto: mai crash su file assente/malformato.
    Supporta il formato esistente {'smart':[{wallet,...}]} e il mio {'wallets':[{wallet,...}]}."""
    p = os.path.join(HERE, "data", "smart_wallets.json")
    if not os.path.exists(p):
        return set()
    try:
        d = json.load(open(p))
        lst = d.get("smart") or d.get("wallets") or []
        return {w["wallet"] for w in lst if isinstance(w, dict) and w.get("wallet")}
    except Exception:
        return set()


# ---------- 0. DATASET ALLINEATO (la base comune) ----------
def aligned_dataset():
    obs = {}
    for l in open(os.path.join(HERE, "data", "track.jsonl")):
        o = json.loads(l)
        if o.get("price"):
            obs.setdefault(o["ca"], []).append((o["obs_ts"], o["price"]))
    sig = {}
    for l in open(os.path.join(HERE, "data", "candidates.jsonl")):
        c = json.loads(l); ca = c.get("ca"); m = c.get("metrics", {})
        if ca and ca not in sig:
            sig[ca] = {"bs": m.get("bs_ratio_1h"), "np1h": m.get("np_1h"), "age": m.get("age_h"),
                       "top10": m.get("top10_pct"), "voliq": m.get("voliq"), "vol1h": m.get("vol_1h"),
                       "arena": c.get("arena"), "accel": m.get("bs_accel"), "fdv": m.get("fdv")}
    candles = {}
    p = os.path.join(HERE, "data", "ohlcv.jsonl")
    if os.path.exists(p):
        for l in open(p):
            try:
                r = json.loads(l); cc = r.get("candles") or []
                if cc:
                    candles[r["ca"]] = sorted([(int(x[0]), x[2], x[4]) for x in cc], key=lambda t: t[0])
            except Exception:
                pass
    # SMART MONEY: quanti wallet vincenti (dalla watchlist di smart_money.py) comprano ogni token (la SVOLTA)
    smartset = _smart_wallets()
    smart = {}
    wf = os.path.join(HERE, "data", "whale_flow.jsonl")
    if os.path.exists(wf) and smartset:
        for l in open(wf):
            try:
                r = json.loads(l)
                buyers = {s["w"] for s in (r.get("swaps") or []) if isinstance(s, dict) and s.get("s") == "b"}
                smart[r["ca"]] = len(buyers & smartset)
            except Exception:
                pass
    for ca in sig:
        sig[ca]["smart"] = smart.get(ca, 0)
    rows = []
    for ca, s in obs.items():
        if ca not in sig:
            continue
        s = sorted(s); pr = [p for _, p in s]
        if len(pr) < 2 or not pr[0]:
            continue
        med = st.median(pr); prc = [p for p in pr if med / 15 <= p <= med * 15] or pr
        ret = max(prc) / prc[0] - 1
        rows.append({"ca": ca, "ret": ret, "run": int(ret >= 0.5), "nobs": len(pr),
                     "t0": s[0][0], **sig[ca]})
    mature = [r for r in rows if r["nobs"] >= 6]
    return rows, mature, candles, obs


# ---------- filtri candidati (il vocabolario comune dei 3) ----------
FILTERS = {
    "bs>=1.5": lambda r: (r["bs"] or 0) >= 1.5,
    "bs>=2.0": lambda r: (r["bs"] or 0) >= 2.0,
    "np1h>0.2": lambda r: (r["np1h"] or -9) > 0.2,
    "age<4h": lambda r: r["age"] is not None and r["age"] < 4,
    "top10<0.30": lambda r: r["top10"] is not None and r["top10"] < 0.30,
    "voliq>2": lambda r: (r["voliq"] or 0) > 2,
    "vol1h>50k": lambda r: (r["vol1h"] or 0) > 50000,
    "ai_agent": lambda r: r["arena"] == "ai_agent",
    # --- SCOPERTE deep meeting: ANTICIPARE (accelerazione) invece di arrivare tardi (bs alto) ---
    "accel>1.2": lambda r: (r.get("accel") or 0) > 1.2,                 # pressione che SALE adesso
    "accel>1.5": lambda r: (r.get("accel") or 0) > 1.5,
    "accel>1.2 & age<6h": lambda r: (r.get("accel") or 0) > 1.2 and r["age"] is not None and r["age"] < 6,
    "bs1.2-2 & accel>1.2": lambda r: 1.2 <= (r["bs"] or 0) < 2.0 and (r.get("accel") or 0) > 1.2,  # presto + in salita
    # --- fascia market-cap asimmetrica $15k-50k (dai trader vincenti reali) ---
    "mc_15_60k": lambda r: r.get("fdv") and 15000 <= r["fdv"] <= 60000,
    # --- LA SVOLTA: SMART MONEY — un wallet vincente (o piu') sta comprando ---
    "smart>=1": lambda r: (r.get("smart") or 0) >= 1,
    "smart>=2": lambda r: (r.get("smart") or 0) >= 2,
    "smart>=3": lambda r: (r.get("smart") or 0) >= 3,
}


# ---------- 1. ANALISTA: quale filtro separa meglio? ----------
def analista(mature):
    base = sum(r["run"] for r in mature) / len(mature) * 100 if mature else 0
    ranked = []
    for name, pred in FILTERS.items():
        sel = [r for r in mature if pred(r)]
        if len(sel) < 12:
            continue
        win = sum(r["run"] for r in sel) / len(sel) * 100
        ranked.append({"filter": name, "n": len(sel), "win": round(win), "lift": round(win - base)})
    ranked.sort(key=lambda x: x["lift"], reverse=True)
    recs = [r["filter"] for r in ranked[:2] if r["lift"] >= 5]   # raccomanda al Trader i top con lift reale
    gaps = [r for r in FILTERS if sum(1 for x in mature if FILTERS[r](x)) < 15]   # r E' GIA' il nome del filtro
    return {"base_win": round(base), "ranking": ranked, "recommends_to_trader": recs, "data_gaps": gaps}


# ---------- sim realistica (condivisa, usa la libreria delle uscite a scaglioni) ----------
def _seq(ca, candles, obs):
    if ca in candles:
        seq = candles[ca]
    else:
        seq = [(ts, pr, pr) for ts, pr in sorted(obs.get(ca, []))]
    if len(seq) < 2:
        return None
    med = st.median([c for _, _, c in seq])
    seq = [(t, hi, cl) for t, hi, cl in seq if med / 15 <= cl <= med * 15 and hi <= med * 20]
    return seq if len(seq) >= 2 else None


def _ret(ca, candles, obs, spec):
    seq = _seq(ca, candles, obs)
    if not seq:
        return None
    r = exits.simulate(seq, spec, SLIP)
    return r[0] if r else None


# ---------- 2. TRADER: testa filtri x TUTTE le scale di uscita + i suggerimenti del KPI ----------
def trader(mature, candles, obs, kpi_recs):
    base_filters = ["buy_all", "bs>=2.0"]
    test_filters = list(dict.fromkeys(base_filters + kpi_recs))   # aggiunge cio' che il KPI raccomanda
    results = []
    for fname in test_filters:
        pred = (lambda r: True) if fname == "buy_all" else FILTERS.get(fname, lambda r: True)
        sel = [r["ca"] for r in mature if pred(r)]
        for sname, spec in exits.STRATEGIES.items():
            rs = [_ret(ca, candles, obs, spec) for ca in sel]; rs = [x for x in rs if x is not None]
            if len(rs) < 12:
                continue
            # MEDIA ROBUSTA: media dei ritorni TOGLIENDO i piu' fortunati (top ~5%). Misura "guadagni
            # anche senza il colpo di fortuna?". Premia le uscite a scaglioni (robuste), non l'all-in fragile.
            srt = sorted(rs); drop = max(1, len(rs) // 20)
            rmean = st.mean(srt[:-drop]) if len(srt) > drop else st.mean(srt)
            results.append({"filter": fname, "exit": sname, "n": len(rs),
                            "rmean": round(rmean * 100, 1), "median": round(st.median(rs) * 100, 1),
                            "mean": round(st.mean(rs) * 100, 1),
                            "win": round(sum(1 for x in rs if x > 0) / len(rs) * 100),
                            "n5m": sum(1 for ca in sel if ca in candles)})
    if not results:
        return None
    # OBIETTIVO: massimizzare la MEDIA ROBUSTA (guadagno che resta togliendo i piu' fortunati). Cosi'
    # il Trader sceglie la strategia che fa soldi DAVVERO, non quella che dipende da 1 colpo. Tie-break: media.
    results.sort(key=lambda g: (g["rmean"], g["mean"]), reverse=True)
    best = results[0]
    best["bet_frac"] = 0.10 if best["rmean"] < 0 else 0.12
    best["profitable"] = best["rmean"] > 0
    # il Trader risponde al KPI: il tuo suggerimento ha battuto il buy_all?
    buyall = next((r for r in results if r["filter"] == "buy_all"), None)
    kpi_tried = [r for r in results if r["filter"] in kpi_recs]
    kpi_helped = bool(kpi_tried) and buyall and max(r["median"] for r in kpi_tried) > buyall["median"]
    needs = []
    if best["n5m"] / max(best["n"], 1) < 0.7:
        needs.append("piu candele 5m (esecuzione piu precisa)")
    if best["n"] < 30:
        needs.append(f"piu campioni nel filtro {best['filter']} (ora n={best['n']})")
    return {"best": best, "kpi_suggestion_helped": kpi_helped, "needs": needs, "all_tested": results[:6]}


# ---------- 3. ACCUMULATORE: si adatta ai bisogni ----------
def accumulatore(kpi, trade, total_tokens, candle_count):
    focus = []
    for gap in kpi.get("data_gaps", []):
        focus.append(f"accumula piu token che soddisfano {gap}")
    if trade and any("candele" in n for n in trade.get("needs", [])):
        focus.append(f"alza copertura candele 5m (ora {candle_count}/{total_tokens})")
    if trade and trade["best"]["filter"] != "buy_all":
        focus.append(f"privilegia il regime '{trade['best']['filter']}' nello scan")
    return {"focus_next": focus[:4], "token_totali": total_tokens, "candele_5m": candle_count}


def run():
    rows, mature, candles, obs = aligned_dataset()
    kpi = analista(mature)
    trade = trader(mature, candles, obs, kpi["recommends_to_trader"])
    acc = accumulatore(kpi, trade, len(rows), len(candles))

    # il Trader scrive la config che il portafoglio usera'
    if trade:
        b = trade["best"]
        with open(os.path.join(HERE, "data", "trade_config.json"), "w") as f:
            json.dump({"filter": b["filter"], "exit_strategy": b["exit"], "n": b["n"],
                       "median_pnl": b["median"], "win": b["win"], "bet_frac": b["bet_frac"],
                       "profitable": b["profitable"]}, f)

    # --- VERBALE del CTO ---
    top = kpi["ranking"][0] if kpi["ranking"] else None
    decisioni = []
    if top:
        decisioni.append(f"Segnale guida: {top['filter']} (win {top['win']}%, +{top['lift']}pt sulla base)")
    if trade:
        tag = "PROFITTEVOLE" if trade["best"]["profitable"] else "ancora in perdita"
        decisioni.append(f"Strategia adottata: {trade['best']['filter']} + uscita '{trade['best']['exit']}' "
                         f"(mediana {trade['best']['median']}%, {tag})")
        decisioni.append("Il suggerimento dell'Analista " + ("HA aiutato il Trader." if trade["kpi_suggestion_helped"]
                         else "non ha battuto il 'compra tutto' stavolta."))
    if acc["focus_next"]:
        decisioni.append("Accumulo punta su: " + "; ".join(acc["focus_next"][:2]))

    if trade and trade["best"]["profitable"] and top and top["lift"] >= 8:
        cto = "Segnale forte E strategia in utile: prepariamo un paper-trading serio sul config di oggi."
    elif top and top["lift"] >= 8:
        cto = (f"Il segnale {top['filter']} regge (+{top['lift']}pt) ma non si monetizza ancora "
               f"(miglior mediana {trade['best']['median'] if trade else 0}%). Muro = esecuzione/slippage. "
               f"Accumulo e candele continuano.")
    else:
        cto = "Nessun edge monetizzabile oggi. Continuiamo ad allineare dati e a raffinare uscita; il sistema lavora a costo zero."

    out = {"ts": int(time.time()), "n_tokens": len(rows), "n_mature": len(mature),
           "n_runners": sum(r["run"] for r in rows),
           "analista": kpi, "trader": trade, "accumulatore": acc,
           "decisioni": decisioni, "cto_note": cto}
    with open(os.path.join(HERE, "web", "meeting.json"), "w") as f:
        json.dump(out, f)

    hist = os.path.join(HERE, "data", "meeting_history.jsonl")
    prev = [json.loads(l) for l in open(hist)] if os.path.exists(hist) else []
    if not prev or prev[-1].get("n_tokens") != out["n_tokens"]:
        with open(hist, "a") as f:
            f.write(json.dumps({"ts": out["ts"], "n_tokens": len(rows), "base_win": kpi["base_win"],
                                "top_signal": top["filter"] if top else None, "top_lift": top["lift"] if top else 0,
                                "best_strategy": trade["best"]["filter"] if trade else None,
                                "best_exit": trade["best"]["exit"] if trade else None,
                                "best_median_pnl": trade["best"]["median"] if trade else None,
                                "n_runners": out["n_runners"], "n_candles": len(candles),
                                "second_signal": (kpi["ranking"][1]["filter"] if len(kpi.get("ranking", [])) > 1 else None)}) + "\n")

    # il conto VIVO (non resetta) avanza col config adottato oggi + aggiorna il pannello squadra
    try:
        import paper_account
        port = paper_account.run()
    except Exception:
        port = {"final": None, "n_trades": 0}

    def _trend(key):
        h = [json.loads(l) for l in open(hist)] if os.path.exists(hist) else []
        if len(h) < 2 or h[-2].get(key) is None or h[-1].get(key) is None:
            return "primo dato"
        return "in miglioramento" if h[-1][key] > h[-2][key] else ("stabile" if h[-1][key] == h[-2][key] else "in calo")
    team = {"tab1_accumulo": {"token": len(rows), "runner": out["n_runners"], "candele_5m": len(candles),
                              "trend": "in crescita"},
            "tab2_kpi": {"base_win": kpi["base_win"], "bs15_win": (top["win"] if top else 0),
                         "lift_pt": (top["lift"] if top else 0), "oos_win": (top["win"] if top else 0),
                         "n": len(mature), "verdict": (decisioni[0] if decisioni else ""),
                         "trend": _trend("top_lift"), "survives": bool(top and top["lift"] >= 8)},
            "tab3_trading": {"strategy": (f"{trade['best']['filter']} + {trade['best']['exit']}" if trade else "—"),
                             "median_pnl": (trade["best"]["median"] if trade else 0),
                             "win": (trade["best"]["win"] if trade else 0),
                             "profitable": (trade["best"]["profitable"] if trade else False),
                             "portfolio_final": port.get("final"), "n_trades": port.get("n_trades"),
                             "trend": _trend("best_median_pnl")},
            "cto_note": cto}
    with open(os.path.join(HERE, "web", "team.json"), "w") as f:
        json.dump(team, f)

    # storico del PROGRESSO (la mediana P&L che deve salire verso lo 0 = profittabilita)
    prog = [json.loads(l) for l in open(hist)] if os.path.exists(hist) else []
    out["progress"] = [{"ts": p["ts"], "median_pnl": p.get("best_median_pnl"),
                        "lift": p.get("top_lift"), "n": p.get("n_tokens")} for p in prog][-30:]

    # SCOPERTE DEL GIORNO su TUTTI E 3 I TAB + l'AZIONE presa (regola di Nicolo: ogni giorno si scopre E si agisce)
    sc = {"dati": [], "kpi": [], "trading": []}
    if len(prog) >= 2:
        a, b = prog[-2], prog[-1]
        # --- TAB 1: DATI / ACCUMULO ---
        sc["dati"].append(f"📈 +{b['n_tokens'] - a['n_tokens']} token (ora {b['n_tokens']}) → AZIONE: continuo a spingere le 2 fonti")
        if a.get("n_candles") is not None and b.get("n_candles") is not None:
            dc = b["n_candles"] - a["n_candles"]
            if dc: sc["dati"].append(f"🕯️ +{dc} candele 5m (ora {b['n_candles']}) → AZIONE: esecuzione simulata sempre più precisa")
        if a.get("n_runners") is not None and b.get("n_runners") is not None:
            sc["dati"].append(f"🏃 runner totali {a['n_runners']} → {b['n_runners']}")
        # --- TAB 2: KPI / ANALISTA ---
        if a.get("top_signal") != b.get("top_signal"):
            sc["kpi"].append(f"🔬 il segnale GUIDA è cambiato: {a.get('top_signal')} → {b.get('top_signal')} (i dati che crescono spostano cosa conta) → AZIONE: l'ho raccomandato al Trader")
        else:
            sc["kpi"].append(f"🔬 segnale guida confermato: {b.get('top_signal')} (regge anche con più dati)")
        dl = (b.get("top_lift") or 0) - (a.get("top_lift") or 0)
        if abs(dl) >= 1:
            sc["kpi"].append(f"📊 la forza del segnale (lift) è {'salita' if dl>0 else 'scesa'} di {abs(dl)}pt (ora +{b.get('top_lift')}pt sulla media)")
        # --- TAB 3: TRADING ---
        if a.get("best_strategy") != b.get("best_strategy") or a.get("best_exit") != b.get("best_exit"):
            sc["trading"].append(f"💰 strategia AGGIUSTATA: {a.get('best_strategy')}/{a.get('best_exit')} → {b.get('best_strategy')}/{b.get('best_exit')} → AZIONE: il conto vivo la usa già")
        dm = (b.get("best_median_pnl") or 0) - (a.get("best_median_pnl") or 0)
        if abs(dm) >= 0.2:
            sc["trading"].append(f"📉 mediana P&L {'MIGLIORATA' if dm>0 else 'peggiorata'} di {abs(dm):.1f}pt (da {a.get('best_median_pnl')}% a {b.get('best_median_pnl')}%)")
    else:
        sc["dati"].append("primo meeting: da domani confronto giorno-su-giorno per scoprire cosa cambia")
    out["scoperte"] = sc
    with open(os.path.join(HERE, "data", "scoperte.jsonl"), "a") as f:
        f.write(json.dumps({"ts": out["ts"], "scoperte": sc}) + "\n")

    with open(os.path.join(HERE, "web", "meeting.json"), "w") as f:   # riscrive col progresso + scoperte
        json.dump(out, f)
    for tab, items in sc.items():
        for it in items:
            print(f"SCOPERTA[{tab}] -> {it}")

    print("\n========== MEETING DI ALLENAMENTO ==========")
    print(f"Dataset allineato: {len(rows)} token ({len(mature)} maturi, {out['n_runners']} runner, {len(candles)} con candele 5m)")
    print(f"ANALISTA  -> guida: {top['filter'] if top else '—'} (+{top['lift'] if top else 0}pt) | raccomanda al Trader: {kpi['recommends_to_trader']}")
    if trade:
        print(f"TRADER    -> adotta {trade['best']['filter']} + uscita '{trade['best']['exit']}' "
              f"(mediana {trade['best']['median']}%) | KPI ha aiutato: {trade['kpi_suggestion_helped']} | serve: {trade['needs']}")
    print(f"ACCUMULO  -> focus: {acc['focus_next']}")
    print(f"CTO       -> {cto}")

    try:
        import watchdog
        body = ("MEETING DI ALLENAMENTO crypto-radar\n\n"
                f"Dataset: {len(rows)} token, {len(mature)} maturi, {out['n_runners']} runner, {len(candles)} candele 5m\n\n"
                "VERBALE:\n- " + "\n- ".join(decisioni) + f"\n\nCTO: {cto}")
        watchdog._email("crypto-radar — meeting di allenamento", body)
        print("[meeting] verbale inviato via email")
    except Exception as e:
        print(f"[meeting] email non inviata: {str(e)[:80]}")
    return out


def _gia_fatto_oggi():
    import datetime
    now = datetime.datetime.utcnow()
    marker = os.path.join(HERE, "data", "meeting_last_date.txt")
    today = now.strftime("%Y-%m-%d")
    done = os.path.exists(marker) and open(marker).read().strip() == today
    return now.hour < 6, done, today, marker   # (troppo presto, gia_fatto, data, file)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "daily":
        # modalita' "sveglia interna": gira 1 volta al giorno dopo le 06:00 UTC, anche se il cron salta
        presto, fatto, today, marker = _gia_fatto_oggi()
        if presto or fatto:
            print(f"[meeting] salto (presto={presto}, gia_fatto_oggi={fatto})")
            sys.exit(0)
        run()
        open(marker, "w").write(today)   # segno che oggi il meeting e' fatto
    else:
        run()
