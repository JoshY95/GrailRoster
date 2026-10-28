const assert = require('node:assert/strict');
const {chromium} = require('playwright');
const {loadCatalogue} = require('../scripts/catalogue_io');
const KEY = 'grailroster.scanner-test.v1';
const base = process.env.GRAILROSTER_BASE_URL || 'http://127.0.0.1:8767';
const catalogue = loadCatalogue();
const target = catalogue.cards.find(c => c.setId === '2026-topps-stadium-club-wwe' && c.subsetCode === 'BASE' && c.number === '1');
async function picture(page, lines) {
 const data = await page.evaluate(lines => {
  const c=document.createElement('canvas');c.width=1100;c.height=1500;
  const ctx=c.getContext('2d');ctx.fillStyle='#fff';ctx.fillRect(0,0,c.width,c.height);
  ctx.fillStyle='#111';ctx.font='bold 62px Arial';
  lines.forEach((line,i)=>ctx.fillText(line,60,160+i*120));
  return c.toDataURL('image/png').split(',')[1];
 }, lines);
 return {name:'scanner-synthetic-fixture.png',mimeType:'image/png',buffer:Buffer.from(data,'base64')};
}
async function ready(page) {
 await page.goto(`${base}/#scanner`);
 await page.locator('#scanCoverage').filter({hasText:'WWE checklist cards'}).waitFor();
}
async function fakeOCR(page, text) {
 await page.evaluate(text => {
  window.Tesseract={createWorker:async()=>({setParameters:async()=>{},recognize:async()=>({data:{text}}),terminate:async()=>{}})};
 },text);
}
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.CHROMIUM_EXECUTABLE_PATH,args:['--no-sandbox']}: {})});
 let page;
 try {
  const context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true});
  page=await context.newPage();const errors=[],photoUploads=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/rest/v1/**',r=>r.abort());
  await page.route('**/auth/v1/**',r=>r.abort());
  page.on('request',r=>{if(r.method()==='POST'&&!r.url().includes('/auth/'))photoUploads.push(r.url());});
  await ready(page);
  assert.equal(await page.locator('#scannerView').isVisible(),true);
  assert.equal(await page.locator('#categoryWorkspace').isVisible(),false);
  assert.equal(await page.locator('#scanStart').isDisabled(),true);
  const original=await page.evaluate(()=>({collection:JSON.stringify(state.collection),catalogue:JSON.stringify(state.catalogue)}));
  const front=await picture(page,['SETH ROLLINS','2026 TOPPS','STADIUM CLUB WWE','BASE CARDS','#1']);
  const back=await picture(page,['SETH ROLLINS','STADIUM CLUB WWE','#1','07/50','2026 TOPPS']);
  await page.locator('#scanFrontInput').setInputFiles(front);
  await page.locator('#scanBackInput').setInputFiles(back);
  await page.locator('#scanBackPreview canvas').waitFor();
  await page.locator('#scanSet').selectOption(target.setId);
  // Real browser OCR: do not stub the first scan, library, worker, WASM or model.
  await page.locator('#scanStart').click();
  await page.locator('#scanCandidates [data-scan-candidate]').first().waitFor({timeout:120000});
  assert.match(await page.locator('#scanText').inputValue(),/SETH\s+ROLLINS/i);
  assert.equal(await page.locator('#scanAllowance').innerText(),'25 / 25');
  assert.equal(await page.locator('#scanSerial').inputValue(),'07/50');
  const candidate=page.locator('.scan-candidate').filter({hasText:'Seth Rollins'}).filter({hasText:'#1 · BASE CARDS'}).first();
  await candidate.click();
  assert.equal(await page.locator('#scanEditionCheck').isChecked(),false);
  await page.locator('#scanParallel').fill('Gold — manually checked');
  await page.locator('#scanEditionCheck').check();
  await page.locator('#scanConfirmButton').click();
  assert.equal(await page.locator('#scanAllowance').innerText(),'24 / 25');
  assert.equal(await page.locator('#scanTestItems li').count(),1);
  const recorded=await page.evaluate(key=>JSON.parse(localStorage.getItem(key)),KEY);
  assert.equal(recorded.attempts[0].photos,2);
  assert.equal(recorded.attempts[0].source,'photo-ocr');
  assert.equal(recorded.attempts[0].status,'confirmed');
  assert.equal(recorded.items[0].cardId,target.id);
  assert.equal(recorded.attempts[0].apiCostUSD,0);
  assert(!JSON.stringify(recorded).includes('data:image'),'No photo bytes persisted');
  assert.deepEqual(await page.evaluate(()=>({collection:JSON.stringify(state.collection),catalogue:JSON.stringify(state.catalogue)})),original);
  assert.deepEqual(photoUploads,[],'No image, collection or payment POSTs');
  const downloading=page.waitForEvent('download');await page.locator('#scanExport').click();
  const downloaded=await downloading;const chunks=[];for await(const chunk of await downloaded.createReadStream())chunks.push(chunk);
  const exported=JSON.parse(Buffer.concat(chunks).toString());assert.equal(exported.items[0].cardId,target.id);
  await page.reload();await page.locator('#scanTestItems li').waitFor();
  assert.equal(await page.locator('#scanAllowance').innerText(),'24 / 25');
  // Remaining tests inject isolated OCR responses to exercise failure/UI branches.
  // Rejection must visibly replace suggestions at the button, including on phones.
  for(const width of [390,1440]) {
   await page.setViewportSize({width,height:900});
   await fakeOCR(page,'SETH ROLLINS\n2026 TOPPS STADIUM CLUB WWE\n#1');
   await page.locator('#scanFrontInput').setInputFiles(front);
   await page.locator('#scanStart').click();await page.locator('.scan-candidate').first().waitFor();
   const originalText=await page.locator('#scanText').inputValue();
   const usage=await page.locator('#scanAllowance').innerText();
   await page.locator('.scan-candidate').first().click();
   await page.locator('#scanEditionCheck').check();
   await page.locator('#scanReject').click();
   await page.locator('#scanRecovery').waitFor();
   assert.equal(await page.locator('.scan-candidate').count(),0,'Rejected suggestions must clear');
   assert.equal(await page.locator('#scanConfirm').isVisible(),false,'An old selection must not remain saveable');
   assert.equal(await page.locator('#scanReject').isVisible(),false);
   assert.match(await page.locator('#scanResultSummary').innerText(),/Suggestions rejected.*No scan credit/);
   assert.equal(await page.locator('#scanAllowance').innerText(),usage);
   assert.equal(await page.locator('#scanTestItems li').count(),1);
   assert.equal(await page.locator('#scanText').inputValue(),originalText,'Rejection preserves OCR text');
   assert.equal(await page.locator('#scanFrontPreview canvas').count(),1,'Rejection preserves the front photo');
   const rejection=await page.evaluate(key=>JSON.parse(localStorage.getItem(key)).attempts.at(-1),KEY);
   assert.equal(rejection.status,'rejected');assert(rejection.rejectedCandidateIds.length>0);
   // Repeated/programmatic rejection cannot consume a credit or save the prior card.
   await page.locator('#scanReject').evaluate(el=>el.click());
   assert.equal(await page.locator('#scanAllowance').innerText(),usage);
   if(width===390) {
    const choosing=page.waitForEvent('filechooser');
    await page.locator('[data-scan-recovery="front"]').click();
    await (await choosing).setFiles(front);
    await page.locator('#scanRecovery').waitFor({state:'hidden'});
   } else {
    await page.locator('[data-scan-recovery="text"]').click();
    assert.equal(await page.locator('#scanResults details').evaluate(el=>el.open),true);
    assert.equal(await page.locator('#scanText').evaluate(el=>el===document.activeElement),true);
    await page.locator('#scanText').fill('SETH ROLLINS\n#1');
    await page.locator('#scanRematch').click();await page.locator('.scan-candidate').first().waitFor();
    assert.equal(await page.locator('#scanRecovery').isVisible(),false);
    assert.equal(await page.locator('#scanReject').isVisible(),true);
    assert.equal(await page.locator('#scanAllowance').innerText(),usage);
   }
  }
  await fakeOCR(page,'UNKNOWN POKEMON CARD #999');
  await page.locator('#scanFrontInput').setInputFiles(front);await page.locator('#scanStart').click();
  await page.locator('#scanMessage').filter({hasText:'No match yet'}).waitFor();
  assert.equal(await page.locator('.scan-candidate').count(),0);
  assert.equal(await page.locator('#scanAllowance').innerText(),'24 / 25');
  await page.locator('#scanResults details').evaluate(el=>{el.open=true;});
  await page.locator('#scanText').fill('SETH ROLLINS\n2026 TOPPS STADIUM CLUB WWE\n#1');
  await page.locator('#scanRematch').click();await page.locator('.scan-candidate').first().click();
  await page.locator('#scanEditionCheck').check();await page.locator('#scanConfirmButton').click();
  const corrected=await page.evaluate(key=>JSON.parse(localStorage.getItem(key)).attempts.at(-1),KEY);
  assert.equal(corrected.correctedText,true);
  assert.equal(await page.locator('#scanAllowance').innerText(),'23 / 25');
  await page.evaluate(()=>{window.Tesseract={createWorker:async()=>{throw Error('Recognition unavailable');}};});
  await page.locator('#scanStart').click();await page.locator('#scanMessage').filter({hasText:'Recognition unavailable'}).waitFor();
  assert.equal(await page.locator('#scanStart').isEnabled(),true);
  assert.equal(await page.locator('#scanAllowance').innerText(),'23 / 25');
  await page.evaluate(()=>{window.Tesseract={createWorker:()=>new Promise(()=>{})};});
  await page.locator('#scanStart').click();await page.locator('#scanCancel').click();
  assert.match(await page.locator('#scanMessage').innerText(),/cancelled/i);
  assert.equal(await page.evaluate(key=>JSON.parse(localStorage.getItem(key)).attempts.at(-1).status,KEY),'cancelled');
  assert.equal(await page.locator('#scanStart').isEnabled(),true);
  // At the quota limit, recognition is disabled. Reset never touches Vault data.
  await page.evaluate(key=>{const v=JSON.parse(localStorage.getItem(key));v.usage.used=25;localStorage.setItem(key,JSON.stringify(v));},KEY);
  await page.reload();await page.locator('#scanCoverage').filter({hasText:'WWE checklist cards'}).waitFor();
  await page.locator('#scanFrontInput').setInputFiles(front);await page.locator('#scanFrontPreview canvas').waitFor();
  assert.equal(await page.locator('#scanAllowance').innerText(),'0 / 25');assert.equal(await page.locator('#scanStart').isDisabled(),true);
  page.once('dialog',d=>d.accept());await page.locator('#scanReset').click();
  assert.equal(await page.locator('#scanAllowance').innerText(),'25 / 25');assert.equal(await page.locator('#scanTestItems li').count(),0);
  assert.deepEqual(await page.evaluate(()=>({collection:JSON.stringify(state.collection),catalogue:JSON.stringify(state.catalogue)})),original);
  await page.locator('#scanFrontInput').setInputFiles({name:'bad.txt',mimeType:'text/plain',buffer:Buffer.from('no image')});
  await page.locator('#scanMessage').filter({hasText:'Choose a JPEG'}).waitFor();
  await page.locator('#scanFrontInput').setInputFiles(front);await page.locator('#scanFrontPreview canvas').waitFor();
  const size=await page.locator('#scanFrontPreview canvas').evaluate(c=>({w:c.width,h:c.height}));
  await page.locator('[data-scan-action="rotate"][data-scan-side="front"]').click();
  const rotated=await page.locator('#scanFrontPreview canvas').evaluate(c=>({w:c.width,h:c.height}));assert.equal(rotated.w,size.h);
  await fakeOCR(page,'SETH ROLLINS\n#1');
  await page.evaluate(()=>{Storage.prototype.setItem=function(){throw new DOMException('Full','QuotaExceededError');};});
  await page.locator('#scanStart').click();await page.locator('.scan-candidate').first().waitFor();
  assert.equal(await page.locator('#scanStorageNote').isVisible(),true);
  await page.locator('#scanReject').click();
  assert.equal(await page.locator('#scanRecovery').isVisible(),true);
  assert.equal(await page.locator('.scan-candidate').count(),0);
  for(const width of [320,390,600,768,1024,1440]){
   await page.setViewportSize({width,height:900});
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,`scanner overflow at ${width}`);
   assert(await page.locator('#scanStart').evaluate(el=>el.getBoundingClientRect().height>=44));
  }
  await page.screenshot({path:'/tmp/grailroster-scanner.png',fullPage:true});
  await page.evaluate(()=>changeCategory('marvel'));
  assert.equal(await page.locator('#scannerView').isVisible(),true);
  await page.evaluate(()=>changeView('dashboard'));
  assert.equal(await page.locator('#categoryEmpty').isVisible(),true);
  assert.deepEqual(errors,[]);
  console.log('PASS: real browser OCR, front/back one credit, confirmed test-only saves, exports/reload, corrections, visible rejection/photo-picker/text recovery on phone and desktop, failure/cancel/quota/reset, blocked storage, category navigation and responsive scanner.');
 } catch(error) {
  if(page) {
   console.error('Scanner state:',await page.locator('#scanMessage').textContent().catch(()=>''));
   console.error('Detected text:',await page.locator('#scanText').inputValue().catch(()=>''));
   await page.screenshot({path:'/tmp/grailroster-scanner.png',fullPage:true}).catch(()=>{});
  }
  throw error;
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
