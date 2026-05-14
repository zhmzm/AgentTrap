window.AT = window.AT || {};
AT.scatter = (() => {
  const NS = 'http://www.w3.org/2000/svg';
  const W = 1200, H = 520;
  const PAD = { t: 36, r: 32, b: 56, l: 64 };
  const MONO = "'JetBrains Mono', monospace";
  const SERIF = "'Fraunces', serif";

  function el(tag, attrs) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    return e;
  }
  function txt(attrs, content) {
    const t = el('text', attrs);
    t.textContent = content;
    return t;
  }

  async function render(runs) {
    if (!runs) runs = (await AT.json('./data/runs/index.json')).runs;
    const svg = document.getElementById('scatter-svg');
    const tip = document.getElementById('scatter-tip');
    if (!svg) return;
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    const points = runs
      .filter(r => r.asr != null && r.benign_acc != null && !r.data_pending)
      .map(r => ({ r, x: r.benign_acc, y: 1 - r.asr }));

    const innerW = W - PAD.l - PAD.r;
    const innerH = H - PAD.t - PAD.b;
    const sx = v => PAD.l + v * innerW;
    const sy = v => PAD.t + (1 - v) * innerH;

    svg.appendChild(el('rect', {
      x: PAD.l, y: PAD.t, width: innerW, height: innerH,
      fill: 'none', stroke: 'var(--rule)', 'stroke-width': 1,
    }));

    svg.appendChild(el('line', {
      x1: sx(0.5), x2: sx(0.5), y1: PAD.t, y2: PAD.t + innerH,
      stroke: 'var(--rule-soft)', 'stroke-width': 1, 'stroke-dasharray': '3 4',
    }));
    svg.appendChild(el('line', {
      x1: PAD.l, x2: PAD.l + innerW, y1: sy(0.5), y2: sy(0.5),
      stroke: 'var(--rule-soft)', 'stroke-width': 1, 'stroke-dasharray': '3 4',
    }));

    const tickAttrs = { 'font-family': MONO, 'font-size': 10.5, fill: 'var(--ink-mute)', 'letter-spacing': '0.12em' };
    [0, 0.5, 1].forEach(t => {
      svg.appendChild(txt({ ...tickAttrs, x: sx(t), y: PAD.t + innerH + 18, 'text-anchor': 'middle' }, (t * 100).toFixed(0) + '%'));
      svg.appendChild(txt({ ...tickAttrs, x: PAD.l - 12, y: sy(t) + 4, 'text-anchor': 'end' }, (t * 100).toFixed(0) + '%'));
    });

    const axisAttrs = { 'font-family': MONO, 'font-size': 10.5, fill: 'var(--ink-mute)', 'letter-spacing': '0.22em' };
    svg.appendChild(txt({ ...axisAttrs, x: PAD.l + innerW / 2, y: H - 14, 'text-anchor': 'middle' }, 'BENIGN ACCURACY →'));
    svg.appendChild(txt({ ...axisAttrs, x: 0, y: 0, 'text-anchor': 'middle', transform: `translate(18 ${PAD.t + innerH / 2}) rotate(-90)` }, 'DEFENSE RATE →'));

    const quad = [
      { x: sx(1) - 8, y: PAD.t + 14, a: 'end', t: 'CAPABLE & SAFE ◆' },
      { x: sx(0) + 8, y: PAD.t + 14, a: 'start', t: 'SAFE BUT WEAK' },
      { x: sx(1) - 8, y: PAD.t + innerH - 8, a: 'end', t: 'CAPABLE BUT UNSAFE' },
      { x: sx(0) + 8, y: PAD.t + innerH - 8, a: 'start', t: 'VULNERABLE & WEAK' },
    ];
    quad.forEach(q => svg.appendChild(txt({
      x: q.x, y: q.y, 'text-anchor': q.a, 'font-family': MONO,
      'font-size': 10.5, fill: 'var(--ink-mute)', 'letter-spacing': '0.18em',
    }, q.t)));

    const sorted = [...points].sort((a, b) => b.y - a.y);
    const placed = [];
    sorted.forEach((p, i) => {
      const cx = sx(p.x), cy = sy(p.y);
      const topSafe = p.x >= 0.5 && p.y >= 0.5;
      const labelLeft = cx > PAD.l + innerW * 0.7;
      const above = chooseSide(cx, placed);
      const labelY = above ? cy - 16 : cy + 28;
      placed.push({ cx, cy, ly: labelY, above });

      const g = el('g', { class: 'sp', style: 'cursor:pointer', opacity: 0 });
      const titleNode = el('title', {});
      titleNode.textContent = `${p.r.model} · ${p.r.framework} — defense ${AT.pct(1 - p.r.asr)}, benign ${AT.pct(p.r.benign_acc)}, ASR ${AT.pct(p.r.asr)} (n=${p.r.observed_denom})`;
      g.appendChild(titleNode);

      const c = el('circle', {
        cx, cy, r: 8,
        fill: topSafe ? 'var(--bc)' : 'var(--ink)',
        stroke: 'var(--paper)', 'stroke-width': 2,
      });
      g.appendChild(c);
      if (topSafe) g.appendChild(txt({
        x: cx + 11, y: cy - 8, 'font-family': SERIF, 'font-size': 14, fill: 'var(--bc)',
      }, '★'));

      const lx = labelLeft ? cx - 12 : cx + 12;
      const labelAnchor = labelLeft ? 'end' : 'start';
      g.appendChild(txt({
        x: lx, y: labelY, 'text-anchor': labelAnchor,
        'font-family': SERIF, 'font-size': 13, fill: 'var(--ink)',
        'font-variation-settings': "'SOFT' 50, 'opsz' 24",
      }, p.r.model));
      g.appendChild(txt({
        x: lx, y: labelY + 13, 'text-anchor': labelAnchor,
        'font-family': MONO, 'font-size': 10,
        fill: 'var(--ink-mute)', 'letter-spacing': '0.08em',
      }, '· ' + p.r.framework));

      g.addEventListener('mouseenter', e => {
        c.setAttribute('r', 11);
        c.setAttribute('stroke', 'var(--signal)');
        showTip(tip, p.r, e);
      });
      g.addEventListener('mousemove', e => moveTip(tip, e));
      g.addEventListener('mouseleave', () => {
        c.setAttribute('r', 8);
        c.setAttribute('stroke', 'var(--paper)');
        tip.style.opacity = 0;
      });
      g.addEventListener('click', () => {
        location.href = './run.html?id=' + encodeURIComponent(p.r.id);
      });

      svg.appendChild(g);
      setTimeout(() => {
        g.style.transition = 'opacity .5s ease';
        g.setAttribute('opacity', 1);
      }, 80 + i * 60);
    });
  }

  function chooseSide(cx, placed) {
    let above = 0, below = 0;
    placed.forEach(p => {
      if (Math.abs(p.cx - cx) > 80) return;
      if (p.above) above++; else below++;
    });
    return above <= below;
  }

  function showTip(tip, r, e) {
    const def = r.asr != null ? (1 - r.asr) : null;
    tip.innerHTML = `
      <div class="sp-h">${AT.escape(r.model)} <span class="sp-fw">· ${AT.escape(r.framework)}</span></div>
      <div class="sp-row"><span>Defense</span><b>${AT.pct(def)}</b></div>
      <div class="sp-row"><span>Benign acc.</span><b>${AT.pct(r.benign_acc)}</b></div>
      <div class="sp-row"><span>Observed ASR</span><b>${AT.pct(r.asr)}</b></div>
      <div class="sp-row"><span>AS + BLK</span><b>${r.observed_denom}</b></div>
    `;
    tip.style.opacity = 1;
    moveTip(tip, e);
  }

  function moveTip(tip, e) {
    const host = tip.parentElement.getBoundingClientRect();
    tip.style.left = (e.clientX - host.left + 14) + 'px';
    tip.style.top = (e.clientY - host.top + 14) + 'px';
  }

  return { render };
})();

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('scatter-svg')) AT.scatter.render();
});
