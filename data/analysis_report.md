# Analisi dataset — 334 eventi

| Segmento | n | mediana copy | win | hold | batte hold? | EDGE? |
|---|---|---|---|---|---|---|
| provato + FLAT | 32 | **-21.2%** | 6% | -19.2% | no |  |
| wallet provato (closed>=10) | 170 | **-21.5%** | 19% | -25.6% | SI |  |
| ingresso FLAT (runup<10%) | 66 | **-22.7%** | 14% | -23.9% | SI |  |
| winrate>=60% + FLAT | 43 | **-29.4%** | 19% | -37.7% | SI |  |
| TUTTO (baseline) | 334 | **-31.6%** | 20% | -38.5% | SI |  |
| liquidita' 20k-200k | 125 | **-31.6%** | 18% | -26.6% | no |  |
| wallet winrate>=60% | 190 | **-32.1%** | 19% | -40.8% | SI |  |

## ❌ Nessun edge ancora
Miglior segmento: **provato + FLAT** (mediana -21.2%) — ma sotto soglia o non batte il hold.
Servono piu' dati / piu' feature (token_age, holders, authority) per segmenti piu' fini.