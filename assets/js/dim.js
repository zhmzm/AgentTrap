(async function() {
  AT.setActive('cases');

  const DIM_DESC = {
    DIM1_DataExfiltration: 'Stealing credentials, keys, environment variables, or workspace secrets.',
    DIM2_SystemIntegrity: 'File deletion, config corruption, shell rc tampering.',
    DIM3_PromptInjection: 'Injected instructions via untrusted artifacts, scraped pages, transcripts.',
    DIM4_ConfigPoisoning: 'Backdoors in config files, CLAUDE.md/SKILL.md poisoning, persistence.',
    DIM5_ResourceAbuse: 'Token bombs, infinite loops, runaway resource consumption.',
    DIM6_ContentSafetyBypass: 'Jailbreaks routed through skill content or generated artifacts.',
    DIM7_OutputTampering: 'Hidden bias, invisible text, data manipulation in deliverables.',
    DIM8_UnauthorizedDisclosure: 'Leaking private data to wrong audiences or external channels.',
    DIM9_CodeInjection: 'Embedding executable payloads in code or generated files.',
    DIM10_Disinformation: 'Coordinated false content, fake CVEs, vendor preference injection.',
    DIM11_CrossSkillCollusion: 'Skills conspiring across tool calls or sessions.',
    DIM12_SteganographicPayload: 'Base64, homoglyph, white-text payload concealment.',
    DIM13_SupplyChainAttack: 'Typosquatting, malicious pin dependencies.',
    DIM14_MCPAbuse: 'OAuth exfiltration, MCP proxy interception.',
    DIM15_PrivilegeEscalation: 'IAM escalation via MCP or tool chains.',
    DIM16_AutonomousAgentEnrollment: 'Recruiting agents into autonomous attack networks.',
  };

  const params = new URLSearchParams(location.search);
  const id = params.get('id');
  const root = document.getElementById('dim-content');
  if (!id || !DIM_DESC[id]) {
    root.innerHTML = `<div class="no-results">Unknown dimension "${AT.escape(id || '')}"</div>`;
    return;
  }

  const [casesIdx, runsIdx] = await Promise.all([
    AT.json('./data/cases/index.json'),
    AT.json('./data/runs/index.json'),
  ]);

  const m = id.match(/^DIM(\d+)_(.+)$/);
  const nn = m ? m[1] : '?';
  const humanName = m
    ? m[2].replace(/([A-Z])/g, ' $1').trim()
    : id;
  const desc = DIM_DESC[id];

  const ts = casesIdx.generatedAt || '';
  document.getElementById('masthead-ts').textContent =
    (ts ? ('Generated ' + ts.split('T')[0] + ' · ') : '') + 'Dim · ' + String(nn).padStart(2, '0');
  document.getElementById('imprint-line').textContent =
    (ts ? ts.split('T')[0] + ' · ' : '') + 'Dim ' + String(nn).padStart(2, '0');
  document.title = `Dim ${nn} · ${humanName} · AgentTrap`;

  const dimCases = casesIdx.cases.filter(c => c.dim === id).sort((a, b) => a.id - b.id);
  const malCount = dimCases.filter(c => !c.is_benign).length;
  const benCount = dimCases.filter(c => c.is_benign).length;

  // Per-sourceId tallies across this dim's cases.
  const order = casesIdx.sources_order || [];
  const perRun = {};
  order.forEach(sid => { perRun[sid] = { AS: 0, BLK: 0, ANT: 0, UI: 0, INF: 0, PJ: 0, BC: 0, BFP: 0, MISS: 0, OTHER: 0 }; });
  dimCases.forEach(c => {
    c.verdicts.forEach((v, i) => {
      const sid = order[i];
      if (!sid || !perRun[sid]) return;
      const slot = perRun[sid];
      if (slot[v] != null) slot[v]++;
      else if (v === '--') slot.MISS++;
      else slot.OTHER++;
    });
  });

  // Aggregate totals.
  let sumAS = 0, sumBLK = 0, sumExcl = 0;
  order.forEach(sid => {
    const r = perRun[sid];
    sumAS += r.AS;
    sumBLK += r.BLK;
    sumExcl += r.ANT + r.UI + r.INF + r.PJ;
  });
  const denom = sumAS + sumBLK;
  const asrAgg = denom > 0 ? (sumAS / denom) : null;

  // Per-run breakdown rows, joined with paper run metadata.
  const runById = {};
  runsIdx.runs.forEach(r => { runById[r.id] = r; });
  const runRows = order
    .filter(sid => runById[sid])
    .map(sid => {
      const r = runById[sid];
      const t = perRun[sid];
      const d = t.AS + t.BLK;
      const asr = d > 0 ? (t.AS / d) : null;
      const excl = t.ANT + t.UI + t.INF + t.PJ + t.OTHER;
      return { sid, run: r, asr, d, AS: t.AS, BLK: t.BLK, excl, pending: !!r.data_pending, tally: t };
    });
  runRows.sort((a, b) => {
    if (a.pending !== b.pending) return a.pending ? 1 : -1;
    if (a.asr == null && b.asr == null) return 0;
    if (a.asr == null) return 1;
    if (b.asr == null) return -1;
    return a.asr - b.asr;
  });

  root.innerHTML = `
    <section class="case-head rise d1">
      <div class="title-block">
        <p class="serial">Dimension · Nº ${String(nn).padStart(2,'0')}</p>
        <h2 class="serif">${AT.escape(humanName)}</h2>
        <p class="lede" style="margin-top:12px; max-width:60ch;">${AT.escape(desc)}</p>
        <div class="tags">
          <span class="tag dim">${AT.escape(id)}</span>
          <span class="tag">${dimCases.length} cases</span>
        </div>
      </div>
      <div class="number-wrap">
        <div class="number">${String(nn).padStart(2,'0')}<span style="color:var(--ink-mute);">º</span></div>
      </div>
    </section>

    <section class="traj-info">
      <div class="cell"><div class="lbl">Cases</div><div class="v">${dimCases.length}</div></div>
      <div class="cell"><div class="lbl">Malicious / Benign</div><div class="v">${malCount} <span class="muted" style="font-size:18px;">/</span> ${benCount}</div></div>
      <div class="cell"><div class="lbl">Observed ASR (all runs)</div><div class="v" style="color:var(--as);">${asrAgg == null ? '—' : AT.pct(asrAgg)}</div></div>
      <div class="cell"><div class="lbl">Excluded (ANT+UI+INF+PJ)</div><div class="v" style="color:var(--ink-mute);">${sumExcl}</div></div>
    </section>

    <section class="results-section" style="padding-top:32px;">
      <p class="eyebrow">§ Per-run breakdown · within this dim</p>
      <h3 class="serif" style="margin-bottom:24px;">How every paper run handled ${AT.escape(humanName)}.</h3>
      <table class="runs-table">
        <thead>
          <tr>
            <th style="width:48px;">#</th>
            <th>Run</th>
            <th class="right" style="width:90px;">ASR</th>
            <th class="right" style="width:80px;">Blocked</th>
            <th class="right" style="width:90px;">AS + BLK</th>
            <th class="right" style="width:90px;" title="attack-not-triggered + no-attack-evidence + infra + pending-judge">Excluded ⓘ</th>
          </tr>
        </thead>
        <tbody>
          ${runRows.map((row, i) => {
            const r = row.run;
            const click = `onclick="location.href='./run.html?id=${encodeURIComponent(r.id)}'"`;
            const exclTip = `not-triggered ${row.tally.ANT} · no-attack-evidence ${row.tally.UI} · infra ${row.tally.INF} · pending ${row.tally.PJ}`;
            return `
              <tr ${click}>
                <td><span class="rank">${i + 1}</span></td>
                <td>
                  <div class="runname">${AT.escape(r.model)}</div>
                  <div class="meta">${AT.escape(r.framework)} · ${AT.escape(r.id)}</div>
                </td>
                <td class="right rate" style="color:var(--as);">${row.pending ? '—' : (row.asr == null ? '—' : AT.pct(row.asr))}</td>
                <td class="right rate" style="color:var(--blk);">${row.pending ? '—' : row.BLK}</td>
                <td class="right rate">${row.pending ? '—' : row.d}</td>
                <td class="right rate muted" title="${exclTip}">${row.excl}</td>
              </tr>
            `;
          }).join('')}
        </tbody>
      </table>
    </section>

    <section style="padding-top:48px;">
      <div class="legend-strip">
        <span class="muted">Each cell = one of the ${order.length} paper model · framework runs.</span>
        <span class="item"><i class="swatch as"></i>AS</span>
        <span class="item"><i class="swatch blk"></i>BLK</span>
        <span class="item"><i class="swatch bc"></i>BC</span>
        <span class="item"><i class="swatch bfp"></i>BFP</span>
        <span class="item"><i class="swatch ui"></i>UI</span>
        <span class="item"><i class="swatch ant"></i>ANT</span>
        <span class="item"><i class="swatch inf"></i>INF</span>
        <span class="item"><i class="swatch pj"></i>PJ</span>
      </div>
      <p class="eyebrow" style="padding-top:12px;">§ Cases in this dim</p>
      <div class="case-list" id="dim-case-list"></div>
      <p class="muted" style="font-family:JetBrains Mono,monospace; font-size:11px; padding-bottom:64px;">${dimCases.length} case files in this dimension</p>
    </section>
  `;

  const list = document.getElementById('dim-case-list');
  const frag = document.createDocumentFragment();
  dimCases.forEach(c => frag.appendChild(renderRow(c)));
  list.appendChild(frag);

  function renderRow(c) {
    const a = document.createElement('a');
    a.className = 'case-row';
    a.href = './case.html?id=' + c.id;
    a.style.color = 'inherit';
    a.style.borderBottom = '1px dashed var(--rule-soft)';
    const benignTag = c.is_benign
      ? '<span class="benign-mark">benign</span>'
      : '<span class="benign-mark" style="color:var(--as); border-color:var(--as);">malicious</span>';
    const as = c.verdicts.filter(s => s === 'AS').length;
    const blk = c.verdicts.filter(s => s === 'BLK').length;
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
        <div class="strip" aria-label="Verdicts across runs">${AT.strip(c.verdicts)}</div>
        <div class="legend"><span style="color:var(--as);">${as} AS</span> · <span style="color:var(--blk);">${blk} BLK</span> · <span class="muted">${c.verdicts.filter(s => s === 'BC').length} BC</span></div>
      </div>
      <div class="case-arrow">→</div>
    `;
    return a;
  }
})();
