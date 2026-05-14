(async function() {
  AT.setActive('runs');
  const params = new URLSearchParams(location.search);
  const id = params.get('id');
  const root = document.getElementById('run-content');
  if (!id) { root.innerHTML = '<div class="no-results">Missing run id.</div>'; return; }

  let run;
  try { run = await AT.json('./data/runs/' + id + '.json'); }
  catch (e) { root.innerHTML = `<div class="no-results">Run "${AT.escape(id)}" not found.</div>`; return; }

  document.title = `${run.label} · AgentTrap`;
  document.getElementById('imprint-line').textContent = id;
  document.getElementById('masthead-ts').textContent = id;

  const tally = run.tally || {};
  const total = Object.values(tally).reduce((a,b) => a + b, 0);
  const scored = Object.entries(tally).filter(([k]) => k !== 'missing' && k !== 'infra_issue').reduce((a, [,v]) => a + v, 0);

  root.innerHTML = `
    <section class="case-head rise d1">
      <div>
        <p class="serial">Run</p>
        <h2 class="serif" style="font-size: clamp(40px, 6vw, 96px); line-height: 0.95; margin-top: 16px; letter-spacing:-0.02em;">${AT.escape(run.label)}</h2>
        <p class="muted" style="font-family:JetBrains Mono,monospace; font-size:12px; margin-top:8px;">${AT.escape(run.id)}</p>
        <div class="tags" style="margin-top:16px;">
          <span class="tag dim">${AT.escape(run.framework)}</span>
          <span class="tag">${AT.escape(run.model)}</span>
        </div>
      </div>
      <div style="min-width:260px; flex:1; max-width: 480px;">
        <div style="display:grid; grid-template-columns: repeat(3,1fr); gap: 12px;">
          <div><div class="eyebrow">Observed ASR</div><div style="font-family:'Fraunces',serif; font-size:36px; color:var(--as); font-variation-settings:'SOFT' 80,'opsz' 60; letter-spacing:-0.02em;">${run.asr != null ? AT.pct(run.asr) : '—'}</div><div class="muted" style="font-size:10px; letter-spacing:0.1em;">AS / (AS+BLK), n=${run.observed_denom || 0}</div></div>
          <div><div class="eyebrow">Blocked</div><div style="font-family:'Fraunces',serif; font-size:36px; color:var(--blk); font-variation-settings:'SOFT' 80,'opsz' 60; letter-spacing:-0.02em;">${run.blocked_rate != null ? AT.pct(run.blocked_rate) : '—'}</div></div>
          <div><div class="eyebrow">Excluded</div><div style="font-family:'Fraunces',serif; font-size:36px; color:var(--ink-mute); font-variation-settings:'SOFT' 80,'opsz' 60; letter-spacing:-0.02em;">${run.excluded_mal || 0}</div><div class="muted" style="font-size:10px; letter-spacing:0.1em;">malicious cases</div></div>
        </div>
      </div>
    </section>

    <section style="padding: 32px 0 16px;">
      <p class="eyebrow">Verdict mix · ${total} total · ${scored} scored</p>
      <div class="distbar" style="margin-top:10px;">${distbarHTML(tally, total)}</div>
      <div class="legend-strip" style="padding-top:12px;">${legendHTML(tally)}</div>
    </section>

    <section class="results-section">
      <p class="eyebrow">§ Cases — ${run.cases.length} entries</p>
      <h3 class="serif" style="margin-bottom:24px;">Case-by-case verdicts.</h3>
      <div class="toolbar" style="grid-template-columns: 2fr 1fr 1fr 1fr; padding-bottom: 12px;">
        <div class="field">
          <label class="label">Search</label>
          <input id="run-q" type="search" placeholder="case, skill, dim…">
        </div>
        <div class="field">
          <label class="label">Verdict</label>
          <select id="run-v"><option value="">Any</option>
            <option value="attack_succeeded">Attack succeeded</option>
            <option value="attack_blocked">Attack blocked</option>
            <option value="attack_not_triggered">Not triggered</option>
            <option value="benign_correct">Benign correct</option>
            <option value="benign_false_positive">Benign false positive</option>
            <option value="utility_incomplete">Utility incomplete</option>
            <option value="infra_issue">Infra issue</option>
            <option value="pending_judge">Pending judge</option>
            <option value="missing">Missing</option>
          </select>
        </div>
        <div class="field">
          <label class="label">Intent</label>
          <select id="run-i"><option value="">Any</option><option value="malicious">Malicious</option><option value="benign">Benign</option></select>
        </div>
        <div class="field">
          <label class="label">Sort</label>
          <select id="run-sort">
            <option value="id">Case Nº</option>
            <option value="verdict">By verdict</option>
            <option value="dim">By dimension</option>
          </select>
        </div>
      </div>
      <table class="results-table">
        <thead>
          <tr>
            <th style="width:72px;">Case</th>
            <th>Dim</th>
            <th>Skill</th>
            <th>Intent</th>
            <th>Verdict</th>
            <th class="right">Trajectory</th>
          </tr>
        </thead>
        <tbody id="rc-body"></tbody>
      </table>
      <p class="muted" id="rc-count" style="font-family:JetBrains Mono,monospace; font-size:11px; padding:16px 0 64px;">—</p>
    </section>
  `;

  const q = document.getElementById('run-q');
  const fV = document.getElementById('run-v');
  const fI = document.getElementById('run-i');
  const fS = document.getElementById('run-sort');
  const tbody = document.getElementById('rc-body');
  const countEl = document.getElementById('rc-count');

  function rerender() {
    const term = (q.value || '').toLowerCase().trim();
    const v = fV.value;
    const intent = fI.value;
    const sort = fS.value;

    let rows = run.cases.filter(c => {
      if (v && c.verdict !== v) return false;
      if (intent === 'benign' && !c.is_benign) return false;
      if (intent === 'malicious' && c.is_benign) return false;
      if (term) {
        const hay = (c.case + ' ' + c.skill + ' ' + c.dim).toLowerCase();
        if (!hay.includes(term)) return false;
      }
      return true;
    });

    if (sort === 'id') rows.sort((a,b) => a.case - b.case);
    else if (sort === 'verdict') rows.sort((a,b) => (a.verdict||'').localeCompare(b.verdict||'') || a.case - b.case);
    else if (sort === 'dim') rows.sort((a,b) => a.dim.localeCompare(b.dim) || a.case - b.case);

    tbody.innerHTML = rows.map(c => {
      const trajHref = c.trajectory
        ? `./traj.html?run=${encodeURIComponent(run.id)}&case=${c.case}`
        : null;
      const caseLink = `<a href="./case.html?id=${c.case}" onclick="event.stopPropagation()" class="muted" style="font-family:JetBrains Mono,monospace; font-size:10.5px; letter-spacing:0.14em; text-transform:uppercase; border-bottom:1px solid var(--rule-soft);">Case spec →</a>`;
      const intentTag = c.is_benign
        ? '<span class="benign-mark">benign</span>'
        : '<span class="benign-mark" style="color:var(--as); border-color:var(--as);">malicious</span>';
      const rowClick = trajHref
        ? `style="cursor:pointer;" onclick="location.href='${trajHref}'"`
        : `style="cursor:default;"`;
      return `
        <tr ${rowClick}>
          <td><span style="font-family:'Fraunces',serif; font-size:24px; font-variation-settings:'SOFT' 80,'opsz' 60;">№${String(c.case).padStart(3,'0')}</span></td>
          <td class="muted">${AT.escape(c.dim.replace(/^DIM(\d+)_/, '$1 · '))}</td>
          <td>${AT.escape(c.skill)}</td>
          <td>${intentTag}</td>
          <td>${AT.pill(c.verdict, c.short)}</td>
          <td class="right">${trajHref ? '<span style="font-family:JetBrains Mono,monospace; font-size:10.5px; letter-spacing:0.14em; text-transform:uppercase;">Trace →</span>' : '<span class="no-traj">— no trace</span>'} &nbsp; ${caseLink}</td>
        </tr>
      `;
    }).join('');
    countEl.textContent = rows.length + ' / ' + run.cases.length + ' cases shown';
  }
  [q, fV, fI, fS].forEach(el => el.addEventListener('input', rerender));
  rerender();

  function distbarHTML(tally, total) {
    if (!total) return '';
    const order = ['attack_succeeded','attack_blocked','attack_not_triggered','benign_correct','benign_false_positive','utility_incomplete','infra_issue','pending_judge','missing','unknown'];
    return order.map(k => {
      const n = tally[k] || 0;
      if (!n) return '';
      const cls = (AT.VERDICTS[k] && AT.VERDICTS[k].cls) || 'unknown';
      return `<span class="${cls}" style="width:${(n/total*100).toFixed(2)}%" title="${k}: ${n}"></span>`;
    }).join('');
  }
  function legendHTML(tally) {
    const order = ['attack_succeeded','attack_blocked','attack_not_triggered','benign_correct','benign_false_positive','utility_incomplete','infra_issue','pending_judge','missing'];
    return order.map(k => {
      const n = tally[k] || 0;
      if (!n) return '';
      const cls = (AT.VERDICTS[k] && AT.VERDICTS[k].cls) || 'unknown';
      return `<span class="item"><i class="swatch ${cls}"></i>${AT.VERDICTS[k].short} ${n}</span>`;
    }).join('');
  }
})();
