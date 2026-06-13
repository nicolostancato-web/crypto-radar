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

## Lezione #2 — Quale arena per il catch-via-X (consulenza Grok, 2026-06-12)

**Domanda posta a Grok live:** non "il mercato piu' fruttifero" ma "quale arena rende di piu' PER IL NOSTRO
metodo" (catch via X, retail lento, finestra ore). Vedi PROMPT_mercato_migliore.txt + CONSULENZA_mercato_2026-06-12.md.

**Verdetto Grok (1 fonte, 1 fotografia — da verificare on-chain):**
1. AI-agent tokens / Virtuals (Base+Solana) — 9/10 intercettabilita' via X
2. Hyperliquid / perp farming — 8/10 MA e' airdrop farming, non token-pump
3. Solana memecoin (attuale) — 7/10, volume alto ma piu' shill/bot, finestra che si stringe

**Mio filtro critico (senior):**
- Hyperliquid = gioco DIVERSO (farming punti, niente CA/liquidita'/entry-exit). Il nostro pipeline NON si
  applica. Scartare per ora.
- Virtuals/AI-agent = SI compatibile col nostro pipeline identico (token con CA su Base/Solana, DexScreener
  li copre, stesso filtro). Arena azionabile.
- Solana resta valido (liquidita' alta); il "piu' bot/finestra stretta" conferma la Lezione #1 (arriviamo tardi).

**Direzione proposta (NON applicata — decide Nicolo):** allargare lo scouting Grok per includere anche
AI-agent token, TENERE Solana, e lasciare che il learner (entry onesto) dica coi numeri quale arena rende di
piu' PER NOI. Fedele al metodo: non scegliere a priori, far decidere i dati.

**Stato:** consulenza registrata. In attesa di OK per allargare lo scouting oltre Solana.

## Lezione #3 — Primo verdetto del learner: gli SCARTATI battono le PERLE (2026-06-13)

**Dati (31 trade conclusi, dati puliti dopo fix glitch JOTCHUA).** Con entry ONESTO (al segnale):
- SCARTATI andati bene: AgentFX +122%, JOTCHUA +57%, ARX +48%, LARP +41%, BRAINDRAIN(ai) +37%.
- PERLE in perdita: GAEJUKI +10% picco ma -56% ORA; BrimfableAI +8% picco, -10% ora.
- runner_rate: memecoin 1/27, ai_agent 0/5 (ai_agent troppo pochi per dire).

**Diagnosi (conferma e rafforza Lezione #1).** Il filtro attuale premia i token con volume/buy-sell GIA' alti =
gia' pompati = li prendiamo al TOP → poi ritracciano. E SCARTA i giovani (eta'/vol assoluto sotto soglia) che
pero' hanno ancora corsa davanti. Cioe' il filtro, con l'entry al segnale, sta selezionando i PERDENTI.

**Direzione proposta (NON applicata — campione ancora piccolo, decide Nicolo):**
1. Rilassare i filtri che bocciano i GIOVANI: min_vol_24h, min_vol_1h, age_max piu' stretto (preferire eta' bassa).
2. Dare peso alla FRESCHEZZA/accelerazione invece che al livello assoluto di volume.
3. Considerare che il "buy/sell alto" e "vol alto" sono sintomi TARDIVI, non precoci.

**Cautela onesta.** 31 trade, solo 1-2 runner: pattern netto ma campione limitato. Prima di toccare config.FILTER
servono piu' trade conclusi e idealmente vedere se il pattern regge su un'altra settimana. Il sistema continua.

**Bug risolto oggi.** Un'osservazione glitch di DexScreener (price 55.27 vs 0.0025 reale) gonfiava JOTCHUA a
+2.020.002%. Aggiunto sanitizzatore: scarta prezzi outlier >15x dalla mediana (in pipeline_export + learner).
Il dato sporco NON e' cancellato (append-only), solo ignorato in lettura.

**Stato:** verdetto registrato. Filtro INVARIATO in attesa di piu' dati.

## Lezione #4 — Review esterna (DeepSeek): il problema e' la LATENZA, non il filtro (2026-06-13)

Double-agent: consulto massivo a DeepSeek + GPT5 (GPT5 timeout). Vedi CONSULENZA_review_deepseek.md.

**Verdetto brutale DeepSeek:** "strutturalmente perdente con la config attuale". Causa precisa: la LATENZA.
La tesi 'X precede il prezzo' regge solo per le PRIME 1-3 ore di un rally; con scan ogni 4h lo vediamo con
2-8h di ritardo -> compriamo sempre dopo il pump. Inoltre, insight chiave: il filtro `vol24h>50k` ESCLUDE i
token <24h -> ecco perche' le green hanno eta' 27h+ (cancelliamo i segnali precoci col nostro stesso filtro).

**Implementato subito (gratis, test coi nostri dati):** il TIMING d'ingresso. Sulle perle:
- entrare al segnale = -16% mediano
- aspettare una correzione -15% poi entrare = +2% mediano (n piccolo, ma direzione coerente col pivot).
Il test ora gira da solo e si popola. Conferma il pivot "compra la correzione, non il top".

**Suggerimenti DeepSeek da DECIDERE (grossi, non applicati alla cieca):**
1. Ridurre latenza scan (streaming/event-driven ~60s) — contraddice la scelta CFO 4h; va valutato (VPS/Twitter stream).
2. Backtest STORICO su 500-1000 token (DexScreener/Birdeye) per sample size vero (ora 31 trade = troppo pochi).
3. Regressione logistica/random forest (sklearn) sulle feature invece del confronto manuale (serve piu' dati).
4. Fix filtro: per token <8h togliere vol24h/vol1h assoluti, usare ACCELERAZIONE volume (% su 30min).
5. Aggiungere: buyers unici, eta'/storia del wallet deployer, slippage simulato (-2% al P&L).

**Non applico:** togliere il watchdog (Nicolo lo vuole per il suo modo di lavorare). Resta.

**Punto onesto:** 31 trade sono troppo pochi per qualunque conclusione forte. La review e' una bussola, non
una verita'. Il valore vero arriva con piu' dati (accumulo) + i test (dip-entry) che ora girano da soli.

## Lezione #5 — Lo SCOUT pesca male: vecchi e rug (watchdog, 2026-06-13)

Il watchdog data-quality ha allertato: "0 perle in 24h su 19 valutati". Investigato: il filtro scarta TUTTO,
ma GIUSTAMENTE — Grok sta ripescando token VECCHI (GORBA 84 giorni, MemesAI 240 giorni, DINKY 71 giorni) e
RUG (DRP top10 100%, ELON top10 72%). Il filtro NON e' rotto, fa il suo lavoro. Il problema e' a MONTE: lo
scout Grok non trova abbastanza token freschi e puliti (e spesso sbaglia l'eta' dichiarata: dice "8h" ma e'
100 giorni -> non fidarsi mai dell'eta' di Grok, contano i dati on-chain).

**Da implementare (loop):** migliorare lo scout perche' peschi piu' fresco/pulito; oppure accettare che le
perle sono rare (1-5%) e imparare anche dai red (gia' facciamo: 34 trade, 4 runner, status READY).
**Fatto subito:** calibrato l'alert watchdog (0 perle: ora su 48h e >=30 valutati, non spammare su varianza).
**Stato:** siamo READY -> il prossimo loop improve fara' l'analisi critica e includera' questa osservazione.
