const assert=require('node:assert/strict');
const {chromium}=require('playwright');
const index=require('../data/catalogue-index.json');
const ids=['2023-panini-immaculate-wwe','2023-panini-chronicles-wwe','2023-panini-impeccable-wwe'];

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
  const original=await page.evaluate(()=>{const c=state.catalogue.cards[0];state.collection[c.id]={status:'wanted',quantity:2,notes:'Prior collector sentinel',updatedAt:'2026-10-27T00:00:00Z'};saveCollection();renderAll();return {id:c.id,value:JSON.stringify(state.collection[c.id])};});
  await page.evaluate(()=>changeView('cards'));
  for(const id of ids){
   await page.locator('#clearFilters').click();await page.locator('#setFilter').selectOption(id);
   assert.equal(await page.locator('#resultCount').innerText(),index.sets.find(s=>s.id===id).cardCount.toLocaleString('en-US')+' cards');
   await page.locator('#cardList .card-row').first().locator('.state-button.owned').click();await saveNewCopy(page);
  }
  assert.equal(await page.evaluate(()=>counts().owned),3);
  await page.locator('#categorySwitcher [data-franchise="star-wars"]').click();assert.equal(await page.evaluate(()=>counts().owned),0);
  await page.locator('#categorySwitcher [data-franchise="wwe"]').click();assert.equal(await page.evaluate(()=>counts().owned),3);
  await page.locator('#clearFilters').click();await page.locator('#setFilter').selectOption(ids[2]);await page.locator('#globalSearch').fill('Nova');
  assert((await page.locator('#cardList .card-row').count())>0);assert((await page.locator('#cardList').innerText()).includes('Indelible Ink'));
  await page.locator('#clearFilters').click();await page.locator('#setFilter').selectOption(ids[0]);await page.locator('#globalSearch').fill('The Sandman');
  assert((await page.locator('#cardList').innerText()).includes('Quad Autographs'));
  const book=await page.evaluate(()=>state.catalogue.cards.find(c=>c.setId==='2023-panini-immaculate-wwe'&&c.subsetCode==='TAE'));
  assert.equal(book.name.split(' / ').length,8);
  await page.locator('#globalSearch').fill('The Attitude Era');assert.equal(await page.locator('#cardList .card-row').count(),1);
  for(const width of [320,390,768,1024,1440]){
   await page.setViewportSize({width,height:900});
   const layout=await page.evaluate(()=>({fits:document.documentElement.scrollWidth<=innerWidth,overflow:Array.from(document.querySelectorAll('main *')).filter(e=>e.getBoundingClientRect().width&&e.getBoundingClientRect().right>innerWidth+1).slice(0,12).map(e=>({tag:e.tagName,class:e.className,text:e.textContent.slice(0,100),width:e.getBoundingClientRect().width,right:e.getBoundingClientRect().right}))}));
   assert(layout.fits,`Overflow at ${width}: ${JSON.stringify(layout.overflow)}`);
  }
  await page.evaluate(id=>setStatus(id,'owned'),book.id);await saveNewCopy(page);assert.equal(await page.evaluate(()=>counts().owned),4);
  await page.reload();await page.locator('#allSets .set-card').first().waitFor({state:'attached'});
  assert.equal(await page.evaluate(id=>JSON.stringify(state.collection[id]),original.id),original.value);assert.equal(await page.evaluate(()=>counts().owned),4);
  const gaps=await page.evaluate(()=>({impeccable:state.catalogue.cards.some(c=>c.setId==='2023-panini-impeccable-wwe'&&c.subsetCode==='BASE'&&c.number==='36'),chronicles:state.catalogue.cards.some(c=>c.setId==='2023-panini-chronicles-wwe'&&c.subsetCode==='BCHR'&&c.number==='14')}));
  assert.deepEqual(gaps,{impeccable:false,chronicles:false});assert.deepEqual(errors,[]);
  console.log('PASS: three 2023 WWE sets, ownership/category separation, prior entry persistence, original numbering gaps, Nova parallel-only identity, corrected four-signer and eight-signer designs, responsive layout.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});

