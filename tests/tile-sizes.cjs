const assert=require('node:assert/strict');
const {chromium}=require('playwright');
const key='grailroster.tile-sizes.v1';
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_EXECUTABLE_PATH,args:['--no-sandbox']});
 try {
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/rest/v1/**',r=>r.abort());
  await page.goto(process.env.GRAILROSTER_BASE_URL);
  await page.locator('#allSets .set-card').first().waitFor({state:'attached'});
  const initial=await page.evaluate(()=>({catalogue:JSON.stringify(state.catalogue),collection:JSON.stringify(state.collection),setCount:categoryCatalogue().setCount,cardCount:categoryCatalogue().cardCount}));
  assert.equal(await page.locator('html').getAttribute('data-set-tile-size'),'standard');
  assert.equal(await page.locator('html').getAttribute('data-card-tile-size'),'standard');
  await page.locator('#displaySettingsButton').click();
  assert.equal(await page.locator('#displaySettingsDialog').isVisible(),true,'Guest users can reach Display settings');
  await page.locator('#displaySettingsDialog [data-tile-kind=sets]').selectOption('compact');
  await page.locator('#displaySettingsDialog [data-tile-kind=cards]').selectOption('large');
  assert.equal(await page.locator('#setsView [data-tile-kind=sets]').inputValue(),'compact');
  assert.equal(await page.locator('#cardsView [data-tile-kind=cards]').inputValue(),'large');
  assert.deepEqual(await page.evaluate(k=>JSON.parse(localStorage.getItem(k)),key),{sets:'compact',cards:'large'});
  await page.locator('#doneDisplaySettings').click();
  await page.locator('.sidebar [data-view=cards]').click();
  assert.equal(await page.locator('#cardsView [data-card-size-target]').isVisible(),false,'Tile size stays out of list mode');
  const listBefore=await page.locator('#cardList .card-row').first().boundingBox();
  await page.locator('[data-layout-target=cardList][data-layout=grid]').click();
  assert.equal(await page.locator('#cardsView [data-card-size-target]').isVisible(),true);
  await page.locator('#cardsView [data-tile-kind=cards]').selectOption('compact');
  assert.equal(await page.locator('html').getAttribute('data-set-tile-size'),'compact');
  // Preferences survive reload and are shared across collection categories and grids.
  await page.reload();await page.locator('#allSets .set-card').first().waitFor({state:'attached'});
  assert.equal(await page.locator('html').getAttribute('data-set-tile-size'),'compact');
  assert.equal(await page.locator('html').getAttribute('data-card-tile-size'),'compact');
  await page.locator('#categorySwitcher [data-franchise="star-wars"]').click();
  assert.equal(await page.locator('html').getAttribute('data-set-tile-size'),'compact');
  await page.locator('#categorySwitcher [data-franchise=wwe]').click();
  // Test the actual layouts, including the narrow phone, tablet/Fold and desktop ranges.
  for(const width of [320,390,600,768,1024,1440]) {
   await page.setViewportSize({width,height:1000});
   await page.evaluate(()=>changeView('sets'));
   const setHeights={};
   for(const size of ['compact','standard','large']) {
    await page.locator('#setsView [data-tile-kind=sets]').selectOption(size);
    setHeights[size]=(await page.locator('#allSets .set-card').first().boundingBox()).height;
    assert.equal(await page.locator('#allSets .set-card').count(),initial.setCount);
    assert.equal(await page.locator('body').evaluate(el=>el.scrollWidth<=innerWidth),true,`${size} set overflow at ${width}`);
    assert((await page.locator('#allSets h3').first().evaluate(el=>parseFloat(getComputedStyle(el).fontSize)))>=12,'Readable set names');
   }
   assert(setHeights.compact<setHeights.standard,`Compact sets should be shorter at ${width}`);
   assert(setHeights.standard<setHeights.large,`Large sets should be larger at ${width}`);
   await page.evaluate(()=>changeView('cards'));
   await page.locator('[data-layout-target=cardList][data-layout=grid]').click();
   const cardHeights={};
   for(const size of ['compact','standard','large']) {
    await page.locator('#cardsView [data-tile-kind=cards]').selectOption(size);
    cardHeights[size]=(await page.locator('#cardList .card-row').first().boundingBox()).height;
    assert.equal(await page.locator('body').evaluate(el=>el.scrollWidth<=innerWidth),true,`${size} card overflow at ${width}`);
    const actions=await page.locator('#cardList .card-row').first().locator('.state-button').evaluateAll(nodes=>nodes.map(el=>({height:el.getBoundingClientRect().height,overflow:el.scrollWidth>el.clientWidth+1})));
    assert(actions.every(a=>a.height>=44&&!a.overflow),`Usable copy/wanted buttons at ${width}/${size}`);
    assert((await page.locator('#cardList .card-name').first().evaluate(el=>parseFloat(getComputedStyle(el).fontSize)))>=12,'Readable card names');
    if(size==='compact')assert.equal(await page.locator('#cardList .card-number').first().isVisible(),true,'Compact cards retain their checklist number');
   }
   assert(cardHeights.compact<cardHeights.standard,`Compact cards should be shorter at ${width}`);
   assert(cardHeights.standard<cardHeights.large,`Large cards should be larger at ${width}`);
  }
  await page.setViewportSize({width:1440,height:1000});
  // List rows retain their dimensions even after the grid size changes.
  await page.locator('[data-layout-target=cardList][data-layout=list]').click();
  assert.equal(await page.locator('#cardsView [data-card-size-target]').isVisible(),false);
  const listAfter=await page.locator('#cardList .card-row').first().boundingBox();
  assert.equal(listAfter.height,listBefore.height);
  assert.equal(await page.evaluate(()=>JSON.stringify(state.catalogue)),initial.catalogue);
  assert.equal(await page.evaluate(()=>JSON.stringify(state.collection)),initial.collection);
  // Real collection fixtures stay byte-identical while preferences change.
  const saved=await page.evaluate(()=>{
   const [owned,wanted]=state.catalogue.cards;
   state.collection[owned.id]={status:'owned',quantity:2,notes:'Tile size preservation',updatedAt:'2026-10-28T00:00:00Z'};
   state.collection[wanted.id]={status:'wanted',notes:'Keep wanted',updatedAt:'2026-10-28T00:00:00Z'};
   saveCollection();renderAll();return JSON.stringify(state.collection);
  });
  await page.locator('.sidebar [data-view=collection]').click();
  await page.locator('#collectionView [data-tile-kind=cards]').selectOption('compact');
  await page.locator('.sidebar [data-view=wanted]').click();
  await page.locator('[data-layout-target=wantedList][data-layout=grid]').click();
  assert.equal(await page.locator('#wantedView [data-tile-kind=cards]').inputValue(),'compact');
  await page.locator('#wantedView [data-tile-kind=cards]').selectOption('standard');
  assert.equal(await page.locator('#collectionView [data-tile-kind=cards]').inputValue(),'standard');
  await page.locator('#displaySettingsButton').click();
  await page.locator('#resetTileSizes').click();
  assert.equal(await page.locator('#displaySettingsDialog [data-tile-kind=sets]').inputValue(),'standard');
  assert.equal(await page.locator('#displaySettingsDialog [data-tile-kind=cards]').inputValue(),'standard');
  assert.equal(await page.evaluate(()=>JSON.stringify(state.collection)),saved);
  // Blocked storage applies the session choice and gives clear feedback.
  await page.evaluate(()=>{window.savedSetItem=Storage.prototype.setItem;Storage.prototype.setItem=()=>{throw Error('Fixture storage unavailable');};});
  await page.locator('#displaySettingsDialog [data-tile-kind=sets]').selectOption('compact');
  assert.match(await page.locator('#displaySettingsMessage').innerText(),/applied for this session/);
  assert.equal(await page.locator('html').getAttribute('data-set-tile-size'),'compact');
  await page.evaluate(()=>Storage.prototype.setItem=window.savedSetItem);
  await page.locator('#closeDisplaySettings').click();
  assert.equal(await page.locator('#displaySettingsDialog').isVisible(),false);
  // Corrupt or obsolete values fall back independently rather than breaking startup.
  await page.evaluate(k=>localStorage.setItem(k,'{"sets":"invalid","cards":"compact"}'),key);
  await page.reload();await page.locator('#allSets .set-card').first().waitFor({state:'attached'});
  assert.equal(await page.locator('html').getAttribute('data-set-tile-size'),'standard');
  assert.equal(await page.locator('html').getAttribute('data-card-tile-size'),'compact');
  assert.equal(await page.evaluate(()=>JSON.stringify(state.collection)),saved);
  assert.deepEqual(errors,[]);
  console.log('PASS: guest Display settings, independent synchronized set/card sizes, saved preferences/reload/category switching, compact/standard/large geometry at 320–1440px, readable names/numbers, 44px buttons, unchanged list rows/catalogue/collector records, reset and storage failure/corruption recovery.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
