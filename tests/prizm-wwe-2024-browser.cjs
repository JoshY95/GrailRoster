const assert=require('node:assert/strict');const {chromium}=require('playwright');
const index=require('../data/catalogue-index.json');
(async()=>{const browser=await chromium.launch({headless:true});try{
 const context=await browser.newContext({viewport:{width:1440,height:900}}),page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.route('**/rest/v1/**',r=>r.abort());
 await page.goto(process.env.GRAILROSTER_BASE_URL||'http://127.0.0.1:8767');await page.locator('#allSets .set-card').first().waitFor({state:'attached'});
 assert.equal(await page.locator('#allSets .set-card').count(),index.sets.filter(s=>s.categoryId==='wwe').length);
 const sentinel=await page.evaluate(()=>{const c=state.catalogue.cards[0];state.collection[c.id]={status:'wanted',notes:'Prizm preservation sentinel',updatedAt:'2026-10-26T00:00:00Z'};saveCollection();renderAll();return {id:c.id,value:JSON.stringify(state.collection[c.id])};});
 await page.evaluate(()=>changeView('cards'));await page.locator('#setFilter').selectOption('2024-panini-prizm-wwe');assert.equal(await page.locator('#resultCount').innerText(),'516 cards');
 const ids=await page.evaluate(()=>categoryCatalogue().sets.filter(s=>s.id.includes('2024-panini-prizm')).map(s=>s.id));assert.deepEqual(ids,['2024-panini-prizm-wwe']);
 await page.locator('#categoryFilter').selectOption('Variation');assert.equal(await page.locator('#resultCount').innerText(),'20 cards');await page.locator('#globalSearch').fill('Ringmaster');assert.equal(await page.locator('#cardList .card-row').count(),1);await page.locator('#cardList .card-row').first().locator('.state-button.owned').click();
 assert.equal(await page.evaluate(()=>state.collection['2024-PPWWE-BHV-14']?.status),'owned');assert.equal(await page.evaluate(()=>state.collection['2024-PPWWE-BH-14']?.status),undefined);
 await page.locator('#categoryFilter').selectOption('Base');await page.locator('#globalSearch').fill('Stone Cold');assert((await page.locator('#cardList .card-row').count())>0);
 await page.locator('#categoryFilter').selectOption('Autograph');await page.locator('#globalSearch').fill('LA Knight');assert((await page.locator('#cardList .card-row').count())>0);
 for(const width of [320,390,768,1024,1440]){await page.setViewportSize({width,height:900});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`Overflow ${width}`);}
 await page.locator('#categorySwitcher [data-franchise="star-wars"]').click();assert.equal(await page.evaluate(()=>counts().owned),0);await page.locator('#categorySwitcher [data-franchise="wwe"]').click();assert.equal(await page.evaluate(()=>counts().owned),1);
 await page.reload();await page.locator('#allSets .set-card').first().waitFor({state:'attached'});assert.equal(await page.evaluate(()=>counts().owned),1);assert.equal(await page.evaluate(id=>JSON.stringify(state.collection[id]),sentinel.id),sentinel.value);assert.deepEqual(errors,[]);
 console.log('PASS: one Prizm parent, 516 cards, 20 independently owned variations, signer search, persistence, category isolation and responsive layouts.');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exit(1)});
