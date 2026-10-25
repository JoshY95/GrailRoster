const assert = require('node:assert/strict');
const {chromium} = require('playwright');

(async()=>{
  const browser=await chromium.launch({headless:true});
  try {
    const context=await browser.newContext({viewport:{width:1440,height:900}});
    const page=await context.newPage();
    const errors=[];page.on('pageerror',error=>errors.push(error.message));
    await page.route('**/rest/v1/**',route=>route.abort());
    await page.goto(process.env.GRAILROSTER_BASE_URL || 'http://127.0.0.1:8767');
    await page.locator('#allSets .set-card').first().waitFor({state:'attached'});
    const before=await page.evaluate(()=>{
      const [owned,wanted]=state.catalogue.cards;
      state.collection[owned.id]={status:'owned',quantity:2,notes:'Category preservation fixture',updatedAt:new Date().toISOString()};
      state.collection[wanted.id]={status:'wanted',updatedAt:new Date().toISOString()};
      saveCollection();renderAll();return localStorage.getItem(GUEST_STORAGE_KEY);
    });
    await page.locator('#categorySwitcher [data-franchise="star-wars"]').click();
    assert.equal(await page.locator('#categoryWorkspace').isVisible(),true);
    assert.equal(await page.evaluate(()=>categoryCatalogue().cardCount),1304);
    assert.equal(await page.locator('#categorySwitcher [data-franchise="star-wars"]').getAttribute('aria-pressed'),'true');
    assert.equal(await page.locator('#allSets .set-card').count(),1);
    for(const view of ['dashboard','sets','cards','collection','wanted']) {
      await page.evaluate(view=>changeView(view),view);
      assert.equal(await page.locator('#categoryEmpty').isVisible(),false);
      assert.equal(await page.locator('#collectionList .card-row').count(),0);
      assert.equal(await page.locator('#wantedList .card-row').count(),0);
    }
    await page.evaluate(()=>changeView('cards'));
    await page.locator('#globalSearch').fill('Ewan McGregor');
    assert((await page.locator('#cardList .card-row').count())>0,'Autographs searchable by signer');
    assert(!(await page.locator('#cardList').innerText()).includes('WWE'));
    await page.locator('#clearFilters').click();
    const starWarsId=await page.evaluate(()=>categoryCatalogue().cards[0].id);
    await page.locator('#cardList .card-row').first().locator('.state-button.owned').click();
    assert.equal(await page.evaluate(()=>counts().owned),1);
    const both=await page.evaluate(()=>localStorage.getItem(GUEST_STORAGE_KEY));
    await page.locator('#categorySwitcher [data-franchise="marvel"]').click();
    for(const width of [320,390,768,1024,1440]) {
      await page.setViewportSize({width,height:900});
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),true,`Category layout overflows at ${width}`);
    }
    await page.evaluate(async()=>{
      await navigator.serviceWorker.ready;
      if(!navigator.serviceWorker.controller) await new Promise(resolve=>navigator.serviceWorker.addEventListener('controllerchange',resolve,{once:true}));
    });
    await context.setOffline(true);
    await page.reload({waitUntil:'domcontentloaded'});
    await page.locator('#categorySwitcher [data-franchise="marvel"]').waitFor();
    assert.equal(await page.locator('#categorySwitcher [data-franchise="marvel"]').getAttribute('aria-pressed'),'true');
    assert.match(await page.locator('#categoryEmptyTitle').innerText(),/Marvel/);
    assert.equal(await page.evaluate(()=>localStorage.getItem(GUEST_STORAGE_KEY)),both);
    await page.locator('#categorySwitcher [data-franchise="wwe"]').click();
    assert.equal(await page.locator('#collectionList .card-row').count(),1);
    assert.equal(await page.locator('#wantedList .card-row').count(),1);
    assert.equal(await page.evaluate(()=>localStorage.getItem(GUEST_STORAGE_KEY)),both);
    assert.equal(JSON.parse(both)[starWarsId].status,'owned');
    for(const [id,entry] of Object.entries(JSON.parse(before))) assert.deepEqual(JSON.parse(both)[id],entry);
    await page.locator('#categorySwitcher [data-franchise="star-wars"]').click();
    assert.equal(await page.locator('#allSets .set-card').count(),1);
    assert.equal(await page.evaluate(()=>counts().owned),1);
    assert.equal(await page.locator('#wantedList .card-row').count(),0);
    for(const width of [320,390,768,1024,1440]) {
      await page.setViewportSize({width,height:900});
      for(const view of ['dashboard','sets','cards','collection','wanted']) {
        await page.evaluate(view=>changeView(view),view);
        assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),true,`Star Wars ${view} overflows at ${width}`);
      }
    }
    assert.deepEqual(errors,[]);
    console.log('PASS: browser category switching, responsive widths, persistent category/offline reload and unchanged saved entries.');
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
