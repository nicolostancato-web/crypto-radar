# METODO ENTRATA / USCITA — come decidiamo e come impariamo

> Documento operativo. Risponde alle 3 domande: come entro, come esco, cosa loggo per imparare.
> Sintesi del nostro ragionamento + consulenza Grok (CONSULENZA_metodo_entrata_uscita.md, 2026-06-13)
> + dati reali del sistema (31 trade paper). Principio: niente stop fissi, si decide su SEGNALI DI STATO.

## Il problema che abbiamo (dai dati, non a parole)
Entriamo TARDI. Le perle, comprate al segnale, rendono -26% mediano (gli scartati -1.7%): becchiamo i
token quando il volume e' GIA' esploso (eta' 27-55h) = siamo sul top, poi ritracciano. Le uscite su
segnale (volume) battono gli stop fissi (-1% vs -3%), ma finche' l'entrata e' tardiva nessuna uscita salva.

---

## 1) COME DETERMINO L'INGRESSO (evitare il top)
Non basta "perla + volume forte" (quello e' gia' tardi). Serve cogliere l'IGNIZIONE, non l'esaurimento.
**Regola d'ingresso (soglie di partenza da testare):** entra se almeno 4 di queste sono vere:
- eta' token **< 8h** (giovane, non gia' corso)
- **accelerazione** volume 1h **≥ +80%** vs l'ora precedente (la DERIVATA, non il livello assoluto)
- buy/sell ratio 1h **≥ 2.8** (compratori dominano)
- whale (top10) in **acquisto netto** nelle ultime 2h (entrano, non escono)
- hype X **non eccessivo**: menzioni **< ~120/h** (troppo hype = sei gia' al top) + sentiment compratori
- **fdv < 650k** e **liquidita' > 45k** (ancora piccolo ma scambiabile)

Chiave: la **derivata del volume** e le **whale che ENTRANO** distinguono "sta partendo" da "gia' pumpato".

## 2) COME DETERMINO L'USCITA (su segnale, mai stop fisso)
Una volta entrato, monitoro lo STATO ogni ora ed esco quando l'hype/struttura si rompe:
- **Volume svanisce:** vol 1h scende **< 35%** del picco assoluto raggiunto → esci (l'onda e' finita)
- **Whale distribuiscono:** top10% supply **sale ≥ +1.8%** in 2h consecutive → esci (ti stanno scaricando)
- **Flusso si inverte:** buy/sell ratio 1h **< 1.2** per 2 ore consecutive → esci (i compratori mollano)

Perche' NON stop fissi: in questo mondo un -30% e' rumore normale dentro una corsa; uscire a soglia fissa
ti fa vendere il dip e perdere il runner. Si esce quando lo STATO (volume/whale/flusso) si deteriora.

## 3) QUALI PARAMETRI LOGGO OGNI ORA (per imparare entry+exit)
Per ogni token "in cui sono entrato" (= tracciato), ogni ora salvo:
**On-chain (✅ = gia' loggato dal tracker):**
- ✅ prezzo, fdv, liquidita'
- ✅ volume 1h, volume 24h
- ✅ buys 1h, sells 1h, buy/sell ratio
- ✅ top1% supply, top10% supply, holders (le WHALE nel tempo, via Helius su Solana)
- 🔣 whale netflow 1h/2h → DERIVATO dagli snapshot consecutivi di top10 (non serve loggarlo a parte)
- 🔣 accelerazione volume → DERIVATA da vol1h consecutivi

**Social per token (❌ non ancora — costoso: 1 query Grok per token per ora):**
- post/h su X del token, sentiment ratio, KOL mentions
- Per ora usiamo il VOLUME on-chain come proxy dell'hype (gratis). Social-per-token = step futuro a pagamento.

**Da scartare (rumore):** market cap totale, holder count grezzo senza contesto, tweet lifetime, prezzo
DexScreener senza il resto dello stato.

## 4) COME IMPARO (backtest onesto, auto-allenamento)
- Ho gia' la serie storica per token (track.jsonl, ricca da 2026-06-13). Su di essa il sistema, ogni ora,
  testa le regole entry/exit sopra e misura cosa avrebbero reso.
- **No look-ahead:** per decidere entry/exit al tempo t+1 si usano SOLO dati fino a t. Mai usare il picco
  di volume o il flusso whale "del futuro".
- **Auto-allenamento:** ogni ciclo il learner si chiede "le soglie attuali rendono? quale regola d'uscita
  vince? entro troppo tardi?" e propone aggiustamenti (decide l'umano prima di toccare config).

## 5) GREEN DEEP TRACKING — il cuore dell'apprendimento (indicazione Nicolo, 2026-06-13)
Quando un token diventa **GREEN** (perla: volume alto + whale dentro, passa il filtro), da quel momento
inizia un tracking PROFONDO e PROLUNGATO — solo per le green, non per le red:
- **Finestra lunga:** green seguite per **5 giorni** (red solo 48h). Una green accumula la sua storia
  completa ora per ora finche' resta viva, poi quando torna red la parcheggiamo MA con tutto lo storico.
- **Tanti attributi ogni ora:** prezzo, fdv, liq, volume 1h/24h, buys/sells, buy/sell ratio, top1%/top10%/
  holders (whale). + derivati: accelerazione volume, whale netflow. + (a pagamento, da attivare) engagement X.
- **Lo studio:** con la storia completa di 6-10 green in una settimana, si capisce DOVE si entrava e DOVE
  si usciva, e quali attributi muovevano il prezzo (es. "partiva con 1 whale -> 3 whale -> prezzo sale ->
  torna 1 whale -> scende"). Il prezzo non si legge col +30/-40 fisso: una green puo' fare -50% e poi x5.

## 6) SOGLIE FLESSIBILI — il sistema si auto-corregge
Tutte le soglie di questo metodo (l'80% di accelerazione, il 35% di volume, il 2.8 di buy/sell...) sono
PUNTI DI PARTENZA, non verita'. Ogni X ore il sistema si auto-allena: testa le soglie sui dati green
accumulati, vede cosa avrebbe reso, e le AGGIUSTA. Magari scopre che l'accelerazione giusta non e' +80%
ma +50%, o che si puo' temporeggiare finche' le whale restano. La regola evolve coi dati. Decide l'umano
prima di applicare in "produzione", ma la proposta di nuove soglie la genera il sistema da solo.

## 7) ATTRIBUTI DA LOGGARE PER LE GREEN (deep agent Grok, 2026-06-13)
Risposta alla domanda "quali attributi accumulare ogni ora per imparare entry/exit".
Fonte: CONSULENZA_attributi_green.md. Legenda: ✅ gia' loggato grezzo · 🔣 derivato dagli snapshot (gratis,
si calcola in analisi) · 💸 a pagamento (Grok per-token).

**I 6 NON-NEGOZIABILI secondo Grok:**
1. Buy/Sell ratio 1h + unique buyers — ✅ ho buys/sells & ratio (unique buyers: proxy, Helius non li conta facile)
2. Whale netflow 1h (wallet >0.5% supply) — 🔣 derivo dai top10 consecutivi (ho top10/top1 ogni ora)
3. **Posts/ora su X (velocity)** — ✅ ATTIVO (green_engagement.py, ogni 4h, cap 5 green). Grok: "anticipa il volume di 1-3h".
4. Top10% supply delta 1h — 🔣 derivo (ho top10_pct ogni ora)
5. Holder growth rate 1h — 🔣 derivo (ho holders ogni ora; limite: Helius campiona ~top20, non il totale esatto)
6. Volume 1h momentum (vol1h / vol1h precedente) — 🔣 derivo (ho vol_1h ogni ora)

**Quindi: 5 su 6 must-have sono GIA' coperti (grezzo o derivato, gratis). Manca solo il social (posts/ora).**

**Derivati gratis che calcoleremo in analisi (dai grezzi gia' loggati):**
price change 1h/4h/12h, volatilita' realizzata, volume momentum & acceleration, top10 delta, whale netflow,
holder growth, buy-ratio acceleration, liquidity delta. — tutti dagli snapshot orari, nessun costo.

**A pagamento (Grok per-token, da decidere CFO):** posts/ora, KOL mentions 1h, follower reach.

**RUMORE da NON loggare (Grok):** holders totali assoluti (conta il delta), sentiment del singolo tweet,
fdv assoluto, market-cap rank, membri Telegram/Discord, "hype score" generico non basato su velocity.

## Stato implementazione
- ✅ Tracker esteso: logga tutti i parametri on-chain sopra, ogni ora (whale incluse).
- ✅ Simulatore uscite su segnale (volume) + confronto con le fisse → su dashboard.
- 🔜 Backtest della regola d'INGRESSO di Grok (serve qualche ora di serie whale, parte ora).
- 🔜 Social-per-token (hype X nel tempo) = step a pagamento, da valutare CFO.
