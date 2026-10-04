const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {loadCatalogue, saveCatalogue} = require('../scripts/catalogue_io');
const root = path.resolve(__dirname, '..');

(async () => {
  const legacy = JSON.parse(fs.readFileSync(path.join(root, 'data/catalogue.json'), 'utf8'));
  const assembled = loadCatalogue();
  const cardMap = new Map(assembled.cards.map(card => [card.id, card]));
  const repairs = JSON.parse(fs.readFileSync(path.join(root, 'scripts/catalogue_repairs.json'), 'utf8'));
  const removed = new Map(repairs.flatMap(repair => repair.removedCards.map(card => [card.id, card])));
  const corrected = new Map(repairs.flatMap(repair => repair.updates.map(update => [update.before.id, update])));
  for (const card of legacy.cards) {
    if (removed.has(card.id)) {
      assert.deepEqual(card, removed.get(card.id), 'Only the reviewed false heading may be removed');
      assert(!cardMap.has(card.id), 'False heading must be absent');
    } else if (corrected.has(card.id)) {
      const update = corrected.get(card.id);
      assert.deepEqual(card, update.before, 'Reviewed correction must match the original identity');
      assert.deepEqual(cardMap.get(card.id), {...card, ...update.changes}, 'Only approved subset fields may change');
    } else assert.deepEqual(cardMap.get(card.id), card, 'Existing identities must remain unchanged');
  }
  assert.equal(removed.size, 2);
  assert.equal(corrected.size, 35);
  assert.equal(assembled.cards.length, assembled.cardCount);
  assert.equal(assembled.sets.length, assembled.setCount);
  const index = JSON.parse(fs.readFileSync(path.join(root, 'data/catalogue-index.json'), 'utf8'));
  const before = index.sets.map(set => fs.statSync(path.join(root, 'data', set.file)).mtimeMs);
  saveCatalogue(assembled);
  assert.deepEqual(index.sets.map(set => fs.statSync(path.join(root, 'data', set.file)).mtimeMs), before, 'Unchanged set files must not be rewritten');
  const fetchFile = async url => ({ok: true, json: async () => JSON.parse(fs.readFileSync(path.join(root, url), 'utf8'))});
  const source = fs.readFileSync(path.join(root, 'app.js'), 'utf8');
  const loader = source.slice(source.indexOf('async function loadCatalogue()'), source.indexOf('\nfunction remoteRowToEntry'));
  const context = vm.createContext({fetch: fetchFile, state: {supabase: null}});
  vm.runInContext(loader, context);
  const loaded = await context.loadCatalogue();
  assert.deepEqual(JSON.parse(JSON.stringify(loaded.cards)), assembled.cards);
  assert.equal(loaded.setCount, index.setCount);
  assert.equal(loaded.cardCount, index.cardCount);
  context.fetch = async url => url.includes('/sets/') ? {ok: false} : fetchFile(url);
  await assert.rejects(context.loadCatalogue(), /failed to load/);

  let install;
  let cachedAssets;
  let skipWaiting = false;
  const sw = vm.createContext({
    fetch: fetchFile, Request: class {constructor(url) {this.url = url;}},
    caches: {open: async () => ({addAll: async requests => {cachedAssets = requests.map(request => request.url);}})},
    self: {addEventListener: (type, callback) => {if (type === 'install') install = callback;}, skipWaiting: async () => {skipWaiting = true;}},
  });
  vm.runInContext(fs.readFileSync(path.join(root, 'sw.js'), 'utf8'), sw);
  let installation;
  install({waitUntil: promise => {installation = promise;}});
  await installation;
  assert(skipWaiting);
  for (const set of index.sets) assert(cachedAssets.includes(`data/${set.file}`), `Offline cache missing ${set.id}`);
  assert(!cachedAssets.includes('data/catalogue.json'));
  console.log(`PASS: ${index.setCount} sets/${index.cardCount} cards, existing identities unchanged, idempotent writes, app loader, failed-chunk handling and all-set offline cache list.`);
})().catch(error => {console.error(error); process.exitCode = 1;});
