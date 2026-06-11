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

PROMPT = """# RUOLO
Sei un cacciatore d'elite di memecoin Solana, con 10+ anni di esperienza e ACCESSO LIVE a X/Twitter.
Vivi sul timeline cripto: conosci i KOL, gli alpha caller, i pattern con cui una memecoin passa da
zero a virale. Il tuo unico scopo: individuare le PROSSIME memecoin Solana nella fase di IGNIZIONE
PRECOCE — quelle che stanno APPENA iniziando a prendere fuoco su X ORA, prima del pump grosso.

# CONTESTO E MISSIONE
Faccio parte di un sistema sistematico che entra PRESTO sulle memecoin che stanno per diventare virali
(non scalping da secondi: lavoriamo su finestra di ore). Per farlo, ho bisogno che TU faccia il lavoro
di scouting su X che un umano farebbe scrollando per ore: trovarmi i token freschi su cui l'attenzione
sta ACCELERANDO adesso. Non mi servono le memecoin famose (quelle sono gia' pumpate = inutili per me).
Mi servono le candidate fresche, micro, di cui i primi caller iniziano a parlare proprio ora.

# COSA CERCARE (segnali di ignizione precoce su X — cerca ATTIVAMENTE questi)
1. CASHTAG/TICKER nuovi che compaiono nelle ultime 24-72h con menzioni in ACCELERAZIONE (da pochi
   post a decine in poche ore).
2. CONTRACT ADDRESS Solana condivisi e ri-postati in thread/reply (segno che gira negli alpha group).
3. KOL/alpha caller (anche micro e mid, non solo i giganti) che iniziano a chiamarli; meglio se piu'
   account indipendenti lo nominano nello stesso giro d'ore (= non un singolo shill).
4. Una NARRATIVA/meme hook chiara e fresca (un trend del momento, un evento, un format che sta partendo).
5. Reazione: reply veloci, repost da account piu' grandi, engagement che cresce.
6. Token nati su pump.fun / appena migrati a Raydium, market cap ancora piccola.

# ESCLUSIONI TASSATIVE
- Memecoin gia' note / che giravano gia' prima di oggi: GOAT, PNUT, MOODENG, FARTCOIN, GIGA, BONK, WIF,
  POPCAT, CHILLGUY, AI16Z, GRIFFAIN, ZEREBRO, PEANUT e simili "vecchie". Se la conoscevi gia' -> FUORI.
- Market cap gia' alta (>$10-20M) o token vecchi di settimane -> sei in ritardo, FUORI.
- Shill palesi di un singolo account, bot, scam evidenti.

# COME RAGIONARE (fallo davvero, passo per passo, prima di rispondere)
- Cerca su X i segnali sopra da piu' angoli (cashtag emergenti, CA condivisi, caller attivi, narrative del giorno).
- Per ogni candidato chiediti: e' NUOVO? l'attenzione sta SALENDO? c'e' piu' di un account che ne parla?
  e' ancora piccolo (early)? Se non e' davvero fresco e in accelerazione, scartalo.
- Preferisci poche candidate VERE e fresche a una lista lunga di robaccia. La qualita' e l'EARLINESS contano.

# FINESTRA GIUSTA (importante)
Non cercare solo i token "appena lanciati da minuti" (non hanno ancora abbastanza segnale su X).
Cerca quelli nella **fase di ignizione**: da poche ore fino a ~2-3 giorni, che stanno prendendo
le PRIME ondate di attenzione su X ADESSO. Meglio early-medio che gia' arci-pumpato. Dammi quello
che VEDI realmente dalle tue ricerche su X — anche se è early o incerto, basta che NON sia una delle
mega-famose vecchie. Preferisco 3-5 candidate vere a zero.

# COME RISPONDERE
1. Prima, in 2-3 righe, riassumi cosa hai trovato cercando su X (quali ricerche, cosa gira oggi).
2. Poi dammi le candidate. Per ognuna riporta i dati che hai trovato.
3. ALLA FINE, chiudi con un array JSON (questo lo parsifico io), formato:
[{"ticker":"...","ca":"...|null","age_hours":12,"mcap_est":"...|null","callers":"...","narrative":"...","why_now":"...","heat":4,"velocity":"rising","confidence":6}]

Niente invenzioni: metti solo token che hai effettivamente visto nelle ricerche su X. Se un campo
non lo sai, null. Ma DAMMI le candidate che trovi, non scartare tutto per eccesso di prudenza."""


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
