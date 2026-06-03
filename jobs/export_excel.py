"""
jobs/export_excel.py — la VETRINA.

Scrive in un .xlsx i top N asset per score, ordinati dal più alto.
È il file che apri tu. NON contiene "segnali da comprare": contiene candidati da
GUARDARE, con il PERCHÉ del voto e il prezzo al momento, così puoi fare paper
trading onesto (segni entrata ipotetica, controlli tra qualche giorno).

Colonne pensate per smascherare l'autoinganno:
  - price_at_score: prezzo quando lo score è scattato (il tuo punto di entrata ipotetico)
  - breakdown: da dove viene il voto (niente numeri magici)
  - age_hours / liquidity: per ricordarti che gli illiquidi non si tradano davvero
"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from config import SCORING, EXPORT_PATH
from db import get_conn, init_db


def _score_10(raw):
    """Mappa lo score grezzo su scala 0-10 (la verità resta il grezzo nel breakdown)."""
    ref = SCORING.get("score_reference", 12.0)
    return round(min(10.0, max(0.0, raw / ref * 10.0)), 1)


def export():
    init_db()
    with get_conn() as c:
        rows = c.execute(
            """SELECT a.ticker, a.name, a.chain, a.contract_address,
                      s.current_score, s.price_at_score, s.breakdown, s.updated_at,
                      a.discovered_at, a.discovery_source
               FROM scores s JOIN assets a ON a.id = s.asset_id
               WHERE a.status='active' AND s.current_score >= ?
               ORDER BY s.current_score DESC
               LIMIT ?""",
            (SCORING["min_score_for_export"], SCORING["top_n_export"]),
        ).fetchall()

    now = time.time()
    data = []
    for r in rows:
        bd = json.loads(r["breakdown"] or "{}")
        bd_str = ", ".join(f"{k}:{v}" for k, v in sorted(bd.items(), key=lambda x: -x[1]))
        data.append({
            "Score_su_10": _score_10(r["current_score"]),
            "Ticker": r["ticker"],
            "Nome": r["name"],
            "Score_grezzo": round(r["current_score"], 2),
            "Prezzo_al_voto_USD": r["price_at_score"],
            "Perche_score": bd_str,
            "Chain": r["chain"],
            "Eta_ore": round((now - r["discovered_at"]) / 3600, 1),
            "Aggiornato_min_fa": round((now - r["updated_at"]) / 60, 1),
            "Fonte": r["discovery_source"],
            "Contract": r["contract_address"],
            # colonne VUOTE che compili tu a mano durante il paper trading:
            "Entrata_ipotetica": "",
            "Prezzo_dopo_3g": "",
            "Esito": "",
        })

    # FIX "Excel stale": se non c'è nulla sopra soglia, scriviamo COMUNQUE un file con
    # un avviso datato, così non resta a video un pick vecchio scaduto.
    if not data:
        import datetime
        stamp = datetime.datetime.fromtimestamp(now).strftime("%Y-%m-%d %H:%M")
        df = pd.DataFrame([{
            "Score_su_10": "", "Ticker": "— nessun candidato sopra soglia —",
            "Nome": f"ultimo controllo: {stamp}", "Score_grezzo": "",
            "Perche_score": "il sistema sta osservando; nessuna confluenza forte ora",
        }])
        df.to_excel(EXPORT_PATH, index=False, sheet_name="Top Scores")
        print(f"[export] nessun asset sopra soglia: scritto avviso datato ({stamp}).")
        return EXPORT_PATH

    df = pd.DataFrame(data)
    df.to_excel(EXPORT_PATH, index=False, sheet_name="Top Scores")

    # formattazione leggera (openpyxl)
    from openpyxl import load_workbook
    wb = load_workbook(EXPORT_PATH)
    ws = wb["Top Scores"]
    header_fill = PatternFill("solid", start_color="1F4E78")
    for col_idx, _ in enumerate(df.columns, start=1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = Font(bold=True, color="FFFFFF", name="Arial")
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")
        # larghezza colonna ~ contenuto
        col = get_column_letter(col_idx)
        maxlen = max([len(str(df.columns[col_idx-1]))] +
                     [len(str(v)) for v in df.iloc[:, col_idx-1].tolist()])
        ws.column_dimensions[col].width = min(maxlen + 2, 45)
    ws.freeze_panes = "A2"
    wb.save(EXPORT_PATH)
    print(f"[export] {len(df)} righe scritte in {EXPORT_PATH}")
    return EXPORT_PATH


if __name__ == "__main__":
    export()
