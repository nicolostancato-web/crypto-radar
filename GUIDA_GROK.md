# Guida: usare Grok al meglio per la caccia ai token virali

> Lezioni imparate sul campo (2026-06-12) costruendo l'agente trend. Cosa funziona, cosa no, perche'.

## 1. LA REGOLA #1: senza ricerca live, Grok e' inutile per noi
Grok via API **normale** (`/v1/chat/completions`) risponde dalla sua **memoria di training** → ti da'
solo le memecoin FAMOSE che gia' conosce (MOODENG, GOAT…), gia' pumpate = inutili. Glielo abbiamo
chiesto e ha confermato: *"Non ho accesso a dati in tempo reale."*

**Per la ricerca live su X serve:**
- Endpoint **`/v1/responses`** (NON chat/completions)
- Campo **`input`** (non `messages`), **`max_output_tokens`** (non `max_tokens`)
- Tool **`"tools": [{"type": "x_search"}]`** ← questo accende la ricerca live su X
- (Il vecchio `search_parameters` e' RITIRATO → da' 410 Gone)
- La risposta finale e' l'ultimo item `type=="message"` nell'array `output`

Con questo, Grok cerca DAVVERO su X (`x_keyword_search` con `since:OGGI`) e ti da' roba fresca con
le **fonti** (link ai post X).

## 2. IL MODELLO giusto
- **grok-4.3** → per lo scouting profondo (ragiona + cerca a piu' angoli). È quello che usiamo.
- grok-4-1-fast → economico, ma per la caccia seria meglio il 4.3.
- Costo reale osservato: **~$0.03 a query** (con 3 ricerche X + ragionamento). Cache input riduce.

## 3. IL PROMPT: massivo, dettagliato, NON difensivo
Errori che abbiamo fatto e corretto:
- ❌ Prompt di 2 righe → roba a caso o vuoto. Grok e' potente: dagli un **brief da senior**.
- ❌ Troppo severo ("solo appena lanciati + micro + multipli caller + [] se incerto") → Grok gioca
  sul sicuro e risponde **[]**. Le ricerche per i token *appena nati* tornano a vuoto (non sono
  ancora abbastanza su X).
- ✅ **Finestra giusta:** fase di **ignizione** (da poche ore a ~2-3 giorni), prime ondate di
  attenzione ADESSO. Non l'ultra-micro-appena-nato (invisibile), non la mega-famosa (gia' pumpata).
- ✅ **Incoraggia a riportare** quello che trova ("dammi le candidate che vedi, anche early/incerte,
  marca la confidence") invece di punirlo con [].
- ✅ **Esclusioni esplicite** delle famose (lista nomi) cosi' non te le ripropone.
- ✅ Chiedi: prima un **riassunto** di cosa ha trovato, poi le candidate, **alla fine un JSON** da parsare.
- ✅ Per ogni token: ticker, **contract address** (fondamentale per l'on-chain), age, narrativa,
  chi ne parla, heat, velocity, confidence.

## 4. NON fidarti mai di Grok: incrocia con l'on-chain
Grok puo' **allucinare** o flaggare rug. Prova reale (12/06): su 4 flag → 1 runner vero (BrimfableAI
+233%, liq sana), 1 spike-trappola (liq $0), 2 dud/rug. **Il segnale c'e' ma e' rumoroso.**
→ Regola: Grok flagga (cosa scalda) **+** conferma on-chain (liquidita' tiene/cresce, non si svuota;
holder salgono) = filtri via i rug. **Mai solo Grok.**

## 5. Il nostro EDGE (non e' avere Grok, ce l'hanno tutti)
- **Sistematicita':** chiamiamo ogni 4h → **serie storica** dei trend (il tizio dell'app chiede una volta)
- **Struttura:** database con timestamp, CA, attributi
- **Validazione:** backtestiamo quali flag Grok diventano runner → impariamo di chi/cosa fidarci
- **Fusione:** trend Grok + on-chain + i nostri attributi = un SETUP, non un'opinione secca

## 6. CFO
- ~$0.03/query, 6/giorno = ~$0.18/giorno. Con €5 ≈ 4 settimane.
- $175/mese GRATIS attivando il **data-sharing** su console.x.ai (per uso illimitato).
- Tieni l'occhio sul consumo nel dashboard xAI.
