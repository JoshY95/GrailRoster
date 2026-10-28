/* Conservative text-to-catalogue matching. Never creates cards or infers editions. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.GrailScanMatch = api;
})(typeof window === 'undefined' ? globalThis : window, function () {
  'use strict';
  function normalize(value) {
    return String(value || '').normalize('NFKD').replace(/[\u0300-\u036f]/g, '')
      .toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim().replace(/\s+/g, ' ');
  }
  const contains = (text, phrase) => !!phrase && ` ${text} `.includes(` ${phrase} `);
  function near(a, b) {
    if (a === b) return true;
    if (Math.min(a.length, b.length) < 4 || Math.abs(a.length - b.length) > 1) return false;
    let i = 0, j = 0, edits = 0;
    while (i < a.length && j < b.length) {
      if (a[i] === b[j]) { i++; j++; continue; }
      if (++edits > 1) return false;
      if (a.length >= b.length) i++;
      if (b.length >= a.length) j++;
    }
    return edits + (i < a.length || j < b.length ? 1 : 0) <= 1;
  }
  function numberKey(value) {
    return normalize(value).replace(/\s/g, '').replace(/^0+(\d)/, '$1');
  }
  function details(raw) {
    const text = String(raw || '').slice(0, 10000);
    const explicit = new Set(), possible = new Set();
    // Remove serials before looking for checklist numbers; /50 is not card #50.
    const withoutSerials = text.replace(/\b\d{1,5}\s*\/\s*\d{1,5}\b/g, ' ');
    for (const m of withoutSerials.matchAll(/(?:#|\b(?:no\.?|number|card)\s*[:.#-]?)\s*([a-z]{0,12}[- ]?\d{1,4}(?:[-][a-z0-9]+)?)(?![a-z0-9])/gi)) explicit.add(numberKey(m[1]));
    for (const m of withoutSerials.matchAll(/\b[a-z]{1,12}-\d{1,4}(?:-[a-z0-9]+)?\b/gi)) explicit.add(numberKey(m[0]));
    for (const line of withoutSerials.split(/\n/)) {
      if (/^\s*\d{1,3}\s*$/.test(line)) possible.add(numberKey(line));
    }
    const serial = text.match(/\b(\d{1,5})\s*\/\s*(\d{1,5})\b/);
    return { text: normalize(text), explicit, possible,
      years: [...new Set(text.match(/\b(?:19|20)\d{2}\b/g) || [])],
      serial: serial ? `${serial[1]}/${serial[2]}` : '' };
  }
  const generic = new Set(['wwe', 'topps', 'panini', 'collection', 'edition', 'cards', 'card', 'the', 'x']);
  function buildIndex(catalogue) {
    const sets = new Map(catalogue.sets.filter(set => set.categoryId === 'wwe').map(set => [set.id, set]));
    return catalogue.cards.filter(card => sets.has(card.setId)).map(card => {
      const set = sets.get(card.setId);
      const names = [card.name, card.subject2].filter(Boolean).flatMap(name => [name, name.replace(/[“"].*?[”"]/g, '').trim(), ...name.split(/\s+[\/&]\s+/)]);
      return { card, set, names: [...new Set(names.map(normalize).filter(Boolean))], number: numberKey(card.number),
        product: normalize(set.name).split(' ').filter(word => !generic.has(word) && !/^\d+$/.test(word)),
        subset: normalize(card.subset) };
    });
  }
  function match(index, raw, setId = 'all', limit = 12) {
    const read = details(raw), words = new Set(read.text.split(' '));
    if (!read.text) return [];
    const results = [], nameCache = new Map(), scanWords = read.text.split(' ');
    for (const row of index) {
      if (setId !== 'all' && row.set.id !== setId) continue;
      let nameScore = 0;
      for (const name of row.names) {
        if (nameCache.has(name)) { nameScore = Math.max(nameScore, nameCache.get(name)); continue; }
        if (contains(read.text, name)) { nameCache.set(name, 60); nameScore = 60; continue; }
        const parts = name.split(' ').filter(word => word !== 'the');
        let fuzzy = 0;
        // Fuzzy matching requires a whole multi-word name, in order and adjacent.
        if (parts.length > 1) {
          for (let i = 0; i <= scanWords.length - parts.length; i++) {
            if (parts.every((part, j) => near(part, scanWords[i + j]))) { fuzzy = 42; break; }
          }
        }
        nameCache.set(name, fuzzy); nameScore = Math.max(nameScore, fuzzy);
      }
      const exactNumber = read.explicit.has(row.number), possibleNumber = read.possible.has(row.number);
      if (!nameScore && !(setId !== 'all' && exactNumber)) continue;
      const evidence = [];
      let score = nameScore;
      if (nameScore) evidence.push(nameScore === 60 ? 'Name found' : 'Similar name');
      if (exactNumber || possibleNumber) { score += exactNumber ? 40 : 24; evidence.push('Card number found'); }
      if (setId !== 'all') evidence.push('Set selected by you');
      if (read.years.includes(String(row.set.year))) { score += 10; evidence.push('Year found'); }
      const productHits = row.product.filter(word => words.has(word)).length;
      if (row.product.length && productHits === row.product.length) { score += 22 + row.product.length; evidence.push('Product text found'); }
      else score += productHits * 3;
      if (contains(read.text, normalize(row.set.manufacturer))) score += 3;
      if (row.subset.length > 4 && !['base', 'base cards'].includes(row.subset) && contains(read.text, row.subset)) { score += 12; evidence.push('Subset text found'); }
      results.push({ card: row.card, set: row.set, score, evidence });
    }
    return results.sort((a, b) => b.score - a.score || a.card.id.localeCompare(b.card.id)).slice(0, limit);
  }
  function period(date = new Date()) { return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`; }
  function loadStore(raw, month = period()) {
    let value;
    try { value = JSON.parse(raw); } catch { value = null; }
    const valid = value && value.version === 1;
    return { version: 1,
      usage: { month, used: valid && value.usage?.month === month && Number.isInteger(value.usage.used) ? Math.max(0, Math.min(25, value.usage.used)) : 0 },
      attempts: valid && Array.isArray(value.attempts) ? value.attempts.filter(item => item && typeof item.id === 'string').slice(-200) : [],
      items: valid && Array.isArray(value.items) ? value.items.filter(item => item && typeof item.cardId === 'string').slice(-500) : [] };
  }
  return { normalize, details, buildIndex, match, period, loadStore };
});
