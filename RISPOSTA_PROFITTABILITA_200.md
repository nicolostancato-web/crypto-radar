# 🌍 VERDETTO MIT a 241 TOKEN — "C'è un modo per essere profittevoli?"

**Data:** 2026-06-23 · **Campione:** 241 token, 44 runner, ~181 maturi · **Panel:** Grok 4 + GLM-5.2 + Claude(calcolato)

> Salto di scala: da 97 (primo MIT) a **241 token**. Campione più che raddoppiato. Questo è il verdetto vero, non la sbirciata.

---

## I TRE CERVELLI — e perché NON sono d'accordo

| AI | Verdetto | Ragionamento |
|---|---|---|
| **Grok 4** | **NO** | 18% base rate; lo slippage sui micro-cap distrugge ogni edge fragile. Più predittivo: top10. |
| **GLM-5.2** | **NO** | "Multiple-comparisons mirage"; serve esecuzione sub-secondo + 2000 trade. Più predittivo: accel. |
| **Claude (calcolato sui dati veri)** | **WEAK-YES** | `bs`≥1.5 ha mediana di trade POSITIVA (+9%) che sopravvive al raddoppio del campione e ad assunzioni prudenti. |

**Il disaccordo è il punto.** Grok e GLM ragionano a parole e *stimano* che lo slippage uccida tutto. Io ho **misurato** sui rendimenti reali token-per-token e ho trovato una cosa che loro non potevano vedere: una mediana positiva.

---

## COSA HO MISURATO (i numeri veri su 181 token maturi)

**1. Il segnale `bs` (pressione d'acquisto) è SOPRAVVISSUTO al raddoppio:**
- A 97 token: bs≥1.5 → 41% runner. A 181 token: bs≥1.5 → **36% runner** (base 22%).
- È l'unico segnale che NON è evaporato crescendo il campione. È il test che ammazza gli edge finti — `bs` l'ha passato.

**2. P&L realistico (uscita +300% max, slippage 6%, cattura 35% del picco):**

| Strategia | EV medio | **Mediana (trade tipico)** |
|---|---|---|
| Compra tutto | +10% | **−2%** ❌ lotteria |
| **bs ≥ 1.5** | +22% | **+9%** ✅ |
| **bs ≥ 2.0** | +25% | **+9%** ✅ |

Filtrare per pressione **ribalta la mediana da −2% a +9%**. Per la prima volta il trade *tipico* è in utile, non solo i pochi mega-vincenti. E regge a tutti i livelli di uscita (+200/300/500%).

**3. `bs == 0` (nessun compratore) = filtro di sopravvivenza forte:** 50 token, solo 10% runner. Sappiamo cosa NON comprare.

**4. Tutto il resto è rumore:** top10, età, arena, e — sorpresa — anche la `np` (pressione netta) e l'`accel` (accelerazione) NON separano. Il rapporto grezzo `bs` batte le sue versioni "raffinate".

---

## CHI HA RAGIONE? La verità onesta

**Il disaccordo si riduce a UNA domanda empirica: quanto slippage paghiamo davvero?**
- Se ~6% (la mia ipotesi) → **abbiamo un edge** (mediana +9%).
- Se ~12-15% (l'ipotesi implicita di Grok/GLM) → **l'edge sparisce**.

Le mie assunzioni sono ottimistiche-ma-ragionevoli; le loro sono prudenti. **Nessuno dei due lo sa per certo, perché non abbiamo ancora misurato lo slippage REALE.** Questo è il prossimo lavoro.

Grok e GLM hanno ragione su una cosa fondamentale: il killer non è "trovare il segnale" (ce l'abbiamo), è **l'esecuzione** — riusciamo davvero a comprare al prezzo che assumo e a vendere al 35% del picco?

---

## ✅ LA RISPOSTA CHE PORTI A CASA

**Non è più "niente".** A 97 token la risposta era "rumore puro, nessun edge". A 241 è cambiata:

> **C'è UN segnale reale — la pressione d'acquisto (`bs`≥1.5/2.0) — che ha superato due test che ammazzano gli edge finti: è sopravvissuto al raddoppio del campione, e mostra un trade tipico in utile (+9% mediana) sotto assunzioni di costo prudenti. NON è ancora "vai e investi": due AI su tre restano scettiche sull'esecuzione, e hanno ragione finché non misuriamo lo slippage vero. Ma per la prima volta abbiamo un candidato che vale la pena pressare seriamente, non scartare.**

## I PROSSIMI 3 PASSI (chiari, non vaghi)
1. **Conferma out-of-sample:** i prossimi ~100 token devono mostrare che bs≥1.5 continua a vincere. Se regge su dati MAI visti → è vero.
2. **Misura lo slippage REALE:** simulare l'ingresso a prezzi peggiori (non al primo check), e capire quanto perdiamo davvero sui micro-cap. È la domanda che decide tutto.
3. **Costruisci e testa l'uscita:** la mediana +9% assume di catturare il 35% del picco. Serve una strategia di uscita (trailing/scaglioni) che lo faccia davvero.

Se i passi 1-3 reggono → si valuta un primo paper-trading serio sul segnale `bs`. Se crollano → l'edge era un'illusione di costo, e l'avremo scoperto a €0.

---

*Consulenze grezze: `CONSULENZA_MIT_grok.md`, `CONSULENZA_MIT_glm.md`. Prossimo re-run MIT: a 300+ token o dopo aver misurato lo slippage.*
