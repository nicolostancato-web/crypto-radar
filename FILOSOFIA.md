# FILOSOFIA — come lavora crypto-radar (il principio cardine)

> Deciso con Nicolò, 2026-06-28. Questo guida TUTTO. Rileggere prima di ogni cambio di strategia.

## L'EDGE NON ESISTE GIA' FATTO. VA COSTRUITO.

Non si "trova" un edge pronto sul piatto. Lo si **costruisce a tentativi**, iterando:
prima la pressione (bs ratio), poi l'accelerazione, poi forse altro ancora. Magari
l'accelerazione è la chiave per fare soldi, magari fra una settimana scopriamo che non lo è.
**Non importa quale sia il pezzo giusto: conta il PROCESSO.**

### L'analogia SpaceX
Il goal "risparmiare sui data center" sembrava impossibile — *"come facciamo a risparmiare?"*.
Finché un giorno arriva l'idea-svolta: **"costruiamo i data center nello spazio"**. Rivoluzionario,
fa milioni. **La svolta non esiste finché il lavoro disciplinato e creativo non la fa esistere.**
Il goal chiaro e ossessivo è il magnete che, prima o poi, attira l'idea.

## L'INVESTITORE (= il deep meeting, ogni ~5 giorni)

L'investitore arriva e chiede: *"Ragazzi, come siamo messi? Qual è il goal? Come ci arriviamo?"*

- ❌ NON si arrabbia se oggi **non c'è l'edge / la soluzione**. Lo sa che va costruita.
- ✅ Vuole sapere se è tutto **organizzato da senior specialisti** affinché si ARRIVI al goal.
- 😌 È **TRANQUILLO** quando vede: il team ha il goal in testa in modo ossessivo, è creativo ogni
  volta, prende **azioni concrete**, e **cambia rotta** quando non ci sono risultati.
- 😟 È **PREOCCUPATO** solo quando vede: tutto **piatto**, confusione, nessun piano, nessuna azione.

> **La calma non viene dall'avere la risposta oggi — viene dall'avere un sistema strutturato e
> creativo che la cerca senza sosta.**

Esempio perfetto (investor meeting 2026-06-28): "non abbiamo edge" → si analizza a fondo con l'AI →
"l'accelerazione anticipa, proviamola" → si implementa subito → i dati confermano (+10pt). L'investitore
va a casa tranquillo: il team **costruisce**, non aspetta.

## CADENZA OPERATIVA
- **Ogni giorno:** solo allenamenti leggeri tra i 3 team (allineamento). Niente meeting pesanti.
- **Ogni ~5 giorni:** il **deep investor meeting** (`deep_meeting.py`) — super profondo, GLM + scan
  mercato, caccia alla svolta. Come siamo, qual è il goal, e si CAMBIA se non ci sono risultati.

## ITERARE È IL METODO (non un fallimento)
Le idee NON vengono subito, ed è GIUSTO così. Un mese fa la pressione era l'idea migliore: l'abbiamo
testata sui dati, vista non ideale, e siamo passati all'accelerazione. **Idea → test sui dati → se non
funziona, prossima idea.** Scartare un'idea testata è progresso, non sconfitta. SpaceX uguale: idee
basate sui dati, scartate, raffinate, finché spunta la svolta.

## IL GOAL AZIENDALE È L'ANCORA
Le migliori aziende non hanno l'idea pronta — hanno il **goal chiaro e ossessivo**, e tutto ci torna
sopra. L'idea arriva *perché* il goal tira. Ogni 5 giorni l'investitore non vuole "l'idea geniale già
fatta": vuole vedere che **il team SA cosa sta facendo, come si sta muovendo, e DOVE SONO I PUNTI
DEBOLI.** Gli allineamenti servono proprio a trovare i punti deboli — perché se non li conosci, sei
alla deriva e non hai più niente.

## L'EDGE ESISTE (convinzione di Nicolò, dato osservato — 2026-06-28)
**L'edge esiste, e' un dato di fatto.** Nicolò l'ha visto: wallet che accumulano in modo NON casuale,
gente (anche ragazzini) che fa soldi davvero. Non e' un'opinione. La disciplina non e' dubitare che
esista — e' capire **quale versione possiamo catturare NOI** (attenti al survivorship: vediamo i
vincenti, non i mille che perdono accanto; e ai vantaggi non trasferibili: velocita', insider, info).

**Il concetto-chiave di Nicolò (giusto e maturo):**
- Basta **un indicatore diverso** da seguire. Forse non e' prevedere il pump (arriviamo tardi): e' un altro angolo.
- Non servono i 100x. Basta **una piccola percentuale ripetibile, sommata e composta**. Per €1000/mese
  serve un piccolo vantaggio che si ripete, non un colpo grosso. Piu' realistico, non meno.

**Il "data center nello spazio" candidato — LA PROSSIMA FRONTIERA:**
Invece di INDOVINARE noi, **seguire/copiare in tempo reale i wallet che GIA' vincono (smart money).**
Non predici il pump — copi chi l'edge ce l'ha gia'. Angolo diverso. Da portare all'investor meeting come
prossimo grande esperimento (vedi skill copy-trading / wallet-profiling in CLAUDE.md).

## 🧪 CONTROLLO QUALITA' GIORNALIERO (no bug, no interruzioni)
Regola di Nicolò (2026-07-02): **un agente ogni giorno deve girare e assicurarsi che TUTTO sia su —
niente bug, niente interruzioni.** Perche': un bug in `team_meeting` (`r['filter']` su stringa) ha fatto
fallire `track.yml` per 11h prima che ce ne accorgessimo. Mai piu'.

`qa_agent.py` (workflow `qa.yml`, ogni giorno 05:00 UTC, prima del meeting):
- **Smoke test vero**: importa e GIRA i pezzi critici (team_meeting dataset+analista+trader, paper_account,
  kpi_daily, import di tutti i moduli) → se uno crasha, lo becca SUBITO (avrebbe preso il bug del 2/7).
- **Integrita' dati**: ogni jsonl/json parseabile (niente file corrotti da merge).
- **Freschezza**: scan/tracking non fermi.
- Se qualcosa e' rotto → **email con l'errore esatto (traceback)** + job rosso (notifica GitHub).
- Ogni check e' isolato: l'agente QA non crasha mai lui stesso.

E' complementare al **watchdog** (che guarda solo la freschezza dei dati): il QA guarda i BUG nel codice.

## LA REGOLA D'ORO
Il mio compito da senior: garantire che ci sia **SEMPRE un piano strutturato e azioni creative verso
il goal** (mamma in pensione, €1000/mese), anche — soprattutto — quando l'edge ancora non c'è.
**Mai lasciare il sistema piatto. Mai confusione. Sempre il prossimo esperimento pronto.**
