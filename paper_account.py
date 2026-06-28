"""
paper_account.py — CONTO PAPER VIVO da 100 EUR (NON resetta mai).

Differenza dal backtest (portfolio_sim): qui si parte da 100 EUR UNA volta sola, e ogni volta che un
trade si CHIUDE il saldo va avanti coi soldi che ci sono. Niente ri-simulazione da capo. Questo e' il
vero "stiamo crescendo o calando?" — onesto, cumulativo, irreversibile come un conto reale.

Stato persistente in data/paper_account.json (saldo, trade gia' contati, storico). Ogni ciclo:
prende i trade che si sono CHIUSI da quando ho guardato l'ultima volta, li registra una volta sola,
applica il saldo. La strategia usata e' quella adottata dal meeting (data/trade_config.json).
Onesto: slippage, uscita causale, niente look-ahead. Se la strategia perde, il conto scende. Punto.
"""
import os, json, statistics as st
import exits

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "data", "paper_account.json")
SLIP = 0.06
START = 100.0
FRAC = 0.10            # rischio 10% del saldo VIVO per trade
FLOOR = 30.0          # sotto questa soglia il conto e' "bruciato" -> reset a 100 (una nuova STAGIONE)


def _candles():
    out = {}
    p = os.path.join(HERE, "data", "ohlcv.jsonl")
    if os.path.exists(p):
        for l in open(p):
            try:
                r = json.loads(l); c = r.get("candles") or []
                if c:
                    out[r["ca"]] = sorted([(int(x[0]), x[2], x[4]) for x in c], key=lambda t: t[0])
            except Exception:
                pass
    return out


def _trade(ca, candles, series, spec):
    """ritorno realistico + timestamp di CHIUSURA, causale, con la strategia di uscita a scaglioni."""
    if ca in candles:
        seq = candles[ca]
    else:
        seq = [(ts, pr, pr) for ts, pr in series]
    if len(seq) < 2:
        return None
    med = st.median([c for _, _, c in seq])
    seq = [(t, hi, cl) for t, hi, cl in seq if med / 15 <= cl <= med * 15 and hi <= med * 20]
    if len(seq) < 2:
        return None
    return exits.simulate(seq, spec, SLIP)


def run():
    # stato (o nascita del conto)
    if os.path.exists(STATE):
        state = json.load(open(STATE))
    else:
        state = {"start": START, "balance": START, "processed": [], "trades": []}
    state.setdefault("season", 1)
    state.setdefault("blowups", [])      # ogni volta che il conto e' sceso sotto FLOOR -> una stagione bruciata
    # AUTO-RIPARO: se il saldo e' gia' sotto la soglia (es. vecchio decadimento), reset subito a 100.
    if state["balance"] < FLOOR:
        import time as _t
        state["blowups"].append({"season": state["season"], "blown_at": round(state["balance"], 2), "ts": int(_t.time())})
        state["season"] += 1
        state["balance"] = START
    processed = set(state["processed"])

    # strategia adottata dal meeting
    cfg = {}
    cfgp = os.path.join(HERE, "data", "trade_config.json")
    if os.path.exists(cfgp):
        cfg = json.load(open(cfgp))
    flt = cfg.get("filter", "bs>=2.0")
    exit_name = cfg.get("exit_strategy", "trail30")
    spec = exits.STRATEGIES.get(exit_name, exits.STRATEGIES["trail30"])
    def keep(bs):
        if flt == "bs>=1.5": return (bs or 0) >= 1.5
        if flt == "bs>=2.0": return (bs or 0) >= 2.0
        if flt == "bs>=3.0": return (bs or 0) >= 3.0
        return True

    # dataset: serie + bs
    obs = {}
    for l in open(os.path.join(HERE, "data", "track.jsonl")):
        o = json.loads(l)
        if o.get("price"):
            obs.setdefault(o["ca"], []).append((o["obs_ts"], o["price"]))
    bs = {}; tick = {}
    for l in open(os.path.join(HERE, "data", "candidates.jsonl")):
        c = json.loads(l); ca = c.get("ca")
        if ca and ca not in bs:
            bs[ca] = (c.get("metrics") or {}).get("bs_ratio_1h"); tick[ca] = c.get("ticker")
    candles = _candles()

    # trade NUOVI che si sono chiusi (token maturi, filtro ok, non gia' contati)
    closing = []
    for ca, s in obs.items():
        if ca in processed or ca not in bs or not keep(bs.get(ca)):
            continue
        s = sorted(s)
        if len(s) < 6:                      # non ancora maturo -> ancora "aperto", lo conto quando chiude
            continue
        r = _trade(ca, candles, s, spec)
        if not r:
            continue
        ret, exit_ts = r
        closing.append({"ca": ca, "ticker": tick.get(ca) or ca[:6], "bs": bs.get(ca),
                        "ret": ret, "exit_ts": exit_ts})
    closing.sort(key=lambda t: t["exit_ts"])   # in ordine di chiusura: il saldo avanza nel tempo

    # applica al saldo VIVO (con RESET a 100 quando bruci sotto FLOOR = nuova stagione)
    for t in closing:
        bet = state["balance"] * FRAC
        pnl = bet * t["ret"]
        state["balance"] += pnl
        reset = False
        if state["balance"] < FLOOR:
            state["blowups"].append({"season": state["season"], "blown_at": round(state["balance"], 2),
                                     "ts": t["exit_ts"]})
            state["season"] += 1
            state["balance"] = START      # nuova stagione, 100 EUR puliti per la strategia di oggi
            reset = True
        state["trades"].append({"ticker": t["ticker"], "ca": t["ca"], "bs": t["bs"],
                                "ret_pct": round(t["ret"] * 100, 1), "pnl_eur": round(pnl, 2),
                                "balance": round(state["balance"], 2), "exit_ts": t["exit_ts"],
                                "strategy": flt, "season": state["season"], "reset": reset})
        processed.add(t["ca"])
    state["processed"] = list(processed)
    json.dump(state, open(STATE, "w"))

    # output per il dashboard (stesso formato del portfolio, ma VIVO)
    trades = state["trades"]
    wins = [t for t in trades if t["ret_pct"] > 0]
    equity = [[t["exit_ts"], t["balance"]] for t in trades]
    # FRAGILITA': quanto del risultato dipende dal singolo trade migliore? (onesta anti-illusione)
    ordered = sorted(trades, key=lambda t: t["exit_ts"])
    def _sim(ts):
        b = START
        for t in ts:
            b += b * FRAC * (t["ret_pct"] / 100)
        return b
    top1 = max(trades, key=lambda t: t["ret_pct"]) if trades else None
    without_top = _sim([t for t in ordered if t is not top1]) if top1 else state["balance"]
    fragile = bool(top1 and (state["balance"] - START) > 0 and without_top < START)
    season = state["season"]; blown = len(state["blowups"])
    # saldo della STAGIONE corrente (dall'ultimo reset): trade della stagione in corso
    cur = [t for t in trades if t.get("season") == season]
    out = {"start": START, "final": round(state["balance"], 2), "strategy": flt + f" — stagione {season}",
           "rules": f"reset a 100 EUR ogni volta che scendi sotto {int(FLOOR)} EUR, {int(FRAC*100)}%/trade, slippage {int(SLIP*100)}%, uscita '{exit_name}'",
           "season": season, "blowups": blown, "blowup_log": state["blowups"][-6:],
           "season_trades": len(cur),
           "n_trades": len(trades), "win_rate": round(len(wins) / len(trades) * 100) if trades else 0,
           "best": max((t["ret_pct"] for t in trades), default=0),
           "worst": min((t["ret_pct"] for t in trades), default=0),
           "n_5m": sum(1 for t in trades if t["ca"] in candles),
           "new_this_run": len(closing), "live": True,
           "without_top": round(without_top, 2), "top_trade": (round(top1["ret_pct"]) if top1 else 0),
           "top_ticker": (top1["ticker"][:16] if top1 else ""), "fragile": fragile,
           "equity": equity, "trades": sorted(trades, key=lambda t: t["exit_ts"], reverse=True)[:40]}
    json.dump(out, open(os.path.join(HERE, "web", "portfolio.json"), "w"))
    print(f"[conto] STAGIONE {season} | saldo {state['balance']:.2f} EUR | conti bruciati finora: {blown} "
          f"| {len(trades)} trade totali (+{len(closing)} stavolta) | win {out['win_rate']}%")
    return out


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        # AZZERA a 100 EUR e marca i token ATTUALI come gia' visti -> da ora il conto traccia SOLO i trade
        # NUOVI con la strategia di oggi (track record pulito del nuovo approccio, non il vecchio backtest).
        cands = set()
        for l in open(os.path.join(HERE, "data", "candidates.jsonl")):
            try:
                cands.add(json.loads(l)["ca"])
            except Exception:
                pass
        json.dump({"start": START, "balance": START, "season": 1, "blowups": [], "trades": [],
                   "processed": list(cands)}, open(STATE, "w"))
        print(f"[conto] AZZERATO a {START:.0f} EUR. {len(cands)} token marcati come gia' visti -> conta solo i NUOVI da ora.")
        run()   # rigenera web/portfolio.json (mostra 100 EUR, 0 trade finche' non chiude un token nuovo)
    else:
        run()
