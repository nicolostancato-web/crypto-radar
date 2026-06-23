"""
geckoterminal_ohlcv.py — scarica candele 5-MIN (gratis, keyless) per i token tracciati.

GeckoTerminal API (prodotto DEX di CoinGecko): copre i memecoin Solana che CoinGecko main NON ha,
e da' OHLCV storico al minuto GRATIS (~30 chiamate/min). Ci serve per simulare l'esecuzione (entrata/
uscita) su granularita' fine invece che oraria — l'unico modo per testare davvero se un edge sopravvive.

Idempotente: salta i token gia' scaricati (data/ohlcv.jsonl). Rate-limited a ~25/min per stare nel free.
Costo: ZERO.
"""
import os, json, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
TRACK = os.path.join(HERE, "data", "track.jsonl")
OUT = os.path.join(HERE, "data", "ohlcv.jsonl")
SLEEP = 2.5  # ~24 chiamate/min (sotto il limite free di 30)


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "crypto-radar", "Accept": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=20))


def _done():
    s = set()
    if os.path.exists(OUT):
        for l in open(OUT):
            try:
                s.add(json.loads(l)["ca"])
            except Exception:
                pass
    return s


def run(limit=None):
    # token unici tracciati (con almeno un prezzo)
    cas = []
    seen = set()
    for l in open(TRACK):
        o = json.loads(l)
        if o.get("price") and o["ca"] not in seen:
            seen.add(o["ca"]); cas.append(o["ca"])
    done = _done()
    todo = [c for c in cas if c not in done]
    if limit:
        todo = todo[:limit]
    print(f"[ohlcv] token totali {len(cas)} | gia' fatti {len(done)} | da fare {len(todo)}")
    f = open(OUT, "a")
    ok = fail = 0
    for i, ca in enumerate(todo):
        try:
            pools = _get(f"https://api.geckoterminal.com/api/v2/networks/solana/tokens/{ca}/pools")
            data = pools.get("data") or []
            if not data:
                f.write(json.dumps({"ca": ca, "candles": [], "note": "no_pool"}) + "\n"); fail += 1; time.sleep(SLEEP); continue
            pid = data[0]["attributes"]["address"]
            time.sleep(SLEEP)
            o = _get(f"https://api.geckoterminal.com/api/v2/networks/solana/pools/{pid}/ohlcv/minute?aggregate=5&limit=1000")
            candles = o["data"]["attributes"]["ohlcv_list"]   # [ts,o,h,l,c,vol], desc
            f.write(json.dumps({"ca": ca, "pool": pid, "candles": candles}) + "\n"); f.flush(); ok += 1
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print("[ohlcv] rate limit, pausa 30s"); time.sleep(30); continue
            f.write(json.dumps({"ca": ca, "candles": [], "note": f"http_{e.code}"}) + "\n"); fail += 1
        except Exception as e:
            print(f"[ohlcv] {ca[:8]} errore: {str(e)[:60]}"); fail += 1
        if (i + 1) % 20 == 0:
            print(f"[ohlcv] {i+1}/{len(todo)} (ok={ok} fail={fail})")
        time.sleep(SLEEP)
    print(f"[ohlcv] FATTO: ok={ok} fail={fail} -> data/ohlcv.jsonl")


if __name__ == "__main__":
    import sys
    run(limit=int(sys.argv[1]) if len(sys.argv) > 1 else None)
