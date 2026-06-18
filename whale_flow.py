"""
whale_flow.py — IL FILM DELLE WHALE (mossa #1, da 60% a ~80% dati whale, gratis).

Invece della sola FOTO (top-20 holder), legge le SINGOLE COMPRAVENDITE di un token via Helius Enhanced
Transactions API (parsate: chi, side, importo, quando) e calcola CHI sta accumulando e chi scarica.
Cosi' passiamo da "la fetta dei grossi e' salita" a "questi wallet stanno comprando ADESSO".

CFO (free Helius 1M crediti/mese): ~101 crediti per token (1 getSignaturesForAddress + 1 batch Enhanced da
100 swap). Cap MAX_TOKENS per ciclo + giro ogni 4h (non ogni ora) -> ben dentro il free tier. Superato il
tetto Helius rate-limita, NON fattura. Append-only su data/whale_flow.jsonl.
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
OUT = os.path.join(HERE, "data", "whale_flow.jsonl")
ENHANCED = "https://api.helius.xyz/v0/transactions"

MAX_TOKENS = 25       # cap CFO per ciclo
WINDOW_H = 48         # solo token segnalati nelle ultime 48h (quelli "vivi")


def _swaps(mint, n=100):
    """Ultime ~n transazioni del mint, parsate dall'Enhanced API (swap human-readable)."""
    sigs = onchain._rpc("getSignaturesForAddress", [mint, {"limit": n}]) or []
    siglist = [s["signature"] for s in sigs if s.get("signature")]
    if not siglist:
        return []
    try:
        r = requests.post(ENHANCED + "?api-key=" + os.getenv("HELIUS_API_KEY", ""),
                          json={"transactions": siglist[:100]}, timeout=40)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


def analyze(mint):
    """Dai singoli swap calcola chi compra/vende il token e chi accumula (netflow per wallet)."""
    txs = _swaps(mint)
    if not txs:
        return None
    flow = {}                      # wallet -> net token amount (ricevuto - mandato)
    buyers, sellers = set(), set()
    early = []                     # (timestamp, wallet) per i primi compratori
    raw = []                       # GREZZO per-swap: irrecuperabile, sblocca ogni feature futura
    for tx in txs:
        fee = tx.get("feePayer")
        if not fee:
            continue
        net = 0.0
        for tt in tx.get("tokenTransfers", []):
            if tt.get("mint") != mint:
                continue
            amt = tt.get("tokenAmount") or 0
            try:
                amt = float(amt)
            except Exception:
                amt = 0
            if tt.get("toUserAccount") == fee:
                net += amt
            elif tt.get("fromUserAccount") == fee:
                net -= amt
        if net == 0:
            continue
        flow[fee] = flow.get(fee, 0) + net
        (buyers if net > 0 else sellers).add(fee)
        if tx.get("timestamp"):
            early.append((tx["timestamp"], fee, net))
        # salva lo swap grezzo: ts, wallet, side (b/s), quantita' token mossa
        raw.append({"ts": tx.get("timestamp"), "w": fee, "s": "b" if net > 0 else "s", "amt": round(abs(net))})

    accumulators = {w: v for w, v in flow.items() if v > 0}
    distributors = {w: v for w, v in flow.items() if v < 0}
    top_buyer = max(accumulators.items(), key=lambda x: x[1]) if accumulators else None
    early.sort(key=lambda x: x[0])
    # indirizzi COMPLETI dei primi accumulatori (servono allo smart-money discovery)
    seen, early_buyers = set(), []
    for ts, w, net in early:
        if net > 0 and w not in seen:
            seen.add(w); early_buyers.append(w)
        if len(early_buyers) >= 5:
            break

    return {
        "n_swaps": len(txs),
        "unique_traders": len(flow),
        "buyers": len(buyers), "sellers": len(sellers),
        "bs_ratio_real": round(len(buyers) / len(sellers), 2) if sellers else float(len(buyers)),
        "accumulators": len(accumulators),     # wallet con netflow POSITIVO (stanno comprando)
        "distributors": len(distributors),     # wallet che scaricano
        "top_buyer": top_buyer[0] if top_buyer else None,   # indirizzo completo
        "early_buyers": early_buyers,                       # indirizzi completi
        # segnale sintetico: piu' accumulatori che distributori = pressione d'acquisto whale
        "whale_pressure": round((len(accumulators) - len(distributors)) / max(1, len(flow)), 2),
        "swaps": raw[:120],   # GREZZO per-swap: da qui si deriva OGNI feature futura (size, sniper, sequenza)
    }


def _active_tokens():
    """Token (mint) segnalati nelle ultime WINDOW_H ore, dedup, i piu' recenti — cap MAX_TOKENS."""
    seen, out = set(), []
    if not os.path.exists(CANDS):
        return []
    now = time.time()
    for l in reversed(list(open(CANDS))):
        try:
            c = json.loads(l)
        except Exception:
            continue
        ca = c.get("ca")
        if not ca or ca in seen or c.get("chain") not in (None, "solana"):
            continue
        if now - (c.get("ts") or 0) > WINDOW_H * 3600:
            continue
        seen.add(ca)
        out.append({"ca": ca, "ticker": c.get("ticker"), "pass": bool(c.get("pass"))})
        if len(out) >= MAX_TOKENS:
            break
    return out


def run():
    if not onchain.available():
        print("[whale_flow] HELIUS_API_KEY assente — no-op."); return 0
    toks = _active_tokens()
    if not toks:
        print("[whale_flow] nessun token attivo da analizzare."); return 0
    f = open(OUT, "a")
    n = 0
    for t in toks:
        a = analyze(t["ca"])
        if not a:
            continue
        row = {"ca": t["ca"], "ticker": t.get("ticker"), "pass": t["pass"], "obs_ts": int(time.time()), **a}
        f.write(json.dumps(row) + "\n")
        n += 1
        print(f"   {str(t.get('ticker')):14} swap={a['n_swaps']} buy/sell={a['buyers']}/{a['sellers']} "
              f"accum={a['accumulators']} distrib={a['distributors']} pressione={a['whale_pressure']}")
        time.sleep(0.3)
    f.close()
    print(f"[whale_flow] analizzati {n} token (cap {MAX_TOKENS}) -> data/whale_flow.jsonl")
    return n


if __name__ == "__main__":
    run()
