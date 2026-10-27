const assert = require('node:assert/strict');
const {chromium} = require('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_EXECUTABLE_PATH,args:['--no-sandbox']});
 try {
  const page=await browser.newPage({viewport:{width:390,height:844}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/rest/v1/**',r=>r.abort());
  await page.goto(process.env.GRAILROSTER_BASE_URL);
  await page.locator('#allSets .set-card').first().waitFor({state:'attached'});
  const [cardId,legacyId]=await page.evaluate(()=>state.catalogue.cards.slice(0,2).map(c=>c.id));
  // The actual card-details entry point must lead straight to an unsaved copy form.
  await page.evaluate(id=>openCard(id),cardId);
  assert.equal(await page.locator('#collectionDetailsForm').count(),0);
  await page.locator('#collectionCopyActions [data-vault-card]').click();
  assert.equal(await page.locator('#vaultForm').isVisible(),true);
  assert.equal(await page.locator('#vaultMoreDetails').getAttribute('open'),null);
  assert.equal(await page.evaluate(id=>entryFor(id),cardId),null);
  await page.locator('#vaultClose').click();
  assert.equal(await page.evaluate(id=>entryFor(id),cardId),null);
  await page.locator('#closeCardDialog').click();
  // Wanted records remain wanted if the user abandons the add form.
  await page.evaluate(id=>setStatus(id,'wanted'),cardId);
  await page.evaluate(id=>Vault.open(id),cardId);
  await page.locator('#vaultClose').click();
  assert.equal(await page.evaluate(id=>statusFor(id),cardId),'wanted');
  await page.evaluate(id=>Vault.open(id),cardId);
  await page.locator('#vaultForm [name=parallel]').fill('Gold');
  await page.locator('#vaultForm [name=serialNumber]').fill('12/50');
  await page.locator('#vaultSaveAnother').click();
  await page.waitForFunction(()=>document.querySelector('#vaultMessage').textContent.includes('Add another copy'));
  assert.equal(await page.locator('#vaultForm [name=parallel]').inputValue(),'');
  assert.equal(await page.locator('#vaultForm [name=serialNumber]').inputValue(),'');
  assert.equal(await page.evaluate(id=>entryFor(id).copies.length,cardId),1);
  await page.locator('#vaultForm [name=parallel]').fill('Orange');
  await page.locator('#vaultForm [name=serialNumber]').fill('07/25');
  await page.locator('#vaultSaveAnother').click();
  await page.waitForFunction(id=>entryFor(id).copies.length===2,cardId);
  await page.locator('#vaultForm [name=parallel]').fill('Red');
  await page.locator('#vaultForm [name=serialNumber]').fill('4/5');
  await page.locator('#vaultSave').click();
  await page.locator('#vaultDialog').waitFor({state:'hidden'});
  let saved=await page.evaluate(id=>entryFor(id),cardId);
  assert.deepEqual(saved.copies.map(c=>c.serialNumber),['12/50','07/25','4/5']);
  assert.equal(new Set(saved.copies.map(c=>c.id)).size,3);
  assert.equal(saved.quantity,3);
  assert.equal(await page.evaluate(()=>counts().owned),1,'Duplicates count once in checklist completion');
  const original=JSON.stringify(saved);
  await page.reload();await page.locator('#allSets .set-card').first().waitFor({state:'attached'});
  assert.equal(await page.evaluate(id=>JSON.stringify(entryFor(id)),cardId),original);
  // Starting a fourth copy, including Escape, cannot create a phantom owned card.
  await page.evaluate(id=>Vault.open(id),cardId);
  await page.locator('#vaultAdd').click();
  await page.keyboard.press('Escape');
  assert.equal(await page.evaluate(id=>JSON.stringify(entryFor(id)),cardId),original);
  // Base cards need no details. A full device must keep both prior state and the draft.
  await page.evaluate(id=>Vault.open(id),legacyId);
  await page.evaluate(()=>{window.originalSetItem=Storage.prototype.setItem;Storage.prototype.setItem=function(){throw new Error('Fixture: storage full');};});
  await page.locator('#vaultSave').click();
  await page.waitForFunction(()=>document.querySelector('#vaultMessage').textContent.includes('storage full'));
  assert.equal(await page.evaluate(id=>entryFor(id),legacyId),null);
  await page.evaluate(()=>Storage.prototype.setItem=window.originalSetItem);
  await page.locator('#vaultSave').click();await page.locator('#vaultDialog').waitFor({state:'hidden'});
  assert.equal(await page.evaluate(id=>entryFor(id).copies.length,legacyId),1);
  assert.equal(await page.evaluate(id=>entryFor(id).copies[0].serialNumber,legacyId),'');
  // Review/cancel leaves an old quantity and all metadata byte-for-byte unchanged.
  const old=await page.evaluate(id=>{
   state.collection[id]={status:'owned',quantity:3,purchasePrice:75,purchaseCurrency:'AUD',acquiredAt:'2026-01-01',notes:'Legacy price and notes',condition:'Near Mint',updatedAt:'2026-10-01T00:00:00Z'};saveCollection();
   Vault.open(id);return JSON.stringify(entryFor(id));
  },legacyId);
  await page.locator('#vaultClose').click();
  assert.equal(await page.evaluate(id=>JSON.stringify(entryFor(id)),legacyId),old);
  await page.evaluate(id=>Vault.open(id),legacyId);
  await page.locator('#vaultForm [name=serialNumber]').fill('03/99');
  await page.locator('#vaultSave').click();await page.waitForFunction(()=>document.querySelector('#vaultMessage').textContent==='Copy saved.');
  saved=await page.evaluate(id=>entryFor(id),legacyId);
  assert.equal(saved.copies.length,3);assert.equal(saved.quantity,3);
  assert.deepEqual(saved.copies.map(c=>c.purchasePrice),[75,null,null]);
  assert.deepEqual(saved.copies.map(c=>c.notes),['Legacy price and notes','','']);
  assert.equal(saved.copies[0].acquiredAt,'2026-01-01');
  assert.equal(saved.purchasePrice,75);assert.equal(saved.notes,'Legacy price and notes');
  assert.equal(await page.evaluate(id=>JSON.stringify(entryFor(id)),cardId),original,'Other cards must remain unchanged');
  for(const width of [320,390,768,1440]) {
   await page.setViewportSize({width,height:900});
   assert.equal(await page.locator('#vaultDialog').evaluate(el=>el.scrollWidth<=el.clientWidth),true,`Copy entry overflow at ${width}`);
  }
  assert.deepEqual(errors,[]);
  console.log('PASS: direct add, optional fields, cancel/Escape, wanted preservation, numbered duplicates, Save & add another, blank base copy, failed device save/retry, legacy metadata and independent card preservation, reload and responsive layout.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
