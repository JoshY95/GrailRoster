const assert=require('node:assert/strict');
const {chromium}=require('playwright');
const index=require('../data/catalogue-index.json');
const ids=['2024-panini-three-count-wwe','2024-panini-select-wwe','2024-panini-photogenic-wwe'];

async function saveNewCopy(page) {
 await page.locator('#vaultSave').click();
 await page.locator('#vaultDialog').waitFor({state:'hidden'});
}
(async()=>{
 const browser=await chromium.launch({headless:true});
 try{
  const context=await browser.newContext({viewport:{width:1440,height:900}}),page=await context.newPage(),errors=[];
  page.on('pageerror',e=>errors.push(e.message));await page.route('**/rest/v1/**',r=>r.abort());
  await page.goto(process.env.GRAILROSTER_BASE_URL||'http://127.0.0.1:8767');await page.locator('#allSets .set-card').first().waitFor({state:'attached'});
  assert.equal(await page.locator('#allSets .set-card').count(),index.sets.filter(s=>s.categoryId==='wwe').length);
  const original=await page.evaluate(()=>{const c=state.catalogue.cards[0];state.collection[c.id]={status:'wanted',quantity:2,notes:'Existing collector sentinel',updatedAt:'2026-10-26T00:00:00Z'};saveCollection();renderAll();return {id:c.id,value:JSON.stringify(state.collection[c.id])};});
  await page.evaluate(()=>changeView('cards'));
  for(const id of ids){
   await page.locator('#clearFilters').click();await page.locator('#setFilter').selectOption(id);
   assert.equal(await page.locator('#resultCount').innerText(),index.sets.find(s=>s.id===id).cardCount.toLocaleString('en-US')+' cards');
   await page.locator('#cardList .card-row').first().locator('.state-button.owned').click();await saveNewCopy(page);
  }
  assert.equal(await page.evaluate(()=>counts().owned),3);
  await page.locator('#categorySwitcher [data-franchise="star-wars"]').click();assert.equal(await page.evaluate(()=>counts().owned),0);
  await page.locator('#categorySwitcher [data-franchise="wwe"]').click();assert.equal(await page.evaluate(()=>counts().owned),3);
  await page.locator('#setFilter').selectOption(ids[2]);await page.locator('#globalSearch').fill('175');
  const conflict=await page.evaluate(()=>categoryCatalogue().cards.filter(c=>c.setId==='2024-panini-photogenic-wwe'&&c.subsetCode==='BV'&&c.number==='175').map(c=>({id:c.id,name:c.name})));
  assert.equal(conflict.length,2);assert.notEqual(conflict[0].id,conflict[1].id);
  await page.evaluate(id=>setStatus(id,'owned'),conflict[0].id);await saveNewCopy(page);assert.equal(await page.evaluate(id=>state.collection[id]?.status,conflict[1].id),undefined);
  await page.locator('#clearFilters').click();await page.locator('#setFilter').selectOption(ids[2]);await page.locator('#categoryFilter').selectOption('Autograph');await page.locator('#globalSearch').fill('Jade Cargill');
  assert((await page.locator('#cardList .card-row').count())>0);
  for(const width of [320,390,768,1024,1440]){await page.setViewportSize({width,height:900});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`Overflow ${width}`);}
  await page.reload();await page.locator('#allSets .set-card').first().waitFor({state:'attached'});
  assert.equal(await page.evaluate(id=>JSON.stringify(state.collection[id]),original.id),original.value);
  assert.equal(await page.evaluate(()=>counts().owned),4);assert.deepEqual(errors,[]);
  console.log('PASS: all three WWE sets, ownership/category isolation, #175 conflict isolation, signer search, persistence and responsive layouts.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});

