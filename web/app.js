/* CRYPTO RADAR — focus: classifica smart money. Legge data.json. */

const pct = (x) => (x * 100).toFixed(0) + "%";
const short = (a) => a ? a.slice(0, 4) + "…" + a.slice(-4) : "?";
const fmtScore10 = (x) => (x == null ? "—" : x.toFixed(1));

function statCard(n, l, hot) {
  return `<div class="stat ${hot ? "hot" : ""}"><div class="n">${n}</div><div class="l">${l}</div></div>`;
}

function walletRow(w) {
  const verified = w.verified && !w.is_bot;
  const badge = w.is_bot ? '<span class="wb bot">bot</span>'
    : verified ? '<span class="wb ok">verificata</span>'
    : '<span class="wb pend">da verificare</span>';
  const win = w.win_rate != null ? Math.round(w.win_rate * 100) + "%" : "—";
  const pnl = w.pnl_sol != null ? (w.pnl_sol >= 0 ? "+" : "") + w.pnl_sol.toFixed(2) + " SOL" : "—";
  const toks = (w.tokens || []).join(" · ");
  return `<a class="wrow2 ${verified ? "is-v" : ""} ${w.is_bot ? "is-bot" : ""}"
      href="https://solscan.io/account/${w.address}" target="_blank" rel="noopener">
    <span class="wscore2 ${w.smart_score > 0 ? "pos" : ""}">${(w.smart_score || 0).toFixed(2)}</span>
    <span class="wmeta">
      <span class="waddr">${short(w.address)} ${badge}</span>
      <span class="wtok">${toks || "—"}</span>
    </span>
    <span class="wpnl ${(w.pnl_sol || 0) >= 0 ? "pos" : "neg"}">${pnl}</span>
    <span class="wwin">win ${win}</span>
  </a>`;
}

function pickRow(p) {
  const sig = (p.signals || []).slice(0, 2).map(s => s.k.replace(/_/g, " ")).join(", ");
  const href = p.dexscreener || "#";
  return `<a class="crow" href="${href}" target="_blank" rel="noopener">
    <span class="cscore">${fmtScore10(p.score10)}</span>
    <span class="cticker">${p.ticker}</span>
    <span class="cchain">${p.chain}</span>
    <span class="csig">${sig || "—"}</span>
  </a>`;
}

function valCell(v) {
  let body;
  if (v.avg_net == null) {
    body = `<div class="vv wait">in maturazione</div>`;
  } else {
    const cls = v.avg_net > 0 ? "pos" : "neg";
    body = `<div class="vv ${cls}">${v.avg_net > 0 ? "+" : ""}${(v.avg_net * 100).toFixed(1)}%</div>
      <div class="vsub">n=${v.n} · win ${pct(v.win_rate)}</div>`;
  }
  return `<div class="vcell"><div class="vh">${v.horizon}</div>${body}</div>`;
}

async function load() {
  let d;
  try {
    d = await (await fetch("./data.json?t=" + Date.now())).json();
  } catch (e) {
    document.getElementById("updated").textContent = "dati non disponibili";
    return;
  }
  document.getElementById("updated").textContent = "agg. " + d.updated_iso;
  const w = d.wallets || { tracked: 0, whales: 0, bots: 0, leaderboard: [] };
  const s = d.stats || {};

  document.getElementById("stats").innerHTML =
    statCard(w.tracked, "wallet tracciati", false) +
    statCard(w.whales || 0, "whale verificate", true) +
    statCard(w.bots || 0, "bot esclusi", false) +
    statCard(s.candidates || 0, "crypto candidati", false) +
    statCard(s.outcomes_open || 0, "paper trade", false);

  document.getElementById("wcount").textContent =
    `${w.whales || 0} verificate · ${w.tracked} tracciati`;

  const lb = w.leaderboard || [];
  const wl = document.getElementById("wallets");
  if (lb.length) {
    wl.innerHTML = lb.map(walletRow).join("");
  } else {
    wl.innerHTML = `<div class="empty">Cattura in corso. I wallet appaiono man mano che il radar entra sui token, poi vengono qualificati col PnL reale.</div>`;
  }

  document.getElementById("validation").innerHTML = (d.validation || []).map(valCell).join("");

  const learn = d.learning || [];
  const le = document.getElementById("learning");
  le.innerHTML = learn.length
    ? learn.map(l => {
        const cls = l.avg_net > 0 ? "pos" : "neg";
        return `<div class="lrow ${l.confidence}">
          <span class="lname">${l.signal.replace(/_/g, " ")}</span>
          <span class="lval ${cls}">${l.avg_net > 0 ? "+" : ""}${(l.avg_net * 100).toFixed(1)}%</span>
          <span class="ln">n=${l.n}</span></div>`;
      }).join("")
    : '<div class="wnote">Nessun esito netto ancora. Si accumula mentre gira.</div>';

  const picks = d.picks || [];
  const pe = document.getElementById("picks"), em = document.getElementById("empty");
  if (picks.length) {
    em.hidden = true;
    pe.innerHTML = picks.slice(0, 15).map(pickRow).join("");
  } else {
    pe.innerHTML = "";
    em.hidden = false;
    em.textContent = "Nessun candidato sopra soglia ora.";
  }

  document.getElementById("counts").textContent =
    `${w.tracked} wallet · ${w.whales || 0} verificate · ${w.bots || 0} bot`;
}

load();
setInterval(load, 5 * 60 * 1000);
