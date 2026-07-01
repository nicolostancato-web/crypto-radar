🎯 MEETING PROFONDO SETTIMANALE — crypto-radar

Ragazzi, e' passato del tempo. Ci ripetiamo la sola cosa che conta: DOBBIAMO ARRIVARE AL GOAL.
La mamma di Nicolo deve poter smettere di lavorare. 1000 EUR/mese. Non un sogno: un piano.

Stato oggi: 1923 token accumulati, 365 runner. Sopravviviamo ma non guadagniamo ANCORA.
Oggi non ci alleniamo soltanto: andiamo NEL PROFONDO. Cosa abbiamo, come spingiamo, come diventiamo
profittevoli, come alziamo la percentuale di successo, come arriviamo al goal.

================================================================
🌍 COSA FUNZIONA NEL MERCATO REALE ADESSO (scan live su X)
================================================================
**Nel 2026 i trader profittevoli su Solana memecoins non sono più i “più veloci a snipare”.** La velocità è diventata trappola: con 30k+ launch al giorno, essere primi significa solo perdere prima. Il vero edge è **filtrazione + sopravvivenza + esecuzione disciplinata**. Ecco cosa fanno di diverso quelli che catturano i 10x reali (non i lottery ticket).

### Segnali on-chain/sociali per entrare PRIMA della folla (non le solite cazzate)
- **Sopravvivenza test run > early sniping**. Non entri a 15-20k. Aspetti che il token superi le prime ore critiche: volume che tiene (non spike isolati), community che resta attiva nei GC/Telegram, incentivi e coordinamento visibili. Solo allora apri.[[1]](https://x.com/funcry/status/2008829881019195689)
- **Relative strength + narrative momentum**. Tracci wallet su Axiom o StalkChain, segui i trader che comprano clean tickers ai bottom quando l’attenzione è altrove, o beta plays del leader del giorno. Non il primo che pompa, ma quello con forza relativa rispetto al mercato.[[2]](https://x.com/watchingmarkets/status/2071184710638670156)
- **Trusted deployers/meta**. Identifichi i deployer con track record reale (non i random). Loro lanciano e mandano, gli altri no. Questo riduce drasticamente i rug.[[3]](https://x.com/haspidox/status/2055584262913486962)
- **Drawdown + supporto**. Filtri: MC 30-350k, età <6h, -50% dal ATH su livello psicologico/supporto. È lì che entrano i bravi, non al breakout verde.[[4]](https://x.com/shehumls/status/2070102361276596674)

Social: entri nei GC prima del pump, osservi comportamento reale (non solo raid), bullposti tu stesso per muovere il tuo bag.[[2]](https://x.com/watchingmarkets/status/2071184710638670156)

### Gestione entrata e uscita (concreta, non teoria)
**Entrata**:
- Mai tutto in una volta. 2-3 tranche o 50% prima + DCA sul dip.
- Solo dopo dip, mai a ATH. Limit orders dove possibile.[[5]](https://x.com/shehumls/status/2070185574976147580)

**Uscita (il punto che fa la differenza)**:
- 20% a 2x → recuperi capitale.
- 20% a 5x → blocchi profitto.
- 60% restante a correre (10x-50x-100x).[[6]](https://x.com/Tradermomike/status/2072157783021994341)
- O variante: initial out a 2-3x, poi “house money” sul resto. Mental SL fisso a -30% (sotto 100k MC può scendere a -40% e rimbalzare, sopra no).[[5]](https://x.com/shehumls/status/2070185574976147580)

Partial profits costanti = non round-tripping life-changing gains. I vincitori vendono, i perdenti guardano il grafico.

### Cosa distingue chi fa 10x da chi perde soldi
- **Selettività estrema** invece di volume di trade. In bassa liquidità sopravvive solo chi è super selettivo e non avido.[[7]](https://x.com/Latuche95/status/2037894692281499711)
- **Una strategia sola, masterizzata**. Non cambi meta ogni giorno. Scegli (es. daily runners, clean bottom, beta plays, bagworking) e la martelli.[[2]](https://x.com/watchingmarkets/status/2071184710638670156)
- **Psicologia blindata**: SOL = munizioni, non soldi del mutuo. Piccoli profitti giornalieri (500-3k/mese) sono vittoria. Gruppi di trading, fast terminal (Axiom), lock profit in USDC/USDT.[[3]](https://x.com/haspidox/status/2055584262913486962)
- **Bagworking vs jeet**. Quelli che tengono e lavorano il meme per settimane (cambiando PF, raidando) battono chi esce al primo +50%.
- **Offramp reale**. I bravi convertono in cash/ETF quando hanno edge, non tengono tutto on-chain per poi perderlo in bear.

In sintesi: 2026 premia chi filtra di più, entra strutturato dopo sopravvivenza, scala parziali aggressivi e ha disciplina psicologica. Chi ancora snipa tutto a 15k o tiene tutto senza parziali, perde. Il mercato ha fatto selezione naturale: ora conta solo l’edge, non la fortuna.

================================================================
📡🔬 TAB 1+2 — DATI & SEGNALI: dove possiamo migliorare (analisi profonda)
================================================================
Ecco l'analisi cruda. Il problema centrale è che state misurando la **fotografia** di un pump (la pressione d'acquisto quando la candela è già verde), ma come retail lento state giocando la **fotografia successiva**, dove i bot e i dev vi passano le bustine.

Il vostro edge sottile c'è (9pt sopra base con `bs1.2-2 & accel>1.2`), ma viene mangiato dal timing e dalle fee. Per portare il win-rate sopra il 30% e la media robusta in territorio positivo, dobbiamo smettere di guardare i token come entità statiche e iniziare a guardare le **dinamiche di esaurimento** e la **qualità strutturale**.

Ecco 4 mosse concrete, testabili immediatamente, in ordine di impatto atteso.

---

### 1. Estrazione: "Time-to-Signal" (L'arma anti-ritardo)
**Dove state sprecando dati:** Avete l'età del token, ma non la state incrociando con il momento in cui scatta il segnale. Un BS ratio > 2 su un token nato da 2 ore ha dinamiche totally diverse da uno nato da 2 giorni.
**L'ipotesi:** I retail lenti non possono comprare l'inizio del pump. Se il segnale `bs1.2-2 & accel>1.2` scatta quando il token ha già fatto +80% o ha 4 ore di vita, state comprando la distribuzione del dev. L'edge reale è nel **primo window**.
**Cosa calcolare:**
*   Estrai `age_at_signal` (in minuti dal primo trade).
*   Estrai `price_change_at_signal` (quanto ha già fatto dalla open al momento del segnale).
**Come testarlo:**
*   Segmenta i vostri 169 trade (`bs1.2-2 & accel>1.2`) in 3 bucket: `age < 60m`, `60m < age < 180m`, `age > 180m`.
*   **Azione:** Scommetto che il win-rate nel bucket `< 60m` è >35%, e nel bucket `> 180m` crolla a <15%. Se è così, la regola d'ingresso diventa: *Segnale valido SOLO se age < 60m e price_change_at_signal < 20%*.

### 2. Estrazione: "Wick Ratio" (La firma dello slippage nascosto)
**Dove state sprecando dati:** Avete le candele 5m ma state solo guardando prezzo/volume. Non state guardando la forma della candela.
**L'ipotesi:** La mediana P&L è -13.4% perché entrate su candele chiuse ultra-rialziste, ma il 5m successivo apre con un gap giù o un picco di volatilità (le classiche "candele a candeliere" con ombra lunga). Stupidi soldi persi per slippage e caccia agli stop.
**Cosa calcolare:**
*   Per la candela 5m in cui scatta il segnale, calcola il `Wick_Ratio = (High - max(Open, Close)) / (High - Low)`.
*   Se il `Wick_Ratio` è alto (es. > 0.3), significa che il prezzo è andato su ma è stato respinto brutalmente prima della chiusura. È un fake pump.
**Come testarlo:**
*   Filtra i vostri trade storici: entri SOLO se il segnale scade su una candela con `Wick_Ratio < 0.2` (cioè chiusa praticamente al top, spinta d'acquisto reale e non finta).
*   **Azione:** Calcolate il nuovo win-rate. Se saliamo al 32-35% reale, abbiamo eliminato i "trap" di liquidità.

### 3. Combinazione: "Quality Filter" (Pluggare l'emorragia dei top10)
**Dove state sprecando dati:** Avete `concentrazione top10` e `rugcheck (insider/lp)` in Tab 1, ma in Tab 3 state testando i ladder SU TUTTO il dataset. State testando uscite su token che matematicamente sono destinati a morire.
**L'ipotesi:** Un BS ratio > 2 su un token dove il top 10 detiene l'80% è una trappola per topin. Non c'è ladder che tenga: il dev svuota e la media robusta va in rosso.
**Cosa calcolare:**
*   Un flag binario: `Safety_Flag = 1` se (top10 < 50% E LP bruciata/lockata), altrimenti `0`.
**Come testarlo:**
*   Applica il `Safety_Flag = 1` al vostro miglior scenario di uscita (`bs>=2.0 + ladder_moon`).
*   **Azione:** La dimensione del campione (n) calerà drasticamente (magari da 169 a 40), ma scommetto che la **mediana** salirà da -13.4% a -5% e la **robusta** diventerà +2% o +3%. Non ci serve volume di trade, ci serve sopravvivenza. Meno trade, ma sicuri.

### 4. Combinazione: "Divergenza multi-timeframe" (Il vero momentum)
**Dove state sprecando dati:** Avete la pressione buy/sell su 5m/1h/6h/24h, ma la state probabilmente valutando in silos. La pressione 5m è rumorosa.
**L'ipotesi:** Un token fa +50% solo se c'è allineamento. Se la 5m è calda, ma la 1h sta già raffreddando, state comprando l'ultimo spike prima del crollo.
**Cosa calcolare:**
*   Un `Momentum_Score = (5m_bs > 1.2) AND (1h_bs > 5m_bs)`. Significa che la pressione oraria è più forte di quella di 5 minuti, quindi il pump è in accelerazione e non in esaurimento.
**Come testarlo:**
*   Incrocia questo `Momentum_Score` con il vostro segnale base `accel>1.2`.
*   **Azione:** Valuta il win rate di questo sotto-insieme. Dovrebbe eliminare i falsi positivi dove la 5m schizza a 3.0 ma la 1h è a 0.8 (classico bot che wash-trading su un token morto).

### Riassunto dell'esecuzione (Cosa fate domani)
1.  Scaricate il dataset, aggiungete le 3 colonne: `age_at_signal`, `Wick_Ratio_candela_segnale`, `Safety_Flag`.
2.  Filtrate i 169 trade di `bs1.2-2 & accel>1.2` per `age < 60m` e `Safety_Flag == 1`.
3.  Ri-calcolate la media robusta con il `ladder_moon`.

Se la media robusta di questo sotto-insieme (anche se ridotto a 30-50 eventi) sale sopra lo 0% reale, avete trovato l'edge per cui la mamma smette di lavorare. Non cercate il 100% di win rate, cercate il 35% di win rate su un set di token che non vi frega a -30% in un minuto.

================================================================
💰 TAB 3 — TRADING: come diventiamo profittevoli (analisi profonda)
================================================================
Niente fronzoli. Hai centrato il problema con una precisione chirurgica: **stiamo applicando la gestione di un asset tecnico (Forex/Azioni) a un asset di attenzione (Memecoin).** 

Le memecoin su Solana non si scalpano con il prezzo, perché il prezzo è una funzione ritardata del flusso di ordini e della manipolazione. Il tuo dato lo conferma: sui token che fanno +10%, catturi -30% del picco. Lo scalping basato sul prezzo in un mercato che fa whipsaws (inversioni violente) del -20% in un minuto ti garantisce di essere sbattuto fuori esattamente prima del pump reale.

Ecco l'analisi profonda e la strategia testabile per uscire da questo stallo.

---

### 1. PERCHÉ LO SCALPING ATTUALE FALLISCE (E PERCHÉ L'INFORMAZIONE VINCE)

Il mercato delle memecoin è guidato da **flussi di attenzione e iniezioni di liquidità**, non da supporti/resistenze.
*   **Il problema del Price Stop/Trailing:** I market maker e bot sanno che i retail mettono stop a -10%/-15% o trailing stretti. Fanno un "wick" (lancio) verso il basso per cacciare gli stop (scuotere i weak hands), assorbire la liquidità, e poi partire per il +200%. Il tuo -13.4% di mediana è la prova che stai finanziando questa caccia allo stop.
*   **Il vantaggio dell'Informazione:** Il prezzo può mentire (può essere manipolato con pochi dollari su pool illiquide), ma la **Pressione d'Acquisto (bs ratio) prolungata** e i **swap grezzi (whale flow)** su base oraria non possono mentire su scala larga. Se usciamo quando il *prezzo* scende, veniamo fottuti. Se usciamo quando l'*informazione* (la pressione buy/sell) inverte, stiamo seguendo i soldi smart.

**Conclusione:** Lo scalping sul prezzo è sbagliato. La gestione della posizione deve essere disaccoppiata dal prezzo a breve termine e ancorata all'informazione.

---

### 2. LA NUOVA STRATEGIA DA TESTARE: "INFO-DRIVEN ASYMMETRIC RIDE"

Questa strategia mira a non farti sbattere fuori dai wicks, garantendo un'esposizione asimmetrica (rischio basso, reward illimitato).

#### A. ENTRATA (Più selettivi, niente FOMO)
Il tuo win rate base è 19%. I migliori segnali portano al 28%. Non abbassiamo la selettività, la alziamo ancora per cercare il 30%+ e ridurre il rumore.
*   **Setup Iniziale:** `bs1.2-2` E `accel>1.2` E `mc_15_60k` (Unisce pressione, momentum e liquidità sufficiente per non essere un rug istantaneo).
*   **Filtro Tempo (Cruciale):** Entra solo se il segnale si verifica nei primi 60-90 minuti di vita del token (eta'). Le memecoin vecchie che si "risvegliano" sono trappole per retail.
*   **Azione:** Entra a mercato. Nessun limite di prezzo, si entra sull'accelerazione.

#### B. GESTIONE E POSITION SIZING (Sopravvivenza)
*   **Position Sizing Fisso (Anti-Kelly):** Kelly è troppo aggressivo per un win rate del 30% con mediana negativa. Usa il **2% fisso del paper account** per trade. Se il conto è 40 EUR, entri con 0.80 EUR. Questo garantisce che non bruci il conto nemmeno con 10 loss di fila (controlliamo il `fragile=False`).
*   **NO STOP-LOSS SUL PREZZO INIZIALE:** Non mettere stop a -10%. Metti uno **Stop-Loss Temporale** + **Stop-Loss di Informazione**:
    1.  *Time Stop:* Se dopo 30 minuti il token non fa almeno +15% dal tuo entry, chiudi a mercato. Il momentum è mancato.
    2.  *Info Stop:* Se la pressione buy/sell (5m o 1h) scende sotto 0.8 (da buy a net sell), chiudi. Ignora il prezzo, guarda il flusso.

#### C. USCITA (Il "Free Ride" Asimmetrico)
Abbandona i ladder statici (vendi a +50%, ecc.). I wicks a -20% ti fermano prima.
Usa il **House Money / Trailing sull'Informazione**:
1.  **Primo Take Profit (Risk-Free):** Quando il token fa +60% dal tuo entry, vendi il 50% della posizione. Hai recuperato l'investimento iniziale + un piccolo profitto. Ora sei in "Free Ride".
2.  **Lascia Correre il Restante (Il Runner):** Sul 50% rimanente, **nessun target di prezzo**. Usa un trailing stop basato *esclusivamente* sull'informazione e candele chiuse (non sui wicks).
    *   *Regola Trailing:* Se la candela 5m o 15m CHIUDE sotto la pressione buy/sell di 1.0 (net sell) per due candele consecutive, O l'accelerazione scende sotto 0.5, chiudi il restante 50%.
    *   *Perché funziona:* Se il token fa +200%, un wick a -30% non ti attiva il trailing se la candele chiude positive o se la pressione d'acquisto resta alta. Cavalchi l'onda finché i bot smettono di comprare.

---

### 3. COME ALZARE IL WIN-RATE E LA "MEDIA ROBUSTA"

*   **Più selettivi o più larghi?** Più selettivi. La coda lunga inganna. Se vai più larghi, aumenti i falsi positivi e bruci capitale nei token che muoiono subito. L'edge del 28% (`bs1.2-2 & accel>1.2`) è solido.
*   **Come alzare il Win-rate reale:** Non cerchiamo di vincere di più (il +50% è fissato dal mercato), cerchiamo di **perdere di meno**. Se il tuo stop temporale a 30 minuti ti fa uscire a -5% invece di aspettare il -15% di default, il tuo P&L medio migliora drasticamente anche senza aumentare la % di token che toccano +50%.

---

### 4. IL TEST DA IMPLEMENTARE SUBITO (PAPER TRADING)

Crea un nuovo setup nel tuo sistema e chiamalo `InfoRide_Strat`. Testalo per i prossimi 50 trade.

**Condizioni di Test:**
1.  **Size:** 2% del conto paper attuale.
2.  **Entry:** `bs1.2-2` AND `accel>1.2` AND `mc_15_60k` AND `eta < 90 min`.
3.  **Chiusura A (Loss/No-pump):** Se dopo 30 min non sei a +60%, chiudi tutto al prezzo attuale. Se prima dei 30 min il `bs_ratio 5m` scende sotto 0.7, chiudi.
4.  **Chiusura B (Protezione):** Se raggiungi +60%, vendi 50%.
5.  **Chiusura C (Runner):** Sul 50% restante, chiudi solo quando 2 candele 15m consecutive chiudono con `bs_ratio < 1.0` o `accel < 0.5`.

### PERCHÉ BATTERÀ LO SCALPING ATTUALE (L'Ipotesi Matematica)
Attualmente prendi +4% sui token che fanno +141% perché esci per volatilità.
Con questa strategia:
*   Sui trade perdenti: Esci per time-stop a circa -5%/-8% (peggio del -1% attuale? No, perché eviti i -13.4% mediani attuali dove tieni troppo a lungo i morenti).
*   Sui trade vincenti: Il 50% viene venduto a +60% (realizzato). Il restante 50% non viene toccato dai w

================================================================
🚀 LA SVOLTA — l'angolo geniale che cambia tutto (pensa come Musk)
================================================================
La diagnosi è brutale e corretta. Fermiamoci sui numeri: la tua "media robusta" migliore è +0.5%. Per fare 1.000 EUR al mese con uno 0.5% di edge per trade, servono 200.000 EUR di capitale rotante mensile. Non li hai. E anche se li avessi, lo slippage su memecoin cancellerebbe quel 0.5% in un nanosecondo. 

L'approccio "retail lento che analizza dati pubblici di memecoin" è morto. Stai cercando di vincere una gara di drag racing con un motorino. SpaceX non ha limato il razzo Falcon 1 per arrivare su Marte: ha cambiato le regole della fisica (atterrare i booster). 

Ecco 3 angoli-svolta radicali, basati su first principles, per arrivare a 1.000 EUR/mese.

---

### SVOLTA 1: Da "Predittori di Token" a "Parassiti di Wallet" (Copy-Trading On-Chain)
**La Premessa Sfidata:** Stai analizzando i token per prevedere il futuro. Sbagliato. I token non hanno futuro, sono lotterie. I wallet sì. Smetti di guardare *cosa* viene comprato, inizia a guardare *chi* compra. 

**Perché potrebbe funzionare:** 
Hai già notato che le balene erano "look-ahead" (compravano durante il pump). Ma lì dentro c'è un sottogruppo di wallet che *non* è look-ahead: i veri snipers, insider e dev che comprano a T-0 (blocco di creazione) o prima del listing. Se un wallet ha fatto 3x su 10 token appena creati, non è fortuna, è un'infrastruttura (MEV, bot di sniffing, o insider info). Copiare in tempo reale chi vince sistematicamente elimina il problema dell'uscita: vendi quando vende lui. Ti trasformi da trader a "parassita automatizzato".

**Cosa servirebbe:**
Un bot che monitora Helius (RPC di Solana) via WebSocket per i swap in tempo reale. Niente più candele da 5 minuti (5 minuti nel casino delle memecoin sono 5 vite). Parliamo di secondi.

**Esperimento a €0 (Validazione in 7 giorni):**
1. Prendi i 365 "runner" che hai tracciato.
2. Scarica la cronologia delle transazioni (con Helius) dei primi 5 minuti di vita di questi token.
3. Trova i wallet che hanno comprato *entrambi* almeno 3 di questi runner nei primi 2 minuti dalla creazione (filtrando i wallet che hanno poi fatto dump istantaneo). 
4. Se trovi un cluster di 5-10 wallet "santi" che sono sempre in profitto, tracciali in tempo reale per una settimana su Telegram. Se vedi che comprano e i token salono del +30% entro 10 minuti, hai trovato l'edge. Non devi analizzare più un cazzo, devi solo copiare loro.

---

### SVOLTA 2: Vendi i Badili (Il Pivot SaaS/Data-as-a-Service)
**La Premessa Sfidata:** Vuoi fare 1.000 EUR/mese tradando un conto da 100-400 EUR. Fisicamente impossibile senza giocarsi d'azzardo al 100% (e bruciare i conti). Ma hai costruito un'infrastruttura pazzesca: tracci 1923 token, fai rugcheck, calcoli la pressione buy/sell su 4 timeframe, integri Grok, DexScreener, GeckoTerminal. Questo *sistema* vale più dei trade che genera. 

**Perché potrebbe funzionare:**
Nel 1849 chi faceva i soldi non erano i cercatori d'oro, ma chi vendeva le pale. Nel mercato delle memecoin, ci sono migliaia di "degens" su Telegram/X che tradano a mano o fanno copy-trading e hanno un disperato bisogno di dati filtrati. 1.000 EUR/mese = 20 abbonati da 50 EUR/mese a un tuo bot di segnali premium. Sposti il rischio dal mercato dei token al mercato del software.

**Cosa servirebbe:**
Il tuo motore attuale, ma con un'interfaccia utente. Un bot Telegram che prende i tuoi KPI (es. `bs1.2-2 & accel>1.2`) e li spara in un canale privato a pagamento.

**Esperimento a €0 (Validazione in 14 giorni):**
1. Apri un canale Telegram pubblico gratuito: "CryptoRadar - Memecoin BS Pressure Tracker".
2. Configura il tuo sistema per sparare lì i segnali in tempo reale (solo i migliori, es. `bs>=2.0`).
3. V

================================================================
🧠 LA SINTESI — IL PIANO PER ARRIVARE AL GOAL
================================================================
Ecco l'analisi spietata e il piano d'azione. Niente giri di parole, guardiamo i numeri per quello che sono.

### I 3 PUNTI DEBOLI PIU' GRAVI (Il muro che ci sta davanti)

**1. Siamo l'exit liquidity dei bot più veloci (Il problema Latenza/Dati)**
Il segnale si basa sulla "pressione d'acquisto" (bs ratio) su candele 5-min. Se un token fa +50% e noi vediamo il bs ratio salire, è già tardi. Noi compriamo *dopo* che i bot istituzionali/MEV hanno già spinto il prezzo e stanno posizionando le sell limit. Il fatto che la "mediana P&L giorno-su-giorno" sia costantemente tra -10% e -14% significa che nella maggior parte dei trade entriamo esattamente vicino al picco locale. I dati pubblici (DexScreener/GT) hanno un ritardo intrinseco. Su candele 5m, un ritardo di 10 secondi ti mangia l'edge.

**2. L'illusione della "Media Robusta" a 0.5% (La matematica non scala)**
Il nostro meglio è `bs>=2.0 + ladder_moon` con una media robusta dello 0.5%. Questo numero è un'illusione ottica. Significa che se investiamo 100 EUR, ne recuperiamo 100.5. Ma non stiamo calcolando l'impatto reale delle fee, del gas e soprattutto dello *slippage* sulle uscite a scaglioni. Inoltre, abbiamo un win rate del 35% con una mediana del -13.4%. Questo significa che perdiamo 6.5 volte su 10, e quando perdiamo, perdiamo il 13%. Per pareggiare col -13.4% fisso, il 35% di trade vincenti deve generare un +24.8% medio. La matematica è appesa a un filo: basta una minima variazione dello slippage per mandare il conto in rosso.

**3. La sindrome dell'"zombie account" (Falsa sopravvivenza)**
Il conto paper è a 39.97 EUR. Non stiamo sopravvivendo, stiamo sanguinando a morte. Passare da 100 a 40 EUR significa un drawdown del 60%. Per tornare a 100 EUR serve un +150%, non un +60%. Chiamarlo "fragile=False" solo perché non è andato a zero è pericoloso. Stiamo martingalando virtualmente la psicologia: continuiamo a scambiare con un capitale decimato, riducendo le dimensioni, rendendo il recupero matematicamente impossibile senza un cambio di paradigma.

---

### QUANTO SIAMO VICINI AL GOAL (1000 EUR/mese)?

**Siamo a chilometri di distanza. Facciamo i conti reali.**
Per fare 1000 EUR/mese con un capitale di trading sicuro (es. 10.000 EUR), serve un rendimento netto del 10% mensile composto.
Con una media robusta lorda dello 0.5% a trade, per fare il 10% servono 20 trade perfettamente consecutivi in pareggio/lieve profitto. Ma con un win rate del 35% e una mediana del -13.4%, il rischio di ruin (andare a zero) prima di raggiungere il 10% è altissimo. 
La mamma di Nicolo non smetterà di lavorare con questo edge, punto. L'edge è troppo sottile e la frizione del mercato (slippage, fee, latenza) lo sta mangiando vivo.

**L'alternativa onesta se i dati pubblici non bastano:**
I dati pubblici 5m non bastano per il *trading direzionale ad alta frequenza* su meme coin. O troviamo un modo per pagare dati privati (Helius websocket grezzo) per leggere le tx *prima* che finiscano nella candela, oppure **cambiamo angolo**.
L'angolo più onesto e realistico oggi non è fare i trader, ma **costruire il radar e venderlo (SaaS) o usarlo per sniping manuale su timeframe maggiori (1h/4h)**. Se il radar trova il 19% dei runner, c'è gente disposta a pagare 50 EUR/mese per avere questi alert su Telegram. 20 clienti = 1000 EUR/mese. Zero rischio di trading, zero slippage. L'edge non è nel trade, è nell'informazione.

---

### PIANO PRIORITIZZATO (5 Giorni - Azioni Brutali)

Se insistiamo per 5 giorni a salvare l'edge di trading, dobbiamo smettere di testare varianti di uscita e attaccare il problema alla radice: il timing d'ingresso e la gestione del capitale.

**Giorno 1: Drop dei timeframe 5m e test su 1H/4H (Esperimento Latenza)**
*   *Azione:* Stop totale ai trade su candele 5m. Ricalcoliamo il segnale `bs>=1.5` ma sulle candele a 1 ora. Se la pressione d'acquisto sopravvive su 1h, abbiamo più tempo per entrare, lo slippage relativo si riduce e i bot HFT fanno meno danni.
*   *Esperimento:* Backtest su `bs>=1.5` (1h candle) con uscita fissa a +20% o -10%. Vogliamo vedere se la mediana P&L migliora rispetto al -13.4% attuale.

**Giorno 2: Kill-switch sul Drawdown (Protezione Capitale)**
*   *Azione:* Implementare una regola ferrea nel paper trading: se il conto scende sotto i 30 EUR (dal 100 iniziale), il bot SI SPEGNE. Zero trade per 48h. L'attuale sistema continua a girare a 40 EUR, accumulando noise. Non stiamo testando strategie, stiamo testando quanto in fretta perdiamo soldi.

**Giorno 3: Analisi del "Time-to-Peak" (Il vero problema dell'uscita)**
*   *Azione:* Scarichiamo i dati dei 169 trade del segnale migliore (`bs1.2-2 & accel>1.2`). Per ogni trade, calcoliamo: quanti minuti/candele ci sono voluti dal segnale di ingresso al picco assoluto? Se il 90% dei picchi avviene entro 2 candele (10 min), le uscite a scaglioni (ladder 5x, 10x) sono una pura illusione. Non prenderemo mai il 5x. Dobbiamo sapere quanto dura *fisicamente* il nostro edge.

**Giorno 4: Simulazione Slippage Reale (Stress Test)**
*   *Azione:* Modifica il backtester. Su ogni uscita a scaglioni, sottrai forzatamente un 3% di slippage medio + 0.5% di fee. Ricalcola la "media robusta" del `ladder_moon`. Scommettiamo che quel 0.5% positivo diventa istantaneamente -3%? Se è così, abbiamo la prova matematica che il modello è morto.

**Giorno 5: La decisione del Socio (Go/No-Go)**
*   *Azione:* Guardiamo i risultati dei giorni 1 e 4. Se l'1h timeframe non porta la mediana in positivo *incluso* lo slippage simulato, dichiariamo morto il trading algoritmico su 5m con dati pubblici.
*   *Pivot immediato:* Trasformiamo il bot in un alert-system per Nicolo. Il bot non compra, manda un messaggio su Telegram: "Token X ha bs ratio > 2 e accel > 1.2". Nicolo (o un cliente) decide manualmente se fare swing trade su TF più alti. Iniziamo a disegnare il modello SaaS. 20 utenti a 50€ = Mamma a casa.

La disciplina non è continuare a sbattere la testa su un muro di matematica avverso. La disciplina è sapere quando il muro è troppo duro e usare la scala che abbiamo appena costruito (il radar).

================================================================
Dobbiamo arrivare al goal. Come spingiamo di piu', come ci miglioriamo, una settimana alla volta.
Prossimo meeting profondo: tra 7 giorni. Nel mezzo: il sistema accumula e si allena ogni giorno.
