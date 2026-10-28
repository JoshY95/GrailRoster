/* Device-only OCR pilot. No image uploads, account writes, payments or API secrets. */
window.GrailScanner = (() => {
  'use strict';
  const KEY = 'grailroster.scanner-test.v1';
  const ENGINE = 'Tesseract.js 6.0.1 / English / sparse text';
  const CDN = 'https://cdn.jsdelivr.net/npm/tesseract.js@6.0.1/dist/';
  const SRI = 'sha384-r1ru3tcf6FhnCFR4B7pIFG+BhFF9LlFtz/P1y4pblWn3AGs9y3lBx5SKLNf4+rED';
  const $ = id => document.getElementById(id);
  const esc = value => GrailUI.escape(value);
  let store, index, catalogue, toast, busy = false, generation = 0, worker = null;
  let loader = null, current = null, candidates = [], selected = null, activeRun = null;
  const photos = { front: null, back: null };
  const selectionGeneration = { front: 0, back: 0 };
  let storageAvailable = true;
  function message(text) { $('scanMessage').textContent = text; }
  function persist() {
    try { localStorage.setItem(KEY, JSON.stringify(store)); storageAvailable = true; }
    catch { storageAvailable = false; }
    $('scanStorageNote').hidden = storageAvailable;
    return storageAvailable;
  }
  function refreshUsage() {
    if (store.usage.month !== GrailScanMatch.period()) { store.usage = { month: GrailScanMatch.period(), used: 0 }; persist(); }
    $('scanAllowance').textContent = `${Math.max(0, 25 - store.usage.used)} / 25`;
    $('scanSavedCount').textContent = String(store.items.length);
    $('scanAttemptCount').textContent = String(store.attempts.length);
    $('scanStart').disabled = busy || !photos.front || store.usage.used >= 25;
    $('scanExport').disabled = !store.attempts.length && !store.items.length;
  }
  function controls(isBusy) {
    busy = isBusy;
    $('scannerView').setAttribute('aria-busy', String(isBusy));
    document.querySelectorAll('#scannerView [data-scan-lock]').forEach(el => { el.disabled = isBusy; });
    $('scanCancel').hidden = !isBusy;
    $('scanProgress').hidden = !isBusy;
    refreshUsage();
  }
  function recordAttempt(attempt) {
    store.attempts.push(attempt); store.attempts = store.attempts.slice(-200); persist(); refreshUsage();
  }
  function clearResult() {
    current = selected = null; candidates = [];
    $('scanResults').hidden = true; $('scanCandidates').innerHTML = '';
    $('scanConfirm').hidden = true; $('scanText').value = '';
    $('scanParallel').value = $('scanSerial').value = '';
    $('scanEditionCheck').checked = false;
  }
  async function choosePhoto(input, side) {
    const file = input.files?.[0]; input.value = '';
    if (!file || busy) return;
    const version = ++selectionGeneration[side];
    if (!/^image\/(jpeg|png|webp|avif)$/i.test(file.type)) { message('Choose a JPEG, PNG, WebP or AVIF photo. Convert HEIC photos to JPEG first.'); return; }
    if (file.size > 12 * 1024 * 1024) { message('That photo is too large. Choose a photo under 12 MB.'); return; }
    const url = URL.createObjectURL(file);
    try {
      const image = new Image(); image.src = url; await image.decode();
      if (image.naturalWidth * image.naturalHeight > 40000000) throw new Error('Choose a smaller photo (under 40 megapixels).');
      const scale = Math.min(2, 2000 / Math.max(image.naturalWidth, image.naturalHeight));
      const canvas = document.createElement('canvas');
      canvas.width = Math.max(1, Math.round(image.naturalWidth * scale)); canvas.height = Math.max(1, Math.round(image.naturalHeight * scale));
      canvas.getContext('2d').drawImage(image, 0, 0, canvas.width, canvas.height);
      if (selectionGeneration[side] !== version || busy) return;
      photos[side] = canvas; clearResult(); updatePhoto(side);
      message('Photo ready. Fill the frame, keep text upright and add the back for the best match.');
      refreshUsage();
    } catch (error) { message(error.message?.includes('megapixels') ? error.message : 'That image could not be opened. Try a JPEG or PNG photo.'); }
    finally { URL.revokeObjectURL(url); }
  }
  function updatePhoto(side) {
    const box = $(side === 'front' ? 'scanFrontPreview' : 'scanBackPreview');
    box.replaceChildren();
    if (photos[side]) {
      const thumb = document.createElement('canvas'); const source = photos[side];
      const scale = Math.min(1, 360 / Math.max(source.width, source.height));
      thumb.width = Math.round(source.width * scale); thumb.height = Math.round(source.height * scale);
      thumb.getContext('2d').drawImage(source, 0, 0, thumb.width, thumb.height);
      thumb.setAttribute('role', 'img'); thumb.setAttribute('aria-label', `${side} card photo`); box.append(thumb);
    } else box.textContent = side === 'front' ? 'Front photo' : 'Back photo (optional)';
    document.querySelectorAll(`[data-scan-side="${side}"]`).forEach(button => { button.hidden = !photos[side]; });
  }
  function rotate(side) {
    if (busy || !photos[side]) return;
    const source = photos[side], rotated = document.createElement('canvas');
    rotated.width = source.height; rotated.height = source.width;
    const ctx = rotated.getContext('2d'); ctx.translate(rotated.width, 0); ctx.rotate(Math.PI / 2); ctx.drawImage(source, 0, 0);
    photos[side] = rotated; clearResult(); updatePhoto(side);
  }
  function loadEngine() {
    if (window.Tesseract) return Promise.resolve(window.Tesseract);
    if (loader) return loader;
    loader = new Promise((resolve, reject) => {
      const script = document.createElement('script'); script.src = `${CDN}tesseract.min.js`;
      script.integrity = SRI; script.crossOrigin = 'anonymous';
      const fail = () => { clearTimeout(timer); script.remove(); loader = null; reject(new Error('The scanner could not download. Check your connection and try again.')); };
      const timer = setTimeout(fail, 25000);
      script.onload = () => { clearTimeout(timer); window.Tesseract ? resolve(window.Tesseract) : fail(); };
      script.onerror = fail; document.head.append(script);
    });
    return loader;
  }
  function stopWorker() { const old = worker; worker = null; if (old) Promise.resolve(old.terminate()).catch(() => {}); }
  function showCandidates() {
    selected = null; $('scanConfirm').hidden = true;
    candidates = GrailScanMatch.match(index, $('scanText').value, $('scanSet').value);
    $('scanResults').hidden = false;
    $('scanResultSummary').textContent = candidates.length ? `${candidates.length} possible matches. Check the set, year and card number.` : 'No supported match found. Try the back photo, select a set or correct the detected text.';
    $('scanCandidates').innerHTML = candidates.map((match, i) => `<button type="button" class="scan-candidate" data-scan-candidate="${i}"><strong>${esc(match.card.name)}</strong><span>${esc(match.set.name)}</span><span>#${esc(match.card.number)} · ${esc(match.card.subset)}</span><small>${esc(match.evidence.join(' · '))}</small></button>`).join('');
    if (current && current.status !== 'confirmed') {
      current.candidateIds = candidates.map(candidate => candidate.card.id);
      current.reviewedText = $('scanText').value.slice(0, 10000);
      current.setFilter = $('scanSet').value; persist();
    }
    $('scanReject').hidden = !candidates.length || !current || current.status === 'confirmed';
  }
  async function scan() {
    refreshUsage();
    if (busy || !photos.front) return;
    if (store.usage.used >= 25) { message('Your simulated allowance is used. Export your results, then reset test data to continue testing. No payment is required.'); return; }
    clearResult(); controls(true);
    const job = ++generation, start = performance.now();
    const attempt = { id: crypto.randomUUID(), at: new Date().toISOString(), engine: ENGINE, status: 'reading',
      photos: photos.back ? 2 : 1, setFilter: $('scanSet').value, apiCostUSD: 0, source: 'photo-ocr' };
    const cancellation = new Promise((_, reject) => { activeRun = { job, attempt, start, cancel: () => reject(new Error('Scan cancelled.')) }; });
    let timer;
    try {
      const work = async () => {
        message('Loading on-device recognition. The first scan downloads the English recognition files.');
        $('scanProgress').removeAttribute('value');
        const engine = await loadEngine();
        if (job !== generation) throw new Error('Scan cancelled.');
        const created = await engine.createWorker('eng', 1, {
          workerPath: `${CDN}worker.min.js`,
          corePath: 'https://cdn.jsdelivr.net/npm/tesseract.js-core@6.0.0',
          langPath: 'https://tessdata.projectnaptha.com/4.0.0',
          logger: update => {
            if (job !== generation) return;
            if (update.status === 'recognizing text') {
              $('scanProgress').value = update.progress || 0;
              message(`Reading card text… ${Math.round((update.progress || 0) * 100)}%`);
            }
          }
        });
        if (job !== generation) { await created.terminate(); throw new Error('Scan cancelled.'); }
        worker = created;
        await worker.setParameters({ tessedit_pageseg_mode: '11' });
        const outputs = [];
        for (const side of ['front', 'back']) {
          if (!photos[side]) continue;
          const output = await created.recognize(photos[side]);
          if (job !== generation) throw new Error('Scan cancelled.');
          outputs.push(output.data.text || '');
        }
        return outputs.join('\n\n').slice(0, 10000);
      };
      const text = await Promise.race([work(), cancellation, new Promise((_, reject) => { timer = setTimeout(() => reject(new Error('Recognition took too long. Try a closer, upright photo with less glare.')), 90000); })]);
      if (job !== generation) return;
      attempt.elapsedMs = Math.round(performance.now() - start); attempt.ocrText = text;
      attempt.status = GrailScanMatch.match(index, text, $('scanSet').value).length ? 'review' : 'no-match';
      current = attempt; recordAttempt(attempt); $('scanText').value = text;
      $('scanSerial').value = GrailScanMatch.details(text).serial;
      $('scanTiming').textContent = `${(attempt.elapsedMs / 1000).toFixed(1)} seconds · no paid API calls`;
      showCandidates();
      message(attempt.status === 'review' ? 'Choose the matching card below. No scan credit is used until you save a test card.' : 'No match yet. No credit used. Add a clearer back photo or review the detected text.');
    } catch (error) {
      if (job !== generation) return;
      generation++;
      attempt.status = 'error'; attempt.elapsedMs = Math.round(performance.now() - start);
      attempt.error = 'Recognition did not finish'; recordAttempt(attempt);
      message(error.message || 'Recognition failed. Check your connection and try a clearer photo. No credit used.');
    } finally {
      clearTimeout(timer);
      if (activeRun?.job === job) activeRun = null;
      // A cancelled job has already cleaned up; do not terminate a newer scan.
      if (job === generation || !busy) { stopWorker(); controls(false); }
      else if (attempt.status === 'error') { stopWorker(); controls(false); }
    }
  }
  function pick(i) {
    if (!current || current.status === 'confirmed' || !candidates[i]) return;
    selected = candidates[i];
    $('scanEditionCheck').checked = false;
    $('scanSelected').textContent = `${selected.card.name} · ${selected.set.name} · #${selected.card.number} · ${selected.card.subset}`;
    $('scanConfirm').hidden = false; $('scanConfirmButton').disabled = false;
    document.querySelectorAll('[data-scan-candidate]').forEach((el, n) => el.setAttribute('aria-pressed', String(n === i)));
    $('scanParallel').focus();
  }
  function saveTest(event) {
    event.preventDefault(); refreshUsage();
    if (!current || !selected || !$('scanEditionCheck').checked || current.status === 'confirmed' || store.usage.used >= 25) return;
    if (store.items.length >= 500) { message('Test collection is full. Export your results, then reset test data.'); return; }
    const item = { id: crypto.randomUUID(), attemptId: current.id, at: new Date().toISOString(), cardId: selected.card.id,
      name: selected.card.name, set: selected.set.name, number: selected.card.number, subset: selected.card.subset,
      parallel: $('scanParallel').value.trim().slice(0, 120), serial: $('scanSerial').value.trim().slice(0, 40), editionConfirmedByUser: true };
    store.items.push(item); store.usage.used++;
    Object.assign(current, { status: 'confirmed', confirmedCardId: item.cardId, selectedRank: candidates.findIndex(candidate => candidate.card.id === item.cardId) + 1, reviewedText: $('scanText').value.slice(0, 10000), setFilter: $('scanSet').value,
      correctedText: $('scanText').value !== current.ocrText });
    const saved = persist(); refreshUsage(); renderItems();
    $('scanConfirm').hidden = true; $('scanReject').hidden = true;
    $('scanCandidates').innerHTML = '';
    $('scanResultSummary').textContent = 'Saved to the scanner test collection. Your Vault has not changed.';
    message(saved ? 'Test card saved. Take another photo to continue.' : 'Test card added for this session only. Download results before leaving.');
    toast('Added to test collection');
  }
  function renderItems() {
    $('scanTestItems').innerHTML = store.items.slice(-20).reverse().map(item => `<li><strong>${esc(item.name)}</strong><span>${esc(item.set)} · #${esc(item.number)}</span><small>${esc([item.parallel || 'Parallel unspecified', item.serial].filter(Boolean).join(' · '))}</small></li>`).join('');
    $('scanTestEmpty').hidden = !!store.items.length;
    $('scanSavedNote').textContent = store.items.length > 20 ? 'Showing the latest 20 test cards. Download results for the full test collection.' : 'Test cards stay on this device, separate from your Vault.';
  }
  function download() {
    refreshUsage();
    const data = { exportedAt: new Date().toISOString(), prototype: 'device-ocr-v1', engine: ENGINE,
      costs: 'No paid recognition API used. Excludes development, hosting, bandwidth and device costs.', ...store };
    const link = document.createElement('a'); const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
    link.href = url; link.download = `grailroster-scanner-tests-${new Date().toISOString().slice(0, 10)}.json`;
    link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function reset() {
    if (busy || !window.confirm('Delete scanner test results and reset the simulated allowance? Your real collection will not change.')) return;
    store = GrailScanMatch.loadStore(null); clearResult(); persist(); refreshUsage(); renderItems();
    for (const side of ['front', 'back']) { selectionGeneration[side]++; photos[side] = null; updatePhoto(side); }
    message('Scanner test data reset. Your Vault is unchanged.');
  }
  function init(options) {
    catalogue = options.catalogue; toast = options.showToast; index = GrailScanMatch.buildIndex(catalogue);
    let raw = null;
    try { raw = localStorage.getItem(KEY); } catch { storageAvailable = false; }
    store = GrailScanMatch.loadStore(raw);
    $('scanStorageNote').hidden = storageAvailable;
    $('scanSet').innerHTML = '<option value="all">All supported WWE sets</option>' + catalogue.sets.filter(set => set.categoryId === 'wwe').map(set => `<option value="${esc(set.id)}">${esc(set.name)}</option>`).join('');
    $('scanCoverage').textContent = `${index.length.toLocaleString()} WWE checklist cards across ${catalogue.sets.filter(set => set.categoryId === 'wwe').length} sets. Other categories are outside this pilot.`;
    for (const [id, side] of [['scanCamera', 'front'], ['scanFrontInput', 'front'], ['scanBackInput', 'back']]) $(id).addEventListener('change', event => choosePhoto(event.target, side));
    $('scanStart').addEventListener('click', scan);
    $('scanCancel').addEventListener('click', () => {
      if (activeRun) {
        const run = activeRun;
        Object.assign(run.attempt, { status: 'cancelled', elapsedMs: Math.round(performance.now() - run.start) });
        recordAttempt(run.attempt); run.cancel();
      }
      generation++; stopWorker(); controls(false); message('Scan cancelled. No credit used.');
    });
    $('scanSet').addEventListener('change', () => { if (current && current.status !== 'confirmed') showCandidates(); });
    $('scanRematch').addEventListener('click', () => {
      if (!current || current.status === 'confirmed') return;
      current.correctedText = $('scanText').value !== current.ocrText; showCandidates();
    });
    $('scanReject').addEventListener('click', () => {
      if (current && current.status !== 'confirmed') { current.status = 'rejected'; current.reviewedText = $('scanText').value.slice(0, 10000); persist(); }
      selected = null; $('scanConfirm').hidden = true; message('Marked as incorrect. No credit used. Try the back photo or another set.');
    });
    $('scanCandidates').addEventListener('click', event => { const el = event.target.closest('[data-scan-candidate]'); if (el) pick(Number(el.dataset.scanCandidate)); });
    $('scanConfirm').addEventListener('submit', saveTest);
    $('scanExport').addEventListener('click', download); $('scanReset').addEventListener('click', reset);
    $('scannerView').addEventListener('click', event => {
      const el = event.target.closest('[data-scan-action]'); if (!el || busy) return;
      const side = el.dataset.scanSide;
      if (el.dataset.scanAction === 'rotate') rotate(side);
      if (el.dataset.scanAction === 'remove') { selectionGeneration[side]++; photos[side] = null; clearResult(); updatePhoto(side); refreshUsage(); }
    });
    refreshUsage(); renderItems();
  }
  return { init };
})();
