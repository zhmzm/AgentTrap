// Vendor + framework logos. Real vendor marks served as <img> via fetched
// SVG files in assets/img/vendors/. Framework marks for "Plain Agent" /
// "OpenClaw" use abstract glyphs (no public logo exists).
window.MARKS = (() => {
  const VENDOR_FILE = {
    openai:    './assets/img/vendors/openai.svg',
    anthropic: './assets/img/vendors/anthropic.svg',
    tencent:   './assets/img/vendors/tencent.svg',
    zhipu:     './assets/img/vendors/zhipu.svg',
    qwen:      './assets/img/vendors/qwen.svg',
    moonshot:  './assets/img/vendors/moonshot.svg',
  };

  const FRAMEWORK_FILE = {
    'claude code': './assets/img/vendors/claude-code.svg',
    'codex cli':   './assets/img/vendors/codex-cli.svg',
  };

  // Abstract SVG fallbacks for items without a real logo.
  const FALLBACK_SVG = (body) =>
    `<svg viewBox="0 0 24 24" width="1em" height="1em" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="flex:none">${body}</svg>`;

  const FRAMEWORK_FALLBACK = {
    'plain agent': FALLBACK_SVG(`
      <path d="M8 4h-4v16h4"/><path d="M16 4h4v16h-4"/>
      <circle cx="12" cy="12" r="2" fill="currentColor"/>
    `),
    'openclaw': FALLBACK_SVG(`
      <circle cx="12" cy="12" r="4"/>
      <path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>
      <path d="M5 5l2 2M19 5l-2 2M5 19l2-2M19 19l-2-2"/>
    `),
  };

  function imgSrc(src, alt) {
    return `<img src="${src}" alt="${alt}" class="brand-mark" loading="lazy" decoding="async">`;
  }

  function vendor(key) {
    const k = (key || '').toLowerCase();
    const path = VENDOR_FILE[k];
    if (path) return imgSrc(path, k);
    return FALLBACK_SVG('<circle cx="12" cy="12" r="9"/>');
  }

  function framework(key) {
    const k = (key || '').toLowerCase();
    const path = FRAMEWORK_FILE[k];
    if (path) return imgSrc(path, k);
    return FRAMEWORK_FALLBACK[k] || FALLBACK_SVG('<circle cx="12" cy="12" r="9"/>');
  }

  return { vendor, framework };
})();
