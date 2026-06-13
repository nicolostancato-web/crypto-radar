"""
green_engagement.py — SOCIAL TRACKER per le sole GREEN (a pagamento, cap CFO).

Per i token GREEN (perle) ancora attivi, ogni ~4h chiede a Grok (X live) quanto se ne parla su X ADESSO:
posts/ora, trend dell'attenzione, KOL coinvolti, sentiment. E' l'attributo #3 della lista (Grok: "anticipa
il volume di 1-3h") — l'unico social che l'on-chain non da'. Logga in data/green_social.jsonl, serie storica
dell'hype per le green, da incrociare col prezzo nello studio entry/exit.

COSTO (CFO): ~$0.03 a query, cap MAX_GREEN green per ciclo, lanciato ogni 4h dal workflow.
Worst case 5 green x 6 cicli/giorno = ~$0.9/giorno. Con poche green molto meno. OK esplicito di Nicolo 2026-06-13.
Append-only. No XAI key -> no-op pulito.
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except Exception:
    pass

import double_agent as da

HERE = os.path.dirname(os.path.abspath(__file__))
CANDS = os.path.join(HERE, "data", "candidates.jsonl")
OUT = os.path.join(HERE, "data", "green_social.jsonl")

MAX_GREEN = 5            # cap CFO: al massimo 5 green per ciclo
GREEN_WINDOW_H = 120     # seguiamo l'hype solo finche' la green e' nella sua finestra di vita (5 giorni)


def _active_greens():
    """Le GREEN (pass=True) col primo segnale entro la finestra, dedup per ca, le piu' recenti prima."""
    first = {}
    if not os.path.exists(CANDS):
        return []
    for l in open(CANDS):
        try:
            c = json.loads(l)
        except Exception:
            continue
        if not c.get("pass"):
            continue
        ca = c.get("ca")
        sig = c.get("snapshot_ts") or c.get("ts")
        if not ca or not sig:
            continue
        if ca not in first or sig < first[ca]["signal_ts"]:
            first[ca] = {"ca": ca, "ticker": c.get("ticker"), "signal_ts": sig,
                         "arena": c.get("arena") or "memecoin", "chain": c.get("chain")}
    now = time.time()
    active = [g for g in first.values() if (now - g["signal_ts"]) / 3600 <= GREEN_WINDOW_H]
    active.sort(key=lambda g: g["signal_ts"], reverse=True)
    return active[:MAX_GREEN]


def _prompt(g):
    return (
        "Sei un analista social crypto con accesso LIVE a X. Misura l'attenzione su X ADESSO per questo "
        "token, cercando i post delle ultime ore (cashtag, contract address, nome).\n"
        f"Ticker: {g.get('ticker')}\nContract: {g.get('ca')}\nChain: {g.get('chain')}\n\n"
        "Stima ONESTAMENTE (se non trovi quasi nulla, mettilo basso, non inventare):\n"
        "- posts_per_hour: numero stimato di post/ora nelle ultime 2-3h\n"
        "- trend: rising | steady | falling (l'attenzione sta salendo o calando?)\n"
        "- kol_count: quanti account VERI con seguito (non bot) ne parlano\n"
        "- sentiment: bullish | mixed | bearish\n"
        "- notes: 1 frase\n\n"
        'Rispondi SOLO con un JSON: {"posts_per_hour": N, "trend": "...", "kol_count": N, '
        '"sentiment": "...", "notes": "..."}'
    )


def _parse(txt):
    if not txt:
        return None
    a, b = txt.find("{"), txt.rfind("}")
    if a == -1 or b == -1:
        return None
    try:
        return json.loads(txt[a:b + 1])
    except Exception:
        return None


def run():
    if not os.getenv("XAI_API_KEY"):
        print("[green_social] XAI_API_KEY assente — no-op.")
        return 0
    greens = _active_greens()
    if not greens:
        print("[green_social] nessuna green attiva — niente da misurare.")
        return 0
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    f = open(OUT, "a")
    n = 0
    for g in greens:
        try:
            txt = da.ask_grok(_prompt(g), max_tokens=900, timeout=180, live_x=True)
        except Exception as e:
            print(f"[green_social] {g.get('ticker')} errore: {str(e)[:100]}")
            continue
        d = _parse(txt) or {}
        row = {"ca": g["ca"], "ticker": g.get("ticker"), "arena": g.get("arena"),
               "obs_ts": int(time.time()), "signal_ts": g["signal_ts"],
               "posts_per_hour": d.get("posts_per_hour"), "trend": d.get("trend"),
               "kol_count": d.get("kol_count"), "sentiment": d.get("sentiment"), "notes": d.get("notes")}
        f.write(json.dumps(row) + "\n")
        n += 1
        print(f"   {str(g.get('ticker')):14} posts/h={d.get('posts_per_hour')} trend={d.get('trend')} "
              f"kol={d.get('kol_count')} sent={d.get('sentiment')}")
    f.close()
    print(f"[green_social] misurate {n} green (cap {MAX_GREEN}) -> data/green_social.jsonl")
    return n


if __name__ == "__main__":
    run()
