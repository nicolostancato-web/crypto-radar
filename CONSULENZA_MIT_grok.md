# grok (re-run MIT, n=241)

**NO**

No repeatable edge survives the data. 44 runners out of 241 tokens is an 18% base rate; after 5–10% slippage on micro-caps and realistic (non-perfect) exits, even a filter that lifts the rate to 30–35% produces negative expectancy. Every candidate rule I tested (low top10, positive np1h/bs, accel>1, heat>5, whale_early, arena=ai_agent, nobs 20–60, etc.) either collapses under missing values, selects <10 tokens, or fails a mental Bonferroni adjustment for the number of slices examined. The single 20 200× row is explicitly a glitch and does not change the distribution.

The most predictive variable that can be observed at entry is **top10** (concentration). Lower top10 shows a mild positive association with runners, but the lift is too small, too noisy, and too often missing to trade.

Structurally missing: forward-looking volume/pressure features that actually move price in the first minutes, plus any reliable liquidity or holder-quality signal. More rows of the same type will not fix this; only richer, lower-latency on-chain features or a larger, cleaner sample with verified fills would.

A weak edge would require at minimum: (1) tick-level or 1-min bars instead of hourly aggregates, (2) actual executed prices rather than first-check prices, and (3) out-of-sample confirmation on the next 300–500 tokens. None of those exist here.

Final memo: pass on the strategy. The data does not contain a tradable signal for a slow retail player.