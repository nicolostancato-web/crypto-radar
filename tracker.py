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
import onchain

HERE = os.path.dirname(os.path.abspath(__file__))
CANDS = os.path.join(HERE, "data", "candidates.jsonl")
OUT = os.path.join(HERE, "data", "track.jsonl")

# Le GREEN (perle) si seguono a lungo per costruire la storia profonda ora-per-ora; le RED (scartate)
# bastano poche ore per il confronto. E' qui che "popoliamo massivamente" solo le green.
GREEN_WINDOW_H = 120   # perle: 5 giorni di tracking ricco
RED_WINDOW_H = 96      # scartate: 4 giorni (non perdiamo i runner tardivi — "TUTTI i dati possibili")


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
        tx = p.get("txns") or {}
        tx5, tx1, tx6, tx24 = tx.get("m5") or {}, tx.get("h1") or {}, tx.get("h6") or {}, tx.get("h24") or {}
        vol, pc, liq = p.get("volume") or {}, p.get("priceChange") or {}, p.get("liquidity") or {}
        info = p.get("info") or {}
        return {
            "ticker": (p.get("baseToken") or {}).get("symbol"),
            "chain": p.get("chainId"),
            # finestre m5/h1/h6 (m5 e h6 sono mobili: persi se non li fotografiamo ORA)
            "buys_m5": tx5.get("buys") or 0, "sells_m5": tx5.get("sells") or 0,
            "buys_1h": tx1.get("buys") or 0, "sells_1h": tx1.get("sells") or 0,
            "buys_6h": tx6.get("buys") or 0, "sells_6h": tx6.get("sells") or 0,
            "buys_24h": tx24.get("buys") or 0, "sells_24h": tx24.get("sells") or 0,
            "price": price,
            "fdv": p.get("fdv"), "mcap": p.get("marketCap"),
            "liq": liq.get("usd") or 0, "liq_base": liq.get("base"), "liq_quote": liq.get("quote"),
            "vol_m5": vol.get("m5") or 0, "vol_1h": vol.get("h1") or 0,
            "vol_6h": vol.get("h6") or 0, "vol_24h": vol.get("h24") or 0,
            "pc_m5": pc.get("m5"), "pc_1h": pc.get("h1"), "pc_6h": pc.get("h6"), "pc_24h": pc.get("h24"),
            "pair_created_ms": p.get("pairCreatedAt"),
            "has_socials": bool(info.get("socials")), "has_website": bool(info.get("websites")),
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
        window = GREEN_WINDOW_H if meta.get("pass") else RED_WINDOW_H
        if age_min > window * 60:
            skipped += 1
            continue
        d = _dex(ca)
        if not d:
            continue
        chain = meta.get("chain") or d.get("chain")
        def _bs(b, s): return (b / s) if s else (b or 0)
        def _np(b, s): return round((b - s) / (b + s), 3) if (b + s) else None
        bs5 = _bs(d.get("buys_m5") or 0, d.get("sells_m5") or 0); bs1 = _bs(d["buys_1h"], d["sells_1h"])
        bs6 = _bs(d.get("buys_6h") or 0, d.get("sells_6h") or 0); bs24 = _bs(d.get("buys_24h") or 0, d.get("sells_24h") or 0)
        bs_accel = round(bs5 / bs1, 2) if bs1 else None
        row = {"ca": ca, "ticker": meta.get("ticker") or d.get("ticker"), "pass": meta["pass"],
               "arena": meta.get("arena") or "memecoin", "chain": chain,
               "signal_ts": meta["signal_ts"], "obs_ts": now, "age_min": round(age_min),
               "price": d["price"], "fdv": d["fdv"], "mcap": d.get("mcap"), "liq": round(d["liq"]),
               "liq_base": d.get("liq_base"), "liq_quote": d.get("liq_quote"),
               "vol_m5": round(d.get("vol_m5") or 0), "vol_1h": round(d["vol_1h"]),
               "vol_6h": round(d.get("vol_6h") or 0), "vol_24h": round(d["vol_24h"]),
               "buys_m5": d.get("buys_m5"), "sells_m5": d.get("sells_m5"),
               "buys_1h": d["buys_1h"], "sells_1h": d["sells_1h"], "bs_ratio_1h": round(bs1, 2),
               "bs_ratio_m5": round(bs5, 2), "bs_ratio_6h": round(bs6, 2), "bs_ratio_24h": round(bs24, 2), "bs_accel": bs_accel,
               "np_m5": _np(d.get("buys_m5") or 0, d.get("sells_m5") or 0), "np_1h": _np(d["buys_1h"], d["sells_1h"]),
               "np_6h": _np(d.get("buys_6h") or 0, d.get("sells_6h") or 0), "np_24h": _np(d.get("buys_24h") or 0, d.get("sells_24h") or 0),
               "buys_6h": d.get("buys_6h"), "sells_6h": d.get("sells_6h"),
               "buys_24h": d.get("buys_24h"), "sells_24h": d.get("sells_24h"),
               "pc_m5": d.get("pc_m5"), "pc_1h": d["pc_1h"], "pc_6h": d.get("pc_6h"), "pc_24h": d["pc_24h"],
               "pair_created_ms": d.get("pair_created_ms"),
               "has_socials": d.get("has_socials"), "has_website": d.get("has_website")}
        # WHALE + sicurezza nel tempo (solo Solana, via Helius): chi tiene il token ORA + authority storicizzate.
        if chain == "solana" and onchain.available():
            s = onchain.token_safety(ca) or {}
            row["top10_pct"] = s.get("top10_pct")
            row["top1_pct"] = s.get("top1_pct")
            row["holders"] = s.get("holders")
            row["mint_revoked"] = s.get("mint_revoked")     # storicizzato: il MOMENTO in cui revoca e' informazione
            row["freeze_revoked"] = s.get("freeze_revoked")
        f.write(json.dumps(row) + "\n")
        n += 1
        time.sleep(0.2)   # gentile con DexScreener
    f.close()
    print(f"[tracker] osservazioni nuove: {n} (green {GREEN_WINDOW_H}h / red {RED_WINDOW_H}h; {skipped} chiusi) "
          f"-> data/track.jsonl")
    return n


if __name__ == "__main__":
    run()
