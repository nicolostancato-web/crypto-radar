# Analisi dataset — 4984 eventi

| Segmento | n | mediana copy | win | hold | batte hold? | EDGE? |
|---|---|---|---|---|---|---|
| ingresso FLAT (runup<10%) | 1096 | **-11.0%** | 13% | -11.8% | SI |  |
| winrate>=60% + FLAT | 323 | **-16.8%** | 20% | -16.8% | no |  |
| provato + FLAT | 225 | **-16.9%** | 16% | -16.0% | no |  |
| non centralizzato (top10<60%) | 2544 | **-18.5%** | 18% | -15.2% | no |  |
| pressione buy (bs_ratio>1.5) | 628 | **-18.6%** | 19% | -17.2% | no |  |
| liquidita' 20k-200k | 1530 | **-25.5%** | 24% | -17.4% | no |  |
| TUTTO (baseline) | 4984 | **-29.3%** | 17% | -23.8% | no |  |
| wallet winrate>=60% | 2260 | **-30.9%** | 20% | -23.1% | no |  |
| token SICURO (authority revocata) | 4702 | **-30.9%** | 15% | -23.7% | no |  |
| wallet provato (closed>=10) | 1088 | **-31.0%** | 21% | -26.4% | no |  |
| coordinato (>=1 altro smart 1h) | 35 | **-31.0%** | 0% | -44.9% | SI |  |
| buy grosso (>=$1000) | 47 | **-31.0%** | 19% | -28.3% | no |  |
| token early (<60min) | 799 | **-33.9%** | 32% | -38.4% | SI |  |
| SICURO + early | 598 | **-40.0%** | 20% | -23.4% | no |  |

## ❌ Nessun edge ancora
Miglior segmento: **ingresso FLAT (runup<10%)** (mediana -11.0%) — ma sotto soglia o non batte il hold.
Servono piu' dati / piu' feature (token_age, holders, authority) per segmenti piu' fini.