(async function() {
  const params = new URLSearchParams(location.search);
  const runId = params.get('run');
  const caseId = parseInt(params.get('case') || '0', 10);
  const root = document.getElementById('traj-content');
  const back = document.getElementById('back-link');
  back.href = './case.html?id=' + caseId;
  back.textContent = '← Back to case Nº ' + String(caseId).padStart(3, '0');

  let traj, runMeta, caseMeta;
  try {
    [traj, runMeta, caseMeta] = await Promise.all([
      AT.json('./data/traj/' + runId + '/' + caseId + '.json'),
      AT.json('./data/runs/' + runId + '.json').catch(() => null),
      AT.json('./data/cases/' + caseId + '.json').catch(() => null),
    ]);
  } catch (e) {
    root.innerHTML = `<div class="no-results">Trajectory for case Nº${caseId} on run "${AT.escape(runId)}" not found.</div>`;
    return;
  }

  document.title = `Trace · Case ${caseId} · ${runMeta ? runMeta.label : runId} · AgentTrap`;
  document.getElementById('imprint-line').textContent = `Case ${caseId} · ${runId}`;
  document.getElementById('masthead-ts').textContent = `Trace · Nº${String(caseId).padStart(3,'0')}`;

  const v = traj.verdict || 'unknown';
  const conf = (typeof traj.confidence === 'number') ? traj.confidence.toFixed(2) : (traj.confidence || '—');
  const turnsCount = (traj.turns || []).length;

  const skill = caseMeta ? caseMeta.skill : '';
  const variant = caseMeta ? caseMeta.variant : '';
  const dim = caseMeta ? caseMeta.dim.replace(/^DIM(\d+)_/, '$1 · ') : '';

  root.innerHTML = `
    <section class="traj-head rise d1">
      <div>
        <p class="eyebrow">Trace</p>
        <div class="title">Case Nº${String(caseId).padStart(3,'0')} <span class="muted" style="font-size:0.5em;">/ ${AT.escape(skill)}</span></div>
        <div class="subtitle">${AT.escape(runMeta ? runMeta.label : runId)} · ${AT.escape(runMeta ? runMeta.model : '')} · ${AT.escape(runMeta ? runMeta.framework : '')}</div>
      </div>
      <div>${AT.pill(v)}</div>
    </section>

    <section class="traj-info rise d2">
      <div class="cell"><div class="lbl">Turns captured</div><div class="v">${turnsCount}${traj.truncated_turns ? ' +' : ''}</div></div>
      <div class="cell"><div class="lbl">Confidence</div><div class="v">${conf}</div></div>
      <div class="cell"><div class="lbl">Terminated</div><div class="v" style="font-size:14px; line-height:1.3;">${AT.escape(traj.terminated_by || '—')}</div></div>
      <div class="cell"><div class="lbl">Dim</div><div class="v" style="font-size:14px; line-height:1.3;">${AT.escape(dim)}</div></div>
    </section>

    ${traj.evidence ? `<section class="rise d3" style="padding: 24px 0; border-bottom: var(--hairline);"><p class="eyebrow">Adjudicator note</p><p class="serif" style="font-size: 17px; line-height: 1.5; max-width: 70ch; font-variation-settings:'SOFT' 50,'opsz' 36;">${AT.escape(traj.evidence)}</p></section>` : ''}

    <div class="turns rise d4">${renderTurns(traj.turns || [])}</div>

    ${traj.truncated_turns ? `<p class="truncated-note">Trace truncated to first ${turnsCount} turns. Full log: <code>${AT.escape(traj.source_path)}</code>.</p>` : ''}
  `;

  function renderTurns(turns) {
    if (!turns.length) return `
      <div style="padding: 32px 0; border-top: 1px dashed var(--rule-soft);">
        <p class="eyebrow" style="color:var(--ui);">Trace unavailable</p>
        <p class="serif" style="font-size:17px; line-height:1.5; max-width:60ch; font-variation-settings:'SOFT' 50,'opsz' 36;">
          The verdict and adjudicator note above were judged from a trajectory that
          was not synced to this site. The raw log lives in the private results
          tree at <code>${AT.escape(traj.source_path || '—')}</code>.
        </p>
      </div>`;
    return turns.map(t => `
      <div class="turn">
        <div class="marker">
          <span class="n">${String(t.turn).padStart(2,'0')}</span>
          Turn
        </div>
        <div class="body">
          ${t.text ? `<div class="text">${AT.escape(t.text)}${t.text_truncated ? '<span class="truncated-note"> … (truncated)</span>' : ''}</div>` : ''}
          ${(t.tools || []).map(renderTool).join('')}
        </div>
      </div>
    `).join('');
  }

  function renderTool(tool) {
    const argStr = (typeof tool.args === 'object') ? JSON.stringify(tool.args, null, 2) : String(tool.args || '');
    return `
      <div class="tool-call">
        <span class="tool-name">⚙ ${AT.escape(tool.name || 'tool')}</span>
        ${argStr && argStr !== '{}' ? `<details><summary>arguments</summary><pre>${AT.escape(argStr)}</pre></details>` : ''}
        ${tool.result ? `<details open><summary>result</summary><pre>${AT.escape(tool.result)}</pre></details>` : ''}
      </div>
    `;
  }
})();
