"""
discovery_dex.py — SECONDA FONTE DI SCOPERTA (gratis, indipendente da Grok/X).

PUSH MODE: per accumulare dati piu' velocemente non basta Grok (vede solo cio' che scalda su X).
Qui peschiamo token freschi DIRETTAMENTE dai feed pubblici gratuiti di DexScreener (boost + profili
piu' recenti), filtriamo Solana, togliamo i gia'-noti, e scriviamo uno snapshot in data/trends.jsonl
nello stesso formato di trend_agent -> il filtro on-chain (filter_tokens.py) li raccoglie da solo.

Costo: ZERO (DexScreener e' gratis e keyless). L'unico costo indiretto e' qualche chiamata Helius in
piu' nel filtro (free tier) -> per questo c'e' un CAP duro di token nuovi per run.
"""
import os, json, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
TRENDS = os.path.join(HERE, "data", "trends.jsonl")
CANDS = os.path.join(HERE, "data", "candidates.jsonl")
MAX_NEW = 25  # CAP duro: max token nuovi per run (protegge il free tier Helius del filtro)

FEEDS = [
    "https://api.dexscreener.com/token-boosts/latest/v1",
    "https://api.dexscreener.com/token-boosts/top/v1",
    "https://api.dexscreener.com/token-profiles/latest/v1",
]


def _get(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "crypto-radar"})
        return json.loads(urllib.request.urlopen(req, timeout=15).read())
    except Exception as e:
        print("[discovery] feed errore %s: %s" % (url.split("/")[-2], str(e)[:80]))
        return []


def _known_cas():
    seen = set()
    if os.path.exists(CANDS):
        for l in open(CANDS):
            try:
                seen.add(json.loads(l)["ca"])
            except Exception:
                pass
    return seen


def run():
    known = _known_cas()
    found = {}
    for url in FEEDS:
        data = _get(url)
        for item in (data if isinstance(data, list) else []):
            if item.get("chainId") != "solana":
                continue
            ca = item.get("tokenAddress")
            if not ca or len(ca) < 30 or ca in known or ca in found:
                continue
            found[ca] = {"ca": ca, "ticker": (item.get("description") or "")[:14] or None,
                         "arena": "memecoin", "chain": "solana", "heat": None, "source": "dexscreener"}
            if len(found) >= MAX_NEW:
                break
        if len(found) >= MAX_NEW:
            break

    if not found:
        print("[discovery] nessun token nuovo dai feed DexScreener (tutti gia' noti)")
        return
    snap = {"ts": int(time.time()), "source": "dexscreener", "tokens": list(found.values())}
    with open(TRENDS, "a") as f:
        f.write(json.dumps(snap) + "\n")
    print("[discovery] +%d token nuovi da DexScreener -> data/trends.jsonl (li filtra filter_tokens)" % len(found))


if __name__ == "__main__":
    run()
