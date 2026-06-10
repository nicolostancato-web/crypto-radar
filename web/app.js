/* CRYPTO RADAR dashboard — legge status.json (scenari) + analysis.json (segmenti). */

const $ = (id) => document.getElementById(id);
const pct = (x, d = 1) => (x == null ? "—" : (x >= 0 ? "+" : "") + (x * 100).toFixed(d) + "%");
const cls = (x) => (x == null ? "" : x >= 0 ? "pos" : "neg");

async function load(name) {
  try {
    const r = await fetch(name + "?t=" + Date.now());
    if (r.ok) return await r.json();
  } catch (e) {}
  return null;
}

const SC_NAME = {
  S2_smartexit: "Smart-Exit",
  S3_cluster: "Cluster",
  S1_regime: "Regime Filter",
  S0_baseline: "Baseline",
};
const SC_DESC = {
  S2_smartexit: "Entra sullo slancio, esce quando i bravi vendono.",
  S3_cluster: "Entra quando più wallet smart comprano lo stesso token.",
  S1_regime: "Entra solo quando il mercato è 'risk-on'.",
  S0_baseline: "Compra a caso — il controllo che deve perdere.",
};

function renderVerdict(an) {
  const box = $("verdict");
  if (!an || an.events < 20) {
    $("verdict-big").textContent = "Stiamo raccogliendo i dati";
    $("verdict-sub").textContent = "Servono migliaia di trade storici prima di poter dire la verità. Il sistema accumula da solo.";
    box.classList.add("no");
    return;
  }
  if (an.edge_found) {
    box.classList.add("yes");
    $("verdict-big").textContent = "SÌ — un segnale c'è";
    $("verdict-sub").innerHTML = "Setup promettenti: <b>" + an.edges.join(", ") + "</b>. Da validare con più dati prima di rischiare denaro.";
  } else {
    box.classList.add("no");
    $("verdict-big").textContent = "Non ancora";
    const best = an.segments && an.segments[0];
    const bestTxt = best ? `Il setup meno peggio ("${best.name}") rende ${pct(best.median)} — perde ancora.` : "";
    $("verdict-sub").innerHTML = `Su ${an.events.toLocaleString()} trade analizzati, nessuna combinazione di fattori è profittevole. ${bestTxt} È un risultato vero: niente soldi rischiati su una strada che non rende.`;
  }
}

function renderScenarios(st) {
  const box = $("scenarios");
  if (!st || !st.scenarios) { box.innerHTML = '<p class="muted">In avvio…</p>'; return; }
  const seen = new Set();
  const rows = st.scenarios.filter((s) => s.horizon_h === 24 && !seen.has(s.name) && seen.add(s.name));
  $("sc-count").textContent = `(${rows.length})`;
  box.innerHTML = rows.map((s) => {
    const med = s.ev_median;
    const beats = s.beats_hold;
    return `<div class="card sc">
      <span class="tag live">in test</span>
      <h3>${SC_NAME[s.name] || s.name}</h3>
      <p class="muted" style="font-size:.86rem">${SC_DESC[s.name] || ""}</p>
      <div class="big ${cls(med)}">${med == null ? "—" : pct(med)}</div>
      <div class="row"><span>guadagno mediano</span><span>${s.trades} trade</span></div>
      <div class="row"><span>batte "tieni e basta"</span><span>${beats == null ? "—" : beats ? "sì" : "no"}</span></div>
    </div>`;
  }).join("");
}

function renderSegments(an) {
  const tb = document.querySelector("#segments tbody");
  if (!an || !an.segments || !an.segments.length) {
    tb.innerHTML = '<tr><td colspan="5" class="muted">Dati insufficienti — in accumulo.</td></tr>';
    $("seg-note").textContent = "";
    return;
  }
  $("seg-note").textContent = `Ogni riga è una "ricetta" d'ingresso testata su ${an.events.toLocaleString()} trade storici. Cerchiamo una riga col guadagno mediano positivo che batte il semplice tenere.`;
  tb.innerHTML = an.segments.map((s) => `
    <tr class="${s.edge ? "edge" : ""}">
      <td>${s.name}</td>
      <td>${s.n}</td>
      <td class="med ${cls(s.median)}">${pct(s.median)}</td>
      <td>${s.win == null ? "—" : (s.win * 100).toFixed(0) + "%"}</td>
      <td><span class="pill ${s.beats_hold ? "y" : "n"}">${s.beats_hold ? "sì" : "no"}</span></td>
    </tr>`).join("");
}

function renderStats(an, st) {
  const t = (st && st.totals) || {};
  const items = [
    [an ? an.events.toLocaleString() : "—", "trade analizzati"],
    [t.smart_wallets ?? "—", "wallet smart seguiti"],
    [t.wallet_sells ?? "—", "vendite catturate"],
    [t.spike_buys ?? "—", "acquisti grossi"],
  ];
  $("stats").innerHTML = items.map(([n, l]) => `<div class="stat"><div class="n">${n}</div><div class="l">${l}</div></div>`).join("");
}

(async function () {
  const [an, st] = [await load("analysis.json"), await load("status.json")];
  const when = (an && an.updated_utc) || (st && st.updated_utc) || "";
  $("updated").textContent = "Aggiornato " + when + " UTC · gira da solo ogni 2h in cloud";
  renderVerdict(an);
  renderScenarios(st);
  renderSegments(an);
  renderStats(an, st);
})();
