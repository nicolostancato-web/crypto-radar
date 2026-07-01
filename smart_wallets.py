"""
smart_wallets.py — LA SVOLTA: trova e SEGUE i wallet che vincono (smart money).

Non predici i token, PARASSITI i wallet. Trova i wallet che hanno preso EARLY piu' runner (hit-rate
molto sopra la base), salva la watchlist, e li OSSERVA in avanti: quando un wallet-vincente compra un
token, lo segnaliamo. Validazione out-of-sample: se i token che comprano diventano runner anche NEL
FUTURO, non era fortuna storica -> abbiamo il seme del copy-trading.

Dati: whale_flow.jsonl (swap grezzi con wallet). Costo: ZERO.
"""
import os, json
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
MIN_RUNNERS = 3      # per entrare in watchlist: preso early >=3 runner
MIN_HIT = 0.30       # e hit-rate >= 30% (la base e' ~20%)


def _runner_set():
    obs = defaultdict(list)
    for l in open(os.path.join(HERE, "data", "track.jsonl")):
        o = json.loads(l)
        if o.get("price"):
            obs[o["ca"]].append((o["obs_ts"], o["price"]))
    runner, first_ts = set(), {}
    for ca, s in obs.items():
        s = sorted(s); pr = [p for _, p in s]
        first_ts[ca] = s[0][0]
        if len(pr) >= 2 and pr[0] and max(pr) / pr[0] - 1 >= 0.5:
            runner.add(ca)
    return runner, first_ts


def build_watchlist():
    runner, _ = _runner_set()
    wt = defaultdict(lambda: {"run": set(), "all": set()})
    for l in open(os.path.join(HERE, "data", "whale_flow.jsonl")):
        r = json.loads(l); ca = r["ca"]; sw = r.get("swaps") or []
        if not sw:
            continue
        sw = sorted(sw, key=lambda x: x["ts"])
        early = sw[:max(5, len(sw) // 3)]
        for s in early:
            if s["s"] == "b":
                wt[s["w"]]["all"].add(ca)
                if ca in runner:
                    wt[s["w"]]["run"].add(ca)
    watch = []
    for w, d in wt.items():
        nr, na = len(d["run"]), len(d["all"])
        if nr >= MIN_RUNNERS and nr / na >= MIN_HIT:
            watch.append({"wallet": w, "runners": nr, "tokens": na, "hit_rate": round(nr / na, 2)})
    watch.sort(key=lambda x: (-x["runners"], -x["hit_rate"]))
    json.dump({"built_from_tokens": len(runner), "n_wallets": len(watch), "wallets": watch},
              open(os.path.join(HERE, "data", "smart_wallets.json"), "w"))
    return watch


if __name__ == "__main__":
    w = build_watchlist()
    print(f"[smart_wallets] watchlist: {len(w)} wallet vincenti (>= {MIN_RUNNERS} runner, hit >= {int(MIN_HIT*100)}%)")
    for x in w[:12]:
        print(f"  {x['wallet']}  runner={x['runners']:>3}  hit={int(x['hit_rate']*100)}%")
    print("-> salvati in data/smart_wallets.json (watchlist da seguire e validare in avanti)")
