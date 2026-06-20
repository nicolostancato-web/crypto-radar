# grok — profittabilita dei dati (2026-06-20)

**NO**

No repeatable edge survives the data. With only 22 runners in 97 samples, extreme outcome variance, heavy missingness, and 2–10 % real slippage, every apparent pattern collapses under even mild scrutiny or a single Bonferroni adjustment.

**Why nothing works**  
- Simple univariate cuts (low age, high bs, low top10, high vol1h, memecoin arena, whale_early > 0, etc.) each produce win-rates of 25–40 % at best and usually < 30 % once the glitch row is neutralized.  
- Any multi-feature rule that reaches ~50 % win-rate selects ≤ 8–10 tokens and is driven by 2–3 observations; removing any one of them drops performance below break-even after slippage.  
- The single strongest point-in-time variable (bs) still yields an AUC barely above 0.55 and loses all significance once age and liquidity are controlled for.

**What is missing**  
We lack (a) a tight enough entry-time proxy for actual execution price, (b) volume or order-book depth at the exact signal minute, and (c) enough positive examples to separate signal from the heavy right-tail noise that defines these markets. Ten times more tokens observed under identical rules would be the minimum starting point to test whether any of the current hints are real.

No filter on this table produces positive expectancy after realistic costs and multiple-testing correction.