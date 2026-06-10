# Analisi dataset — 862 eventi

| Segmento | n | mediana copy | win | hold | batte hold? | EDGE? |
|---|---|---|---|---|---|---|
| ingresso FLAT (runup<10%) | 159 | **-18.6%** | 14% | -18.6% | no |  |
| provato + FLAT | 50 | **-19.6%** | 6% | -18.7% | no |  |
| winrate>=60% + FLAT | 110 | **-20.5%** | 20% | -22.1% | SI |  |
| wallet provato (closed>=10) | 260 | **-23.2%** | 19% | -25.2% | SI |  |
| liquidita' 20k-200k | 228 | **-31.5%** | 21% | -22.9% | no |  |
| wallet winrate>=60% | 576 | **-31.7%** | 17% | -32.1% | SI |  |
| TUTTO (baseline) | 862 | **-32.0%** | 17% | -32.1% | SI |  |

## ❌ Nessun edge ancora
Miglior segmento: **ingresso FLAT (runup<10%)** (mediana -18.6%) — ma sotto soglia o non batte il hold.
Servono piu' dati / piu' feature (token_age, holders, authority) per segmenti piu' fini.