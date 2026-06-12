/* CRYPTO RADAR dashboard — pipeline X-FIRST. Legge pipeline.json. */

const $ = (id) => document.getElementById(id);
const fmtUsd = (x) => {
  if (x == null) return "—";
  if (x >= 1e6) return "$" + (x / 1e6).toFixed(1) + "M";
  if (x >= 1e3) return "$" + (x / 1e3).toFixed(0) + "k";
  return "$" + Math.round(x);
};
const fmtPct = (x) => (x == null ? "—" : Math.round(x * 100) + "%");

async function load(name) {
  try {
    const r = await fetch(name + "?t=" + Date.now());
    if (r.ok) return await r.json();
  } catch (e) {}
  return null;
}

const arenaTag = (a) =>
  a === "ai_agent"
    ? '<span class="atag ai">AI agent</span>'
    : '<span class="atag meme">memecoin</span>';

function heatDots(h) {
  h = Math.max(0, Math.min(10, h || 0));
  const full = Math.round(h / 2); // 0..5
  return "●".repeat(full) + "○".repeat(5 - full);
}

function renderTrends(d) {
  const box = $("trends");
  const sc = (d && d.last_scan) || {};
  $("scan-when").textContent = sc.utc ? `— ${sc.utc} UTC` : "";
  const toks = sc.tokens || [];
  if (!toks.length) {
    box.innerHTML = '<p class="muted">In attesa del prossimo ascolto di Grok…</p>';
    return;
  }
  box.innerHTML = toks.map((t) => {
    const mom = t.momentum || t.velocity || "—";
    const flags = t.red_flags
      ? `<div class="row flag"><span>⚠ red flag</span><span>${t.red_flags}</span></div>` : "";
    const thesis = t.entry_thesis
      ? `<p class="thesis">“${t.entry_thesis}”</p>` : "";
    const callers = t.distinct_callers != null
      ? `${t.distinct_callers} account${t.distinct_callers == 1 ? "" : " indip."}` : (t.callers || "—");
    return `
    <div class="card sc">
      <div class="ttop"><h3>${t.ticker || "?"} ${arenaTag(t.arena)}</h3><span class="heat" title="quanto scalda su X">${heatDots(t.heat)}</span></div>
      <p class="muted" style="font-size:.86rem">${t.narrative || ""}</p>
      ${thesis}
      <div class="row"><span>chi ne parla</span><span>${callers}</span></div>
      <div class="row"><span>momentum</span><span>${mom}${t.confidence != null ? " · conf " + t.confidence + "/10" : ""}</span></div>
      <div class="row"><span>età</span><span>${t.age_hours != null ? t.age_hours + "h" : "—"}</span></div>
      ${flags}
    </div>`;
  }).join("");
}

function metricChip(label, value, ok) {
  const c = ok === true ? "ok" : ok === false ? "bad" : "";
  return `<span class="chip ${c}"><i>${label}</i>${value}</span>`;
}

function renderCandidates(d) {
  const box = $("candidates");
  const list = (d && d.candidates) || [];
  if (!list.length) {
    box.innerHTML = '<p class="muted">Nessuna candidata valutata ancora.</p>';
    $("filter-note").textContent = "";
    return;
  }
  $("filter-note").innerHTML =
    `Su <b>${d.evaluated}</b> token segnalati da X, il filtro ne ha promosso <b>${d.passed_count}</b> a perla. ` +
    `Verde = passa tutti i controlli. Rosso = scartato (il perché è scritto). Niente euro in gioco.`;

  box.innerHTML = list.map((c) => {
    const safe = c.mint_revoked && c.freeze_revoked;
    const chips = [
      metricChip("liquidità", fmtUsd(c.liq), c.liq != null ? c.liq >= 10000 && c.liq <= 2000000 : null),
      metricChip("vol 24h", fmtUsd(c.vol_24h), c.vol_24h != null ? c.vol_24h >= 50000 : null),
      metricChip("vol 1h", fmtUsd(c.vol_1h), c.vol_1h != null ? c.vol_1h >= 3000 : null),
      metricChip("età", c.age_h != null ? c.age_h + "h" : "—", c.age_h != null ? c.age_h >= 1 && c.age_h <= 72 : null),
      metricChip("top 10 wallet", fmtPct(c.top10_pct), c.top10_pct != null ? c.top10_pct <= 0.5 : null),
      metricChip("wallet #1", fmtPct(c.top1_pct), c.top1_pct != null ? c.top1_pct <= 0.3 : null),
      metricChip("buy/sell 1h", c.bs_ratio_1h != null ? c.bs_ratio_1h + "×" : "—", c.bs_ratio_1h != null ? c.bs_ratio_1h >= 1.2 : null),
      metricChip("authority", safe ? "revocata" : "attiva", safe),
    ].join("");
    const why = c.pass
      ? '<span class="verdict-pearl">★ PERLA — passa tutti i controlli</span>'
      : `<div class="reasons"><b>Scartato perché:</b> ${c.fails.join(" · ")}</div>`;
    return `
      <div class="cand ${c.pass ? "pass" : "fail"}">
        <div class="chead">
          <div class="cname">${c.ticker} ${arenaTag(c.arena)} ${c.pass ? '<span class="badge y">PERLA</span>' : '<span class="badge n">scartato</span>'}</div>
          <a class="ca" href="https://dexscreener.com/solana/${c.ca}" target="_blank" rel="noopener">vedi su DexScreener →</a>
        </div>
        <div class="chips">${chips}</div>
        ${why}
      </div>`;
  }).join("");
}

function renderOutcomes(d) {
  const tb = document.querySelector("#outcomes tbody");
  const L = d && d.learning;
  const list = (d && d.outcomes) || [];
  if (!list.length) {
    tb.innerHTML = '<tr><td colspan="7" class="muted">Tracciamento appena avviato — gli esiti compaiono dopo qualche ora di osservazioni.</td></tr>';
    return;
  }
  // box apprendimento
  const lb = document.getElementById("learnbox");
  if (L) {
    const pr = L.pearls_2x_rate, rr = L.rejects_2x_rate;
    const f = (x) => (x == null ? "—" : Math.round(x * 100) + "%");
    lb.innerHTML = `<div class="learn">
      <div class="li"><div class="ln">${L.tracked_tokens}</div><div class="ll">token tracciati</div></div>
      <div class="li"><div class="ln pos">${f(pr)}</div><div class="ll">perle che fanno ≥2x</div></div>
      <div class="li"><div class="ln ${rr ? "neg" : ""}">${f(rr)}</div><div class="ll">scartati che fanno 2x<br><span class="muted">(se alto → filtro troppo severo)</span></div></div>
    </div>`;
    const ba = L.by_arena || {};
    const arows = Object.entries(ba).map(([a, v]) =>
      `<div class="arow"><span>${arenaTag(a)}</span><span>${v.tracked} tracciati${v.settled ? " · " + v.settled + " conclusi · " + Math.round((v.runner_rate || 0) * 100) + "% runner" : ""}</span></div>`).join("");
    if (arows) lb.innerHTML += `<div class="arenacmp"><div class="acl">Confronto arene — chi rende di più per il nostro metodo</div>${arows}</div>`;
  }
  tb.innerHTML = list.map((o) => {
    const rm = o.ret_max == null ? "—" : (o.ret_max >= 0 ? "+" : "") + Math.round(o.ret_max * 100) + "%";
    const rn = o.ret_now == null ? "—" : (o.ret_now >= 0 ? "+" : "") + Math.round(o.ret_now * 100) + "%";
    return `<tr class="${o.hit_2x ? "edge" : ""}">
      <td>${o.ticker || "?"}</td>
      <td><span class="pill ${o.pass ? "y" : "n"}">${o.pass ? "perla" : "scarto"}</span></td>
      <td class="med ${cls(o.ret_max)}">${rm}</td>
      <td class="${cls(o.ret_now)}">${rn}</td>
      <td>${o.hit_2x ? "✅" : o.rugged ? "💀" : "—"}</td>
      <td>${fmtUsd(o.sig_vol_1h)}</td>
      <td>${o.n_obs}</td>
    </tr>`;
  }).join("");
}

function renderLessons(d) {
  const box = document.getElementById("lessons");
  const L = d && d.lessons;
  if (!L) { box.innerHTML = '<p class="muted">Apprendimento in avvio…</p>'; return; }

  if (L.status === "accumulo") {
    const pct = Math.min(100, Math.round((L.settled / L.prelim_at) * 100));
    box.innerHTML = `<div class="lacc">
      <div class="lbar"><div class="lbarfill" style="width:${pct}%"></div></div>
      <p><b>${L.settled}/${L.prelim_at}</b> trade conclusi. Le prime regole compaiono qui appena ci sono abbastanza
      token seguiti per qualche ora. Il sistema impara da solo, ogni ora.</p>
    </div>`;
    return;
  }

  const badge = L.status === "ready"
    ? '<span class="lbadge ok">DATI SOLIDI</span>'
    : '<span class="lbadge prelim">PRELIMINARE — pochi trade, indicativo</span>';
  const fmt = (k, v) => {
    if (v == null) return "—";
    if (["volume 1h", "volume 24h", "liquidità"].includes(k)) return fmtUsd(v);
    if (k === "top 10 wallet") return Math.round(v * 100) + "%";
    return (typeof v === "number" ? (Math.round(v * 100) / 100) : v);
  };
  const rows = (L.lessons || []).map((le) => {
    const stronger = le.ratio && (le.ratio >= 1.3 || le.ratio <= 0.77);
    return `<tr class="${stronger ? "edge" : ""}">
      <td>${le.label}</td>
      <td class="med pos">${fmt(le.label, le.runner_median)}</td>
      <td class="neg">${fmt(le.label, le.dead_median)}</td>
      <td>${le.ratio == null ? "—" : le.ratio + "×"}</td>
    </tr>`;
  }).join("");

  box.innerHTML = `
    <p class="note">${badge} &nbsp; ${L.settled} trade conclusi · ${L.runners} hanno corso (≥+${L.runner_pct}%).
    Le righe evidenziate sono le condizioni che separano di più i runner dai morti.</p>
    <div class="tablewrap"><table>
      <thead><tr><th>condizione al segnale</th><th>runner (mediana)</th><th>morti (mediana)</th><th>divario</th></tr></thead>
      <tbody>${rows || '<tr><td colspan="4" class="muted">Calcolo in corso…</td></tr>'}</tbody>
    </table></div>`;
}

function renderStats(d) {
  const items = [
    [d ? d.scans_total : "—", "ascolti di X fatti"],
    [d ? d.evaluated : "—", "token passati al filtro"],
    [d ? d.passed_count : "—", "perle trovate"],
    ["€0", "speso finora"],
  ];
  $("stats").innerHTML = items
    .map(([n, l]) => `<div class="stat"><div class="n">${n}</div><div class="l">${l}</div></div>`)
    .join("");
}

(async function () {
  const d = await load("pipeline.json");
  $("updated").textContent = d
    ? `Aggiornato ${d.updated_utc} UTC · Grok ascolta X ogni 4h, il filtro gira subito dopo`
    : "In avvio…";
  renderTrends(d);
  renderCandidates(d);
  renderOutcomes(d);
  renderLessons(d);
  renderStats(d);
})();
