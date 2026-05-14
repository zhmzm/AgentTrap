(async function() {
  AT.setActive('runs');
  const data = await AT.json('./data/runs/index.json');
  const runs = data.runs;
  document.getElementById('masthead-ts').textContent =
    data.generatedAt ? ('Generated ' + data.generatedAt.split('T')[0]) : '—';
  document.getElementById('imprint-line').textContent =
    (data.generatedAt ? data.generatedAt.split('T')[0] : '—');

  const fFw = document.getElementById('f-framework');
  [...new Set(runs.map(r => r.framework))].sort().forEach(f => {
    const o = document.createElement('option');
    o.value = f; o.textContent = f;
    fFw.appendChild(o);
  });

  const q = document.getElementById('q');
  const fSc = document.getElementById('f-scored');
  const fSort = document.getElementById('f-sort');
  const body = document.getElementById('runs-body');
  const count = document.getElementById('count');

  function render() {
    const term = (q.value || '').toLowerCase().trim();
    const fw = fFw.value;
    const minSc = parseInt(fSc.value, 10);
    const sort = fSort.value;

    let rows = runs.filter(r => {
      if (fw && r.framework !== fw) return false;
      if ((r.scored || 0) < minSc && !r.data_pending) return false;
      if (term) {
        const hay = (r.label + ' ' + r.model + ' ' + r.framework + ' ' + (r.id || '')).toLowerCase();
        if (!hay.includes(term)) return false;
      }
      return true;
    });

    // Stable sort that always pushes data_pending rows last.
    const pick = key => r => (r.data_pending ? null : r[key]);
    function num(a, b, descending) {
      const av = a, bv = b;
      if (av == null && bv == null) return 0;
      if (av == null) return 1;
      if (bv == null) return -1;
      return descending ? bv - av : av - bv;
    }
    const cmp = {
      'asr-asc':  (a,b) => num(pick('asr')(a),         pick('asr')(b),         false),
      'asr-desc': (a,b) => num(pick('asr')(a),         pick('asr')(b),         true),
      'blk-desc': (a,b) => num(pick('blocked_rate')(a),pick('blocked_rate')(b),true),
      'bc-desc':  (a,b) => num(pick('benign_acc')(a),  pick('benign_acc')(b),  true),
      'ui-desc':  (a,b) => num(pick('ui_rate')(a),     pick('ui_rate')(b),     true),
    }[sort];
    rows.sort(cmp);

    // Champion / Worst flags — based on the full scored roster, not the
    // filtered view, so badges remain stable as filters change.
    const scoredRuns = runs.filter(r => !r.data_pending && r.asr != null);
    const champion = scoredRuns.reduce((b, r) => (b == null || r.asr < b.asr ? r : b), null);
    const worst    = scoredRuns.reduce((b, r) => (b == null || r.asr > b.asr ? r : b), null);
    const flagFor  = r =>
      !r || r.data_pending ? null
      : r === champion ? 'champion'
      : r === worst    ? 'worst'
      : null;

    body.innerHTML = '';
    if (rows.length === 0) {
      body.innerHTML = '<tr><td colspan="10" class="no-results" style="padding: 64px 0;">No runs match those filters.</td></tr>';
    } else {
      rows.forEach((r, i) => body.appendChild(renderRow(r, i + 1, flagFor(r))));
    }
    count.textContent = rows.length + ' / ' + runs.length + ' runs shown';
  }

  function renderRow(r, rank, flag) {
    const tr = document.createElement('tr');
    if (flag) tr.classList.add('flag-' + flag);
    if (r.data_pending) {
      tr.style.opacity = 0.5;
      tr.style.cursor = 'default';
      tr.innerHTML = `
        <td><span class="rank">—</span></td>
        <td><div class="runname">${AT.escape(r.label)}</div><div class="meta">data pending</div></td>
        <td>${AT.escape(r.model)}</td>
        <td class="muted">${AT.escape(r.framework)}</td>
        <td class="rate">—</td>
        <td class="muted" colspan="4" style="font-family:'Fraunces',serif; font-size:16px; font-variation-settings:'SOFT' 50,'opsz' 24;">awaiting run</td>
        <td class="right muted">—</td>
      `;
      return tr;
    }
    tr.addEventListener('click', () => window.location.href = './run.html?id=' + encodeURIComponent(r.id));
    const hasSec = r.asr != null;
    const badge = flag === 'champion'
      ? '<span class="run-badge champion">★ Champion</span>'
      : flag === 'worst'
      ? '<span class="run-badge worst">Worst</span>'
      : '';
    tr.innerHTML = `
      <td><span class="rank">${String(rank).padStart(2,'0')}</span></td>
      <td>
        <div class="runname">${AT.escape(r.label)} ${badge}</div>
        <div class="meta">${AT.escape(r.id)}</div>
      </td>
      <td>${AT.escape(r.model)}</td>
      <td class="muted">${AT.escape(r.framework)}</td>
      <td class="rate">${hasSec ? r.observed_denom : (r.pending_judge_count || 0)}<div class="muted" style="font-size:9.5px;">${hasSec ? 'AS+BLK' : 'PJ'}</div></td>
      <td><div class="bar"><i style="width:${hasSec ? (r.asr*100).toFixed(1) : 0}%"></i></div><div class="muted" style="font-size:10px; margin-top:2px;">${hasSec ? AT.pct(r.asr) : '— PJ'}</div></td>
      <td><div class="bar blk"><i style="width:${hasSec ? (r.blocked_rate*100).toFixed(1) : 0}%"></i></div><div class="muted" style="font-size:10px; margin-top:2px;">${hasSec ? AT.pct(r.blocked_rate) : '—'}</div></td>
      <td><div class="bar bc"><i style="width:${r.benign_total ? (r.benign_acc*100).toFixed(1) : 0}%"></i></div><div class="muted" style="font-size:10px; margin-top:2px;">${r.benign_total ? AT.pct(r.benign_acc) : '—'} <span class="muted">(${r.benign_total})</span></div></td>
      <td class="rate right muted">${AT.pct(r.ui_rate)}</td>
      <td class="right">→</td>
    `;
    return tr;
  }

  [q, fFw, fSc, fSort].forEach(el => el.addEventListener('input', render));
  render();
})();
