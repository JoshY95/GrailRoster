const assert = require('node:assert/strict');
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true, ...(process.env.CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.CHROMIUM_EXECUTABLE_PATH, args:['--no-sandbox']} : {}) });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, acceptDownloads: true });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    // Verify the bundled catalogue fallback without relying on a live Supabase project.
    await page.route('**/rest/v1/**', route => route.abort());
    await page.goto(process.env.GRAILROSTER_BASE_URL || 'http://127.0.0.1:8765/');
    assert.equal(await page.title(), 'GrailRoster');
    assert.equal(await page.locator('.brand strong').innerText(), 'GrailRoster');
    await page.locator('#allSets .set-card').first().waitFor({ state: 'attached' });
    assert.equal(await page.locator('#allSets .set-card').count(), 17);
    assert.equal(await page.locator('#heroProgress strong').first().innerText(), '0%');
    assert.equal(await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--accent').trim()), '#69e9bf');
    await page.locator('.sidebar [data-view="sets"]').click();
    await page.locator('#setSearch').fill('Cactus Jack');
    assert.equal(await page.locator('#allSets .set-card').count(), 2);
    await page.locator('#setSearch').fill('');
    assert.equal(await page.locator('#allSets .set-card').count(), 17);
    await page.locator('.sidebar [data-view="dashboard"]').click();

    await page.locator('#dashboardSets .set-card').first().click();
    assert.equal(await page.locator('#cardsView').isVisible(), true);
    assert.notEqual(await page.locator('#setFilter').inputValue(), 'all');
    await page.locator('#cardList .card-row').first().locator('.state-button.owned').click();
    assert.equal(await page.locator('#dashboardRecent .recent-card').count(), 1);
    await page.reload();
    await page.locator('#allSets .set-card').first().waitFor({ state: 'attached' });
    assert.equal(await page.locator('#dashboardRecent .recent-card').count(), 1);

    await page.locator('.sidebar [data-view="collection"]').click();
    assert.equal(await page.locator('#collectionList .card-row').count(), 1);
    await page.locator('#collectionList .card-name-button').first().click();
    assert.equal(await page.locator('#cardDialog').isVisible(), true);
    await page.locator('#collectionDetailsForm [name="quantity"]').fill('2');
    await page.locator('#collectionDetailsForm button[type="submit"]').click();
    await page.locator('#closeCardDialog').click();
    await page.locator('#collectionList .card-name-button').first().click();
    assert.equal(await page.locator('#collectionDetailsForm [name="quantity"]').inputValue(), '2');
    await page.locator('#closeCardDialog').click();

    await page.locator('.sidebar [data-view="cards"]').click();
    await page.locator('#clearFilters').click();
    await page.locator('#globalSearch').fill('unlikely-nonexistent-card-zzzz');
    assert.equal(await page.locator('#resultCount').innerText(), '0 cards');
    await page.locator('#clearFilters').click();
    assert.notEqual(await page.locator('#resultCount').innerText(), '0 cards');
    await page.locator('#cardList .card-row').nth(1).locator('.state-button.wanted').click();
    await page.locator('.sidebar [data-view="wanted"]').click();
    assert.equal(await page.locator('#wantedList .card-row').count(), 1);
    await page.locator('#wantedSearch').fill('nonexistent-zzzz');
    assert.equal(await page.locator('#wantedList .card-row').count(), 0);
    await page.locator('#wantedSearch').fill('');
    await page.locator('[data-layout-target="wantedList"][data-layout="grid"]').click();
    assert.equal(await page.locator('#wantedList').getAttribute('data-layout'), 'grid');
    await page.reload();
    await page.locator('#wantedList .card-row').first().waitFor();
    assert.equal(await page.locator('#wantedList .card-row').count(), 1);
    const downloadPromise = page.waitForEvent('download');
    await page.locator('#backupButton').click();
    assert.match((await downloadPromise).suggestedFilename(), /^grailroster-backup-.*\.json$/);
    await page.locator('#authButton').click();
    assert.equal(await page.locator('#authDialog').isVisible(), true);
    await page.locator('#forgotPasswordButton').click();
    assert.equal(await page.locator('#authTitle').innerText(), 'Reset your password.');
    assert.equal(await page.locator('#authPassword').isVisible(), false);
    assert.equal(await page.locator('#authSubmit').innerText(), 'Send reset link');
    await page.locator('#authBackButton').click();
    await page.locator('#authSignUpTab').click();
    assert.equal(await page.locator('#authSubmit').innerText(), 'Create account');
    await page.evaluate(() => setAuthMode('update-password'));
    assert.equal(await page.locator('#authTitle').innerText(), 'Choose a new password.');
    assert.equal(await page.locator('#authEmail').isVisible(), false);
    assert.equal(await page.locator('#authPasswordConfirm').isVisible(), true);
    assert.equal(await page.locator('#authSubmit').innerText(), 'Save new password');
    await page.locator('#closeAuthDialog').click();

    await page.locator('.sidebar [data-view="dashboard"]').click();
    await page.setViewportSize({ width: 390, height: 844 });
    assert.equal(await page.locator('#menuButton').isVisible(), true);
    await page.locator('#menuButton').click();
    assert.equal(await page.locator('.sidebar').evaluate(el => el.classList.contains('open')), true);
    await page.locator('.sidebar [data-view="sets"]').click();
    assert.equal(await page.locator('#setsView').isVisible(), true);
    assert.equal(await page.locator('.sidebar').evaluate(el => el.classList.contains('open')), false);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true);
    for (const width of [320, 390, 768, 1024, 1440]) {
      await page.setViewportSize({ width, height:900 });
      for (const view of ['dashboard','sets','cards','collection','wanted']) {
        await page.evaluate(view => changeView(view), view);
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true, `${view} overflows at ${width}`);
      }
    }
    await page.setViewportSize({width:390,height:844});
    await page.locator('.mobile-nav [data-view="dashboard"]').click();
    await page.locator('.mobile-nav [data-profile]').click();
    assert.equal(await page.locator('#menuButton').getAttribute('aria-expanded'), 'true');
    await page.keyboard.press('Escape');
    assert.equal(await page.locator('#menuButton').getAttribute('aria-expanded'), 'false');
    await page.evaluate(() => {
      const sameSet = state.catalogue.cards.filter(card => card.setId === state.catalogue.cards[0].setId).slice(0, 8);
      const updatedAt = new Date().toISOString();
      sameSet.forEach(card => { state.collection[card.id] = { status:'owned', quantity:1, updatedAt }; });
      renderRecent();
    });
    assert.equal(await page.locator('#dashboardRecent .recent-batch').count(), 1);
    assert.ok(await page.locator('#dashboardRecent .recent-card').count() <= 8);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true);
    assert.deepEqual(errors, []);
    console.log('PASS: catalogue, progress, sets, owned persistence, details, search, backup, auth and password-reset UI, and mobile navigation');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
