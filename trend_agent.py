"""
trend_agent.py — L'AGENTE TREND. Chiede a Grok (che ha X integrato in tempo reale) cosa sta
scaldando sulle memecoin Solana, e SALVA il segnale nel tempo (serie storica).

Il nostro edge NON e' avere Grok (ce l'hanno tutti). E' il SISTEMA: interroghiamo in modo
sistematico ogni X ore, strutturiamo un database con timestamp, e (prossimo step) incrociamo
con l'on-chain + backtestiamo quali segnali Grok predicono davvero un pump. L'informazione e'
di tutti; l'edge e' la struttura che la valida e la trasforma in decisione.

Output: data/trends.jsonl (1 riga per chiamata, con timestamp e la lista di token segnalati).
Costo: ~$0.01 a chiamata (entro i $175/mese di crediti free xAI). No key XAI -> no-op pulito.
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except Exception:
    pass

import double_agent as da

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "trends.jsonl")

PROMPT = """Sei un analista crypto on-chain in tempo reale con accesso a X/Twitter LIVE.

Dimmi ADESSO quali memecoin / narrative su SOLANA stanno guadagnando attenzione su X nelle ULTIME ORE.
Voglio roba EARLY (che inizia a scaldare ora), non quella gia' arcinota e pumpata.

Per ognuna (max 8): ticker, contract address se lo trovi, perche' sta scaldando (chi ne parla:
KOL/account grossi? quale narrativa?), e lo stage (early = appena parte, mid = sta correndo,
late = gia' pompata). Dai un punteggio heat 1-10 e velocity (sta accelerando l'attenzione?).

REGOLE: solo roba REALE e recente da X, NIENTE invenzioni. Se non sei sicuro di un contract address,
lascialo null. Meglio poche ma vere.

Rispondi SOLO con un array JSON valido, niente testo attorno:
[{"ticker":"...","ca":"...|null","why":"...","stage":"early|mid|late","heat":1-10,"velocity":"rising|flat|fading"}]"""


def _parse(txt):
    if not txt:
        return []
    s = txt.strip()
    if s.startswith("```"):
        s = s.split("```")[1].replace("json", "", 1).strip() if "```" in s else s
    a, b = s.find("["), s.rfind("]")
    if a == -1 or b == -1:
        return []
    try:
        return json.loads(s[a:b + 1])
    except Exception:
        return []


def run():
    if not os.getenv("XAI_API_KEY"):
        print("[trend] XAI_API_KEY assente — crea la key su console.x.ai. No-op.")
        return []
    try:
        txt = da.ask_grok(PROMPT, max_tokens=2000, timeout=120, live_x=True)
    except Exception as e:
        print(f"[trend] Grok errore: {str(e)[:150]}")
        return []
    tokens = _parse(txt)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    row = {"ts": int(time.time()), "utc": time.strftime("%Y-%m-%d %H:%M", time.gmtime()),
           "n": len(tokens), "tokens": tokens}
    with open(OUT, "a") as f:
        f.write(json.dumps(row) + "\n")
    early = [t for t in tokens if str(t.get("stage")) == "early"]
    print(f"[trend] Grok: {len(tokens)} token segnalati ({len(early)} EARLY) -> data/trends.jsonl")
    for t in tokens[:8]:
        print(f"   {t.get('ticker','?'):12} stage={t.get('stage','?'):5} heat={t.get('heat','?')} "
              f"vel={t.get('velocity','?'):7} {str(t.get('why',''))[:60]}")
    return tokens


if __name__ == "__main__":
    run()
