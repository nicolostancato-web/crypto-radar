"""
tracker.py — PIPELINE X-FIRST, step 4: il TRACCIAMENTO DEGLI ESITI.

Per OGNI token che Grok ha chiamato (perle E scartati — vedi principio "impara da tutti"),
segue il prezzo/market cap nel tempo. Ogni ora registra una fotografia (prezzo, fdv, liq, volume)
finche' il token e' dentro la finestra di tracking. Cosi' dopo possiamo calcolare, in modo ONESTO
e senza look-ahead, com'e' andata: entrata ipotetica al primo check dopo il segnale, picco, ritorno
a +1h/+6h/+24h, max drawdown, se ha fatto 2x, se e' ruggato.

NON giudica e NON simula strategie qui: raccoglie solo la VERITA' della curva prezzo (principio del
progetto: misurare != giudicare). Le simulazioni entrata/uscita le fa pipeline_export sui dati raccolti.

Free: solo DexScreener (no key). Append-only su data/track.jsonl (1 riga per osservazione per token).
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except Exception:
    pass

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
CANDS = os.path.join(HERE, "data", "candidates.jsonl")
OUT = os.path.join(HERE, "data", "track.jsonl")

TRACK_WINDOW_H = 48   # seguiamo ogni token per 48h dal PRIMO segnale, poi lo consideriamo chiuso


def _dex(ca):
    """Fotografia DexScreener del pair piu' liquido (Solana o Base): prezzo, fdv, liq, volumi, var%."""
    try:
        r = requests.get("https://api.dexscreener.com/latest/dex/tokens/" + ca, timeout=10)
        pairs = [p for p in (r.json().get("pairs") or []) if p.get("chainId") in ("solana", "base")]
        if not pairs:
            return None
        p = max(pairs, key=lambda x: (x.get("liquidity") or {}).get("usd") or 0)
        price = None
        try:
            price = float(p.get("priceUsd")) if p.get("priceUsd") else None
        except Exception:
            price = None
        return {
            "ticker": (p.get("baseToken") or {}).get("symbol"),
            "chain": p.get("chainId"),
            "price": price,
            "fdv": p.get("fdv"),
            "liq": (p.get("liquidity") or {}).get("usd") or 0,
            "vol_1h": (p.get("volume") or {}).get("h1") or 0,
            "vol_24h": (p.get("volume") or {}).get("h24") or 0,
            "pc_1h": (p.get("priceChange") or {}).get("h1"),
            "pc_24h": (p.get("priceChange") or {}).get("h24"),
        }
    except Exception:
        return None


def _first_signals():
    """Per ogni contract address: il PRIMO istante in cui Grok l'ha segnalato + se e' mai passato il filtro."""
    first = {}
    if not os.path.exists(CANDS):
        return first
    for l in open(CANDS):
        try:
            c = json.loads(l)
        except Exception:
            continue
        ca = c.get("ca")
        if not ca:
            continue
        sig = c.get("snapshot_ts") or c.get("ts")
        if not sig:
            continue
        if ca not in first:
            first[ca] = {"signal_ts": sig, "ticker": c.get("ticker"), "pass": bool(c.get("pass")),
                         "arena": c.get("arena") or "memecoin", "chain": c.get("chain")}
        else:
            if sig < first[ca]["signal_ts"]:
                first[ca]["signal_ts"] = sig
            if c.get("pass"):
                first[ca]["pass"] = True
    return first


def run():
    first = _first_signals()
    if not first:
        print("[tracker] niente candidate da tracciare ancora.")
        return 0
    now = int(time.time())
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    f = open(OUT, "a")
    n = skipped = 0
    for ca, meta in first.items():
        age_min = (now - meta["signal_ts"]) / 60
        if age_min > TRACK_WINDOW_H * 60:
            skipped += 1
            continue
        d = _dex(ca)
        if not d:
            continue
        row = {"ca": ca, "ticker": meta.get("ticker") or d.get("ticker"), "pass": meta["pass"],
               "arena": meta.get("arena") or "memecoin", "chain": meta.get("chain") or d.get("chain"),
               "signal_ts": meta["signal_ts"], "obs_ts": now, "age_min": round(age_min),
               "price": d["price"], "fdv": d["fdv"], "liq": round(d["liq"]),
               "vol_1h": round(d["vol_1h"]), "vol_24h": round(d["vol_24h"]),
               "pc_1h": d["pc_1h"], "pc_24h": d["pc_24h"]}
        f.write(json.dumps(row) + "\n")
        n += 1
        time.sleep(0.2)   # gentile con DexScreener
    f.close()
    print(f"[tracker] osservazioni nuove: {n} (token in finestra {TRACK_WINDOW_H}h; {skipped} chiusi) "
          f"-> data/track.jsonl")
    return n


if __name__ == "__main__":
    run()
