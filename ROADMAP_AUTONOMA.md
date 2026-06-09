# Roadmap Autonoma — Crypto Radar

## 🎯 SCOPO PRINCIPALE (rileggere prima di ogni decisione)

> C'è gente che entra nel mercato crypto e **fa soldi veri**. Noi sfruttiamo la potenza
> di **cloud + AI + multi-agent** per capire **COSA sta funzionando** e **COME fanno** a
> farli — in modo **schematico, organizzato, e imparando dai nostri errori**.

Non ci interessa il caso singolo (il pischello con 40k che magari è il figlio dello sceicco
che brucia soldi prelevati da Binance). Ci interessa il **pattern ripetibile**: se esiste
un modo sistematico con cui qualcuno fa soldi e noi possiamo **rilevarlo, copiarlo o
sfruttarlo** con strumenti gratis + cloud, lo troviamo. Se NON esiste, lo **dimostriamo**
escludendo gli scenari uno per uno — e questo è un risultato, non un fallimento.

**Vincoli ferrei:** solo API gratuite (~€0), paper trading prima (mai soldi veri finché
non è provato statisticamente), gira in cloud (Mac spento), onestà brutale sui dati.

---

## 🔬 METODO: SCENARI A ELIMINAZIONE SISTEMATICA

Invece di "provare a caso", testiamo una **roadmap di 10 scenari** (ipotesi su come si fa
soldi), **uno alla volta**, con un protocollo rigoroso. Ogni scenario ha criteri chiari di
**successo** e di **park** (vicolo cieco), così non ci innamoriamo di niente e non ci
blocchiamo all'infinito su un'idea morta.

### Il ciclo di vita di uno scenario

```
ATTIVA scenario N
   │
   ├─ gira ~6h, accumula dati / paper-trade in cloud (GitHub Actions, gratis)
   │
   ├─ AUTO-ANALISI (ogni 6h, automatica, senza che Nick chieda):
   │    1. leggo i dati accumulati
   │    2. [opzionale] chiamo il DOUBLE AGENT (GPT-5/DeepSeek, costa centesimi)
   │    3. valuto: sta funzionando? c'è un limite strutturale?
   │    4. AGGIUSTO i parametri/logica da solo (come quando Nick chiede "come siamo messi")
   │    5. committo + pusho (git = storico + safety net)
   │
   ├─ dopo K iterazioni (3-5, decido io in base ai dati):
   │    ├─ FUNZIONA (EV netto +, criterio di successo raggiunto) → STOP + AVVISA NICK 🟢
   │    ├─ LIMITE STRUTTURALE (mixer, latenza, base-rate, dati assenti) → PARK ("unachievable") → scenario N+1
   │    └─ INCERTO ma non morto → continua ad accumulare
   │
   └─ log del verdetto in ROADMAP_STATO.md
```

### Regole del loop autonomo

1. **Auto-analisi ogni ~6h** — non aspetto che Nick chieda "come siamo messi". Lo faccio io.
2. **Il Double Agent è parte dell'auto-analisi** — ogni analisi PUÒ chiamare GPT-5/DeepSeek
   per una seconda opinione. Costa centesimi (≠ generare 50 immagini). CFO ok.
3. **Aggiusto da solo** parametri, soglie, e quale scenario è attivo. Le modifiche grosse
   restano comunque su git (Nick può rivedere la history).
4. **Park ≠ cancella.** Uno scenario parcheggiato resta documentato col MOTIVO del blocco,
   così non lo riproviamo per errore e impariamo dall'errore.
5. **Quando qualcosa FUNZIONA → STOP e avvisa Nick.** Non si rischiano soldi veri in autonomia.
6. **Onestà statistica:** servono decine/centinaia di osservazioni prima di credere a un edge.
   Pochi trade fortunati ≠ edge.

---

## 🤖 DOUBLE AGENT — protocollo (recap)

Quando serve una seconda opinione vera (non la mia stessa prospettiva):
1. Genero un **prompt-bomba** su misura con tutto lo stato del progetto.
2. Lo mando a **GPT-5 + DeepSeek** (famiglie diverse) via `double_agent.py` — automatico.
3. Leggo le risposte, estraggo l'oro, **agisco**.
4. Salvo la consulenza in `CONSULENZA_*.md` / `SCENARI_*.md`.

**Costo:** centesimi a chiamata. **Trigger:** "double agent <argomento>" oppure dentro
ogni auto-analisi del loop.

---

## 📋 STATO ROADMAP

Vedi `ROADMAP_STATO.md` (aggiornato a ogni auto-analisi): scenario attivo, iterazione,
verdetti, scenari parcheggiati col motivo.

I 10 scenari sono progettati con il Double Agent → file `SCENARI_gpt5.md` + `SCENARI_deepseek.md`
→ sintetizzati qui sotto.
