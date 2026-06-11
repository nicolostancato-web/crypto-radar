# Analisi dataset — 1611 eventi

| Segmento | n | mediana copy | win | hold | batte hold? | EDGE? |
|---|---|---|---|---|---|---|
| winrate>=60% + FLAT | 238 | **-17.8%** | 21% | -16.8% | no |  |
| ingresso FLAT (runup<10%) | 339 | **-17.9%** | 17% | -17.4% | no |  |
| non centralizzato (top10<60%) | 931 | **-19.6%** | 22% | -15.1% | no |  |
| provato + FLAT | 108 | **-23.2%** | 17% | -19.7% | no |  |
| pressione buy (bs_ratio>1.5) | 169 | **-30.8%** | 25% | -19.6% | no |  |
| wallet winrate>=60% | 1174 | **-30.9%** | 19% | -25.0% | no |  |
| TUTTO (baseline) | 1611 | **-31.0%** | 18% | -26.0% | no |  |
| token SICURO (authority revocata) | 1607 | **-31.0%** | 18% | -26.2% | no |  |
| liquidita' 20k-200k | 420 | **-31.4%** | 22% | -15.8% | no |  |
| wallet provato (closed>=10) | 500 | **-32.0%** | 19% | -31.8% | no |  |
| token early (<60min) | 91 | **-43.1%** | 12% | -57.8% | SI |  |
| SICURO + early | 91 | **-43.1%** | 12% | -57.8% | SI |  |

## ❌ Nessun edge ancora
Miglior segmento: **winrate>=60% + FLAT** (mediana -17.8%) — ma sotto soglia o non batte il hold.
Servono piu' dati / piu' feature (token_age, holders, authority) per segmenti piu' fini.