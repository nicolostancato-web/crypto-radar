# Analisi dataset — 1535 eventi

| Segmento | n | mediana copy | win | hold | batte hold? | EDGE? |
|---|---|---|---|---|---|---|
| ingresso FLAT (runup<10%) | 281 | **-18.7%** | 19% | -16.9% | no |  |
| provato + FLAT | 97 | **-19.7%** | 18% | -16.4% | no |  |
| winrate>=60% + FLAT | 206 | **-21.7%** | 23% | -19.9% | no |  |
| pressione buy (bs_ratio>1.5) | 77 | **-31.2%** | 22% | -14.3% | no |  |
| wallet provato (closed>=10) | 553 | **-31.2%** | 22% | -25.2% | no |  |
| liquidita' 20k-200k | 480 | **-31.5%** | 23% | -18.2% | no |  |
| TUTTO (baseline) | 1535 | **-31.6%** | 19% | -26.7% | no |  |
| wallet winrate>=60% | 1118 | **-31.7%** | 20% | -27.6% | no |  |
| token early (<60min) | 43 | **-41.8%** | 12% | +8.4% | no |  |

## ❌ Nessun edge ancora
Miglior segmento: **ingresso FLAT (runup<10%)** (mediana -18.7%) — ma sotto soglia o non batte il hold.
Servono piu' dati / piu' feature (token_age, holders, authority) per segmenti piu' fini.