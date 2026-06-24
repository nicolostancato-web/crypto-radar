"""
exits.py — LIBRERIA DELLE STRATEGIE DI USCITA (il vocabolario che il Trader impara a usare).

Il miglioramento del trading sta qui: non un take-profit secco, ma USCITE A SCAGLIONI (vendi una parte
a +50%, una parte a 2x, lasci correre il resto col trailing). Cosi' proteggi il guadagno tipico E
catturi i +1000% (la coda lunga). Il Trader prova TUTTE queste strategie sui dati storici (causale,
con slippage, no look-ahead) e adotta la migliore, evolvendola giorno dopo giorno.

Una strategia = lista di take-profit (moltiplicatore sull'entrata, frazione da vendere) + un trailing
stop per la parte che resta a correre.
"""
SLIP_DEFAULT = 0.06

STRATEGIES = {
    # --- secche (baseline di confronto) ---
    "trail20":        {"tps": [], "trail": 0.20},
    "trail30":        {"tps": [], "trail": 0.30},
    "fix30":          {"tps": [(1.30, 1.0)], "trail": 0.30},          # vendi tutto a +30%
    # --- a scaglioni (il vero miglioramento) ---
    "ladder_2x80":    {"tps": [(2.0, 0.80)], "trail": 0.40},          # a 2x vendi 80%, il 20% corre
    "ladder_balanced":{"tps": [(1.5, 0.40), (2.0, 0.30)], "trail": 0.30},  # 40% a +50%, 30% a 2x, 30% trailing
    "ladder_runner":  {"tps": [(1.5, 0.33), (2.5, 0.33)], "trail": 0.50},  # lascia correre i runner
    "ladder_quick":   {"tps": [(1.3, 0.60)], "trail": 0.25},          # incassa presto: 60% a +30%
    "ladder_3step":   {"tps": [(1.5, 0.33), (2.0, 0.33), (3.0, 0.20)], "trail": 0.30},
    "ladder_moon":    {"tps": [(2.0, 0.50), (5.0, 0.30)], "trail": 0.45},  # tieni per il 5x
}


def _clamp(r):
    return max(min(r, 10.0), -0.95)


def simulate(seq, spec, slip=SLIP_DEFAULT):
    """seq = lista (ts, high, close) ASCENDENTE, point-in-time, gia' deglitchata dal chiamante.
    Ritorna (ritorno_combinato, ts_chiusura) oppure None. L'high serve a vedere se un take-profit
    viene toccato dentro la candela (ordine limit); il close per il trailing."""
    if len(seq) < 2:
        return None
    entry = seq[0][2] * (1 + slip)
    if entry <= 0:
        return None
    tps = sorted(spec.get("tps", []), key=lambda x: x[0])
    trail = spec.get("trail", 0.30)
    remaining = 1.0
    realized = 0.0
    peak = seq[0][1]
    ti = 0
    for ts, hi, cl in seq[1:]:
        peak = max(peak, hi)
        # take-profit a scaglioni: se il MASSIMO tocca il livello, vendo quella frazione li'
        while ti < len(tps) and hi >= entry * tps[ti][0] and remaining > 1e-9:
            frac = min(tps[ti][1], remaining)
            sell = entry * tps[ti][0] * (1 - slip)
            realized += frac * (sell / entry - 1)
            remaining -= frac
            ti += 1
        if remaining <= 1e-9:
            return _clamp(realized), ts
        # trailing sul residuo
        if cl <= peak * (1 - trail):
            realized += remaining * (cl * (1 - slip) / entry - 1)
            return _clamp(realized), ts
    # fine serie: liquido il residuo all'ultimo prezzo noto
    realized += remaining * (seq[-1][2] * (1 - slip) / entry - 1)
    return _clamp(realized), seq[-1][0]
