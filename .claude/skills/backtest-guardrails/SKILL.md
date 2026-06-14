---
name: backtest-guardrails
description: Regole anti-bias per qualsiasi simulazione di trading/backtest su serie temporali jsonl append-only (prezzo/volume/whale ora-per-ora). USE WHEN si scrive o si modifica logica di entrata/uscita, simulazione P&L, backtester, learner, o si calcolano metriche di performance. SKIP WHEN si tratta solo di raccolta dati (scan/tracking) senza decisioni simulate.
---

# Backtest Guardrails — non illuderti con numeri finti

Il rischio #1 di crypto-radar e' fabbricare un edge che NON esiste (look-ahead, overfit, survivorship).
Un backtest che mostra +70% win-rate quasi sempre sbircia il futuro. Applica SEMPRE questa checklist
quando scrivi o rivedi simulazioni di entrata/uscita o metriche.

## Le 6 regole ferree

1. **POINT-IN-TIME (no look-ahead).** Per decidere un'azione al tempo `t+1`, usa SOLO dati con timestamp `<= t`.
   Mai il prezzo/volume/whale dell'ora futura. Entry onesto = primo check DOPO il segnale, mai sul segnale stesso.

2. **No data leakage nei derivati.** Rolling/medie/momentum devono essere causali: usa `shift(1)` o finestre
   che finiscono a `t`, mai centrate. Il picco di volume/prezzo "del futuro" non puo' entrare nel calcolo a `t`.

3. **Survivorship bias.** Includi i token MORTI (rug, andati a zero, scartati): se guardi solo i sopravvissuti,
   il win-rate e' gonfiato. Nel dataset entra anche cio' che e' fallito prima del tracking.

4. **Walk-forward, mai re-fit retroattivo.** Tara le soglie su una finestra PASSATA, testa su una finestra
   FUTURA mai vista. Niente ottimizzazione delle soglie sugli stessi dati su cui poi misuri la performance.

5. **Costi reali.** Sottrai sempre slippage simulato (su memecoin e' IL costo dominante, non le fee) + fee DEX.
   Un edge che sparisce con -2% slippage non e' un edge. Vedi [[slippage-cost-model]].

6. **Campione sufficiente.** Niente conclusioni sotto ~30 trade conclusi con >=3 runner. Un singolo runner
   distorce tutto. Dichiara sempre n e quanti runner. Distingui PRELIMINARE da SOLIDO.

## Checklist veloce prima di committare una simulazione
- [ ] Ogni decisione usa solo dati <= t? (riguarda gli indici della serie)
- [ ] I derivati sono shiftati di 1? Nessuna finestra centrata o futura?
- [ ] Ci sono i token falliti nel campione (non solo le perle)?
- [ ] Soglie tarate su dati diversi da quelli su cui misuro?
- [ ] P&L al netto di slippage+fee?
- [ ] n e runner dichiarati, e n >= soglia per concludere?

## Reference (solo lettura, NON eseguire nella working dir con le chiavi)
- github.com/kernc/backtesting.py — struttura segnale->ordine senza look-ahead (verificato, ~8k stelle)
- github.com/paperswithbacktest/awesome-systematic-trading — mappa walk-forward / validazione
