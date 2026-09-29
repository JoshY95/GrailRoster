const assert = require('node:assert/strict');
const {chromium} = require('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_EXECUTABLE_PATH,args:['--no-sandbox']});
 try {
  const page=await browser.newPage({viewport:{width:390,height:844}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/rest/v1/**',r=>r.abort());
  await page.goto(process.env.GRAILROSTER_BASE_URL || 'http://127.0.0.1:8766');
  await page.locator('#allSets .set-card').first().waitFor({state:'attached'});
  const cardId=await page.evaluate(()=>{
   const id=state.catalogue.cards[0].id;
   state.collection[id]={status:'owned',quantity:2,purchasePrice:30,purchaseCurrency:'AUD',notes:'Original notes',updatedAt:new Date().toISOString()};
   saveCollection();renderAll();Vault.open(id);return id;
  });
  assert.match(await page.locator('#vaultContent').innerText(),/2 existing copies/);
  await page.locator('#vaultSetup').click();
  await page.locator('#vaultForm').waitFor();
  assert.equal(await page.locator('[data-vault-edit]').count(),2);
  await page.locator('[data-vault-edit]').first().click();
  assert.equal(await page.locator('[name=purchasePrice]').last().inputValue(),'30');
  assert.equal(await page.locator('#vaultForm [name=notes]').inputValue(),'Original notes');
  await page.locator('#vaultForm [name=parallel]').fill('Gold');
  await page.locator('#vaultForm [name=serialNumber]').fill('07/25');
  await page.locator('#vaultForm [name=format]').selectOption('graded');
  await page.locator('#vaultForm [name=gradingCompany]').fill('PSA');
  await page.locator('#vaultForm [name=grade]').fill('10');
  await page.locator('#vaultForm [name=certification]').fill('0012345');
  await page.locator('#vaultForm [name=estimatedValue]').fill('50');
  await page.locator('#vaultForm [name=location]').fill('Binder A');
  await page.locator('#vaultForm button[type=submit]').click();
  await page.waitForFunction(()=>document.querySelector('#vaultMessage').textContent==='Copy saved.');
  assert.match(await page.locator('#vaultContent').innerText(),/Unrealised gain\/loss.*\$20\.00/);
  await page.locator('#vaultForm [name=status]').selectOption('sold');
  await page.locator('#vaultForm details').evaluate(el=>el.open=true);
  await page.locator('#vaultForm [name=salePrice]').fill('65');
  await page.locator('#vaultForm [name=saleFees]').fill('5');
  await page.locator('#vaultForm [name=soldAt]').fill('2026-09-30');
  await page.locator('#vaultForm button[type=submit]').click();
  await page.waitForFunction(()=>document.querySelector('#vaultMessage').textContent==='Copy saved.');
  assert.match(await page.locator('#vaultContent').innerText(),/Realised gain\/loss.*\$30\.00/);
  assert.equal(await page.evaluate(id=>entryFor(id).quantity,cardId),1);
  await page.locator('[data-vault-edit]').nth(1).click();
  assert.equal(await page.locator('#vaultForm [name=purchasePrice]').inputValue(),'');
  await page.locator('#vaultForm [name=status]').selectOption('traded');
  await page.locator('#vaultForm button[type=submit]').click();
  await page.waitForFunction(()=>document.querySelector('#vaultMessage').textContent==='Copy saved.');
  assert.equal(await page.evaluate(id=>statusFor(id),cardId),'missing');
  await page.reload();await page.locator('#allSets .set-card').first().waitFor({state:'attached'});
  assert.equal(await page.evaluate(id=>entryFor(id).copies.length,cardId),2);
  await page.evaluate(id=>Vault.open(id),cardId);
  await page.locator('#vaultAdd').click();
  await page.waitForFunction(()=>document.querySelectorAll('[data-vault-edit]').length===3);
  assert.equal(await page.evaluate(id=>statusFor(id),cardId),'owned');
  for(const width of [320,390,768,1440]) {
   await page.setViewportSize({width,height:900});
   assert.equal(await page.locator('#vaultDialog').evaluate(el=>el.scrollWidth<=el.clientWidth),true,`Vault overflow at ${width}`);
  }
  await page.setViewportSize({width:390,height:844});
  await page.screenshot({path:'/workspace/scratch/4c525d9bd229/vault-mobile.png',fullPage:true});
  page.on('dialog',d=>d.accept());await page.locator('#vaultDelete').click();
  await page.waitForFunction(()=>document.querySelectorAll('[data-vault-edit]').length===2);
  assert.equal(await page.evaluate(id=>statusFor(id),cardId),'missing');
  assert.deepEqual(errors,[]);
  console.log('PASS: legacy conversion, per-copy edits, grading, serials, valuations, sale/trade history, quantities, reload, add/delete and responsive layout.');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
