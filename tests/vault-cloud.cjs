const assert=require('node:assert/strict');
const {chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_EXECUTABLE_PATH,args:['--no-sandbox']});
 try {
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  await page.route('**/rest/v1/**',r=>r.abort());
  await page.goto(process.env.GRAILROSTER_BASE_URL);
  await page.locator('#allSets .set-card').first().waitFor({state:'attached'});
  await page.evaluate(()=>{
   const id=state.catalogue.cards[0].id;const timestamp=new Date().toISOString();
   state.user={id:'11111111-1111-4111-8111-111111111111',email:'fixture@example.invalid'};
   state.collection[id]={status:'owned',quantity:1,purchaseCurrency:'AUD',updatedAt:timestamp};
   window.vaultTest={row:{updated_at:timestamp},fail:false,conflict:false,uploads:[],removals:[],queries:[]};
   state.supabase={from:()=>({update(row){const filters={};return {eq(k,v){filters[k]=v;return this;},async select(){vaultTest.queries.push(filters);if(vaultTest.fail)return {error:Error('Fixture: network failure')};if(vaultTest.conflict || filters.updated_at!==vaultTest.row.updated_at)return {data:[]};vaultTest.row=row;return {data:[{card_id:row.card_id}]};}}},async insert(row){vaultTest.row=row;return {error:null};}}),storage:{from:()=>({async upload(path,blob){vaultTest.uploads.push({path,type:blob.type,size:blob.size});return {error:null};},async remove(paths){vaultTest.removals.push(...paths);return {error:null};},async createSignedUrl(){return {error:Error('Fixture unavailable')};}})}};
   Vault.open(id);
  });
  await page.locator('#vaultSetup').click();await page.locator('#vaultForm').waitFor();
  await page.locator('#vaultForm [name=serialNumber]').fill('01/10');
  await page.evaluate(()=>vaultTest.conflict=true);
  await page.locator('#vaultForm button[type=submit]').click();
  await page.waitForFunction(()=>document.querySelector('#vaultMessage').textContent.includes('changed elsewhere'));
  assert.equal(await page.evaluate(()=>Object.values(state.collection)[0].copies[0].serialNumber),'');
  await page.evaluate(()=>vaultTest.conflict=false);
  const image=await page.evaluate(()=>{const c=document.createElement('canvas');c.width=20;c.height=40;c.getContext('2d').fillRect(0,0,20,40);return c.toDataURL('image/png').split(',')[1];});
  await page.locator('#vaultForm [name=frontFile]').setInputFiles({name:'front.png',mimeType:'image/png',buffer:Buffer.from(image,'base64')});
  await page.locator('#vaultForm button[type=submit]').click();
  await page.waitForFunction(()=>document.querySelector('#vaultMessage').textContent==='Copy saved.');
  assert.equal(await page.evaluate(()=>vaultTest.uploads[0].type),'image/jpeg');
  assert.match(await page.evaluate(()=>vaultTest.row.vault_copies[0].front),/^11111111-1111-4111-8111-111111111111\//);
  assert.equal(await page.evaluate(()=>vaultTest.queries.at(-1).user_id),'11111111-1111-4111-8111-111111111111');
  await page.locator('#vaultForm [name=backFile]').setInputFiles({name:'back.png',mimeType:'image/png',buffer:Buffer.from(image,'base64')});
  await page.evaluate(()=>vaultTest.fail=true);
  await page.locator('#vaultForm button[type=submit]').click();
  await page.waitForFunction(()=>document.querySelector('#vaultMessage').textContent.includes('network failure'));
  assert.equal(await page.evaluate(()=>vaultTest.removals.length),1);
  assert.equal(await page.evaluate(()=>vaultTest.row.vault_copies[0].back),null);
  await page.evaluate(()=>{vaultTest.fail=false;Object.values(state.collection)[0].updatedAt='2030-01-01T00:00:00.000Z';});
  await page.locator('#vaultForm button[type=submit]').click();
  await page.waitForFunction(()=>document.querySelector('#vaultMessage').textContent.includes('while you were editing'));
  await page.evaluate(()=>Vault.reset());
  assert.equal(await page.locator('#vaultDialog').isVisible(),false);
  assert.equal(await page.locator('#vaultContent').innerText(),'');
  console.log('PASS: cloud write contract, optimistic conflicts, photo JPEG processing, failed-save cleanup, in-session conflict detection and private view reset (mocked network).');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
