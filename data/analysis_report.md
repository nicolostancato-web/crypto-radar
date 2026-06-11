# Analisi dataset — 5611 eventi

| Segmento | n | mediana copy | win | hold | batte hold? | EDGE? |
|---|---|---|---|---|---|---|
| provato + FLAT | 319 | **-16.1%** | 18% | -15.7% | no |  |
| ingresso FLAT (runup<10%) | 746 | **-17.9%** | 17% | -18.6% | SI |  |
| winrate>=60% + FLAT | 365 | **-17.9%** | 22% | -18.5% | SI |  |
| non centralizzato (top10<60%) | 2058 | **-23.7%** | 23% | -17.6% | no |  |
| pressione buy (bs_ratio>1.5) | 554 | **-31.0%** | 20% | -23.8% | no |  |
| wallet provato (closed>=10) | 1580 | **-31.0%** | 21% | -26.4% | no |  |
| coordinato (>=1 altro smart 1h) | 20 | **-31.0%** | 0% | -30.7% | no |  |
| buy grosso (>=$1000) | 79 | **-31.0%** | 19% | -28.2% | no |  |
| wallet winrate>=60% | 3443 | **-31.1%** | 19% | -29.0% | no |  |
| liquidita' 20k-200k | 1211 | **-31.5%** | 22% | -17.8% | no |  |
| TUTTO (baseline) | 5611 | **-31.7%** | 17% | -30.6% | no |  |
| token SICURO (authority revocata) | 5545 | **-31.8%** | 18% | -30.6% | no |  |
| token early (<60min) | 1387 | **-37.9%** | 26% | -39.7% | SI |  |
| SICURO + early | 1386 | **-37.9%** | 26% | -39.7% | SI |  |

## ❌ Nessun edge ancora
Miglior segmento: **provato + FLAT** (mediana -16.1%) — ma sotto soglia o non batte il hold.
Servono piu' dati / piu' feature (token_age, holders, authority) per segmenti piu' fini.