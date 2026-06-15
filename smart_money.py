"""
smart_money.py — SCOPRI I WALLET VINCENTI (mossa #3 reimmaginata, gratis, no API esterne).

La tesi del founder: "copia le balene che vincono". Qui la realizziamo coi NOSTRI dati:
incrocia CHI compra presto (data/whale_flow.jsonl: early_buyers/top_buyer per token) con COSA poi corre
(gli esiti dei token). Un wallet che compra PRESTO sui token che diventano runner, e NON sui morti, e'
"smart money" — da seguire. Output: data/smart_wallets.json, classifica dei wallet da copiare.

Free: solo lettura di file locali. Si popola man mano che whale_flow accumula. Idempotente.
"""
import os, json, time

HERE = os.path.dirname(os.path.abspath(__file__))
WHALE = os.path.join(HERE, "data", "whale_flow.jsonl")
TRACK = os.path.join(HERE, "data", "track.jsonl")
OUT = os.path.join(HERE, "data", "smart_wallets.json")

RUNNER_PCT = 0.5      # un token "ha corso" se max ritorno >= +50% dal primo tracking
MIN_PLAYS = 2         # un wallet conta come smart solo se l'abbiamo visto su >=2 token


def _read_jsonl(path):
    if not os.path.exists(path):
        return []
    out = []
    for l in open(path):
        l = l.strip()
        if l:
            try:
                out.append(json.loads(l))
            except Exception:
                pass
    return out


def _token_runner():
    """Per ogni ca: ha corso? (dai dati di tracking, ret_max >= RUNNER_PCT)."""
    obs = {}
    for o in _read_jsonl(TRACK):
        obs.setdefault(o.get("ca"), []).append(o)
    res = {}
    for ca, series in obs.items():
        series = sorted(series, key=lambda x: x.get("obs_ts") or 0)
        prices = [s.get("price") for s in series if s.get("price")]
        if len(prices) < 2 or not prices[0]:
            continue
        res[ca] = (max(prices) / prices[0] - 1) >= RUNNER_PCT
    return res


def run():
    whale = _read_jsonl(WHALE)
    if not whale:
        print("[smart_money] niente whale_flow ancora — gira prima whale_flow.py."); return
    runner = _token_runner()

    # per ogni wallet: su quanti token-runner vs token-morti l'abbiamo visto comprare presto
    wallets = {}   # addr -> {"hits": set(ca runner), "miss": set(ca non-runner), "tickers": set}
    for row in whale:
        ca = row.get("ca")
        if ca not in runner:
            continue   # esito non ancora noto per quel token
        is_run = runner[ca]
        addrs = set(row.get("early_buyers") or [])
        if row.get("top_buyer"):
            addrs.add(row["top_buyer"])
        for a in addrs:
            w = wallets.setdefault(a, {"hits": set(), "miss": set(), "tickers": set()})
            (w["hits"] if is_run else w["miss"]).add(ca)
            if row.get("ticker"):
                w["tickers"].add(row["ticker"])

    ranked = []
    for a, w in wallets.items():
        plays = len(w["hits"]) + len(w["miss"])
        if plays < MIN_PLAYS:
            continue
        winrate = len(w["hits"]) / plays
        ranked.append({
            "wallet": a, "plays": plays, "hits": len(w["hits"]),
            "winrate": round(winrate, 2), "tickers": sorted(w["tickers"])[:6],
        })
    # i migliori: alto win-rate, poi piu' giocate (piu' affidabile)
    ranked.sort(key=lambda x: (x["winrate"], x["plays"]), reverse=True)

    data = {
        "updated_utc": time.strftime("%Y-%m-%d %H:%M", time.gmtime()),
        "wallets_seen": len(wallets),
        "qualified": len(ranked),
        "min_plays": MIN_PLAYS,
        "smart": ranked[:20],   # i top 20 wallet da seguire
    }
    with open(OUT, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[smart_money] wallet visti={len(wallets)} qualificati(>= {MIN_PLAYS} giocate)={len(ranked)} "
          f"-> data/smart_wallets.json")
    for w in ranked[:8]:
        print(f"   {w['wallet'][:8]}.. winrate={w['winrate']} su {w['plays']} token  {w['tickers']}")
    return data


if __name__ == "__main__":
    run()
