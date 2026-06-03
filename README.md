# crypto-radar

Pipeline di **screening** di token crypto su **dati pubblici**. Aggrega segnali,
filtra trappole (rugpull / distribuzione / impersonazioni), assegna un punteggio e
produce un Excel ordinato che **tu rivedi a mano** per fare **paper trading**.

> ⚠️ È uno strumento di *analisi e apprendimento*, non un consulente finanziario e
> non un bot di trading. Non esegue ordini. L'aspettativa onesta è che un edge
> sfruttabile **probabilmente non esista**: il sistema serve a verificarlo coi dati
> *senza rischiare denaro*. Vedi la sezione "Onestà" sotto e `CLAUDE.md`.

## Architettura (pipeline a 4 stadi)

```
DEXScreener (free)          on-chain / DEXScreener        somma pesata           top_scores.xlsx
        │                           │                          │                       │
   ┌────▼─────┐   candidati   ┌─────▼──────┐  segnali   ┌──────▼──────┐  voto   ┌───────▼───────┐
   │ DISCOVERY├──────────────►│ ENRICHMENT ├───────────►│   SCORING   ├────────►│    EXPORT     │
   │buttafuori│   (assets)    │investigatore│ (signals) │   giudice   │(scores) │   vetrina     │
   └──────────┘               └────────────┘            └─────────────┘         └───────────────┘
```

- **Discovery** — "merita osservazione?" Filtra spazzatura, pesa segnali *precoci*.
- **Enrichment** — sicurezza (→ **esclusione permanente**), anti-distribuzione, qualità.
- **Scoring** — somma pesata con decay temporale + bonus di confluenza.
- **Export** — rigenera `top_scores.xlsx` da solo, ordinato per score. Tu apri e basta.

## Setup

```bash
pip install -r requirements.txt
python run.py --once     # un giro singolo (test)
python run.py            # loop continuo
```

SQLite di default: **zero configurazione**. Per Postgres cambi solo `get_conn` in `db.py`.

### (Opzionale ma consigliato) RPC on-chain
I segnali più *anticipati* (netflow exchange, crescita holder) sono on-chain. Sono
già predisposti nei punti **[RPC]** di `jobs/enrichment.py`. Metti una chiave free-tier
(es. Alchemy/Infura) in `config.ENRICHMENT["rpc"]` e implementali. Senza chiave il
sistema gira lo stesso, semplicemente non li misura.

## Tarare il sistema
Tutto sta in **`config.py`**. Parte conservativo (pochi candidati, pochi falsi
positivi). Allarga le soglie guardando i dati veri — è più facile allargare che
ripulire un Excel pieno di spazzatura.

## Onestà (leggila)
- L'Excel ha le colonne `Entrata_ipotetica`, `Prezzo_dopo_3g`, `Esito`: compilale a mano.
  È paper trading. Il prossimo modulo sensato è una tabella `outcomes` che lo automatizza
  e calcola il **valore atteso al netto di slippage**, non la semplice % di colpi giusti.
- Il paper trading è *ottimistico* (niente slippage/emozioni/senno di poi). Servono
  centinaia di osservazioni in regimi di mercato diversi prima di credere a un edge.
- I filtri anti-distribuzione/rugpull esistono per tenerti **fuori** dalle trappole
  (i token già pompati in fase di "exit liquidity"), non per inseguirle.

## Costi
Discovery solo su fonti gratuite. Enrichment (costoso) solo sui candidati attivi, con
tetto duro e frequenza decrescente. Ogni chiamata passa da un rate limiter (`net.py`).
Prima di aggiungere una fonte a pagamento, calcola il costo mensile.
