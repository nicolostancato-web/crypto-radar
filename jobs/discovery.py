"""
jobs/discovery.py — il BUTTAFUORI.

Una sola domanda: "questo token merita osservazione, si' o no?"
NON da' punteggi fini (quello e' lo scoring). E' volutamente largo ed economico:
fonte gratuita (DEXScreener), filtra la spazzatura ovvia, e fa entrare in
`assets` solo cio' che si discosta dal normale — DANDO PESO AI SEGNALI PRECOCI
(liquidita' in crescita, accelerazione volume) sopra quelli tardivi (spike).

Consulta SEMPRE la lista nera: niente duplicati, niente spazzatura gia' scartata.
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DISCOVERY, LIMITS
from db import get_conn, init_db, upsert_asset, add_signal, update_baseline, get_baseline, is_excluded
from net import RateLimiter, get_json
from sources import get_candidates

DEX_BASE = "https://api.dexscreener.com"
limiter = RateLimiter(LIMITS["dexscreener_max_calls_per_min"])


def _age_hours(pair):
    created_ms = pair.get("pairCreatedAt")
    if not created_ms:
        return None
    return (time.time() - created_ms / 1000.0) / 3600.0


def _passes_hard_filters(pair):
    """Filtri di esclusione: scartano la spazzatura PRIMA di sprecare enrichment."""
    liq = (pair.get("liquidity") or {}).get("usd") or 0
    vol24 = (pair.get("volume") or {}).get("h24") or 0
    if liq < DISCOVERY["min_liquidity_usd"]:
        return False, "liquidita' troppo bassa"
    ratio = vol24 / liq if liq else 999
    if ratio > DISCOVERY["max_vol_liq_ratio"]:
        return False, "vol/liq sospetto (possibile wash trading)"
    if ratio < DISCOVERY["min_vol_liq_ratio"]:
        return False, "vol/liq troppo basso (token fermo)"
    age = _age_hours(pair)
    if age is not None:
        if age < DISCOVERY["min_age_hours"]:
            return False, "troppo giovane (rischio pump.fun appena nato)"
        if age > DISCOVERY["max_age_days"] * 24:
            return False, "troppo vecchio e piatto"
    return True, None


def _score_early_signals(c, asset_id, pair):
    """Calcola i segnali di ingresso pesati per PRECOCITA'. Ritorna (somma, dettaglio)."""
    liq = (pair.get("liquidity") or {}).get("usd") or 0
    vol24 = (pair.get("volume") or {}).get("h24") or 0
    vol6 = (pair.get("volume") or {}).get("h6") or 0
    age = _age_hours(pair)

    base = get_baseline(c, asset_id)
    total = 0.0
    detail = {}

    # 1) LIQUIDITA' IN CRESCITA (il piu' precoce) — rispetto alla baseline del token
    if base and base["avg_liquidity"]:
        growth = (liq - base["avg_liquidity"]) / base["avg_liquidity"]
        if growth > 0.15:  # +15% liquidita' rispetto alla media recente
            pts = DISCOVERY["weight_liquidity_growth"] * min(growth, 1.0)
            total += pts; detail["liquidity_growth"] = round(pts, 2)

    # 2) ACCELERAZIONE VOLUME (derivata): il volume delle ultime 6h proiettato
    #    supera la media giornaliera? Volume che ACCELERA, non livello assoluto.
    if vol24:
        vol6_annualized = vol6 * 4  # 6h * 4 = 24h equivalenti
        accel = (vol6_annualized - vol24) / vol24
        if accel > 0.20:
            pts = DISCOVERY["weight_volume_accel"] * min(accel, 1.0)
            total += pts; detail["volume_accel"] = round(pts, 2)

    # 3) SPIKE VOLUME ASSOLUTO (TARDIVO, basso peso, solo conferma)
    if base and base["avg_volume"] and base["avg_volume"] > 0:
        spike = vol24 / base["avg_volume"]
        if spike > 3:
            pts = DISCOVERY["weight_volume_spike"] * min(spike / 5, 1.0)
            total += pts; detail["volume_spike"] = round(pts, 2)

    # 4) POOL GIOVANE CHE GIA' SI MUOVE
    if age is not None and age < 72 and vol24 > DISCOVERY["min_liquidity_usd"]:
        pts = DISCOVERY["weight_young_with_volume"]
        total += pts; detail["young_with_volume"] = round(pts, 2)

    return total, detail


def discover_once():
    init_db()
    found, inserted = 0, 0
    # CANDIDATI da TUTTE le fonti gratis, deduplicati, MULTI-CHAIN.
    # Non fissiamo le chain: seguiamo l'attenzione dove va (chain-rotation).
    candidates = get_candidates()
    with get_conn() as c:
        for cand in candidates:
            chain, token = cand["chain"], cand["token"]
            # consulta la lista nera PRIMA di qualsiasi chiamata aggiuntiva
            if is_excluded(c, chain, token):
                continue

            # dettaglio della coppia per avere liquidita'/volume/eta'
            pd = get_json(f"{DEX_BASE}/latest/dex/tokens/{token}", limiter)
            pairs = (pd or {}).get("pairs") or []
            if not pairs:
                continue
            pair = max(pairs, key=lambda p: (p.get("liquidity") or {}).get("usd") or 0)
            found += 1

            ok, why = _passes_hard_filters(pair)
            if not ok:
                continue

            bt = pair.get("baseToken") or {}
            asset_id = upsert_asset(
                c, chain, token, bt.get("symbol"), bt.get("name"),
                pair.get("pairAddress"), source=cand["source"],
            )
            if asset_id is None:
                continue

            # aggiorna baseline (serve a misurare lo spike DI DOMANI)
            update_baseline(
                c, asset_id,
                (pair.get("liquidity") or {}).get("usd") or 0,
                (pair.get("volume") or {}).get("h24") or 0,
            )

            total, detail = _score_early_signals(c, asset_id, pair)
            if total >= DISCOVERY["candidate_threshold"]:
                for k, v in detail.items():
                    add_signal(c, asset_id, "discovery", k, v, weight=1.0)
                inserted += 1
    print(f"[discovery] candidati_fonti={len(candidates)} esaminati={found} confermati={inserted}")
    return inserted


if __name__ == "__main__":
    if "--once" in sys.argv:
        discover_once()
    else:
        while True:
            try:
                discover_once()
            except Exception as e:
                print(f"[discovery] errore: {e}")
            time.sleep(DISCOVERY["poll_seconds"])
