/* Franchise categories are separate from card types such as Base / Autograph.
 * Unknown categories fail closed; never guess a franchise from a name or ID.
 */
const GrailCategories = (() => {
  const storageKey = 'grailroster.category.v1';
  const all = Object.freeze([
    Object.freeze({id:'wwe', name:'WWE', subject:'Wrestler', description:'Your ringside collection.'}),
    Object.freeze({id:'star-wars', name:'Star Wars', subject:'Character', description:'A new galaxy for your collection.'}),
    Object.freeze({id:'marvel', name:'Marvel', subject:'Character', description:'Your next collecting universe.'}),
  ]);
  const get = id => all.find(category => category.id === id);
  function initial() {
    try { const saved = localStorage.getItem(storageKey); return get(saved)?.id || 'wwe'; }
    catch { return 'wwe'; }
  }
  function remember(id) { try { localStorage.setItem(storageKey, id); } catch {} }
  function validate(catalogue) {
    const ids = new Set();
    for (const set of catalogue.sets) {
      if (!get(set.categoryId)) throw Error(`Missing or unknown franchise category: ${set.id}`);
      if (ids.has(set.id)) throw Error(`Duplicate set identity: ${set.id}`);
      ids.add(set.id);
    }
    const cardIds = new Set();
    for (const card of catalogue.cards) {
      if (!ids.has(card.setId) || cardIds.has(card.id)) throw Error(`Invalid card identity: ${card.id}`);
      cardIds.add(card.id);
    }
    return catalogue;
  }
  function scope(catalogue, categoryId) {
    const sets = catalogue.sets.filter(set => set.categoryId === categoryId);
    const ids = new Set(sets.map(set => set.id));
    const cards = catalogue.cards.filter(card => ids.has(card.setId));
    return {sets, cards, setCount:sets.length, cardCount:cards.length};
  }
  return {all, get, initial, remember, validate, scope};
})();
