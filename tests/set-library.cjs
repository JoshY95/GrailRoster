const assert=require('node:assert/strict');
const {chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_EXECUTABLE_PATH,args:['--no-sandbox']});
 try {
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/rest/v1/**',route=>route.abort());
  await page.goto(process.env.GRAILROSTER_BASE_URL);
  await page.locator('#allSets .set-card').first().waitFor({state:'attached'});
  await page.locator('.sidebar [data-view=sets]').click();
  const initial=await page.evaluate(()=>({sets:categoryCatalogue().sets.map(s=>({...s})),source:JSON.stringify(state.catalogue),collection:JSON.stringify(state.collection)}));
  const ids=()=>page.locator('#allSets .set-card').evaluateAll(nodes=>nodes.map(n=>n.dataset.setId));
  const dates=async()=>{const shown=await ids();return shown.map(id=>initial.sets.find(s=>s.id===id).releaseDate||null);};
  const assertDates=(values,ascending)=>{
   let undated=false,last=null;
   for(const value of values){
    if(!value){undated=true;continue;}
    assert.equal(undated,false,'Undated sets must appear last');
    if(last)assert(ascending?value>=last:value<=last,`Release dates out of order: ${last}, ${value}`);
    last=value;
   }
  };
  assert.equal(await page.locator('#setSort').inputValue(),'newest');
  assertDates(await dates(),false);
  await page.locator('#setSort').selectOption('oldest');assertDates(await dates(),true);
  for(const [sort,direction] of [['name-asc',1],['name-desc',-1]]){
   await page.locator('#setSort').selectOption(sort);
   const names=await page.locator('#allSets h3').allTextContents();
   for(let i=1;i<names.length;i++)assert(direction*names[i-1].localeCompare(names[i],'en-AU',{numeric:true,sensitivity:'base'})<=0);
  }
  for(const [sort,direction] of [['cards-desc',-1],['cards-asc',1]]){
   await page.locator('#setSort').selectOption(sort);
   const sizes=(await ids()).map(id=>initial.sets.find(s=>s.id===id).cardCount);
   for(let i=1;i<sizes.length;i++)assert(direction*(sizes[i]-sizes[i-1])>=0);
  }
  await page.locator('#setYear').selectOption('2024');await page.locator('#setBrand').selectOption('Panini');
  const filtered=initial.sets.filter(s=>s.year===2024&&s.manufacturer==='Panini');
  assert.deepEqual(new Set(await ids()),new Set(filtered.map(s=>s.id)));
  await page.locator('#setSearch').fill('Prizm');
  assert.deepEqual(await ids(),['2024-panini-prizm-wwe']);
  await page.locator('#setSearch').fill('no-matching-set-zzzz');
  assert.equal((await ids()).length,0);
  assert.match(await page.locator('#allSets').innerText(),/No sets match these filters/);
  await page.locator('#resetSetLibrary').click();
  assert.equal(await page.locator('#setSearch').inputValue(),'');
  assert.equal(await page.locator('#setYear').inputValue(),'all');
  assert.equal(await page.locator('#setBrand').inputValue(),'all');
  assert.equal(await page.locator('#setSort').inputValue(),'newest');
  assert.equal((await ids()).length,initial.sets.length);
  // Distinct physical copies must count once toward set completion.
  const fixture=await page.evaluate(()=>{
   const sets=categoryCatalogue().sets;
   const completed=sets.find(s=>s.cardCount===1);
   const partial=sets.find(s=>s.cardCount>100&&s.id!==completed.id);
   const wanted=sets.find(s=>s.id!==completed.id&&s.id!==partial.id);
   const completeCard=state.catalogue.cards.find(c=>c.setId===completed.id);
   const partialCard=state.catalogue.cards.find(c=>c.setId===partial.id);
   const wantedCard=state.catalogue.cards.find(c=>c.setId===wanted.id);
   state.collection[completeCard.id]={status:'owned',quantity:1};
   state.collection[partialCard.id]={status:'owned',quantity:3,copies:Array.from({length:3},()=>({status:'owned',currency:'AUD',purchasePrice:null,estimatedValue:null}))};
   state.collection[wantedCard.id]={status:'wanted'};
   saveCollection();renderAll();return {completed:completed.id,partial:partial.id,wanted:wanted.id,collection:JSON.stringify(state.collection)};
  });
  for(const [filter,expected] of [['collecting',[fixture.completed,fixture.partial]],['in-progress',[fixture.partial]],['completed',[fixture.completed]],['wanted',[fixture.wanted]]]){
   await page.locator('#setOwnership').selectOption(filter);
   assert.deepEqual(new Set(await ids()),new Set(expected),filter);
  }
  await page.locator('#setOwnership').selectOption('not-started');
  assert.equal((await ids()).length,initial.sets.length-2);
  await page.locator('#setOwnership').selectOption('all');
  await page.locator('#setSort').selectOption('progress-desc');
  assert.deepEqual((await ids()).slice(0,2),[fixture.completed,fixture.partial]);
  await page.locator('#setSort').selectOption('progress-asc');
  assert.deepEqual((await ids()).slice(-2),[fixture.partial,fixture.completed]);
  // Preferences survive both reloads and switching collection category.
  await page.locator('#setYear').selectOption('2024');await page.locator('#setBrand').selectOption('Panini');
  const wweIds=await ids();
  await page.locator('#categorySwitcher [data-franchise="star-wars"]').click();
  assert.equal(await page.locator('#setYear').inputValue(),'all');
  assert.equal(await page.locator('#setBrand option[value="Panini"]').count(),0);
  await page.locator('#setSort').selectOption('oldest');
  await page.locator('#setYear').selectOption('2025');
  await page.locator('#categorySwitcher [data-franchise=wwe]').click();
  assert.equal(await page.locator('#setSort').inputValue(),'progress-asc');
  assert.equal(await page.locator('#setYear').inputValue(),'2024');
  assert.equal(await page.locator('#setBrand').inputValue(),'Panini');
  assert.deepEqual(await ids(),wweIds);
  await page.reload();await page.locator('#allSets .set-card').first().waitFor({state:'attached'});
  assert.deepEqual(await ids(),wweIds);
  assert.equal(await page.locator('#setSort').inputValue(),'progress-asc');
  assert.equal(await page.evaluate(()=>JSON.stringify(state.collection)),fixture.collection);
  assert.equal(await page.evaluate(()=>JSON.stringify(state.catalogue)),initial.source,'Sorting never mutates catalogue order');
  for(const width of [320,390,768,1440]){
   await page.setViewportSize({width,height:900});
   assert.equal(await page.locator('body').evaluate(el=>el.scrollWidth<=innerWidth),true,`Library overflow at ${width}`);
   assert.equal(await page.locator('#setSort').isVisible(),true);
   assert.equal(await page.locator('#setOwnership').isVisible(),true);
  }
  await page.locator('#resetSetLibrary').click();
  await page.locator('#setSearch').fill('Prizm');
  await page.locator('#allSets .set-card').first().click();
  assert.equal(await page.locator('#cardsView').isVisible(),true);
  assert.equal(await page.locator('#setFilter').inputValue(),'2024-panini-prizm-wwe');
  assert.deepEqual(errors,[]);
  console.log('PASS: all eight set sorts, undated-last release order, combined search/year/brand filters, unique-card progress/status filters, reset, per-category preferences/reload, preserved catalogue and collection, checklist navigation and 320–1440px layouts.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
