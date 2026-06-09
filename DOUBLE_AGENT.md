# DOUBLE AGENT — protocollo (consulto cross-AI)

## L'idea
Un prompt fatto BENE a un'altra AI rende molto più di una domanda diretta. Quindi:
Claude scrive il prompt-bomba → l'utente lo incolla in un'ALTRA AI (ChatGPT/GPT-5) → salva la
risposta in TXT → la ridà a Claude → Claude ne estrae l'oro e si agisce. Diversità di modello =
prospettiva diversa = idee/errori che un solo modello non vede.

## Trigger
Quando l'utente dice **"double agent <argomento>"** (o "facciamo un double agent"), Claude:

1. **Genera un PROMPT MASSIVO e ben ingegnerizzato** per l'altra AI, su misura per:
   - il ruolo da far assumere all'altra AI (es. "senior quant on-chain, brutalmente onesto")
   - lo STATO ATTUALE reale del progetto (dati, numeri, cosa funziona/non funziona)
   - la domanda specifica (es. "trova 10 strategie/analisi diverse, con pro/contro e come implementarle")
   - il formato di risposta voluto (concreto, formule, soglie, niente fuffa) + "sii brutale"
2. **Salva il prompt** in un file `PROMPT_<argomento>.txt` nella cartella del progetto.
3. L'utente lo **incolla in ChatGPT** (modello più potente disponibile), salva la risposta in `.txt`.
4. L'utente **ridà il TXT** a Claude.
5. Claude **legge, filtra, distilla** solo i consigli applicabili (scarta la fuffa) e li salva in
   `CONSULENZA_<argomento>_<data>.md`, poi propone le azioni.

## Regole
- **Manuale di default** (usa il ChatGPT Plus dell'utente = gratis, qualità GPT-5 vera).
- **Auto (Claude chiama l'API di un'altra AI) SOLO se**: c'è una OpenAI/other API key configurata
  E un budget cap esplicito (regola CFO). Non usare l'API Anthropic per il double agent: stessa
  famiglia = nessuna prospettiva diversa.
- Il prompt deve essere **autosufficiente** (l'altra AI parte da zero contesto): includere sempre
  lo stato attuale con numeri reali, non riferimenti vaghi.
- Claude resta il filtro: la risposta dell'altra AI è materiale grezzo, non vangelo. Si prende solo
  ciò che è applicabile e onesto.

## Storico
- 2026-06-05: primo double agent (strategia smart-money) -> PROMPT_CHATGPT.txt ->
  CONSULENZA_GPT_2026-06-05.md. Esito: ottimo, ha guidato i punti 1-3 + il pivot whale.
