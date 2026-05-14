(async function() {
  AT.setActive('cases');

  const data = await AT.json('./data/cases/index.json');
  const cases = data.cases;
  document.getElementById('masthead-ts').textContent =
    data.generatedAt ? ('Generated ' + data.generatedAt.split('T')[0]) : '—';
  document.getElementById('imprint-line').textContent =
    (data.version || 'v6') + ' · ' + (data.generatedAt ? data.generatedAt.split('T')[0] : 'local');

  // Populate filters.
  const dims = [...new Set(cases.map(c => c.dim))].sort();
  const mods = [...new Set(cases.map(c => c.modality))].sort();
  const fDim = document.getElementById('f-dim');
  dims.forEach(d => {
    const o = document.createElement('option');
    o.value = d; o.textContent = d.replace(/^DIM(\d+)_/, '$1 · ');
    fDim.appendChild(o);
  });
  const fMod = document.getElementById('f-mod');
  mods.forEach(m => {
    const o = document.createElement('option');
    o.value = m; o.textContent = m;
    fMod.appendChild(o);
  });

  const q = document.getElementById('q');
  const fIntent = document.getElementById('f-intent');
  const fVerdict = document.getElementById('f-verdict');
  const fSort = document.getElementById('f-sort');
  const list = document.getElementById('case-list');
  const count = document.getElementById('count-line');

  function asCount(c)  { return c.verdicts.filter(s => s === 'AS').length; }
  function blkCount(c) { return c.verdicts.filter(s => s === 'BLK').length; }

  function render() {
    const term = (q.value || '').toLowerCase().trim();
    const dim = fDim.value;
    const mod = fMod.value;
    const intent = fIntent.value;
    const verdict = fVerdict.value;
    const sort = fSort.value;

    let rows = cases.filter(c => {
      if (dim && c.dim !== dim) return false;
      if (mod && c.modality !== mod) return false;
      if (intent === 'benign' && !c.is_benign) return false;
      if (intent === 'malicious' && c.is_benign) return false;
      if (verdict && !c.verdicts.includes(verdict)) return false;
      if (term) {
        const hay = (c.skill + ' ' + c.variant + ' ' + c.plan + ' ' + c.dim + ' ' + c.modality).toLowerCase();
        if (!hay.includes(term)) return false;
      }
      return true;
    });

    if (sort === 'id') rows.sort((a,b) => a.id - b.id);
    else if (sort === 'as') rows.sort((a,b) => asCount(b) - asCount(a) || a.id - b.id);
    else if (sort === 'blk') rows.sort((a,b) => blkCount(b) - blkCount(a) || a.id - b.id);
    else if (sort === 'skill') rows.sort((a,b) => a.skill.localeCompare(b.skill));

    list.innerHTML = '';
    if (rows.length === 0) {
      list.innerHTML = '<div class="no-results">No case files match those filters.</div>';
    } else {
      const frag = document.createDocumentFragment();
      rows.forEach(c => frag.appendChild(renderRow(c)));
      list.appendChild(frag);
    }
    count.textContent = rows.length + ' / ' + cases.length + ' case files shown';
  }

  function renderRow(c) {
    const a = document.createElement('a');
    a.className = 'case-row';
    a.href = './case.html?id=' + c.id;
    a.style.color = 'inherit';
    a.style.borderBottom = '1px dashed var(--rule-soft)';

    const benignTag = c.is_benign
      ? '<span class="benign-mark">benign</span>'
      : '<span class="benign-mark" style="color:var(--as); border-color:var(--as);">malicious</span>';

    const as = asCount(c);
    const blk = blkCount(c);

    a.innerHTML = `
      <div class="case-num">№${String(c.id).padStart(3,'0')}</div>
      <div class="case-meta">
        <span class="tag" style="color:var(--ink);">${AT.escape(c.dim.replace(/^DIM(\d+)_/, '$1 · '))}</span>
        <span class="tag muted">${AT.escape(c.modality)}</span>
        <span>${benignTag}</span>
      </div>
      <div class="case-body">
        <div class="skill">${AT.escape(c.skill)} · ${AT.escape(c.variant)}</div>
        <div>${AT.escape(c.plan)}</div>
      </div>
      <div class="case-strip">
        <div class="strip" aria-label="Verdicts across 24 runs">${AT.strip(c.verdicts)}</div>
        <div class="legend"><span style="color:var(--as);">${as} AS</span> · <span style="color:var(--blk);">${blk} BLK</span> · <span class="muted">${c.verdicts.filter(s => s === 'BC').length} BC</span></div>
      </div>
      <div class="case-arrow">→</div>
    `;
    return a;
  }

  [q, fDim, fMod, fIntent, fVerdict, fSort].forEach(el => el.addEventListener('input', render));
  render();
})();
