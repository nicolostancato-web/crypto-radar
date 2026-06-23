/* CRYPTO RADAR — centro di comando. Tutto da pipeline.json, auto-aggiornato ogni ciclo. */

const $ = (id) => document.getElementById(id);
const fmtUsd = (x) => {
  if (x == null) return "—";
  if (x >= 1e6) return "$" + (x / 1e6).toFixed(1) + "M";
  if (x >= 1e3) return "$" + (x / 1e3).toFixed(0) + "k";
  return "$" + Math.round(x);
};
const pp = (x) => (x == null ? "—" : (x >= 0 ? "+" : "") + Math.round(x * 100) + "%");
const cls = (x) => (x == null ? "" : x >= 0 ? "pos" : "neg");
const arenaTag = (a) => a === "ai_agent"
  ? '<span class="atag ai">AI agent</span>' : '<span class="atag meme">memecoin</span>';

async function load(name) {
  try { const r = await fetch(name + "?t=" + Date.now()); if (r.ok) return await r.json(); } catch (e) {}
  return null;
}
function heatDots(h) { h = Math.max(0, Math.min(10, h || 0)); const f = Math.round(h / 2); return "●".repeat(f) + "○".repeat(5 - f); }

const ICON = { whale: "🐋", timing: "⏱", warn: "⚠️" };

/* ---------- HERO + PROGETTO ---------- */
function renderProject(d) {
  const p = d.project || {};
  $("mission").textContent = p.mission || "";
  $("method").textContent = p.method || "";
  $("day").textContent = "Giorno " + (p.day ?? "—");
  $("phase").textContent = p.phase || "—";
  $("updated").textContent = "agg. " + (d.updated_utc || "") + " UTC";
  $("foot-updated").textContent = "Dashboard auto-aggiornata ogni 30 min · ultimo: " + (d.updated_utc || "") + " UTC";

  // scoperta del momento
  const f = p.headline_finding;
  const ins = $("insight");
  if (f) {
    ins.innerHTML = `<div class="insight">
      <div class="ins-ico">${ICON[f.icon] || "💡"}</div>
      <div class="ins-body">
        <div class="ins-head">${f.headline} <span class="ins-conf ${f.confidence === "solido" ? "ok" : ""}">${f.confidence}</span></div>
        <div class="ins-metric">${f.metric}</div>
        <div class="ins-detail">${f.detail}</div>
      </div></div>`;
  } else {
    ins.innerHTML = '<div class="insight"><div class="ins-body"><div class="ins-detail muted">Ancora nessuna scoperta forte — stiamo accumulando i primi dati.</div></div></div>';
  }

  // numeri
  const s = p.stats || {};
  const items = [
    [s.trades ?? "—", "trade conclusi", "quante operazioni simulate complete"],
    [s.runners ?? "—", "runner (≥+50%)", "quanti hanno corso davvero"],
    [s.pearls ?? "—", "perle trovate", "token promossi dal filtro"],
    [s.observations ?? "—", "osservazioni", "fotografie orarie accumulate"],
    [s.evaluated ?? "—", "token valutati", "passati al filtro"],
    [s.scans ?? "—", "ascolti di X", "scansioni di Grok"],
  ];
  $("bignums").innerHTML = items.map(([n, l, t]) =>
    `<div class="bn"><div class="bn-n">${n}</div><div class="bn-l">${l}</div><div class="bn-t">${t}</div></div>`).join("");

  // timeline scoperte
  $("timeline").innerHTML = (p.discoveries || []).map((x) =>
    `<div class="tl ${x.highlight ? "hot" : ""}">
      <div class="tl-day">${x.day}</div>
      <div class="tl-dot"></div>
      <div class="tl-body"><b>${x.title}</b><span>${x.body}</span></div>
    </div>`).join("");

  // roadmap
  const RST = { done: ["✓", "fatto"], doing: ["◐", "in corso"], next: ["○", "prossimo"] };
  $("roadmap").innerHTML = (p.roadmap || []).map((r) => {
    const [ic, lab] = RST[r.status] || ["○", ""];
    return `<div class="rm ${r.status}"><span class="rm-ic">${ic}</span><span class="rm-t">${r.title}</span><span class="rm-s">${lab}</span></div>`;
  }).join("");
}

/* ---------- COSA SCALDA SU X ---------- */
function renderTrends(d) {
  const box = $("trends"); const sc = (d && d.last_scan) || {};
  $("scan-when").textContent = sc.utc ? `— ${sc.utc} UTC` : "";
  const toks = sc.tokens || [];
  if (!toks.length) { box.innerHTML = '<p class="muted">In attesa del prossimo ascolto…</p>'; return; }
  box.innerHTML = toks.map((t) => {
    const flags = t.red_flags ? `<div class="row flag"><span>⚠ red flag</span><span>${t.red_flags}</span></div>` : "";
    const thesis = t.entry_thesis ? `<p class="thesis">"${t.entry_thesis}"</p>` : "";
    const callers = t.distinct_callers != null ? `${t.distinct_callers} account` : (t.callers || "—");
    return `<div class="card sc">
      <div class="ttop"><h3>${t.ticker || "?"} ${arenaTag(t.arena)}</h3><span class="heat">${heatDots(t.heat)}</span></div>
      <p class="muted sm">${t.narrative || ""}</p>${thesis}
      <div class="row"><span>chi ne parla</span><span>${callers}</span></div>
      <div class="row"><span>fase</span><span>${t.momentum || t.velocity || "—"}${t.confidence != null ? " · conf " + t.confidence + "/10" : ""}</span></div>
      ${flags}</div>`;
  }).join("");
}

/* ---------- FILTRO ---------- */
function renderCandidates(d) {
  const box = $("candidates"); const list = (d && d.candidates) || [];
  if (!list.length) { box.innerHTML = '<p class="muted">Nessuna candidata ancora.</p>'; $("filter-note").textContent = ""; return; }
  $("filter-note").innerHTML = `Su <b>${d.evaluated}</b> token, il filtro ne ha promosso <b>${d.passed_count}</b> a perla. Verde = passa, rosso = scartato (col perché).`;
  box.innerHTML = list.slice(0, 12).map((c) => {
    const safe = c.mint_revoked && c.freeze_revoked;
    const chip = (l, v, ok) => `<span class="chip2 ${ok === true ? "ok" : ok === false ? "bad" : ""}"><i>${l}</i>${v}</span>`;
    const chips = [
      chip("liq", fmtUsd(c.liq), c.liq != null ? c.liq >= 10000 && c.liq <= 2000000 : null),
      chip("vol 1h", fmtUsd(c.vol_1h), c.vol_1h != null ? c.vol_1h >= 3000 : null),
      chip("età", c.age_h != null ? c.age_h + "h" : "—", c.age_h != null ? c.age_h <= 72 : null),
      chip("top10", c.top10_pct != null ? Math.round(c.top10_pct * 100) + "%" : "—", c.top10_pct != null ? c.top10_pct <= 0.5 : null),
      chip("buy/sell", c.bs_ratio_1h != null ? c.bs_ratio_1h + "×" : "—", c.bs_ratio_1h != null ? c.bs_ratio_1h >= 1.2 : null),
      chip("authority", safe ? "ok" : "attiva", safe),
    ].join("");
    const why = c.pass ? '<span class="verdict-pearl">★ PERLA</span>'
      : `<div class="reasons"><b>Scartato:</b> ${(c.fails || []).join(" · ")}</div>`;
    return `<div class="cand ${c.pass ? "pass" : "fail"}">
      <div class="chead"><div class="cname">${c.ticker} ${arenaTag(c.arena)} ${c.pass ? '<span class="badge y">PERLA</span>' : '<span class="badge n">scartato</span>'}</div>
        <a class="ca" href="https://dexscreener.com/${c.chain || "solana"}/${c.ca}" target="_blank" rel="noopener">DexScreener →</a></div>
      <div class="chips">${chips}</div>${why}</div>`;
  }).join("");
}

/* ---------- DETTAGLI (esiti, strategie, regole) ---------- */
function renderDetails(d) {
  // outcomes
  const tb = document.querySelector("#outcomes tbody");
  const L = d.learning, list = d.outcomes || [];
  if (list.length) {
    const lb = $("learnbox");
    if (L) {
      const f = (x) => (x == null ? "—" : Math.round(x * 100) + "%");
      lb.innerHTML = `<div class="learn">
        <div class="li"><div class="ln">${L.tracked_tokens}</div><div class="ll">token tracciati</div></div>
        <div class="li"><div class="ln pos">${f(L.pearls_2x_rate)}</div><div class="ll">perle ≥2x</div></div>
        <div class="li"><div class="ln ${L.rejects_2x_rate ? "neg" : ""}">${f(L.rejects_2x_rate)}</div><div class="ll">scartati 2x</div></div>
      </div>`;
    }
    tb.innerHTML = list.slice(0, 14).map((o) => `<tr class="${o.hit_2x ? "edge" : ""}">
      <td>${o.ticker || "?"}</td>
      <td><span class="pill ${o.pass ? "y" : "n"}">${o.pass ? "perla" : "scarto"}</span></td>
      <td class="med ${cls(o.ret_max)}">${pp(o.ret_max)}</td>
      <td class="${cls(o.ret_now)}">${pp(o.ret_now)}</td>
      <td>${o.hit_2x ? "✅" : o.rugged ? "💀" : "—"}</td>
      <td>${fmtUsd(o.sig_vol_1h)}</td><td>${o.n_obs}</td></tr>`).join("");
  } else { tb.innerHTML = '<tr><td colspan="7" class="muted">In accumulo…</td></tr>'; }

  // strategie
  const stb = document.querySelector("#simtable tbody");
  const s = d.simulation;
  if (s && s.strategies && s.strategies.length) {
    const hrs = (m) => (m >= 60 ? (m / 60).toFixed(1) + "h" : m + "min");
    stb.innerHTML = s.strategies.map((st, i) => `<tr class="${i === 0 ? "edge" : ""}">
      <td>${st.label}${i === 0 ? ' <span class="pill y">migliore</span>' : ""}</td>
      <td class="med ${cls(st.median)}">${pp(st.median)}</td><td>${Math.round(st.win_rate * 100)}%</td><td>${hrs(st.avg_hold_min)}</td></tr>`).join("");
    const v = $("sim-verdict"); const pm = s.pass_median, fm = s.fail_median;
    const late = pm != null && fm != null && pm < fm;
    v.innerHTML = `<div class="simverdict ${late ? "bad" : "ok"}">
      ${late ? "<b>⚠ Entriamo troppo tardi.</b> " : ""}Perle ${pp(pm)} vs scartati ${pp(fm)} (entry al segnale).
      ${s.whale_confirmed ? `<br><b>Whale precoci:</b> ${pp(s.whale_confirmed.median)} (n=${s.whale_confirmed.n}) vs ${s.no_confirmation ? pp(s.no_confirmation.median) : "—"} senza → è il segnale da seguire.` : ""}
      ${s.entry_timing && s.entry_timing.dip15 ? `<br><b>Timing:</b> al segnale ${pp(s.entry_timing.at_signal.median)} → dopo dip −15% ${pp(s.entry_timing.dip15.median)}.` : ""}</div>`;
  } else { stb.innerHTML = '<tr><td colspan="4" class="muted">In accumulo…</td></tr>'; }

  // regole apprese
  const lessons = d.lessons;
  const lb = $("lessons");
  if (lessons && lessons.status !== "accumulo" && (lessons.lessons || []).length) {
    const fmt = (lab, v) => v == null ? "—" : (["volume 1h", "volume 24h", "liquidità"].includes(lab) ? fmtUsd(v) : lab === "top 10 wallet" ? Math.round(v * 100) + "%" : Math.round(v * 100) / 100);
    lb.innerHTML = `<p class="note">${lessons.settled} trade · ${lessons.runners} runner. Le righe evidenziate separano di più i vincenti dai morti.</p>
      <div class="tablewrap"><table><thead><tr><th>condizione al segnale</th><th>runner</th><th>morti</th><th>divario</th></tr></thead><tbody>${(lessons.lessons || []).map((le) => {
        const strong = le.ratio && (le.ratio >= 1.3 || le.ratio <= 0.77);
        return `<tr class="${strong ? "edge" : ""}"><td>${le.label}</td><td class="med pos">${fmt(le.label, le.runner_median)}</td><td class="neg">${fmt(le.label, le.dead_median)}</td><td>${le.ratio == null ? "—" : le.ratio + "×"}</td></tr>`;
      }).join("")}</tbody></table></div>`;
  } else {
    const n = lessons ? lessons.settled : 0, need = lessons ? lessons.prelim_at : 8;
    lb.innerHTML = `<div class="lacc"><div class="lbar"><div class="lbarfill" style="width:${Math.min(100, Math.round((n / need) * 100))}%"></div></div><p><b>${n}/${need}</b> trade conclusi: le regole numeriche compaiono qui appena ce ne sono abbastanza.</p></div>`;
  }
}

function renderWhales(d) {
  const w = d.whales; const tb = document.querySelector("#whales tbody");
  if (!w || !w.tokens || !w.tokens.length) { tb.innerHTML = '<tr><td colspan="5" class="muted">Lettura swap in avvio…</td></tr>'; return; }
  const pcls = (p) => p == null ? "" : p > 0.1 ? "pos" : p < -0.1 ? "neg" : "";
  tb.innerHTML = w.tokens.map((t) => `<tr>
    <td>${t.ticker || "?"} ${t.pass ? '<span class="pill y">perla</span>' : ""}</td>
    <td class="med ${pcls(t.pressure)}">${t.pressure == null ? "—" : (t.pressure > 0 ? "+" : "") + t.pressure}</td>
    <td class="pos">${t.accumulators ?? "—"}</td><td class="neg">${t.distributors ?? "—"}</td><td>${t.n_swaps ?? "—"}</td></tr>`).join("");
  const sm = $("smart");
  if (w.smart && w.smart.length) {
    sm.innerHTML = `<div class="smartbox"><div class="acl">Wallet "smart" da seguire <span class="muted">(${w.smart_qualified} qualificati)</span></div>${w.smart.map((s) =>
      `<div class="srow"><a href="https://solscan.io/account/${s.wallet}" target="_blank" rel="noopener">${s.wallet.slice(0, 8)}…</a><span>winrate ${Math.round(s.winrate * 100)}% su ${s.plays} token</span></div>`).join("")}</div>`;
  } else {
    sm.innerHTML = `<p class="note">I <b>wallet vincenti</b> da copiare compaiono qui appena qualche balena ricorre sui token che corrono. ${w.smart_qualified ? w.smart_qualified + " in osservazione." : "In costruzione."}</p>`;
  }
}

function sparkline(eq) {
  if (!eq || eq.length < 2) return "";
  const ys = eq.map(p => p[1]), min = Math.min(...ys), max = Math.max(...ys), W = 600, H = 70;
  const span = (max - min) || 1;
  const pts = eq.map((p, i) => [i / (eq.length - 1) * W, H - (p[1] - min) / span * (H - 6) - 3]);
  const dd = pts.map((p, i) => (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1)).join(" ");
  const base = H - (100 - min) / span * (H - 6) - 3; // linea dei €100 di partenza
  const up = eq[eq.length - 1][1] >= 100;
  return `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" class="spark">
    <line x1="0" y1="${base.toFixed(1)}" x2="${W}" y2="${base.toFixed(1)}" class="spark-base"/>
    <path d="${dd}" class="${up ? 'spark-up' : 'spark-down'}"/></svg>`;
}

function trendIcon(t) {
  if (!t) return "";
  if (t.includes("miglior") || t.includes("cresc")) return "<span class='tr up'>▲ " + t + "</span>";
  if (t.includes("calo")) return "<span class='tr down'>▼ " + t + "</span>";
  return "<span class='tr flat'>● " + t + "</span>";
}

function renderTeam(tm) {
  if (!tm) { document.getElementById("team-sec").style.display = "none"; return; }
  const a = tm.tab1_accumulo, k = tm.tab2_kpi, t = tm.tab3_trading;
  const cards = [
    { n: "1 · Accumulo", icon: "📡", lines: [
      `<b>${a.token}</b> token · <b>${a.runner}</b> runner`,
      `${a.candele_5m} candele 5m`, trendIcon(a.trend) ] },
    { n: "2 · Analista (KPI)", icon: "🔬", lines: [
      `base <b>${k.base_win}%</b> → bs≥1.5 <b>${k.bs15_win}%</b>`,
      `lift +${k.lift_pt}pt · OOS ${k.oos_win}%`,
      (k.survives ? "<span class='tr up'>segnale vivo</span>" : "<span class='tr down'>nessun edge</span>") + " " + trendIcon(k.trend) ] },
    { n: "3 · Trading", icon: "💰", lines: [
      `${t.strategy}`,
      `P&L mediano <b class='${t.median_pnl >= 0 ? "pos" : "neg"}'>${t.median_pnl}%</b> · €100→€${t.portfolio_final}`,
      (t.profitable ? "<span class='tr up'>profittevole</span>" : "<span class='tr down'>perde (meno peggio)</span>") + " " + trendIcon(t.trend) ] },
  ];
  $("team-grid").innerHTML = cards.map(c =>
    `<div class="team-card"><div class="team-h">${c.icon} ${c.n}</div>${c.lines.map(l => `<div class="team-l">${l}</div>`).join("")}</div>`).join("");
  $("cto-note").innerHTML = "<b>🧠 Il CTO:</b> " + tm.cto_note;
}

function renderPortfolio(p) {
  if (!p) { document.getElementById("portfolio-sec").style.display = "none"; return; }
  const up = p.final >= p.start, cls = up ? "pos" : "neg";
  $("port-head").innerHTML =
    `<div class="port-big ${cls}">€${p.final.toFixed(2)}</div>
     <div class="port-meta">
       <span>da €${p.start}</span>
       <span class="${cls}">${up ? "+" : ""}${(p.final - p.start).toFixed(2)}€ (${((p.final / p.start - 1) * 100).toFixed(0)}%)</span>
       <span>${p.n_trades} trade · ${p.win_rate}% vincenti</span>
       <span class="muted">strategia ${p.strategy}</span>
     </div>`;
  $("port-curve").innerHTML = sparkline(p.equity);
  $("port-rules").textContent = "Regole: " + p.rules + " · candele 5-min su " + p.n_5m + "/" + p.n_trades + " trade (resto orario).";
  const tb = document.querySelector("#port-trades tbody");
  tb.innerHTML = (p.trades || []).slice(0, 40).map(t => {
    const w = t.ret_pct > 0;
    return `<tr><td>${t.ticker || "?"}</td><td>${t.bs == null ? "—" : t.bs}</td>
      <td class="${w ? 'pos' : 'neg'}">${w ? "+" : ""}${t.ret_pct}%</td>
      <td class="${t.pnl_eur >= 0 ? 'pos' : 'neg'}">${t.pnl_eur >= 0 ? "+" : ""}${t.pnl_eur}</td>
      <td>€${t.balance}</td><td class="muted">${t.src}</td></tr>`;
  }).join("");
}

(async function () {
  const d = await load("pipeline.json");
  if (!d) { $("mission").textContent = "In avvio…"; return; }
  renderProject(d);
  renderTeam(await load("team.json"));
  renderPortfolio(await load("portfolio.json"));
  renderWhales(d);
  renderTrends(d);
  renderCandidates(d);
  renderDetails(d);
})();
