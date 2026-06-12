# Analisi dataset — 9611 eventi

| Segmento | n | mediana copy | win | hold | batte hold? | EDGE? |
|---|---|---|---|---|---|---|
| provato + FLAT | 406 | **-14.3%** | 17% | -14.7% | SI |  |
| ingresso FLAT (runup<10%) | 2154 | **-14.6%** | 17% | -18.6% | SI |  |
| winrate>=60% + FLAT | 440 | **-16.1%** | 22% | -17.4% | SI |  |
| pressione buy (bs_ratio>1.5) | 1296 | **-16.6%** | 14% | -16.6% | no |  |
| non centralizzato (top10<60%) | 3884 | **-17.9%** | 18% | -15.4% | no |  |
| liquidita' 20k-200k | 2276 | **-25.5%** | 17% | -16.6% | no |  |
| coordinato (>=1 altro smart 1h) | 46 | **-31.0%** | 4% | -28.3% | no |  |
| coordinato forte (>=2) | 28 | **-31.0%** | 7% | -27.5% | no |  |
| wallet provato (closed>=10) | 1930 | **-31.0%** | 20% | -26.1% | no |  |
| buy grosso (>=$1000) | 88 | **-31.0%** | 20% | -28.1% | no |  |
| provato + coordinato | 21 | **-31.0%** | 0% | -28.3% | no |  |
| wallet winrate>=60% | 3991 | **-31.7%** | 17% | -30.6% | no |  |
| TUTTO (baseline) | 9611 | **-31.8%** | 16% | -30.2% | no |  |
| token SICURO (authority revocata) | 9420 | **-32.1%** | 16% | -31.1% | no |  |
| token early (<60min) | 2913 | **-60.6%** | 22% | -39.7% | no |  |
| SICURO + early | 2912 | **-60.6%** | 22% | -39.7% | no |  |

## ❌ Nessun edge ancora
Miglior segmento: **provato + FLAT** (mediana -14.3%) — ma sotto soglia o non batte il hold.
Servono piu' dati / piu' feature (token_age, holders, authority) per segmenti piu' fini.