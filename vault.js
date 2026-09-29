/* Collector Vault: one identified record per physical copy.
 * Stored with its parent checklist entry, so copies and quantity sync atomically.
 * No catalogue image or automated market-price permissions are implied.
 */
const Vault = (() => {
  const textFields = { parallel:120, serialNumber:40, gradingCompany:40, grade:40, certification:100, condition:80, seller:160, location:160, notes:2000 };
  const moneyFields = ['purchasePrice','estimatedValue','salePrice','saleFees'];
  const active = entry => (entry?.copies || []).filter(copy => copy.status === 'owned');
  const managed = entry => Array.isArray(entry?.copies);
  const money = (amount, currency) => amount == null ? 'Not recorded' : new Intl.NumberFormat('en-AU', {style:'currency', currency}).format(amount);
  let busy = false;
  let generation = 0;

  function validate(copy) {
    if (!copy || typeof copy !== 'object' || !/^[\w-]{1,80}$/.test(copy.id || '')) throw Error('Invalid copy identifier.');
    if (!['owned','sold','traded'].includes(copy.status)) throw Error('Choose a valid copy status.');
    if (!/^[A-Z]{3}$/.test(copy.currency || '')) throw Error('Enter a three-letter currency code.');
    try { new Intl.NumberFormat('en', {style:'currency', currency:copy.currency}); } catch { throw Error('Invalid currency.'); }
    for (const [field, max] of Object.entries(textFields)) if (typeof copy[field] !== 'string' || copy[field].length > max) throw Error(`Invalid ${field}.`);
    for (const field of moneyFields) if (copy[field] !== null && (typeof copy[field] !== 'number' || !Number.isFinite(copy[field]) || copy[field] < 0 || copy[field] > 9999999999.99)) throw Error('Amounts must be between 0 and 9,999,999,999.99.');
    for (const field of ['acquiredAt','soldAt','valuedAt']) {
      const value = copy[field];
      if (value && (!/^\d{4}-\d{2}-\d{2}$/.test(value) || !Number.isFinite(Date.parse(value)) || new Date(value).toISOString().slice(0,10) !== value)) throw Error('Enter valid dates.');
    }
    if (!['raw','graded'].includes(copy.format)) throw Error('Choose raw or graded.');
    if (copy.format === 'graded' && (!copy.gradingCompany.trim() || !copy.grade.trim())) throw Error('Graded copies need a grading company and grade.');
    if (copy.status === 'sold' && (copy.salePrice === null || !copy.soldAt)) throw Error('Sold copies need a sale price and sale date.');
    if (copy.soldAt && copy.acquiredAt && copy.soldAt < copy.acquiredAt) throw Error('Sale date cannot be before purchase date.');
    for (const side of ['front','back']) if (copy[side] && !/^[a-f0-9-]{36}\/[\w-]+\.jpg$/.test(copy[side])) throw Error('Invalid private photo path.');
    return copy;
  }

  function blank(entry = {}) {
    return {id:crypto.randomUUID(), status:'owned', format:entry.condition === 'Graded' ? 'graded' : 'raw',
      ...Object.fromEntries(Object.keys(textFields).map(key => [key,''])), condition:entry.condition || '',
      purchasePrice:entry.purchasePrice ?? null, estimatedValue:null, salePrice:null, saleFees:null,
      currency:entry.purchaseCurrency || 'AUD', acquiredAt:entry.acquiredAt || '', soldAt:'', valuedAt:'',
      notes:entry.notes || '', front:null, back:null, updatedAt:new Date().toISOString()};
  }

  // Legacy quantities never invent separate purchase prices or repeat an unknown total.
  function legacyCopies(entry) {
    if (managed(entry)) return structuredClone(entry.copies);
    if (entry?.status !== 'owned') return [];
    return Array.from({length:Math.min(999, Math.max(1, Number(entry.quantity) || 1))}, (_, i) => blank(i === 0 ? entry : {purchaseCurrency:entry.purchaseCurrency}));
  }

  function summary(entry, copies) {
    const owned = active({copies});
    return {...entry, copies, status:owned.length ? 'owned' : entry?.status === 'wanted' ? 'wanted' : 'owned',
      quantity:Math.max(1, owned.length), updatedAt:new Date().toISOString()};
  }

  function effectiveStatus(entry) {
    if (!managed(entry)) return entry?.status || 'missing';
    return active(entry).length ? 'owned' : entry.status === 'wanted' ? 'wanted' : 'missing';
  }

  function mount(cardId) {
    const form = document.querySelector('#collectionDetailsForm');
    if (!form) return;
    const entry = entryFor(cardId);
    if (managed(entry)) form.hidden = true;
    form.insertAdjacentHTML('afterend', `<section class="vault-entry"><p class="eyebrow">COLLECTOR VAULT</p><h3>Your physical copies</h3><p class="muted">Track individual serials, grades, costs and private photos.</p><button type="button" class="secondary-button" data-vault-card="${escapeHtml(cardId)}">${managed(entry) ? `Manage ${active(entry).length} owned copies` : 'Set up physical copies'}</button></section>`);
  }

  function open(cardId, editId = null) {
    if (document.querySelector('#vaultForm')?.dataset.dirty === 'true' && !confirm('Discard your unsaved copy changes?')) return;
    const card = state.catalogue.cards.find(c => c.id === cardId);
    if (!card) return;
    const entry = entryFor(cardId) || {};
    const dialog = document.querySelector('#vaultDialog');
    const copies = managed(entry) ? entry.copies : [];
    const selected = copies.find(c => c.id === editId);
    dialog.dataset.card = cardId;
    dialog.dataset.edit = editId || '';
    dialog.dataset.version = entry.updatedAt || '';
    document.querySelector('#vaultContent').innerHTML = `<p class="eyebrow">COLLECTOR VAULT · #${escapeHtml(card.number)}</p><h2>${escapeHtml(card.name)}</h2><p class="muted">${escapeHtml(state.catalogue.sets.find(s => s.id === card.setId)?.name || '')}</p>
      <p class="vault-notice">${state.user ? 'Private to your account. Photos are never added to the public catalogue.' : 'Guest records stay on this device. Sign in to sync and upload private photos.'}</p>
      ${!managed(entry) ? `<p class="vault-notice">${entry.status === 'owned' ? `Your ${entry.quantity || 1} existing copies will be preserved. Existing price, date and notes are kept on the first copy only; review them before recording costs for other copies.` : 'Add your first physical copy. Your wanted status is preserved until you save.'}</p><button type="button" class="primary-button" id="vaultSetup">${entry.status === 'owned' ? 'Create records for existing copies' : 'Add first copy'}</button>` : `<div class="vault-copy-list">${copies.length ? copies.map((copy,i) => `<button type="button" class="vault-copy ${copy.id === editId ? 'selected' : ''}" data-vault-edit="${escapeHtml(copy.id)}"><strong>Copy ${i+1} · ${escapeHtml(copy.parallel || 'Parallel unspecified')}</strong><span>${escapeHtml([copy.serialNumber,copy.format === 'graded' ? `${copy.gradingCompany} ${copy.grade}` : copy.condition || 'Raw',copy.status].filter(Boolean).join(' · '))}</span><small>${copy.purchasePrice == null ? 'Cost not recorded' : escapeHtml(money(copy.purchasePrice,copy.currency))}</small></button>`).join('') : '<p>No copy records yet.</p>'}</div><button type="button" class="secondary-button" id="vaultAdd" ${copies.length >= 999 ? 'disabled' : ''}>+ Add another copy</button>`}
      ${managed(entry) && !active(entry).length ? `<button type="button" class="secondary-button" id="vaultWanted">${entry.status === 'wanted' ? 'Remove from wanted list' : 'Add to wanted list'}</button>` : ''}
      ${selected ? editor(selected) : ''}<p id="vaultMessage" role="status" aria-live="polite"></p>`;
    if (!dialog.open) dialog.showModal();
    if (selected) renderPhotos(selected);
  }

  function editor(copy) {
    const input = (name,label,type='text',extra='') => `<label>${label}<input name="${name}" type="${type}" value="${escapeHtml(copy[name] ?? '')}" ${textFields[name] ? `maxlength="${textFields[name]}"` : ''} ${extra}></label>`;
    const select = (name,label,choices) => `<label>${label}<select name="${name}">${choices.map(([v,l]) => `<option value="${v}" ${copy[name] === v ? 'selected' : ''}>${l}</option>`).join('')}</select></label>`;
    const pnl = copy.purchasePrice == null ? null : copy.status === 'sold' && copy.salePrice != null ? copy.salePrice - (copy.saleFees || 0) - copy.purchasePrice : copy.status === 'owned' && copy.estimatedValue != null ? copy.estimatedValue - copy.purchasePrice : null;
    return `<form id="vaultForm"><h3>Copy details</h3><div class="form-grid">${select('status','Status',[['owned','Owned'],['sold','Sold'],['traded','Traded away']])}${input('parallel','Parallel / variation')}${input('serialNumber','Printed serial (e.g. 07/25)')}${select('format','Format',[['raw','Raw'],['graded','Graded']])}${input('condition','Condition')}${input('gradingCompany','Grading company')}${input('grade','Grade / label')}${input('certification','Certification number')}</div>
      <h3>Purchase and storage</h3><div class="form-grid">${input('purchasePrice','Purchase cost','number','min="0" max="9999999999.99" step="0.01"')}${select('currency','Currency',[['AUD','AUD'],['USD','USD'],['GBP','GBP'],['EUR','EUR'],['CAD','CAD'],['NZD','NZD'],['JPY','JPY'],...(!['AUD','USD','GBP','EUR','CAD','NZD','JPY'].includes(copy.currency)?[[escapeHtml(copy.currency),escapeHtml(copy.currency)]]:[])])}${input('acquiredAt','Purchase date','date')}${input('seller','Seller / source')}${input('location','Storage location')}</div>
      <h3>Your valuation</h3><p class="muted">Manual estimates only—not verified market prices. All amounts on this copy use the currency above.</p><div class="form-grid">${input('estimatedValue','Estimated value','number','min="0" max="9999999999.99" step="0.01"')}${input('valuedAt','Valuation date','date')}</div>
      <details ${copy.status === 'sold' ? 'open' : ''}><summary>Sale details</summary><div class="form-grid">${input('salePrice','Sale price','number','min="0" max="9999999999.99" step="0.01"')}${input('saleFees','Selling fees / costs','number','min="0" max="9999999999.99" step="0.01"')}${input('soldAt','Sale date','date')}</div></details>
      ${pnl !== null ? `<p class="vault-notice">${copy.status === 'sold' ? 'Realised gain/loss (recorded costs only)' : 'Unrealised gain/loss (your estimate)'}: <strong>${escapeHtml(money(pnl,copy.currency))}</strong></p>` : ''}
      <label class="notes-field">Notes<textarea name="notes" maxlength="2000" rows="3">${escapeHtml(copy.notes)}</textarea></label>
      <h3>Private photographs</h3><p class="muted">JPEG, PNG or WebP, up to 10 MB. Saved photos are resized and stripped of metadata. JSON backups include photo references, not image files.</p><div class="vault-photos">${['front','back'].map(side=>`<div><div id="vaultPhoto-${side}" class="vault-photo">${side === 'front' ? 'Front' : 'Back'}</div><label class="notes-field">${side} photo<input type="file" name="${side}File" accept="image/jpeg,image/png,image/webp" ${state.user ? '' : 'disabled'}></label>${copy[side] ? `<label><input type="checkbox" name="${side}Remove"> Remove photo</label>` : ''}</div>`).join('')}</div>
      <div class="vault-actions"><button class="primary-button" type="submit">Save copy</button><button class="secondary-button" type="button" id="vaultDelete">Delete this copy</button></div></form>`;
  }

  async function renderPhotos(copy) {
    const token = ++generation;
    const userId = state.user?.id;
    if (!userId) return;
    for (const side of ['front','back']) {
      if (!copy[side]?.startsWith(`${userId}/`)) continue;
      const {data,error} = await state.supabase.storage.from('vault-photos').createSignedUrl(copy[side],120);
      if (token !== generation || userId !== state.user?.id) return;
      const target = document.querySelector(`#vaultPhoto-${side}`);
      if (target) target.innerHTML = error ? '<span>Photo unavailable. Try reopening.</span>' : `<img src="${escapeHtml(data.signedUrl)}" alt="Private ${side} of your card">`;
    }
  }

  async function photo(file, userId) {
    if (!['image/jpeg','image/png','image/webp'].includes(file.type) || file.size > 10*1024*1024) throw Error('Use JPEG, PNG or WebP images smaller than 10 MB.');
    const bitmap = await createImageBitmap(file);
    try {
      if (bitmap.width * bitmap.height > 50000000) throw Error('Please choose a smaller photo (under 50 megapixels).');
      const scale = Math.min(1,1600/Math.max(bitmap.width,bitmap.height));
      const canvas = document.createElement('canvas'); canvas.width = Math.max(1,Math.round(bitmap.width*scale)); canvas.height = Math.max(1,Math.round(bitmap.height*scale));
      const ctx = canvas.getContext('2d'); ctx.fillStyle = '#ffffff'; ctx.fillRect(0,0,canvas.width,canvas.height); ctx.drawImage(bitmap,0,0,canvas.width,canvas.height);
      const blob = await new Promise(resolve => canvas.toBlob(resolve,'image/jpeg',0.85));
      if (!blob) throw Error('Could not process that photo.');
      const path = `${userId}/${crypto.randomUUID()}.jpg`;
      const {error} = await state.supabase.storage.from('vault-photos').upload(path,blob,{contentType:'image/jpeg',upsert:false});
      if (error) throw error;
      return path;
    } finally { bitmap.close(); }
  }

  async function persist(cardId, copies, wanted = null) {
    if (copies.length > 999 || new Set(copies.map(c=>c.id)).size !== copies.length) throw Error('Invalid number of copies.');
    copies.forEach(validate);
    const previous = entryFor(cardId) || {};
    const next = summary(wanted === null ? previous : {...previous,status:wanted ? 'wanted' : 'owned'},copies);
    const userId = state.user?.id;
    if (userId) {
      // Cloud-first edits: failed writes never masquerade as a saved copy.
      const row = {...entryToRemote(cardId,next), vault_copies:copies};
      let query = state.supabase.from('collection_items').update(row).eq('user_id',userId).eq('card_id',cardId);
      if (previous.updatedAt) query = query.eq('updated_at',previous.updatedAt);
      const {data,error} = await query.select('card_id');
      if (error) throw error;
      if (!data?.length) {
        if (previous.updatedAt) throw Error('This card changed elsewhere, or has not synced yet. Close this window, sync your collection and reopen it before saving.');
        const result = await state.supabase.from('collection_items').insert(row);
        if (result.error) throw result.error;
      }
      if (state.user?.id !== userId) throw Error('Your account changed. Reopen the Vault.');
    }
    // Preserve prior state if guest storage is full.
    try { localStorage.setItem(collectionStorageKey(),JSON.stringify({...state.collection,[cardId]:next})); }
    catch(error) { if(!userId)throw error; showToast('Saved to your account; device backup storage is full.'); }
    state.collection[cardId] = next;
    const form=document.querySelector('#vaultForm');if(form)form.dataset.dirty='false';
    renderAll();
    return next;
  }

  async function act(fn) {
    if (busy) return;
    busy = true;
    const dialog = document.querySelector('#vaultDialog');
    dialog.querySelectorAll('button').forEach(b=>b.disabled=true);
    try { await fn(); }
    catch (error) { const target = document.querySelector('#vaultMessage'); if (target) target.textContent = error.message || 'Unable to save. Your previous records are unchanged.'; }
    finally { busy=false; dialog.querySelectorAll('button').forEach(b=>b.disabled=false); }
  }

  function overview() {
    const target = document.querySelector('#vaultOverview');
    if (!target || !state.catalogue) return;
    const entries = Object.entries(state.collection).filter(([,e])=>managed(e));
    const copies = entries.flatMap(([,e])=>e.copies);
    const totals = {};
    for (const copy of copies.filter(c=>c.status==='owned')) {
      const group = totals[copy.currency] ||= {cost:0,value:0,valued:0};
      group.cost += copy.purchasePrice || 0; group.value += copy.estimatedValue || 0; group.valued += copy.estimatedValue !== null ? 1 : 0;
    }
    target.innerHTML = `<div class="vault-entry"><p class="eyebrow">COLLECTOR VAULT</p><h3>${copies.filter(c=>c.status==='owned').length} detailed copies · ${copies.filter(c=>c.status!=='owned').length} archived</h3><p class="muted">Open any card to manage its individual copies. Checklist completion counts unique card designs, not duplicates.</p>${Object.entries(totals).map(([currency,t])=>`<p>${escapeHtml(currency)} · Recorded cost ${escapeHtml(money(t.cost,currency))} · Manual estimates ${escapeHtml(money(t.value,currency))} (${t.valued} valued copies)</p>`).join('')}${entries.some(([,e])=>e.copies.some(c=>c.status!=='owned')) ? `<details><summary>Sold / traded history</summary>${entries.filter(([,e])=>e.copies.some(c=>c.status!=='owned')).map(([id])=>`<button class="secondary-button" data-vault-card="${escapeHtml(id)}">${escapeHtml(state.catalogue.cards.find(c=>c.id===id)?.name || id)}</button>`).join('')}</details>` : ''}</div>`;
  }

  function reset() { generation++; document.querySelector('#vaultDialog')?.close(); document.querySelector('#vaultContent')?.replaceChildren(); }

  async function removeAccountPhotos() {
    const userId=state.user?.id;
    if(!userId)return;
    while(true) {
      const {data,error}=await state.supabase.storage.from('vault-photos').list(userId,{limit:100});
      if(error)throw error;
      if(!data?.length)return;
      const result=await state.supabase.storage.from('vault-photos').remove(data.map(file=>`${userId}/${file.name}`));
      if(result.error)throw result.error;
    }
  }

  function init() {
    document.body.insertAdjacentHTML('beforeend','<dialog id="vaultDialog" class="vault-dialog"><button type="button" class="dialog-close" id="vaultClose" aria-label="Close Collector Vault">×</button><div id="vaultContent"></div></dialog>');
    const dialog = document.querySelector('#vaultDialog');
    const canClose=()=>!busy && (document.querySelector('#vaultForm')?.dataset.dirty!=='true' || confirm('Discard your unsaved copy changes?'));
    dialog.addEventListener('cancel',e=>{if(!canClose())e.preventDefault();else generation++;});
    dialog.addEventListener('input',()=>{const form=document.querySelector('#vaultForm');if(form)form.dataset.dirty='true';});
    dialog.addEventListener('change',()=>{const form=document.querySelector('#vaultForm');if(form)form.dataset.dirty='true';});
    document.addEventListener('click',event=>{
      const launch = event.target.closest('[data-vault-card]');
      if (launch) {event.stopImmediatePropagation(); open(launch.dataset.vaultCard);return;}
      if (!dialog.contains(event.target)) return;
      const cardId = dialog.dataset.card;
      const edit = event.target.closest('[data-vault-edit]');
      if (edit && !busy) { open(cardId,edit.dataset.vaultEdit); return; }
      if (event.target.id === 'vaultClose' && canClose()) {dialog.close();generation++;document.querySelector('#vaultContent').replaceChildren();return;}
      if (event.target.id === 'vaultWanted') act(async()=>{
        const entry=entryFor(cardId);
        if((entry.updatedAt || '')!==dialog.dataset.version)throw Error('This card changed. Close and reopen the Vault.');
        await persist(cardId,entry.copies,entry.status!=='wanted');open(cardId);
      });
      if (['vaultSetup','vaultAdd'].includes(event.target.id)) act(async()=>{
        const existing = entryFor(cardId) || {};
        if ((existing.updatedAt || '') !== dialog.dataset.version) throw Error('This card changed while the Vault was open. Close and reopen it to load the latest version.');
        const copies = legacyCopies(existing);
        if (event.target.id === 'vaultAdd' || !copies.length) copies.push(blank());
        // Historical "Graded" labels lack company/grade; keep them raw until reviewed.
        copies.forEach(c=>{if(c.format==='graded' && !c.gradingCompany)c.format='raw';});
        await persist(cardId,copies);open(cardId,copies.at(-1).id);
      });
      if (event.target.id === 'vaultDelete') act(async()=>{
        if (!confirm('Delete this physical copy and its private photos? This does not delete the card from the catalogue.')) return;
        const entry = entryFor(cardId); const copy = entry.copies.find(c=>c.id===dialog.dataset.edit);
        if ((entry.updatedAt || '') !== dialog.dataset.version) throw Error('This card changed while the Vault was open. Close and reopen it before deleting.');
        await persist(cardId,entry.copies.filter(c=>c.id!==copy.id));
        if(state.user) { const paths=[copy.front,copy.back].filter(p=>p?.startsWith(`${state.user.id}/`)); if(paths.length) { const {error}=await state.supabase.storage.from('vault-photos').remove(paths); if(error) showToast('Copy deleted; photo cleanup needs a retry.'); } }
        open(cardId);
      });
    },true);
    document.addEventListener('submit',event=>{
      if(event.target.id!=='vaultForm')return;
      event.preventDefault();
      act(async()=>{
        const cardId=dialog.dataset.card; const userId=state.user?.id; const entry=entryFor(cardId);
        if ((entry.updatedAt || '') !== dialog.dataset.version) throw Error('This card changed while you were editing. Your changes have not been saved. Close and reopen it to load the latest version.');
        const old=entry.copies.find(c=>c.id===dialog.dataset.edit); const values=new FormData(event.target);
        const copy={...old,updatedAt:new Date().toISOString()};
        for(const key of [...Object.keys(textFields),'status','format','currency','acquiredAt','soldAt','valuedAt']) copy[key]=String(values.get(key)||'').trim();
        for(const key of moneyFields) copy[key]=values.get(key)===''?null:Number(values.get(key));
        validate(copy);
        const uploads=[]; const obsolete=[];
        try {
          for(const side of ['front','back']) {
            const file=values.get(`${side}File`);
            if(file?.size) { if(!userId)throw Error('Sign in before uploading photos.');copy[side]=await photo(file,userId);uploads.push(copy[side]); }
            else if(values.has(`${side}Remove`))copy[side]=null;
            if(old[side] && old[side]!==copy[side])obsolete.push(old[side]);
          }
          if(state.user?.id!==userId)throw Error('Your account changed. Please reopen the Vault.');
          await persist(cardId,entry.copies.map(c=>c.id===copy.id?copy:c));
        } catch(error) { if(uploads.length)await state.supabase.storage.from('vault-photos').remove(uploads);throw error; }
        if(obsolete.length && userId)await state.supabase.storage.from('vault-photos').remove(obsolete.filter(p=>p.startsWith(`${userId}/`)));
        open(cardId,copy.id);document.querySelector('#vaultMessage').textContent='Copy saved.';
      });
    });
  }
  return {active,managed,validate,legacyCopies,summary,effectiveStatus,mount,open,overview,reset,init,removeAccountPhotos};
})();
