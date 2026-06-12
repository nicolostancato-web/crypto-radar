# Setup trigger esterno — scan ogni ora GARANTITO (gratis)

**Problema:** GitHub Actions salta i cron schedulati (gira ~ogni 6h invece di ogni ora).
**Soluzione:** un servizio cron esterno gratuito (cron-job.org) chiama l'API GitHub ogni ora
e lancia il workflow. Affidabile al minuto, costo €0.

---

## PASSO 1 — Crea account (2 min)
Vai su https://cron-job.org → **Sign up** (email + password gratis). Conferma la mail.

## PASSO 2 — (consigliato) Crea un token GitHub a permessi minimi
Per non mettere il token "potente" su un sito terzo, creane uno che sa SOLO lanciare workflow:
1. https://github.com/settings/personal-access-tokens/new (Fine-grained token)
2. **Repository access** → Only select repositories → `nicolostancato-web/crypto-radar`
3. **Permissions** → Repository permissions → **Actions: Read and write**
4. Genera, copia il token (inizia con `github_pat_...`)

> Scorciatoia se hai fretta: puoi usare il token classico già esistente (in CLAUDE.md),
> ma è meno sicuro perché ha più permessi. Meglio il fine-grained sopra.

## PASSO 3 — Crea il cronjob su cron-job.org
**Dashboard → Create cronjob**, e imposta:

| Campo | Valore |
|---|---|
| **Title** | crypto-radar scan ogni ora |
| **URL** | `https://api.github.com/repos/nicolostancato-web/crypto-radar/actions/workflows/trends.yml/dispatches` |
| **Schedule** | Every hour — minuto `0` (Expert: `0 * * * *`) |
| **Request method** | **POST** |

Poi apri **Advanced / Headers** e aggiungi 2 header:
```
Authorization: token IL_TUO_TOKEN_QUI
Accept: application/vnd.github+json
```
E in **Request body** metti:
```
{"ref":"main"}
```

Salva. Fatto.

## PASSO 4 — Verifica
- Su cron-job.org il job deve risultare verde con risposta **HTTP 204** (= trigger ok).
- Su GitHub → Actions → "crypto-radar-trends" devi vedere un run nuovo ogni ora con event = `workflow_dispatch`.

---

## Note CFO
- cron-job.org free tier: fino a esecuzioni ogni minuto, basta e avanza. Costo €0.
- Ogni trigger lancia 1 run da ~40s → ~720 run/mese GitHub, dentro il free tier (2000 min).
- Costo Grok invariato: ~$0.03/scan × 24/giorno ≈ $0.72/giorno (tetto blindato dai crediti caricati).
- Il cron schedulato dentro trends.yml lo lasciamo come rete di sicurezza (se cron-job.org cade, GitHub
  comunque ogni tanto parte).
