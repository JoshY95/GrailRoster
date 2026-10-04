const assert = require('node:assert/strict');
const {chromium} = require('playwright');
const index = require('../data/catalogue-index.json');

(async () => {
  const browser = await chromium.launch({headless:true});
  try {
    const context = await browser.newContext();
    const page = await context.newPage();
    await page.route('**/rest/v1/**', route => route.abort());
    await page.goto(process.env.GRAILROSTER_BASE_URL || 'http://127.0.0.1:8767');
    await page.locator('#allSets .set-card').first().waitFor({state:'attached'});
    await page.evaluate(async () => {
      await navigator.serviceWorker.ready;
      if (!navigator.serviceWorker.controller) await new Promise(resolve => navigator.serviceWorker.addEventListener('controllerchange', resolve, {once:true}));
    });
    const before = await page.evaluate(() => {
      const card = state.catalogue.cards.find(c => c.id === '2025-TNWWE-BASE-1');
      state.collection[card.id] = {status:'owned',quantity:1,updatedAt:new Date().toISOString()};
      saveCollection();
      return {id:card.id,count:state.catalogue.cards.length};
    });
    assert.equal(before.count,index.cardCount);
    await context.setOffline(true);
    await page.reload({waitUntil:'domcontentloaded'});
    await page.locator('#allSets .set-card').first().waitFor({state:'attached'});
    const after = await page.evaluate(id => ({count:state.catalogue.cards.length,owned:state.collection[id]?.status,
      sets:state.catalogue.sets.map(s=>s.id)}),before.id);
    assert.equal(after.count,index.cardCount);
    assert.equal(after.owned,'owned');
    assert.deepEqual([...after.sets].sort(),index.sets.map(s=>s.id).sort());
    console.log('PASS: real offline reload includes every split set and preserves ownership.');
  } finally { await browser.close(); }
})().catch(error => {console.error(error);process.exitCode=1;});
