(async function() {
  AT.setActive('home');

  const [summary, runsIdx, casesIdx] = await Promise.all([
    AT.json('./data/summary.json'),
    AT.json('./data/runs/index.json'),
    AT.json('./data/cases/index.json'),
  ]);

  const ts = summary.generatedAt || '';
  document.getElementById('masthead-ts').textContent =
    ts ? ('Generated ' + ts.split('T')[0]) : '—';
  document.getElementById('imprint-line').textContent =
    (summary.version || 'v6') + ' · ' + (ts.split('T')[0] || 'locally');

  // Hero stats (run count is paper roster).
  document.getElementById('m-cases').textContent = String(summary.cases);
  document.getElementById('m-runs').textContent = String(runsIdx.runs.length);
  document.getElementById('m-traj').textContent = String(summary.trajectories.toLocaleString());

  // ---- Model+framework ticker (replaces case ticker) ----
  const ticker = document.getElementById('ticker');
  const tickRuns = [...runsIdx.runs, ...runsIdx.runs]; // duplicate for seamless scroll
  ticker.innerHTML = tickRuns.map(r => `
    <span class="t-item">
      ${MARKS.vendor(r.vendor)}
      <span class="t-text"><span class="t-model">${AT.escape(r.model)}</span> <span class="t-fw">${AT.escape(r.framework)}</span></span>
      ${MARKS.framework(r.framework)}
    </span>
  `).join('');

  // ---- Per-model results bar chart ----
  const bars = document.getElementById('model-bars');
  const rows = [...runsIdx.runs].sort((a, b) => {
    if (a.data_pending && !b.data_pending) return 1;
    if (!a.data_pending && b.data_pending) return -1;
    return (a.asr ?? 1) - (b.asr ?? 1);
  });
  bars.innerHTML = rows.map(r => modelBarRow(r)).join('');

  // ---- Overall verdict distribution ----
  const order = ['attack_succeeded','attack_blocked','attack_not_triggered','benign_correct','benign_false_positive','utility_incomplete','infra_issue','pending_judge','unknown'];
  const tally = {};
  runsIdx.runs.forEach(r => {
    Object.entries(r.tally || {}).forEach(([k,v]) => { tally[k] = (tally[k]||0) + v; });
  });
  const total = Object.values(tally).reduce((a,b)=>a+b, 0);
  const bar = document.getElementById('overall-bar');
  const legend = document.getElementById('overall-legend');
  order.forEach(k => {
    const n = tally[k] || 0;
    if (!n) return;
    const pct = (n / total) * 100;
    const span = document.createElement('span');
    span.className = AT.VERDICTS[k].cls;
    span.style.width = pct + '%';
    span.title = `${AT.VERDICTS[k].label} · ${n} (${pct.toFixed(1)}%)`;
    bar.appendChild(span);
    const item = document.createElement('span');
    item.className = 'item';
    item.innerHTML = `<i class="swatch ${AT.VERDICTS[k].cls}"></i>${AT.VERDICTS[k].short} · ${n.toLocaleString()} (${pct.toFixed(1)}%)`;
    legend.appendChild(item);
  });

  // ---- DIM distribution ----
  const dimList = document.getElementById('dim-list');
  const dims = Object.entries(summary.dims).sort((a,b) => b[1]-a[1]);
  const maxDim = Math.max(...dims.map(d => d[1]));
  dims.forEach(([dim, n]) => {
    const w = (n / maxDim) * 100;
    const row = document.createElement('div');
    row.className = 'dim-row';
    row.innerHTML = `
      <span>${AT.escape(dim.replace(/^DIM(\d+)_/, '$1 · '))}</span>
      <span class="dim-bar"><i style="width:${w}%"></i></span>
      <span class="right">${n}</span>
    `;
    dimList.appendChild(row);
  });

  // ---- Featured exhibits ----
  const featured = pickFeatured(casesIdx.cases);
  const fEl = document.getElementById('featured');
  featured.forEach(c => fEl.appendChild(renderExhibit(c)));

  function pickFeatured(cases) {
    const malicious = cases.filter(c => !c.is_benign);
    function asCount(c) { return c.verdicts.filter(s => s === 'AS').length; }
    function blkCount(c) { return c.verdicts.filter(s => s === 'BLK').length; }
    const mostAttacked = [...malicious].sort((a,b) => asCount(b) - asCount(a))[0];
    const mostBlocked = [...malicious].sort((a,b) => blkCount(b) - blkCount(a))[0];
    const benign = cases.filter(c => c.is_benign);
    const trickyBenign = [...benign].sort((a,b) =>
      (b.verdicts.filter(s => s === 'BFP' || s === 'UI').length) -
      (a.verdicts.filter(s => s === 'BFP' || s === 'UI').length)
    )[0];
    const seen = new Set();
    return [mostAttacked, mostBlocked, trickyBenign].filter(c => c && !seen.has(c.id) && seen.add(c.id));
  }

  function renderExhibit(c) {
    const a = document.createElement('a');
    a.className = 'exhibit';
    a.href = './case.html?id=' + c.id;
    a.style.borderBottom = '1px solid var(--rule)';
    a.style.color = 'inherit';
    const benignTag = c.is_benign ? '<span class="benign-mark">benign</span>' : '';
    a.innerHTML = `
      <div class="num">№${String(c.id).padStart(3, '0')}</div>
      <div class="skill"><span>${AT.escape(c.dim.replace(/^DIM(\d+)_/, '$1 · '))}</span> · ${AT.escape(c.skill)} ${benignTag}</div>
      <div class="blurb">${AT.escape(c.plan)}</div>
      <div class="strip">${AT.strip(c.verdicts)}</div>
      <div class="open"><span class="muted" style="font-family:JetBrains Mono,monospace; font-size:11px; letter-spacing:.14em; text-transform:uppercase;">Open case file</span><span class="arr">→ ${String(c.id).padStart(3,'0')}</span></div>
    `;
    return a;
  }

  function modelBarRow(r) {
    if (r.data_pending) {
      return `
        <div class="mbar pending">
          <div class="mbar-mark">${MARKS.vendor(r.vendor)}</div>
          <div class="mbar-label">
            <div class="m-model">${AT.escape(r.model)}</div>
            <div class="m-fw">${AT.escape(r.framework)}</div>
          </div>
          <div class="mbar-bars muted" style="font-family:'Fraunces',serif; font-size:18px; font-variation-settings:'SOFT' 50,'opsz' 36;">data pending</div>
          <div class="mbar-cases muted">—</div>
        </div>
      `;
    }
    const hasSec = r.asr != null;          // Observed denominator is non-zero.
    const asW  = hasSec ? (r.asr * 100).toFixed(1) : 0;
    const blkW = hasSec ? (r.blocked_rate * 100).toFixed(1) : 0;
    const bcW  = r.benign_total ? (r.benign_acc * 100).toFixed(1) : 0;
    const uiW  = (r.ui_rate * 100).toFixed(1);
    const judgingNote = (!hasSec && r.pending_judge_count)
      ? `<div class="mb-row"><span class="mb-key">PJ</span><span class="mb-bar"><i class="pj" style="width:100%; background:var(--pj);"></i></span><span class="mb-val">${r.pending_judge_count} cases awaiting judge</span></div>`
      : '';
    return `
      <a class="mbar" href="./run.html?id=${encodeURIComponent(r.id)}">
        <div class="mbar-mark">${MARKS.vendor(r.vendor)}</div>
        <div class="mbar-label">
          <div class="m-model">${AT.escape(r.model)}</div>
          <div class="m-fw">${MARKS.framework(r.framework)}<span>${AT.escape(r.framework)}</span></div>
        </div>
        <div class="mbar-bars">
          <div class="mb-row">
            <span class="mb-key">ASR</span>
            <span class="mb-bar"><i class="as" style="width:${asW}%"></i></span>
            <span class="mb-val">${hasSec ? AT.pct(r.asr) : '—'}</span>
          </div>
          <div class="mb-row">
            <span class="mb-key">BLK</span>
            <span class="mb-bar"><i class="blk" style="width:${blkW}%"></i></span>
            <span class="mb-val">${hasSec ? AT.pct(r.blocked_rate) : '—'}</span>
          </div>
          <div class="mb-row">
            <span class="mb-key">BC</span>
            <span class="mb-bar"><i class="bc" style="width:${bcW}%"></i></span>
            <span class="mb-val">${r.benign_total ? AT.pct(r.benign_acc) : '—'}</span>
          </div>
          ${judgingNote || `<div class="mb-row">
            <span class="mb-key">UI</span>
            <span class="mb-bar"><i class="ui" style="width:${uiW}%"></i></span>
            <span class="mb-val">${AT.pct(r.ui_rate)}</span>
          </div>`}
        </div>
        <div class="mbar-cases">
          <div class="n">${hasSec ? r.observed_denom : (r.pending_judge_count || 0)}</div>
          <div class="lbl">${hasSec ? 'AS + BLK' : 'pending<br>judge'}</div>
        </div>
      </a>
    `;
  }
})();
