🎯 MEETING PROFONDO SETTIMANALE — crypto-radar

Ragazzi, e' passato del tempo. Ci ripetiamo la sola cosa che conta: DOBBIAMO ARRIVARE AL GOAL.
La mamma di Nicolo deve poter smettere di lavorare. 1000 EUR/mese. Non un sogno: un piano.

Stato oggi: 1036 token accumulati, 204 runner. Sopravviviamo ma non guadagniamo ANCORA.
Oggi non ci alleniamo soltanto: andiamo NEL PROFONDO. Cosa abbiamo, come spingiamo, come diventiamo
profittevoli, come alziamo la percentuale di successo, come arriviamo al goal.

================================================================
🌍 COSA FUNZIONA NEL MERCATO REALE ADESSO (scan live su X)
================================================================
**Nel 2026 i trader profittevoli su Solana memecoin operano in modo radicalmente diverso dalla folla.** Non è “ricerca narrativa” o “sniping random”: è selezione chirurgica per range di MC, timing su dip confermati e disciplina ferrea su sizing/exit. Ecco cosa emerge dalle discussioni reali di trader con PNL reali (6-fig in pochi mesi, runner ripetuti).

### Cosa fanno di diverso (non ovvietà)
- **Classificano il mercato per fasce MC e si specializzano solo dove il R/R è asimmetrico.**  
  Il range $15k-$50k è dove si confermano i runner precoci (molti soldi fatti qui nel bullrun). Sotto $15k è per pochi con ore su memescopes e capacità di tenere senza jeet. Sopra $50k diventa take-profit zone o zona pericolosa in bassa liquidità. Sopra $150k solo conviction forte e se tiene 24h+. Molti ex high-cap hanno bruciato perché continuavano a fare top-blast. I vincenti si spostano fluidamente e diventano ultra-selettivi quando la liquidità cala.[[1]](https://x.com/Latuche95/status/2037894692281499711)

- **Non tradano tutti i giorni.** Aspettano il “right play” e size in proporzione. Large MC con narrative resiliente + community + traction battono i low-cap flip veloci.[[2]](https://x.com/W0LF0FCRYPT0/status/2018450577563222457)

- **Usano gruppi ristretti** (non Twitter pubblico). Un cervello solo perde dettagli; più trader sincronizzati beccano news pair e deployer trusted prima.[[3]](https://x.com/haspidox/status/2055584262913486962)

### Segnali on-chain/sociali per entrare PRIMA della folla
- **On-chain reali (non volume fake):** transazioni continue (non pump singolo), distribuzione naturale di buy (non solo bot), retail follow-through invece di insider-only.[[4]](https://x.com/geng_one/status/2068963425665876061)
- **Social:** narrative nuova e spreadabile (AI+meme, political, Solana-native culture), discussioni non-official su X, engagement reale su TG/Discord, derivative meme content che nasce spontaneamente. Il deployer trusted/meta è l’edge più grande: le loro launch mandano spesso.
- **Entry trigger concreto:** -50% drawdown dall’ATH su supporto psicologico + età <6h + MC $30k-$350k su pump.fun/Pumpswap.[[5]](https://x.com/shehumls/status/2070102361276596674)

### Gestione entrata e uscita (scaglioni + trailing)
- **Entrata:** 2-3 tranche piccole, mai tutto in una volta, solo dopo dip (non ATH). Limiti quando possibile.[[6]](https://x.com/shehumls/status/2070185574976147580)
- **Uscita:**  
  – Initial investment out a 2-3x.  
  – Resto come “house money”, lascia correre.  
  – Mental SL fisso -30% (sotto $100k MC può scendere a -40% e rimbalzare, sopra è più stabile).  
  – Sell into volume quando il noise è massimo.  
  – Cash-out 80-90% dei profitti e ripeti (non tenere tutto). One entry, one exit principale.[[5]](https://x.com/shehumls/status/2070102361276596674)[[7]](https://x.com/DeltaXtc/status/2020114842707697944)

### Cosa distingue chi fa 10x da chi perde
- **Disciplina + psicologia:** non convertono SOL in “soldi persi” emotivamente; trattano SOL come ammo. Piccoli profitti giornalieri ($50-100) sono vittoria. Non confrontano con screen Twitter.[[3]](https://x.com/haspidox/status/2055584262913486962)
- **Strumenti veloci** (Axiom o equivalenti) > cashback fee. Terminal lento = entry brutte.
- **Una strategia sola, masterizzata** (es. solo news pair o solo trusted deployer). Non chase meta ogni settimana.
- **Lock profit in stable** non appena il bag diventa serio → cambia mindset e protegge i guadagni.
- I perdenti overtrade, tengono su noise, entrano su hype, non hanno SL mentale e confrontano ego con gli altri.

In bassa liquidità 2026 vince solo chi è selettivo, paziente e ripete il processo (conviction holder su runner confermati + sell into volume). Il resto è casino mascherato da trading.

================================================================
📡🔬 TAB 1+2 — DATI & SEGNALI: dove possiamo migliorare (analisi profonda)
================================================================
Ecco l'analisi spietata sui dati (Tab 1) e i segnali (Tab 2). 
Il problema centrale è chiaro: **siamo in ritardo.** Se `bs>=2.0` ha un win rate del 19% (sotto la base del 20%), significa che quando la pressione d'acquisto è *già* così alta, il pump è avvenuto e noi siamo la liquidità di uscita di chi è entrato prima.

Per battere il muro dello slippage e della velocità, non dobbiamo essere "più veloci dei bot" (impossibile), ma dobbiamo anticipare la *fase di accelerazione* ed evitare le trappole di liquidità. 

Ecco le 5 mosse concrete, in ordine di impatto, basate sui dati che **già abbiamo** ma che stiamo calcolando male o non stiamo usando.

---

### 1. PASSARE DALLA PRESSIONE ASSOLUTA ALLA "DERIVATA" (Accelerazione di Phase 1)
**Dove stiamo sbagliando:** Usiamo `bs>=1.5` o `bs>=2.0` come soglie statiche. Sono lagging indicators. 
**L'ipotesi testabile:** Il edge non sta nel *livello* di pressione, ma nella *velocità* con cui cambia. Un token con bs=1.2 passato da 0.8 a 1.2 in 5 minuti è molto più promettente di un token passato da 1.8 a 2.0.
**Cosa calcolare:** 
- Creare la feature `bs_delta_5m` (variazione del bs ratio negli ultimi 5 minuti).
- Creare l'incrocio: `bs_1h < 1.3` AND `bs_5m > 1.5` (pressione generale ancora neutra, ma esplosione in tempo reale).
**Test:** Filtrare i 243 trade con `bs>=1.5` e dividere in due gruppi: quelli con `bs_delta_5m` nel quartile più alto vs il resto. Scommettere che il quartile più alto porta il win rate dal 23% al 26%+.

### 2. SFRUTTARE L'UNICO SEGNALE CHE FUNZIONA: IL NARRATIVE EDGE (`ai_agent`)
**Dove stiamo sbagliando:** `ai_agent` ha il win rate più alto (26%, n=35) ma lo stiamo trattando come un filtro secondario. In crypto memecoin, la narrativa batte la matematica on-chain per i retail lenti.
**L'ipotesi testabile:** I bot non leggono il "senso" di X, leggono solo i volumi. Grok ci dà un vantaggio qualitativo. Se un token è `ai_agent`, la market cap di ingresso può essere più alta (meno rischio rug) ma la tenuta è maggiore.
**Cosa calcolare:**
- Incrociare `ai_agent == True` con `voli>2` (segnale di volume) e `top10<0.30` (non in mano a pochi).
- **Test:** Isolare i 35 trade `ai_agent`. Qual era la `media robusta` di questi 35 rispetto alla media generale? Se è positiva, dobbiamo smettere di tradare qualsiasi cosa non sia taggata `ai_agent` finché il sample non supera i 100 trade. Concentriamo il fuoco dove c'è già un +6pt confermato.

### 3. BUCKETING DELL'ETA' (Il filtro Anti-Slippage)
**Dove stiamo sprecando dati:** Tracciamo l'`eta'` del token ma non la stiamo usando per segmentare le uscite. Un token di 10 minuti e uno di 6 ore hanno dinamiche di slippage e rug-pull opposte.
**L'ipotesi testabile:** Il muro dello slippage si manifesta soprattutto nei token neonati (liquidity fragile, wide spreads). Nei token "adulti" (es. > 4 ore) che fanno un nuovo pump, la liquidità è più spessa e il nostro ladder di uscita (`ladder_moon`) ha più probabilità di riempirsi a buon prezzo.
**Cosa calcolare:**
- Dividere i 204 runner in 3 bucket: `< 1h`, `1h-6h`, `> 6h`.
- **Test:** Calcolare la `media robusta` del nostro miglior exit strategy (`bs>=2.0 + ladder_moon`) per ogni bucket di eta'. Ipotesi: il bucket `< 1h` ha media robusta -5% (slippage ci uccide), il bucket `1h-6h` ha media robusta +4% (edge reale). Se confermato, **vietiamo trade sotto 1h**.

### 4. ANALISI DELLE WICK CANDLE 5-min (Misurare il rischio di entrata)
**Dove stiamo sprecando dati:** Abbiamo le candele 5m ma le usiamo solo per confermare il trend. Non le usiamo per misurare la *volatilità intracandle*, che è ciò che genera lo slippage in entrata e scatta gli stop loss prematuri.
**L'ipotesi testabile:** Se le candele 5m precedenti al segnale hanno wick (ombre) enormi rispetto al corpo, il market maker sta cacciando i retail. Entrare qui significa beccarsi un -10% in 2 minuti prima del pump reale.
**Cosa calcolare:**
- Estrai la candela 5m del momento del segnale. Calcola `Wick_Ratio = (High - Low) / |Close - Open|`.
- **Test:** Dividere i trade in due gruppi: `Wick_Ratio > 3` (altamente volatile/manipolato) vs `Wick_Ratio < 3`. Scommettere che la `media robusta` dei trade con `Wick_Ratio < 3` è positive, mentre l'altra è negativa.

### 5. INTERAZIONE TOP10 HOLDERS E BALENE (Il filtro Anti-Dump)
**Dove stiamo sprecando dati:** Usiamo `top10<0.30` come segnale singolo (22% win rate). Ma sappiamo dalle scoperte dure che le balene erano look-ahead. Se top10 ha il 28% ma *una singola balena* ha il 15% ed è attiva nei swap grezzi, è una bomba a orologeria.
**L'ipotesi testabile:** L'edge retail esiste solo se il token è distribuito. Se c'è concentrazione, anche con alta pressione d'acquisto, il pump è artificiale (wash trading da parte di pochi) o destinato a essere venduto a piccoli scaglioni.
**Cosa calcolare:**
- Incrociare `top10 > 0.40` (alta concentrazione) con `bs_5m >= 1.5`. 
- **Test:** Verificare se questi trade hanno un tasso di "instant rug" o candele rosse immediate molto superiore alla media. Se sì, usiamo `top10<0.30` non come un segnale per *comprare*, ma come un硬 filtro (hard block) per *NON comprare*. 

---

### RIASS

================================================================
💰 TAB 3 — TRADING: come diventiamo profittevoli (analisi profonda)
================================================================
Ecco l'analisi spietata e il piano d'azione. Nessuna frase di incoraggiamento, solo numeri, logica e regole da eseguire.

### 1. DIAGNOSI: PERCHÉ LA MEDIANA È A -10.7% E LA ROBUSTA A -1%
Il problema non è l'ingresso, è la **geometria del P&L**. 
Se il tuo win rate è ~38% e la mediana delle perdite è fissa a -10.7% (probabilmente lo stop loss iniziale), significa che nel 62% dei casi perdi il 10%. 
Matematica attuale: per pareggiare nel "lungo coda" (robust), il 38% dei trade vincenti deve recuperare il 62% dei trade perdenti. Se perdi il 10.7% 62 volte su 100, hai un buco di -6.63%. I tuoi trade vincenti medi (robusti) ti danno +7% netto. Ne esci quasi in pari, ma le commissioni e lo slippage ti rimandano sotto lo zero (-1%).

**L'errore fatale:** Stai usando uno stop loss fisso (es. -10%) su asset ad altissima volatilità. Nei meme token 5m, un wick del -12% seguito da un +80% è normale. Ti stanno cacciando fuori con il rumore prima del movimento.

### 2. IL PARADOSSO DELLA SELETTIVITÀ (bs>=2.0)
In Tab 2 noti che `bs>=2.0` ha un win rate del 19% (-1pt rispetto al 20% base). Eppure in Tab 3 è il filtro che usi per i ladder. Perché?
Perché `bs>=2.0` non predice il win rate, predice la **magnitude**. Abbassi la frequenza di vittoria ma alzi l'aspettativa del singolo colpo vincente (è per questo che con `ladder_moon` la media "fortunata" schizza a 16.5% ma la robusta si salva a 2.3%). 
**Conclusione:** Continuiamo a usare `bs>=2.0`, ma accoppiato con un filtro *vettore* (es. `voliq>2` o `ai_agent`) per alzare il win rate sopra il 25%.

---

### 3. LA NUOVA STRATEGIA DI USCITA: "TIME-KILL & COST-RECOVERY"
Gli stop fissi non funzionano su una coda lunga a 5minuti. I trailing stop (trail20) ti fottono i rendimenti robusti (-3.2%) perché si attivano troppo presto sulle

================================================================
🧠 LA SINTESI — IL PIANO PER ARRIVARE AL GOAL
================================================================
Siamo soci. La mamma di Nicolo non ha bisogno delle nostre speranze, ha bisogno di 1000 EUR al mese. E i numeri che mi hai messo davanti dicono una cosa sola, chiara e brutale: **su questa strada esatta, a questa velocità, siamo a anni di distanza dall'obiettivo. Forse non ci arriveremo mai.**

Ecco la verità sui numeri che hai portato.

### 1. Quanto siamo REALMENTE lontani dai 1000 EUR/mese?
Per fare 1000 EUR/mese in modo stabile, servono 12.000 EUR/anno.
Il tuo unico KPI positivo reale è `bs>=2.0 + ladder_moon` con una **media robusta del +2.3%**. 
Se fai 20 trade al mese (un ritmo già intenso per un retail che lavora a mano), su un conto da 1000 EUR fai 23 EUR al mese. 
Per farne 1000, ti serve un bankroll di **~43.000 EUR**. Nicolo ha 43k EUR da mettere sul piatto di un bot su memecoin con un win rate del 38% e una mediana del -10.7%? No.

La distanza non è solo di capitale. La distanza è di **modello**. 
Il tuo edge è passato da "perdiamo tutto" a "sopravviviamo perdendo poco". Ma il mercato retail su dati pubblici 5-minuti è una trappola di adverse selection: quando vedi tu la pressione d'acquisto (bs>=2.0), i bot sniping hanno già comprato 3 secondi prima, e la tua entrata coincide con la loro uscita. Il +2.3% robusto è un'illusione che si dissolverà non appena metti slippage reale (1-3%) e fees.

### 2. Continuare su questo edge o cambiare angolo?
**Va cambiato. Ma non le regole, il timeframe.**
L'edge c'è: sai trovare la pressione d'acquisto. Ma stai giocando a ping-pong contro un muro di cemento armato (i bot HFT) sui 5 minuti. 
Il dato più prezioso del tuo dossier è questo: `ai_agent: win 26% (n=35)`. È un campione piccolo, ma è l'unico segnale *narrativo* (non solo matematico) che batte la base del 20% di netto. 

L'alternativa onesta, se non si vuole fare il salto infrastrutturale (pagare un RPC premium, scrivere in Rust, fare mempool sniping a latenza zero, che è un lavoro da ingegneri a tempo pieno), è **spostarsi dove la velocità retail non è un handicap: la duration e la narrativa.**
Smettere di cercare il pump del momento su DexScreener, e iniziare a cercare i token "ai_agent" (o altre categorie forti) quando sono a 50k-100k di market cap, prima che esplodano, usando il bot per il monitoraggio, non per l'esecuzione panicosa su candele 5m.

### 3. PIANO 7 GIORNI: 3 azioni brutali per spingere verso il goal

Se il goal è la mamma di Nicolo, i prossimi 7 giorni non servono a "ottimizzare il trailing stop". Servono a smettere di mentire a noi stessi sul vantaggio competitivo.

**GIORNO 1-2: Il Test dell'Assassinio (Kill the Edge Test)**
*   **Azione:** Prendi la strategia `bs>=2.0 + ladder_moon` (la tua migliore) e applica uno slippage forzato del 2.5% in entrata e dell'1.5% in uscita, più le fees.
*   **Ipotesi:** La media robusta del +2.3% diventerà negativa.
*   **Scopo:** Se confermato, dichiariamo ufficialmente morto il trading 5m su segnali di pressione ritardati. Smetti di perdere tempo a ottimizzare ladder su un segnale che non ha margine per coprire i costi di transazione. 

**GIORNO 3-5: Spostamento sul "Pre-Pump" (Il cambio di angolo)**
*   **Azione:** Cambia la query dei dati. Ignora i token che hanno già un bs ratio alto sui 5m (sei in ritardo). Crea un nuovo tab: monitora i token nati da meno di 1 ora con `top10<0.30` (come hai visto, è un buon segnale di non-rug) e trackka l'**accelerazione** dei primi swap grezzi (Helius) e il match con tag `ai_agent` su X via Grok. 
*   **Ipotesi:** Comprare "pre-pump" (quando il volume è ancora basso ma la narrativa inizia) annulla lo svantaggio della latenza retail. Se entri quando nessuno guarda, 3 secondi di ritardo non ti uccidono.
*   **Scopo:** Trovare 5 token alla settimana con potenziale 5x-10x, comprando in fase di accumulo, non di inseguimento. Meno trade, duration più lunga (ore/giorni, non minuti).

**GIORNO 6-7: Il Reality Check sul Capitale (Il Goal della Mamma)**
*   **Azione:** Fai i conti. 1000 EUR/mese su un conto da 1000 EUR significa fare il +100% al mese. Nessuno al mondo fa +100% al mese in modo stabile. Se la strategia regge e trovi un edge reale del +5% mensile, per arrivare a 1000 EUR/mese servono 20.000 EUR di capitale.
*   **Ipotesi:** Nicolo non ha 20k EUR oggi.
*   **Scopo (Brutale):** La via più veloce per far smettere lavorare la mamma non è "azzeccare il token giusto con 100 EUR". È costruire un **track-record verificato di 3 mesi** (es. +4% net al mese, drawdown sotto il 10%) su un conto paper/live da 200 EUR, e usare quel report per trovare 1 investitore (amico, famiglia, piccolo fondo crypto) che metta 20.000 EUR gestiti da voi con una divisione 50/50 dei profitti. 

**Sintesi per il socio:** 
Stiamo lucidando lo specchietto su una macchina senza motore. Il motore (latenza/velocità) non ci appartiene. Dobbiamo cambiare strada: o andiamo dove la latenza non conta (token very early, narrativa, duration lunga) o accettiamo che il nostro prodotto finale non sia il profitto di 100 EUR, ma un "modulo di segnali" pre-pump da vendere/licenziare a chi i 20k EUR ce li ha già. 

Carta e penna: nei prossimi 7 giorni, ammazziamo il 5m e iniziamo a cacciare i token ai_agent ai primi blocchi della loro vita.

================================================================
Dobbiamo arrivare al goal. Come spingiamo di piu', come ci miglioriamo, una settimana alla volta.
Prossimo meeting profondo: tra 7 giorni. Nel mezzo: il sistema accumula e si allena ogni giorno.
