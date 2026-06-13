# IL LOOP DEL MIGLIORAMENTO — come si costruisce l'edge migliore

> Il principio centrale di TUTTO il progetto (e di ogni tool che deve migliorare nel tempo).
> Nicolo, 2026-06-13: "Come facciamo ad avere l'edge migliore? Implementare le modifiche, accumulare dati
> 24h, capire dove sbagliamo, rifare un prompt massivo, reimplementare, aspettare dati, e cosi' via."

## IL CICLO (si ripete all'infinito)

```
   ┌─────────────────────────────────────────────────────────────┐
   │  1. PROMPT MASSIVO a un'AI esterna: "dato lo stato e i dati   │
   │     accumulati, cosa miglioreresti ADESSO?"                   │
   │                          ↓                                    │
   │  2. IMPLEMENTARE le modifiche proposte (le piu' sensate)      │
   │                          ↓                                    │
   │  3. ASPETTARE e ACCUMULARE dati (≈24h, o piu')                │
   │                          ↓                                    │
   │  4. ANALIZZARE: dove stiamo sbagliando? cosa non funziona?    │
   │                          ↓                                    │
   │         └──────────────► torna al punto 1 ◄──────────────┘    │
   └─────────────────────────────────────────────────────────────┘
```

## PERCHE' FUNZIONA
Nessuno trova l'edge perfetto al primo colpo. Si trova **iterando**: ogni giro il sistema vede i propri
errori NEI DATI (non nelle opinioni) e li corregge. Il tempo e la pazienza sono parte del metodo, non un costo.
Implementare tutto in un colpo, su pochi dati, e' overfitting = illusione. Il loop e' l'unico modo onesto.

## DUE TIPI DI LAVORO (non confonderli)
- **SENSORI** (cambiano cosa/come accumuliamo: filtro, feature, pulizia): si implementano SUBITO, perche'
  ogni giorno senza = un giorno di dati poveri.
- **ANALISI** (backtest, regressione, calibrazione soglie): si fanno DOPO l'accumulo, mai a campione minuscolo.

## AUTOMAZIONE (improve_agent.py, ogni 24h)
Il loop e' AUTOMATICO al punto 1: ogni giorno un agente raccoglie lo stato reale del sistema (n. trade,
entry timing, performance strategie, confronto arene, lezioni, config attuale) e lo invia a un'AI esterna
(DeepSeek) con la domanda "cosa miglioreresti adesso?". Salva il feedback e lo manda via EMAIL a Nicolo.
Poi l'umano (Nicolo + Claude) decide cosa implementare. Punto 2-3-4 restano umani-nel-loop, di proposito.

## IL GATE — abbastanza dati E dati sensati? (le due paure di Nicolo)
Prima di fare l'analisi critica ogni 24h, l'agente si chiede: "ho abbastanza dati, e sono SENSATI?".
- **READY** (>= 30 trade conclusi E >= 3 runner) -> fa l'analisi critica (DeepSeek) e manda il feedback.
- **SKIP** (dati insufficienti) -> NIENTE analisi (nessun costo): manda solo un'email "giorno di accumulo,
  X/30 trade, Y runner", e aspetta.
- **FORCE** -> se sono passati 4 giorni di SKIP consecutivi, forza COMUNQUE un'analisi (preliminare). Cosi'
  non ci si blocca mai per perfezionismo (paura #1: loop di rinvio infinito).
Contro l'accumulo di TRASH (paura #2), ad ogni giro il gate controlla la QUALITA': i trade conclusi
crescono rispetto a ieri? ci sono vincitori? il filtro fa passare delle perle? Se la raccolta e' FERMA o
SENZA VINCITORI, lo segnala subito nell'email — non si accumula spazzatura per giorni senza accorgersene.
Soglie tarabili in improve_agent.py (MIN_TRADES, MIN_RUNNERS, MAX_SKIP_DAYS).

## I RUOLI
- **Nicolo = amministratore / guida.** Porta la direzione, fa la domanda giusta al momento giusto.
- **Claude = la mente / esecutore.** Capisce, struttura, costruisce, fa girare il loop.
Non abbiamo un "metodo magico" preconfezionato: abbiamo QUESTO loop, guidato da Nicolo, eseguito da Claude.

## LA VERITA' DI FONDO
**Non esiste un edge perfetto gia' pronto. Questo loop E' il metodo per arrivarci.** L'onesta' brutale di
un'AI esterna ogni 24h fa emergere cose che dall'interno non vedi (e' successo oggi, 2026-06-13: una domanda
secca ha rivelato che il filtro escludeva i token giovani). Si accetta la critica, si reimplementa, si accumula.
All'infinito, finche' l'edge emerge dai dati — o finche' i dati dimostrano onestamente che non c'e'.

## REGOLA D'ORO
**Mai implementare e basta. Mai accumulare e basta. Sempre: implementa → accumula → critica → reimplementa.**
Questo vale per crypto-radar e per ogni altro tool che costruiamo.
