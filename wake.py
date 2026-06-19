"""
wake.py — CRON-JOB.ORG INTERNO (gratis, autonomo). Risolve i cron saltati di GitHub.

Il tracking gira ogni 30 min (frequente -> GitHub lo salta meno). Alla fine di ogni run, questo script
controlla se gli SCAN piu' pesanti (trends, whale) sono in ritardo e li RI-LANCIA via API. Cosi' il
workflow frequente fa da "sveglia" agli altri, senza dipendere dai cron inaffidabili di GitHub ne' da
servizi esterni. Serve WORKFLOW_PAT (gia' secret). Costo: zero (solo qualche chiamata API).
"""
import os, json, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def _last_ts(path, key_candidates=("ts", "obs_ts")):
    p = os.path.join(HERE, path)
    if not os.path.exists(p):
        return 0
    rows = [l for l in open(p) if l.strip()]
    if not rows:
        return 0
    try:
        last = json.loads(rows[-1])
    except Exception:
        return 0
    for k in key_candidates:
        if last.get(k):
            return last[k]
    return 0


def _trigger(wf):
    pat = os.getenv("WORKFLOW_PAT")
    if not pat:
        print("[wake] WORKFLOW_PAT assente — non posso svegliare", wf); return
    url = "https://api.github.com/repos/nicolostancato-web/crypto-radar/actions/workflows/%s/dispatches" % wf
    req = urllib.request.Request(url, data=json.dumps({"ref": "main"}).encode(), method="POST")
    req.add_header("Authorization", "token " + pat)
    req.add_header("Accept", "application/vnd.github+json")
    try:
        urllib.request.urlopen(req, timeout=15)
        print("[wake] svegliato", wf)
    except Exception as e:
        print("[wake] errore su %s: %s" % (wf, str(e)[:90]))


def run():
    now = time.time()
    # SCAN trends ogni ~3h: se l'ultimo e' piu' vecchio di 2.5h, svglialo
    if now - _last_ts("data/trends.jsonl") > 2.5 * 3600:
        _trigger("trends.yml")
    # WHALE ogni ~4h: se piu' vecchio di 3.5h, svglialo
    if now - _last_ts("data/whale_flow.jsonl") > 3.5 * 3600:
        _trigger("whale.yml")


if __name__ == "__main__":
    run()
