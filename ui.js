/* Presentation only: no authentication, storage or network operations. */
window.GrailUI = (() => {
  const paths = {
    crown: '<path d="m3 6 5 4 4-7 4 7 5-4-2 14H5Z"/>',
    collection: '<rect x="6" y="5" width="14" height="16" rx="2"/><path d="M16 5V3H3v15h3"/>',
    sets: '<path d="m12 3 10 5-10 5L2 8Zm-10 9 10 5 10-5M2 16l10 5 10-5"/>',
    wanted: '<path d="M6 21V4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v17l-6-4Z"/>',
    profile: '<circle cx="12" cy="7" r="4"/><path d="M4 21v-2a8 8 0 0 1 16 0v2"/>',
    search: '<circle cx="10" cy="10" r="7"/><path d="m15 15 6 6"/>',
    grid: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
    list: '<path d="M9 5h12M9 12h12M9 19h12M3 5h1M3 12h1M3 19h1"/>',
    arrow: '<path d="m9 5 7 7-7 7"/>',
    check: '<path d="m5 12 4 4L19 6"/>',
    menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
  };
  const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function icon(name) {
    return `<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.collection}</svg>`;
  }
  function coverStyle(set) {
    const name = (set?.name || set?.shortName || '').toLowerCase();
    if (name.includes('wrestlemania')) return 'wrestlemania';
    if (name.includes('cactus')) return 'cactus';
    if (name.includes('sapphire')) return 'sapphire';
    if (name.includes('bape')) return 'bape';
    if (name.includes('finest')) return 'finest';
    if (name.includes('universe')) return 'universe';
    return 'default';
  }
  function setCover(set) {
    return `<div class="set-cover-placeholder" data-cover="${coverStyle(set)}"><div class="cover-top"><span>GRAILROSTER</span><span>${escape(set.year)}</span></div><strong>${escape(set.shortName)}</strong><small>WWE · SET CHECKLIST</small></div>`;
  }
  function cardPlaceholder(card, set) {
    return `<div class="card-placeholder" data-cover="${coverStyle(set)}"><div class="cover-top"><span>${escape(set?.year || '')} · WWE</span><span>#${escape(card.number)}</span></div><div class="card-placeholder-name">${escape(card.name)}</div><div class="placeholder-bottom"><span>${escape(card.subset)}</span><small>Image pending</small></div></div>`;
  }
  function mountIcons() {
    document.querySelectorAll('[data-icon]').forEach(el => { el.innerHTML = icon(el.dataset.icon); });
  }
  return { icon, escape, setCover, cardPlaceholder, mountIcons };
})();
