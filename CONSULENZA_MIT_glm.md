# GLM-5.2 (n=241)

1) **VERDICT: NO.** 
Base rate is 18% (44/241). Any "profitable" subset (e.g., liq>5k & accel>1.2 = 3 winners in 7 trades) is a multiple-comparisons mirage. Realistic exits + 5% slippage on micro-caps mathematically destroy the fragile paper edge.

2) **Best coincidental rule:** `liq > 5000` & `accel > 1.2`. 
Selects 7 tokens, 43% win-rate, +53% avg paper return. After a 5% slippage haircut and capturing only 50% of `ret_max` (realistic exit), EV is nominally +15% per trade—but with N=7, this is pure noise and fails Bonferroni.

3) **Most predictive variable:** `accel` (bs 5min/1h ratio). 
It captures early momentum breakouts point-in-time safely, but its predictive power is non-monotonic and completely lacks the separation needed to survive live trading costs.

4) Structurally, the system lacks alpha for slow retail. You are trading highly illiquid micro-caps where the edge is entirely eaten by slippage and execution speed. More data won't fix structural slowness.

5) To turn a weak edge real: You need 2,000+ trades for statistical power, sub-second execution (SLOW retail is structurally unable to fill these safely), and automated dynamic trailing stops rather than relying on perfect-timing `ret_max`.