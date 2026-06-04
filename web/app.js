/* CRYPTO RADAR — focus: classifica smart money. Legge data.json. */

const pct = (x) => (x * 100).toFixed(0) + "%";
const short = (a) => a ? a.slice(0, 4) + "…" + a.slice(-4) : "?";
const fmtScore10 = (x) => (x == null ? "—" : x.toFixed(1));

function statCard(n, l, hot) {
  return `<div class="stat ${hot ? "hot" : ""}"><div class="n">${n}</div><div class="l">${l}</div></div>`;
}

function stat(label, val, cls) {
  return `<div class="wcs"><span class="wcs-v ${cls || ""}">${val}</span><span class="wcs-l">${label}</span></div>`;
}

const usd = (n) => "$" + Math.round(n || 0).toLocaleString("en-US");

function bossRow(b, rank) {
  const toks = b.tokens || 1;
  return `<a class="brow" href="https://solscan.io/account/${b.wallet}" target="_blank" rel="noopener">
    <span class="brank">${rank}</span>
    <span class="bmeta">
      <span class="baddr">${short(b.wallet)}</span>
      <span class="bsub">${toks} token diversi · ${b.buys || toks} big-buy</span>
    </span>
    <span class="btot">${usd(b.total_usd)}</span>
    <span class="bbig">max ${usd(b.biggest)}</span>
  </a>`;
}

function spikeRow(sp) {
  return `<a class="srow" href="https://solscan.io/account/${sp.wallet}" target="_blank" rel="noopener">
    <span class="saddr">${short(sp.wallet)}</span>
    <span class="spool">${sp.pool_name || "—"}</span>
    <span class="susd">${usd(sp.usd)}</span>
  </a>`;
}

function walletRow(w) {
  const verified = w.verified && !w.is_bot;
  const badge = w.is_bot ? '<span class="wb bot">bot · non copiabile</span>'
    : verified ? '<span class="wb ok">verificata</span>'
    : '<span class="wb pend">da verificare</span>';
  const closed = w.closed_count != null ? w.closed_count : "—";
  const won = w.win_rate != null && w.closed_count != null ? Math.round(w.win_rate * w.closed_count) : null;
  const lost = won != null ? w.closed_count - won : null;
  const win = w.win_rate != null ? Math.round(w.win_rate * 100) + "%" : "—";
  const pnl = w.pnl_sol != null ? (w.pnl_sol >= 0 ? "+" : "") + w.pnl_sol.toFixed(2) : "—";
  const tokens = w.tokens_count != null ? w.tokens_count : "—";
  const open = w.open_count != null ? w.open_count : "—";
  const act = w.tx_per_day != null ? w.tx_per_day + "/g" : "—";
  const ourToks = (w.tokens || []).join(" · ");
  return `<a class="wcard ${verified ? "is-v" : ""} ${w.is_bot ? "is-bot" : ""}"
      href="https://solscan.io/account/${w.address}" target="_blank" rel="noopener">
    <div class="wc-head">
      <span class="wscore2 ${w.smart_score > 0 ? "pos" : ""}">${(w.smart_score || 0).toFixed(2)}</span>
      <div class="wc-id">
        <span class="waddr">${short(w.address)} ${badge}</span>
        <span class="wpnl ${(w.pnl_sol || 0) >= 0 ? "pos" : "neg"}">PnL ${pnl} SOL realizzati</span>
      </div>
      <div class="wc-win"><span class="wcw-n ${(w.win_rate || 0) >= 0.5 ? "pos" : ""}">${win}</span><span class="wcw-l">win rate</span></div>
    </div>
    <div class="wc-stats">
      ${stat("chiuse", closed)}
      ${stat("vinte", won != null ? won : "—", "pos")}
      ${stat("perse", lost != null ? lost : "—", "neg")}
      ${stat("token tradati", tokens)}
      ${stat("ancora aperte", open)}
      ${stat("attività", act, w.is_bot ? "neg" : "")}
    </div>
    ${ourToks ? `<div class="wc-tokens">ha comprato dai nostri: <b>${ourToks}</b></div>` : ""}
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

  // BOSS — Who Knows More Than Me
  const sp = d.spikes || { big_buys: 0, wallets: 0, bosses: [], recent: [] };
  document.getElementById("bcount").textContent =
    `${sp.bosses.length} boss · ${sp.big_buys} big-buy · ${sp.wallets} wallet`;
  const be = document.getElementById("bosses");
  if (sp.bosses.length) {
    be.innerHTML = sp.bosses.map((b, i) => bossRow(b, i + 1)).join("");
  } else if (sp.recent.length) {
    be.innerHTML = `<div class="wnote">Nessun ricorrente ancora — servono più big-buy per trovare chi torna. Ultimi big-buy catturati:</div>`
      + sp.recent.map(spikeRow).join("");
  } else {
    be.innerHTML = `<div class="empty">In ascolto degli spike. I big-buy ($1k+) appaiono man mano che i token si muovono.</div>`;
  }

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
