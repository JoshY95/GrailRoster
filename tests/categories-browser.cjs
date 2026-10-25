const assert = require('node:assert/strict');
const {chromium} = require('playwright');
const starWarsSets=require('../data/catalogue-index.json').sets.filter(s=>s.categoryId==='star-wars');
const starWarsCount=starWarsSets.reduce((n,s)=>n+s.cardCount,0);

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
    assert.equal(await page.evaluate(()=>categoryCatalogue().cardCount),starWarsCount);
    assert.equal(await page.locator('#categorySwitcher [data-franchise="star-wars"]').getAttribute('aria-pressed'),'true');
    assert.equal(await page.locator('#allSets .set-card').count(),starWarsSets.length);
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
    // Real imported Chrome/Galaxy cards share #1 but never share ownership keys.
    await page.locator('#setFilter').selectOption('2026-topps-chrome-star-wars-galaxy');
    assert.equal(await page.locator('#resultCount').innerText(),'323 cards');
    await page.locator('#cardList .card-row').first().locator('.state-button.owned').click();
    assert.equal(await page.evaluate(()=>counts().owned),2);
    assert.equal(await page.evaluate(()=>state.collection['2026-TCSW-BASE-1']?.status),'owned');
    assert.equal(await page.evaluate(()=>state.collection['2026-TCSWG-BASE-1']?.status),'owned');
    await page.locator('#setFilter').selectOption('2025-topps-star-wars-masterwork');
    assert.equal(await page.locator('#resultCount').innerText(),'589 cards');
    await page.locator('#cardList .card-row').first().locator('.state-button.owned').click();
    assert.equal(await page.evaluate(()=>counts().owned),3);
    assert.equal(await page.evaluate(()=>state.collection['2025-TSWMW-BASE-1']?.status),'owned');
    await page.locator('#categoryFilter').selectOption('Autograph Relic');
    assert.equal(await page.locator('#resultCount').innerText(),'137 cards');
    await page.locator('#globalSearch').fill('RAR-C3');
    assert.equal(await page.locator('#cardList .card-row').count(),1);
    assert.match(await page.locator('#cardList').innerText(),/Anthony Daniels/);
    await page.locator('#globalSearch').fill('');
    await page.locator('#categoryFilter').selectOption('Autograph');
    await page.locator('#globalSearch').fill('UBC-456');
    assert.equal(await page.locator('#cardList .card-row').count(),1);
    assert.match(await page.locator('#cardList').innerText(),/Harrison Ford/);
    for(const width of [320,390,768,1024,1440]) {
      await page.setViewportSize({width,height:900});
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),true,`Ten-signer book card overflows at ${width}`);
    }
    await page.locator('#clearFilters').click();
    await page.locator('#setFilter').selectOption('2025-topps-star-wars-smugglers-outpost');
    assert.equal(await page.locator('#resultCount').innerText(),'806 cards');
    await page.locator('#cardList .card-row').first().locator('.state-button.owned').click();
    assert.equal(await page.evaluate(()=>counts().owned),4);
    assert.equal(await page.evaluate(()=>state.collection['2025-TSWSO-F-F-1']?.status),'owned');
    await page.locator('#categoryFilter').selectOption('Sketch');
    assert.equal(await page.locator('#resultCount').innerText(),'125 cards');
    await page.locator('#categoryFilter').selectOption('Insert');
    await page.locator('#globalSearch').fill('ARS-25');
    assert.equal(await page.locator('#cardList .card-row').count(),2);
    assert.match(await page.locator('#cardList').innerText(),/Jar Jar Binks/);
    assert.match(await page.locator('#cardList').innerText(),/Darth Vader/);
    await page.locator('#categoryFilter').selectOption('Autograph');
    await page.locator('#globalSearch').fill('LSU-BC');
    assert.equal(await page.locator('#cardList .card-row').count(),1);
    assert.match(await page.locator('#cardList').innerText(),/Carrie Fisher/);
    for(const width of [320,390,768,1024,1440]) {
      await page.setViewportSize({width,height:900});
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),true,`Twenty-signer book overflows at ${width}`);
    }
    await page.locator('#clearFilters').click();
    await page.locator('#setFilter').selectOption('2025-topps-chrome-star-wars-galaxy');
    assert.equal(await page.locator('#resultCount').innerText(),'293 cards');
    await page.locator('#cardList .card-row').first().locator('.state-button.owned').click();
    assert.equal(await page.evaluate(()=>counts().owned),5);
    assert.equal(await page.evaluate(()=>state.collection['2025-TCSWG-BASE-1']?.status),'owned');
    assert.equal(await page.evaluate(()=>state.collection['2026-TCSWG-BASE-1']?.status),'owned');
    await page.locator('#categoryFilter').selectOption('Buyback');
    assert.equal(await page.locator('#resultCount').innerText(),'20 cards');
    await page.locator('#globalSearch').fill('MCQ-1');
    assert.match(await page.locator('#cardList').innerText(),/1993 Star Wars Galaxy Series 1 #15/);
    await page.locator('#categoryFilter').selectOption('Autograph');
    await page.locator('#globalSearch').fill('Q-JNJF');
    assert.equal(await page.locator('#cardList .card-row').count(),1);
    assert.match(await page.locator('#cardList').innerText(),/Jude Law/);
    await page.locator('#clearFilters').click();
    await page.locator('#setFilter').selectOption('2025-topps-chrome-sapphire-star-wars');
    assert.equal(await page.locator('#resultCount').innerText(),'358 cards');
    await page.locator('#cardList .card-row').first().locator('.state-button.owned').click();
    assert.equal(await page.evaluate(()=>counts().owned),6);
    assert.equal(await page.evaluate(()=>state.collection['2025-TCSSW-BASE-1']?.status),'owned');
    assert.equal(await page.evaluate(()=>state.collection['2025-TCSWG-BASE-1']?.status),'owned');
    await page.locator('#categoryFilter').selectOption('Insert');
    assert.equal(await page.locator('#resultCount').innerText(),'10 cards');
    await page.locator('#categoryFilter').selectOption('Autograph');
    await page.locator('#globalSearch').fill('DA-MJj');
    assert.equal(await page.locator('#cardList .card-row').count(),1);
    assert.match(await page.locator('#cardList').innerText(),/Lee Jung-jae/);
    assert.match(await page.locator('#cardList').innerText(),/Manny Jacinto/);
    await page.locator('#globalSearch').fill('TA-JSM');
    assert.equal(await page.locator('#cardList .card-row').count(),1);
    assert.match(await page.locator('#cardList').innerText(),/Thundercat/);
    await page.locator('#clearFilters').click();
    await page.locator('#setFilter').selectOption('2025-topps-chrome-star-wars');
    assert.equal(await page.locator('#resultCount').innerText(),'1,235 cards');
    await page.locator('#cardList .card-row').first().locator('.state-button.owned').click();
    assert.equal(await page.evaluate(()=>counts().owned),7);
    assert.equal(await page.evaluate(()=>state.collection['2025-TCSW-BASE-1']?.status),'owned');
    assert.equal(await page.evaluate(()=>state.collection['2025-TCSSW-BASE-1']?.status),'owned');
    await page.locator('#categoryFilter').selectOption('Insert');
    assert.equal(await page.locator('#resultCount').innerText(),'840 cards');
    await page.locator('#globalSearch').fill('HF-1');
    assert.match(await page.locator('#cardList').innerText(),/Admiral Ackbar/);
    await page.locator('#globalSearch').fill('R-11');
    assert.equal(await page.locator('#cardList .card-row').count(),1);
    await page.locator('#categoryFilter').selectOption('Autograph');
    await page.locator('#globalSearch').fill('DA-MJj');
    assert.equal(await page.locator('#cardList .card-row').count(),1);
    assert.match(await page.locator('#cardList').innerText(),/Lee Jung-jae/);
    assert.match(await page.locator('#cardList').innerText(),/Manny Jacinto/);
    await page.locator('#globalSearch').fill('TA-JRN');
    assert.equal(await page.locator('#cardList .card-row').count(),1);
    assert.match(await page.locator('#cardList').innerText(),/Jude Law/);
    await page.locator('#clearFilters').click();
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
    assert.equal(await page.locator('#allSets .set-card').count(),starWarsSets.length);
    assert.equal(await page.evaluate(()=>counts().owned),7);
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
