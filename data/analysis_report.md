# Analisi dataset — 1084 eventi

| Segmento | n | mediana copy | win | hold | batte hold? | EDGE? |
|---|---|---|---|---|---|---|
| ingresso FLAT (runup<10%) | 206 | **-18.7%** | 17% | -15.8% | no |  |
| provato + FLAT | 75 | **-19.7%** | 16% | -15.0% | no |  |
| winrate>=60% + FLAT | 154 | **-20.5%** | 22% | -16.2% | no |  |
| wallet provato (closed>=10) | 376 | **-31.1%** | 22% | -21.1% | no |  |
| pressione buy (bs_ratio>1.5) | 41 | **-31.1%** | 29% | -10.3% | no |  |
| liquidita' 20k-200k | 348 | **-31.5%** | 24% | -16.0% | no |  |
| TUTTO (baseline) | 1084 | **-31.7%** | 19% | -28.0% | no |  |
| wallet winrate>=60% | 788 | **-31.7%** | 19% | -27.6% | no |  |
| token early (<60min) | 21 | **-40.1%** | 10% | +2.1% | no |  |

## ❌ Nessun edge ancora
Miglior segmento: **ingresso FLAT (runup<10%)** (mediana -18.7%) — ma sotto soglia o non batte il hold.
Servono piu' dati / piu' feature (token_age, holders, authority) per segmenti piu' fini.