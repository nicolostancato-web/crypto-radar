"""
qa_agent.py — L'AGENTE QA GIORNALIERO (il controllo qualità).

Gira 1x al giorno e si assicura che TUTTO sia su: NO bug, NO interruzioni. E' diverso dal watchdog
(che guarda la freschezza dei dati): questo fa uno SMOKE TEST vero della pipeline — importa e GIRA i
pezzi critici e verifica che non crashino — + controlla l'integrita' dei dati + la freschezza.
Se qualcosa e' rotto, manda un'email con l'errore ESATTO (traceback), cosi' un bug si becca in minuti,
non in ore. Non crasha mai lui stesso: ogni check e' isolato.

Perche' esiste: il 2026-07-02 un bug in team_meeting (r['filter'] su stringa) ha fatto fallire track.yml
per 11h prima che ce ne accorgessimo. Questo agente esiste per non farlo succedere mai piu'.
"""
import os, json, time, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
results = []


def check(name):
    """decorator: isola ogni verifica, registra OK/FAIL + dettaglio, non propaga mai eccezioni."""
    def deco(fn):
        try:
            detail = fn()
            results.append((True, name, detail or "ok"))
        except Exception as e:
            tb = traceback.format_exc().strip().splitlines()
            results.append((False, name, f"{type(e).__name__}: {str(e)[:150]} | {tb[-2].strip() if len(tb) > 1 else ''}"))
        return fn
    return deco


def _age_h(path, keys=("ts", "obs_ts")):
    p = os.path.join(HERE, path)
    rows = [l for l in open(p) if l.strip()]
    last = json.loads(rows[-1])
    for k in keys:
        if last.get(k):
            return (time.time() - last[k]) / 3600
    return None


# ---------- 1. INTEGRITA' DATI: ogni file parseabile ----------
@check("integrita dati (jsonl/json parseabili)")
def _integrity():
    bad = []
    for f in os.listdir(os.path.join(HERE, "data")):
        p = os.path.join(HERE, "data", f)
        if f.endswith(".jsonl"):
            for i, l in enumerate(open(p)):
                if l.strip():
                    try:
                        json.loads(l)
                    except Exception:
                        bad.append(f"{f}:riga{i+1}"); break
        elif f.endswith(".json"):
            try:
                json.load(open(p))
            except Exception:
                bad.append(f)
    if bad:
        raise ValueError("file corrotti: " + ", ".join(bad[:5]))
    return "tutti i file dati validi"


# ---------- 2. SMOKE TEST: i pezzi critici GIRANO senza crash ----------
@check("smoke test — team_meeting (dataset+analista+trader)")
def _meeting():
    import importlib, team_meeting as tm
    importlib.reload(tm)
    rows, mature, candles, obs = tm.aligned_dataset()
    kpi = tm.analista(mature)                       # <- qui crashava il 2/7
    tr = tm.trader(mature, candles, obs, kpi["recommends_to_trader"])
    return f"{len(rows)} token, guida {kpi['ranking'][0]['filter'] if kpi['ranking'] else '-'}, trader {'ok' if tr else 'no'}"


@check("smoke test — paper_account (conto)")
def _account():
    import importlib, paper_account as pa
    importlib.reload(pa)
    out = pa.run()
    return f"conto {out.get('final')} EUR, {out.get('n_trades')} trade"


@check("smoke test — kpi_daily")
def _kpi():
    import importlib, kpi_daily as k
    importlib.reload(k)
    o = k.run()
    return f"base {o['base_win']}%"


@check("smoke test — moduli importano")
def _imports():
    import importlib
    for m in ("exits", "filter_tokens", "tracker", "learner", "pipeline_export", "smart_money", "deep_meeting", "double_agent", "watchdog"):
        importlib.import_module(m)
    return "tutti i moduli ok"


# ---------- 3. FRESCHEZZA: niente interruzioni ----------
@check("freschezza — scan/tracking non fermi")
def _fresh():
    warn = []
    a = _age_h("data/trends.jsonl")
    if a and a > 6:
        warn.append(f"scan trend fermo {a:.0f}h")
    t = _age_h("data/track.jsonl")
    if t and t > 3:
        warn.append(f"tracking fermo {t:.0f}h")
    if warn:
        raise TimeoutError("; ".join(warn))
    return f"scan {a:.1f}h fa, track {t:.1f}h fa"


def run():
    ok = sum(1 for r in results if r[0])
    tot = len(results)
    red = [r for r in results if not r[0]]
    print(f"\n===== QA AGENT — {ok}/{tot} check OK =====")
    for good, name, detail in results:
        print(f"  {'✅' if good else '❌'} {name}: {detail}")

    status = "✅ TUTTO OK" if not red else f"🛑 {len(red)} PROBLEMI"
    body = f"QA AGENT crypto-radar — {status}\n\n{ok}/{tot} check superati.\n\n"
    for good, name, detail in results:
        body += f"{'OK ' if good else 'FAIL'} · {name}\n     {detail}\n"
    if red:
        body += "\n>>> INTERVENTO: c'e' un bug/interruzione. Dettaglio errore sopra. <<<"
    # email SOLO se ci sono problemi (niente spam quando tutto ok), o sempre se vuoi il polso quotidiano
    if red:
        try:
            import watchdog
            watchdog._email(f"crypto-radar QA — {status}", body)
            print("[qa] email di allerta inviata")
        except Exception as e:
            print(f"[qa] email non inviata: {str(e)[:60]}")
    with open(os.path.join(HERE, "data", "qa_last.json"), "w") as f:
        json.dump({"ts": int(time.time()), "ok": ok, "tot": tot,
                   "checks": [{"ok": g, "name": n, "detail": d} for g, n, d in results]}, f)
    return not red


if __name__ == "__main__":
    import sys
    healthy = run()
    # esce 1 se ci sono problemi: cosi' anche il workflow lo segna rosso e arriva la notifica GitHub
    sys.exit(0 if healthy else 1)
