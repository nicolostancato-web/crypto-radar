# APPUNTI TRADING — lezioni vere dai trade reali

> Documento vivo. Qui scriviamo le lezioni QUALITATIVE che traiamo osservando i trade.
> Il learner (learnings.json) dà i numeri; qui scriviamo cosa significano e cosa cambiare.

---

## Lezione #1 — Il filtro becca i buoni, ma li becca TARDI (2026-06-12)

**Osservazione.** Le prime 2 perle promosse dal filtro:
- **GAEJUKI**: +501% in 24h (token vero, non rug). Ma quando l'abbiamo catturato (entry onesto al primo
  check dopo il segnale) era a fdv **$2.1M**, e nelle ore successive **−31% in 1h, −47% in 6h**. Già al top.
- **BrimfableAI**: +162% in 24h. Nostro entry a fdv **$515k**, poi **−17% in 1h**. Anche qui oltre il picco.

**Diagnosi.** Il +500% è il movimento DALL'INIZIO del token, NON da quando entriamo noi. Quando Grok li
segnala hanno gia': volume esploso ($4M/24h), eta' 27-55h, buy/sell ancora alto. Cioe' i bei numeri che
fanno scattare il "PERLA" sono il **RISULTATO** del pump gia' avvenuto, non i segnali che lo PRECEDONO.
Risultato: entriamo a onda quasi finita → da li' ritracciano → entry in perdita.

**Cosa cambiare (da testare, NON ancora applicato — decide l'umano):**
1. **Anticipare la cattura.** Premiare token piu' GIOVANI (es. eta' 2-12h invece di fino a 72h) con
   volume in ACCELERAZIONE ma non ancora esploso.
2. **Misurare la derivata, non il livello.** Non "vol_24h alto" (tardivo) ma "vol_1h che cresce rispetto
   alle ore precedenti" (anticipato). Serve confrontare snapshot consecutivi dello stesso token.
3. **Distinguere ignizione da esaurimento.** Un token a +400% con buy/sell che scende = sta finendo, non
   inizia. Il filtro oggi non lo vede.

**Come lo dimostriamo (gia' attivo).** Il tracker registra l'entry ONESTO (primo check dopo il segnale).
Su questi due gli entry saranno in ROSSO → il learner, accumulando, confermera' quantitativamente che
"perle vecchie + volume gia' esploso = entry in perdita". Quando il campione e' sufficiente, sapremo le
soglie d'eta'/volume che separano l'ignizione vera dall'onda gia' partita.

**Stato:** osservazione registrata. In attesa di piu' trade conclusi prima di toccare config.FILTER.

---
