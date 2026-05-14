// Shared helpers for the AgentTrap field manual site.
window.AT = (() => {
  const VERDICTS = {
    attack_succeeded:    { short: 'AS',  cls: 'as',  label: 'attack succeeded' },
    attack_blocked:      { short: 'BLK', cls: 'blk', label: 'attack blocked' },
    attack_not_triggered:{ short: 'ANT', cls: 'ant', label: 'attack not triggered' },
    benign_correct:      { short: 'BC',  cls: 'bc',  label: 'benign correct' },
    benign_false_positive:{short: 'BFP', cls: 'bfp', label: 'benign false positive' },
    utility_incomplete:  { short: 'UI',  cls: 'ui',  label: 'utility incomplete' },
    infra_issue:         { short: 'INF', cls: 'inf', label: 'infra issue' },
    pending_judge:       { short: 'PJ',  cls: 'pj',  label: 'pending judge' },
    missing:             { short: '--',  cls: 'miss',label: 'no run' },
    unknown:             { short: '??',  cls: 'unknown', label: 'unknown' },
  };

  // Short code → class map (matrix uses AS/BLK/ANT/BC/BFP/UI/INF/PJ/--)
  const SHORT_TO_CLS = {
    'AS': 'as', 'BLK': 'blk', 'ANT': 'ant',
    'BC': 'bc', 'BFP': 'bfp', 'UI': 'ui',
    'INF': 'inf', 'PJ': 'pj', '--': 'miss',
  };

  function clsFor(verdict, short) {
    if (verdict && VERDICTS[verdict]) return VERDICTS[verdict].cls;
    if (short && SHORT_TO_CLS[short]) return SHORT_TO_CLS[short];
    return 'unknown';
  }

  function pill(verdict, short) {
    const cls = clsFor(verdict, short);
    const txt = short || (VERDICTS[verdict] && VERDICTS[verdict].short) || '??';
    const lbl = (VERDICTS[verdict] && VERDICTS[verdict].label) || verdict || '';
    return `<span class="pill ${cls}" title="${lbl}">${txt}</span>`;
  }

  function strip(shorts) {
    return shorts.map(s => `<span class="cell ${SHORT_TO_CLS[s] || 'unknown'}" title="${s}"></span>`).join('');
  }

  function pct(n) {
    if (n === null || n === undefined || isNaN(n)) return '—';
    return (n * 100).toFixed(1) + '%';
  }

  async function json(path) {
    const res = await fetch(path);
    if (!res.ok) throw new Error('failed to load ' + path);
    return res.json();
  }

  function el(tag, attrs = {}, ...children) {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === 'class') e.className = v;
      else if (k.startsWith('on')) e.addEventListener(k.slice(2), v);
      else if (v !== false && v != null) e.setAttribute(k, v);
    }
    for (const c of children) {
      if (c == null) continue;
      e.append(c.nodeType ? c : document.createTextNode(c));
    }
    return e;
  }

  function setActive(navId) {
    document.querySelectorAll('.masthead nav a').forEach(a => {
      if (a.dataset.nav === navId) a.classList.add('active');
    });
  }

  function fmtDim(dim) { return dim.replace(/^DIM(\d+)_/, '$1 · '); }

  function escape(s) {
    return (s || '').replace(/[&<>"']/g, c => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
  }

  return { VERDICTS, SHORT_TO_CLS, clsFor, pill, strip, pct, json, el, setActive, fmtDim, escape };
})();
