// DOM integration tests use the real page, renderers and event handlers.
// They do not replace Chromium layout/offline/cloud checks.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {parseHTML} = require('linkedom');
const {loadCatalogue} = require('../scripts/catalogue_io');
const root = path.resolve(__dirname, '..');
const read = name => fs.readFileSync(path.join(root,name),'utf8');
const shipped=loadCatalogue();
const starWarsSets=shipped.sets.filter(s=>s.categoryId==='star-wars');
const starWarsIds=new Set(starWarsSets.map(s=>s.id));
const starWarsCount=shipped.cards.filter(c=>starWarsIds.has(c.setId)).length;

async function harness(storage = new Map()) {
  const {window} = parseHTML(read('index.html'));
  const {document} = window;
  // LinkeDOM lacks the browser's select.value setter and dialog methods.
  Object.defineProperty(window.HTMLSelectElement.prototype,'value',{
    configurable:true,
    get() {return [...this.options].find(o=>o.hasAttribute('selected'))?.value || this.options[0]?.value || '';},
    set(value) {for(const option of this.options) option.toggleAttribute('selected',option.value===value);},
  });
  const errors=[];
  const downloads=[];
  const location={href:'http://localhost/',hash:'',protocol:'http:',origin:'http://localhost'};
  const context = vm.createContext({
    window, document, location, navigator:{},
    localStorage:{getItem:k=>storage.get(k)??null,setItem:(k,v)=>storage.set(k,String(v)),removeItem:k=>storage.delete(k)},
    fetch:async url=>({ok:true,json:async()=>JSON.parse(read(url))}),
    history:{replaceState:(_a,_b,url)=>{location.hash=url;}},
    console:{...console,error:(...args)=>errors.push(args.join(' ')),warn:()=>{}},
    setTimeout:()=>1,clearTimeout:()=>{},structuredClone,crypto:require('node:crypto').webcrypto,
    Blob,URL:class extends URL {static createObjectURL(blob){downloads.push(blob);return 'blob:test';} static revokeObjectURL(){}},
  });
  window.scrollTo=()=>{};
  window.matchMedia=()=>({matches:false});
  for(const name of ['categories.js','ui.js','vault.js','app.js']) {
    const source=read(name).replace(/\ninit\(\);\s*$/,'');
    vm.runInContext(source,context,{filename:name});
    if(name==='ui.js') context.GrailUI=window.GrailUI;
  }
  const run=code=>vm.runInContext(code,context);
  await run('init()');
  for(const dialog of document.querySelectorAll('dialog')) {
    dialog.showModal=()=>{dialog.open=true;};dialog.close=()=>{dialog.open=false;};
  }
  assert.deepEqual(errors,[],'Page init must succeed');
  return {run,document,storage,context,errors,downloads};
}

(async()=>{
  const page=await harness();
  const {run,document,storage}=page;
  assert.equal(document.querySelectorAll('#allSets .set-card').length,24);
  assert.equal(run('categoryCatalogue().cardCount'),11298);
  const original=JSON.stringify(loadCatalogue().cards);
  // Seed only this isolated DOM. No external writes or real collection fixtures.
  const owned=run('state.catalogue.cards[0].id');
  const wanted=run('state.catalogue.cards[1].id');
  run(`state.collection[${JSON.stringify(owned)}]={status:'owned',quantity:2,notes:'Preserve me',updatedAt:'2026-10-25T00:00:00Z'};
       state.collection[${JSON.stringify(wanted)}]={status:'wanted',updatedAt:'2026-10-25T00:00:00Z'};saveCollection();renderAll();`);
  const before=storage.get('grailroster.collection.v1');
  run(`state.setId=state.catalogue.sets[0].id;state.query='John';state.category='Base';state.status='owned';`);
  document.querySelector('[data-franchise="star-wars"]').click();
  assert.equal(run('state.franchise'),'star-wars');
  assert.equal(run('state.query'),'');
  assert.equal(run('state.setId'),'all');
  assert.equal(document.querySelector('#categoryWorkspace').hidden,false);
  assert.equal(document.querySelector('#categoryEmpty').hidden,true);
  assert.equal(run('categoryCatalogue().cardCount'),starWarsCount);
  assert.equal(document.querySelectorAll('#allSets .set-card').length,starWarsSets.length);
  run("changeView('cards')");
  assert(!document.querySelector('#cardList').textContent.includes('WWE'));
  document.querySelector('[data-franchise="marvel"]').click();
  for(const view of ['dashboard','sets','cards','collection','wanted']) {
    run(`changeView('${view}')`);
    assert.equal(document.querySelectorAll('#allSets .set-card, #cardList .card-row, #collectionList .card-row, #wantedList .card-row, #dashboardRecent .recent-card').length,0,view);
  }
  await run(`setStatus(${JSON.stringify(owned)},'wanted')`);
  run(`openCard(${JSON.stringify(owned)});Vault.open(${JSON.stringify(owned)})`);
  assert(!document.querySelector('#cardDialog').open);
  assert(!document.querySelector('#vaultDialog').open);
  assert.equal(storage.get('grailroster.collection.v1'),before);
  assert.equal(run('counts().owned'),0);
  document.querySelector('[data-franchise="marvel"]').click();
  assert.equal(run('state.franchise'),'marvel');
  const reloaded=await harness(storage);
  assert.equal(reloaded.run('state.franchise'),'marvel','Category preference survives reload');
  assert.equal(storage.get('grailroster.collection.v1'),before,'Reload preserves entries');
  run("changeCategory('wwe')");
  assert.equal(document.querySelectorAll('#collectionList .card-row').length,1);
  assert.equal(document.querySelectorAll('#wantedList .card-row').length,1);
  assert.equal(run('counts().owned'),1);
  assert.equal(storage.get('grailroster.collection.v1'),before);
  run('backupCollection()');
  assert.deepEqual(JSON.parse(await page.downloads[0].text()).collection,JSON.parse(before),'Backup contains every category');

  // Three future sets deliberately share a card number and display name.
  run(`for(const categoryId of ['star-wars','marvel']) {
    const set={...state.catalogue.sets[0],id:'fixture-'+categoryId,categoryId,shortName:categoryId,cardCount:1};
    state.catalogue.sets.push(set);
    const card={...state.catalogue.cards[0],id:'fixture-'+categoryId+'-1',setId:set.id,number:'1',name:'Same name'};
    state.catalogue.cards.push(card);
    state.collection[card.id]={status:'owned',copies:[{status:'owned',currency:'AUD',purchasePrice:categoryId==='marvel'?500:25,estimatedValue:null}]};
  }`);
  for(const [id,cost] of [['star-wars',25],['marvel',500]]) {
    run(`changeCategory('${id}');changeView('cards')`);
    const imported=id==='star-wars'?starWarsCount:0;
    assert.equal(run('categoryCatalogue().cardCount'),imported+1);
    assert.equal(run('counts().owned'),1);
    assert.equal(document.querySelectorAll('#allSets .set-card').length,imported?starWarsSets.length+1:1);
    assert(document.querySelectorAll('#cardList .card-row').length>=1);
    assert.equal(document.querySelectorAll('#collectionList .card-row').length,1);
    assert.equal(document.querySelectorAll('#wantedList .card-row').length,0);
    assert.match(document.querySelector('#vaultOverview').textContent,new RegExp('\\$'+cost.toFixed(2)));
    assert(!document.querySelector('#vaultOverview').textContent.includes(cost===25?'$500.00':'$25.00'));
    assert.equal(document.querySelector('#setFilter').options.length,imported?starWarsSets.length+2:2);
    assert.equal(document.querySelector('#categoryWorkspace').hidden,false);
  }
  run('backupCollection()');
  const completeBackup=JSON.parse(await page.downloads[1].text()).collection;
  for(const id of [owned,wanted,'fixture-star-wars-1','fixture-marvel-1']) assert(completeBackup[id],'Backup must include inactive categories');
  run("changeCategory('wwe')");
  assert.equal(run('counts().owned'),1,'Same card number never transfers ownership');
  assert.throws(()=>run("GrailCategories.validate({sets:[{id:'unknown',categoryId:'other'}],cards:[]})"),/unknown franchise/);
  assert.throws(()=>run("GrailCategories.validate({sets:[{id:'x',categoryId:'wwe'}],cards:[{id:'a',setId:'orphan'}]})"),/Invalid card/);
  assert.equal(JSON.stringify(loadCatalogue().cards),original,'All shipped identities remain unchanged');
  // The cloud catalogue inherits exact reviewed set membership from the bundle.
  const cloud=await harness();
  const source=loadCatalogue();
  cloud.context.cloudRows={
    catalogue_sets:source.sets.map(s=>({id:s.id,name:s.name,short_name:s.shortName,year:s.year,manufacturer:s.manufacturer,release_date:s.releaseDate,accent:s.accent,card_count:s.cardCount,subset_count:s.subsetCount})),
    catalogue_subsets:source.sets.flatMap(s=>s.subsets.map(sub=>({set_id:s.id,subset_code:sub.code,name:sub.name,category:sub.category,card_count:sub.count}))),
    catalogue_cards:source.cards.map(c=>({id:c.id,set_id:c.setId,checklist_order:c.order,card_number:c.number,display_name:c.name,category:c.category,subset_code:c.subsetCode})),
  };
  cloud.run('state.supabase={};fetchAllRows=async table=>cloudRows[table]');
  assert.equal((await cloud.run('loadCatalogue()')).sets[0].categoryId,'wwe');
  cloud.context.cloudRows.catalogue_sets.push({...cloud.context.cloudRows.catalogue_sets[0],id:'unreviewed-cloud-set'});
  assert.equal((await cloud.run('loadCatalogue()')).setCount,source.setCount,'Unclassified remote sets must fall back to the reviewed bundle');
  cloud.context.cloudRows.catalogue_sets.pop();
  cloud.context.cloudRows.catalogue_cards[0].id='unexpected-replacement';
  assert.equal((await cloud.run('loadCatalogue()')).cards[0].id,source.cards[0].id,'Missing bundled IDs must trigger fallback');
  assert.deepEqual(page.errors,[]);
  console.log('PASS: real-page DOM initialization, category switching/reload, every view, filters, future imports, Vault costs, card-number collisions, full backup and collection preservation.');
})().catch(error=>{console.error(error);process.exitCode=1;});
