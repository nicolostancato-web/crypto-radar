# Analisi dataset — 15209 eventi

| Segmento | n | mediana copy | win | hold | batte hold? | EDGE? |
|---|---|---|---|---|---|---|
| FLAT + coordinato | 23 | **-8.5%** | 39% | -8.5% | no |  |
| SICURO + FLAT + coordinato | 23 | **-8.5%** | 39% | -8.5% | no |  |
| buy grosso (>=$1000) | 150 | **-11.4%** | 13% | -11.3% | no |  |
| pressione buy (bs_ratio>1.5) | 2607 | **-12.4%** | 9% | -12.4% | no |  |
| provato + FLAT | 484 | **-13.9%** | 17% | -14.0% | SI |  |
| non centralizzato (top10<60%) | 5518 | **-15.6%** | 16% | -14.2% | no |  |
| ingresso FLAT (runup<10%) | 4058 | **-15.9%** | 17% | -33.7% | SI |  |
| winrate>=60% + FLAT | 595 | **-18.3%** | 20% | -19.4% | SI |  |
| liquidita' 20k-200k | 4090 | **-19.6%** | 15% | -14.1% | no |  |
| coordinato (>=1 altro smart 1h) | 98 | **-31.0%** | 12% | -38.1% | SI |  |
| coordinato forte (>=2) | 68 | **-31.0%** | 16% | -30.7% | no |  |
| provato + coordinato | 46 | **-31.0%** | 17% | -28.3% | no |  |
| wallet provato (closed>=10) | 2267 | **-31.1%** | 19% | -27.2% | no |  |
| TUTTO (baseline) | 15209 | **-31.4%** | 15% | -29.8% | no |  |
| wallet winrate>=60% | 6151 | **-31.8%** | 14% | -26.9% | no |  |
| token SICURO (authority revocata) | 14614 | **-31.8%** | 15% | -32.4% | SI |  |
| token early (<60min) | 5438 | **-48.3%** | 20% | -39.7% | no |  |
| SICURO + early | 5232 | **-60.6%** | 21% | -39.7% | no |  |

## ❌ Nessun edge ancora
Miglior segmento: **FLAT + coordinato** (mediana -8.5%) — ma sotto soglia o non batte il hold.
Servono piu' dati / piu' feature (token_age, holders, authority) per segmenti piu' fini.