# Metodo: tracciare gli OPERATORI seguendo i FLUSSI (non i singoli trade)

> Input Nicolò 2026-06-10. Progettato da Fable 5 (Anthropic). NON costruito ancora — è il piano.
> Obiettivo: chi ha soldi/sa, usa un MAIN wallet → carica wallet usa-e-getta → tradeggia → svuota.
> Tracciare il singolo wallet usa-e-getta è inutile (sparisce). Tracciare il MAIN e i FLUSSI sì.

## Il problema noto (già sbattuto contro)
Il funding-graph naive ("chi ha finanziato questo wallet?") porta SEMPRE a un **hub CEX**
(Binance/Coinbase): tutti prelevano da un exchange. Quindi "il funder" da solo è rumore.
→ La sfida vera NON è seguire i flussi, è **distinguere l'OPERATORE personale dall'EXCHANGE.**

## La soluzione: il "grafo degli operatori"

### 1. Filtro OPERATORE vs HUB (il cuore)
Quando wallet A manda SOL a wallet B, classifica A:
- **Operatore personale** se: ha finanziato **5-50 wallet** (non migliaia), bassa frequenza tx,
  pochi counterparty unici. → TIENI, è un "main" da tracciare.
- **Hub CEX/servizio** se: finanzia **centinaia/migliaia** di wallet, alta frequenza,
  tantissimi counterparty. → SCARTA (è Binance & co.).
(Helius: getSignaturesForAddress + conteggio destinatari/frequenza. Avevamo già `MAIN` config:
min_funded, max_funded_hub, tx_per_hour.)

### 2. Clustering per FINANZIAMENTO condiviso
I wallet di trading finanziati dallo **stesso main personale** = stesso operatore.
→ Traccia il comportamento AGGREGATO del cluster (i loro buy sommati = la posizione vera dell'operatore).

### 3. Clustering per COMPORTAMENTO (anche senza link di funding)
Wallet che comprano gli **stessi token nelle stesse finestre**, ripetutamente = stesso operatore/gruppo.
(Similarità di Jaccard sui set di token + timing. Becca i coordinati che non condividono il funder.)

### 4. Seguire i FLUSSI nel tempo (la firma dell'operatore serio)
Pattern: **main accumula → distribuisce a wallet di trading → tradano → profitti tornano al main**
(o a wallet freschi). Tracciando il MAIN (persistente, ha i soldi) becchiamo **ogni nuovo
wallet usa-e-getta dal minuto zero** → risolve la disposabilità (il main non sparisce).

### 5. L'IPOTESI DI EDGE (perché questo potrebbe funzionare dove "copia singolo wallet" fallisce)
Non copiamo un wallet usa-e-getta a caso. Copiamo **l'OPERATORE**: quando un operatore i cui cluster
passati erano profittevoli **finanzia/spawna un nuovo wallet e questo inizia a comprare** → segnale
precoce ad alta confidenza. Si valida nel dataset: i buy "da operatore-noto-profittevole" hanno EV+ ?

## Dati da popolare (per questo metodo)
- Grafo funding (chi→chi, importo, timestamp) coi filtri operatore/hub
- Cluster id per wallet (da funding + co-trading)
- Storia del MAIN: quanti spawn, quando, quanto carica, profitti che rientrano
- Label: i cluster/operatori passati erano profittevoli? (collega al dataset eventi)

## Stato / trigger
NON costruire ora (prima finiamo dataset + segmentazione su Solana). Tirare fuori quando:
- il dataset "copia singolo wallet" è esaurito senza edge chiaro, OPPURE
- vogliamo il livello successivo: copiare OPERATORI invece di wallet singoli.
Rischio noto: il filtro operatore-vs-hub è delicato (già preso una cantonata col caso Binance).
