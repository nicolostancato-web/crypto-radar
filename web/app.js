/* CRYPTO RADAR — console. Legge data.json e disegna i candidati. */

const CHAIN_COLORS = {
  solana: "#9b7cff", ethereum: "#7aa2ff", base: "#4b8bff",
  bsc: "#f3c34a", polygon: "#a06bff", arbitrum: "#6bd0ff", ton: "#4bb6ff",
};

const fmtPrice = (p) => {
  if (p == null) return "—";
  if (p >= 1) return "$" + p.toLocaleString("en-US", { maximumFractionDigits: 2 });
  if (p >= 0.0001) return "$" + p.toFixed(6);
  return "$" + p.toExponential(2);
};
const fmtUsd = (n) => {
  if (n == null) return "—";
  if (n >= 1e6) return "$" + (n / 1e6).toFixed(1) + "M";
  if (n >= 1e3) return "$" + (n / 1e3).toFixed(0) + "k";
  return "$" + n;
};
const fmtAge = (h) => (h == null ? "—" : h < 24 ? h.toFixed(0) + "h" : (h / 24).toFixed(1) + "g");
const pct = (x) => (x * 100).toFixed(1) + "%";

function gauge(score10) {
  const r = 24, c = 2 * Math.PI * r;
  const off = c * (1 - score10 / 10);
  return `<div class="gauge">
    <svg width="58" height="58" viewBox="0 0 58 58">
      <circle class="track" cx="29" cy="29" r="${r}" fill="none" stroke-width="5"/>
      <circle class="val" cx="29" cy="29" r="${r}" fill="none" stroke-width="5"
        stroke-dasharray="${c.toFixed(1)}" stroke-dashoffset="${off.toFixed(1)}"/>
    </svg>
    <div class="num">${score10.toFixed(1)}<small>/10</small></div>
  </div>`;
}

function card(p, i) {
  const col = CHAIN_COLORS[p.chain] || "#7d8d87";
  const sigs = p.signals.map(s =>
    `<span class="sig ${s.k === "confluence_bonus" ? "bonus" : ""}">${s.k.replace(/_/g, " ")}</span>`
  ).join("");
  const link = p.dexscreener ? `<a class="card-link" href="${p.dexscreener}" target="_blank" rel="noopener" aria-label="apri ${p.ticker} su DEXScreener"></a>` : "";
  const go = p.dexscreener ? `<span class="go">grafico ↗</span>` : "";
  return `<article class="card ${p.above_threshold ? "hot" : "watch"}" style="animation-delay:${i * 0.04}s">
    ${link}
    <div class="card-top">
      <div class="id">
        <div class="ticker">${p.ticker}</div>
        <div class="name">${p.name || "—"}</div>
        <div class="chip"><span class="cd" style="background:${col}"></span>${p.chain}</div>
      </div>
      ${gauge(p.score10)}
    </div>
    <div class="signals">${sigs || '<span class="sig">nessun segnale</span>'}</div>
    <div class="meta">
      <div>prezzo<b>${fmtPrice(p.price)}</b></div>
      <div>liquidità<b>${fmtUsd(p.liquidity)}</b></div>
      <div>età<b>${fmtAge(p.age_h)}</b></div>
    </div>
    ${go}
  </article>`;
}

function statCard(n, l, hot) {
  return `<div class="stat ${hot ? "hot" : ""}"><div class="n">${n}</div><div class="l">${l}</div></div>`;
}

function chainBar(name, val, max) {
  const col = CHAIN_COLORS[name] || "#7d8d87";
  const w = max ? Math.max(6, (val / max) * 100) : 0;
  return `<div class="cbar">
    <span class="cname"><span class="cd" style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${col};margin-right:7px"></span>${name}</span>
    <span class="ctrack"><span class="cfill" style="width:${w}%"></span></span>
    <span class="cval">${val}</span>
  </div>`;
}

function valCell(v) {
  let body;
  if (v.avg_net == null) {
    body = `<div class="vv wait">in maturazione</div><div class="vsub">i prezzi futuri non sono ancora pronti</div>`;
  } else {
    const cls = v.avg_net > 0 ? "pos" : "neg";
    const sign = v.avg_net > 0 ? "+" : "";
    body = `<div class="vv ${cls}">${sign}${pct(v.avg_net)}</div>
      <div class="vsub">valore atteso netto · n=${v.n} · win ${pct(v.win_rate)}</div>`;
  }
  return `<div class="vcell"><div class="vh">${v.horizon}</div>${body}</div>`;
}

async function load() {
  let d;
  try {
    const res = await fetch("./data.json?t=" + Date.now());
    d = await res.json();
  } catch (e) {
    document.getElementById("updated").textContent = "dati non disponibili";
    return;
  }

  document.getElementById("updated").textContent = "agg. " + d.updated_iso;

  const s = d.stats;
  document.getElementById("stats").innerHTML =
    statCard(s.candidates, "candidati", false) +
    statCard(s.above_threshold, "in evidenza", true) +
    statCard(s.watching, "in osservazione", false) +
    statCard(s.outcomes_open, "paper trade aperti", false) +
    statCard(s.excluded, "esclusi (trappole)", false);

  const chains = Object.entries(d.by_chain).sort((a, b) => b[1] - a[1]);
  const max = chains.length ? chains[0][1] : 0;
  document.getElementById("chains").innerHTML =
    chains.length ? chains.map(([n, v]) => chainBar(n, v, max)).join("")
                  : '<div class="hint">nessun candidato attivo</div>';

  const picks = d.picks || [];
  if (picks.length) {
    document.getElementById("picks").innerHTML = picks.map(card).join("");
    document.getElementById("empty").hidden = true;
  } else {
    document.getElementById("picks").innerHTML = "";
    const e = document.getElementById("empty");
    e.hidden = false;
    e.textContent = "Nessun candidato sul radar in questo momento. Il sistema sta osservando.";
  }

  document.getElementById("validation").innerHTML = d.validation.map(valCell).join("");

  const learn = d.learning || [];
  const le = document.getElementById("learning");
  if (learn.length) {
    le.innerHTML = learn.map(l => {
      const cls = l.avg_net > 0 ? "pos" : "neg";
      const sign = l.avg_net > 0 ? "+" : "";
      const m = l.multiplier != null ? l.multiplier : 1;
      const mcls = m > 1.02 ? "pos" : m < 0.98 ? "neg" : "";
      return `<div class="lrow ${l.confidence}">
        <span class="lname">${l.signal.replace(/_/g, " ")}</span>
        <span class="lbar"><span class="lfill ${cls}" style="width:${Math.min(100, Math.abs(l.avg_net) * 400)}%"></span></span>
        <span class="lval ${cls}">${sign}${pct(l.avg_net)}</span>
        <span class="lmult ${mcls}" title="peso appreso applicato allo score">${m}×</span>
        <span class="ln">n=${l.n} · ${l.confidence}</span>
      </div>`;
    }).join("");
  } else {
    le.innerHTML = '<div class="empty">Ancora nessun esito maturo. Il sistema sta accumulando il materiale per imparare.</div>';
  }

  document.getElementById("counts").textContent =
    `${s.candidates} candidati · ${s.excluded} esclusi · soglia ${d.threshold}`;
}

load();
setInterval(load, 5 * 60 * 1000); // ricarica ogni 5 min (la dashboard resta fresca)
