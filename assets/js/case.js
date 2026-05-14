(async function() {
  AT.setActive('cases');
  const params = new URLSearchParams(location.search);
  const id = parseInt(params.get('id') || '1', 10);
  const root = document.getElementById('case-content');

  let detail;
  try {
    detail = await AT.json('./data/cases/' + id + '.json');
  } catch (e) {
    root.innerHTML = `<div class="no-results">Case file Nº ${id} could not be found.</div>`;
    return;
  }

  document.title = `Case Nº ${id} · ${detail.skill} · AgentTrap`;
  document.getElementById('imprint-line').textContent = `v6 · case ${id}`;
  document.getElementById('masthead-ts').textContent = `Case file Nº ${String(id).padStart(3,'0')}`;

  // Build verdict tally for header summary bar.
  const tally = {};
  detail.results.forEach(r => { tally[r.verdict] = (tally[r.verdict] || 0) + 1; });
  const total = detail.results.length;

  const benignTag = detail.is_benign
    ? '<span class="tag benign">benign task</span>'
    : '<span class="tag malicious">malicious target</span>';

  const head = `
    <div class="case-head rise d1">
      <div class="title-block">
        <p class="serial">Case file · Nº${String(id).padStart(3,'0')}</p>
        <h2 class="serif">${AT.escape(detail.skill)} <span class="muted" style="font-family:JetBrains Mono,monospace; font-size:14px;">· ${AT.escape(detail.variant)}</span></h2>
        <p class="source-line">${AT.escape(detail.source)}</p>
        <div class="tags">
          <span class="tag dim">${AT.escape(detail.dim.replace(/^DIM(\d+)_/, '$1 · '))}</span>
          <span class="tag modality">${AT.escape(detail.modality)}</span>
          ${benignTag}
          ${(detail.mitre || []).map(t => `<span class="tag mitre">MITRE ${AT.escape(t)}</span>`).join('')}
          ${(detail.atlas || []).map(t => `<span class="tag atlas">ATLAS ${AT.escape(t)}</span>`).join('')}
        </div>
      </div>
      <div class="number-wrap">
        <div class="number">Nº${String(id).padStart(3,'0')}</div>
      </div>
    </div>

    <div class="case-body-grid rise d2">
      <div class="block">
        <h4>User trigger</h4>
        <div class="prose">${AT.escape(detail.trigger)}</div>
      </div>
      <div class="block">
        <h4>Brief plan</h4>
        <div class="prose">${AT.escape(detail.plan)}</div>
        <div class="spacer-sm"></div>
        <h4 style="color:var(--blk);">Pass condition</h4>
        <div class="prose mono accent blk">${AT.escape(detail.pass)}</div>
        <div class="spacer-sm"></div>
        <h4 style="color:var(--as);">Fail condition</h4>
        <div class="prose mono accent as">${AT.escape(detail.fail)}</div>
        ${detail.signal ? `<div class="spacer-sm"></div><h4>Success signal</h4><div class="prose mono">${AT.escape(detail.signal)}</div>` : ''}
      </div>
    </div>

    <section class="results-section rise d3">
      <div style="display:flex; justify-content: space-between; align-items: flex-end; gap: 24px; flex-wrap: wrap; margin-bottom: 32px;">
        <div>
          <p class="eyebrow">§ Results</p>
          <h3 class="serif">How every run handled this case.</h3>
        </div>
        <div style="min-width: 260px; flex: 1; max-width: 480px;">
          <div class="distbar">${distbarHTML(tally, total)}</div>
          <div class="legend-strip" style="margin-top: 8px;">${legendHTML(tally, total)}</div>
        </div>
      </div>
      <table class="results-table">
        <thead>
          <tr>
            <th style="width:48px;">Verdict</th>
            <th>Run</th>
            <th>Model · framework</th>
            <th style="width:64px;">Conf.</th>
            <th>Evidence</th>
            <th style="width:120px;" class="right">Trajectory</th>
          </tr>
        </thead>
        <tbody>${detail.results.map(rowHTML).join('')}</tbody>
      </table>
    </section>
  `;
  root.innerHTML = head;

  // Wire row hover scroll-into-context-friendly: nothing extra needed.

  function rowHTML(r) {
    const trajCell = r.trajectory
      ? `<a class="open-btn" href="./traj.html?run=${encodeURIComponent(r.sourceId)}&case=${id}">Open →</a>`
      : '<span class="no-traj">— no trace</span>';
    const conf = (typeof r.confidence === 'number') ? r.confidence.toFixed(2) : (r.confidence || '—');
    return `
      <tr>
        <td>${AT.pill(r.verdict, r.short)}</td>
        <td><div style="font-family:'Fraunces',serif; font-size:17px; font-variation-settings:'SOFT' 50,'opsz' 36;">${AT.escape(r.label)}</div><div class="muted" style="font-size:10.5px; text-transform:uppercase; letter-spacing:0.1em; margin-top:2px;">${AT.escape(r.sourceId)}</div></td>
        <td>${AT.escape(r.model)} <span class="muted">· ${AT.escape(r.framework)}</span></td>
        <td class="muted">${conf}</td>
        <td class="ev">${AT.escape(r.evidence || '—')}</td>
        <td class="right">${trajCell}</td>
      </tr>
    `;
  }

  function distbarHTML(tally, total) {
    if (!total) return '';
    const order = ['attack_succeeded','attack_blocked','attack_not_triggered','benign_correct','benign_false_positive','utility_incomplete','infra_issue','pending_judge','missing','unknown'];
    return order.map(k => {
      const n = tally[k] || 0;
      if (!n) return '';
      const cls = (AT.VERDICTS[k] && AT.VERDICTS[k].cls) || 'unknown';
      const label = (AT.VERDICTS[k] && AT.VERDICTS[k].label) || k;
      return `<span class="${cls}" style="width:${(n/total*100).toFixed(2)}%" title="${label}: ${n}"></span>`;
    }).join('');
  }
  function legendHTML(tally, total) {
    const order = ['attack_succeeded','attack_blocked','benign_correct','benign_false_positive','utility_incomplete','attack_not_triggered','infra_issue','pending_judge','missing'];
    return order.map(k => {
      const n = tally[k] || 0;
      if (!n) return '';
      const cls = (AT.VERDICTS[k] && AT.VERDICTS[k].cls) || 'unknown';
      return `<span class="item"><i class="swatch ${cls}"></i>${AT.VERDICTS[k].short} ${n}</span>`;
    }).join('');
  }
})();
