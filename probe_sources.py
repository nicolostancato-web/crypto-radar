"""
probe_sources.py — verifica a COSTO ZERO che le fonti gratis rispondano e con che dati.
Una chiamata per fonte. Nessuna API a pagamento. Serve a validare le fondamenta
PRIMA di costruirci sopra (disciplina: testa piccolo prima di scalare).
"""
import requests, json

UA = {"User-Agent": "crypto-radar/2.0 (research; paper-trading only)"}
T = 12

def show(name, ok, detail):
    flag = "OK " if ok else "KO "
    print(f"[{flag}] {name}: {detail}")

# 1) DEXScreener — token boosts (trending), gratis no key
try:
    r = requests.get("https://api.dexscreener.com/token-boosts/latest/v1", headers=UA, timeout=T)
    d = r.json()
    n = len(d) if isinstance(d, list) else len(d.get("pairs", []))
    chains = sorted({x.get("chainId") for x in (d if isinstance(d, list) else [])})[:8]
    show("DEXScreener boosts", r.ok, f"{n} item, chain viste={chains}")
except Exception as e:
    show("DEXScreener boosts", False, repr(e))

# 2) GeckoTerminal — trending pools (gratis, no key), multi-network
try:
    r = requests.get("https://api.geckoterminal.com/api/v2/networks/trending_pools",
                     headers={**UA, "Accept": "application/json"}, timeout=T)
    d = r.json()
    pools = d.get("data", [])
    sample = pools[0]["attributes"]["name"] if pools else "?"
    show("GeckoTerminal trending", r.ok, f"{len(pools)} pool, es: {sample}")
except Exception as e:
    show("GeckoTerminal trending", False, repr(e))

# 3) CoinGecko — trending (keyless, rate-limited)
try:
    r = requests.get("https://api.coingecko.com/api/v3/search/trending", headers=UA, timeout=T)
    d = r.json()
    coins = d.get("coins", [])
    names = [c["item"]["symbol"] for c in coins[:5]]
    show("CoinGecko trending (keyless)", r.ok, f"{len(coins)} coin, top={names}")
except Exception as e:
    show("CoinGecko trending (keyless)", False, repr(e))

# 4) 4chan /biz/ — catalog (gratis, no key)
try:
    r = requests.get("https://a.4cdn.org/biz/catalog.json", headers=UA, timeout=T)
    d = r.json()
    threads = sum(len(p.get("threads", [])) for p in d)
    show("4chan /biz/ catalog", r.ok, f"{threads} thread attivi (narrativa degen)")
except Exception as e:
    show("4chan /biz/ catalog", False, repr(e))

# 5) Google Trends — via pytrends (gratis, no key, non ufficiale)
try:
    from pytrends.request import TrendReq
    py = TrendReq(hl="en-US", tz=0)
    py.build_payload(["bitcoin"], timeframe="now 7-d")
    df = py.interest_over_time()
    show("Google Trends (pytrends)", not df.empty, f"{len(df)} punti per 'bitcoin' 7g")
except Exception as e:
    show("Google Trends (pytrends)", False, repr(e))

print("\n--- Costo di questo probe: 0 EUR (solo GET pubbliche gratuite) ---")
