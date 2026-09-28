const assert = require('node:assert/strict');
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, acceptDownloads: true });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    // Verify the bundled catalogue fallback without relying on a live Supabase project.
    await page.route('**/rest/v1/**', route => route.abort());
    await page.goto(process.env.RINGVAULT_BASE_URL || 'http://127.0.0.1:8765/');
    await page.locator('#allSets .set-card').first().waitFor();
    assert.equal(await page.locator('#allSets .set-card').count(), 17);
    assert.equal(await page.locator('#heroProgress strong').first().innerText(), '0%');

    await page.locator('#dashboardSets .set-card').first().click();
    assert.equal(await page.locator('#cardsView').isVisible(), true);
    assert.notEqual(await page.locator('#setFilter').inputValue(), 'all');
    await page.locator('#cardList .card-row').first().locator('.state-button.owned').click();
    assert.equal(await page.locator('#dashboardRecent .recent-card').count(), 1);
    await page.reload();
    await page.locator('#allSets .set-card').first().waitFor();
    assert.equal(await page.locator('#dashboardRecent .recent-card').count(), 1);

    await page.locator('[data-view="collection"]').click();
    assert.equal(await page.locator('#collectionList .card-row').count(), 1);
    await page.locator('#collectionList .card-name-button').first().click();
    assert.equal(await page.locator('#cardDialog').isVisible(), true);
    await page.locator('#collectionDetailsForm [name="quantity"]').fill('2');
    await page.locator('#collectionDetailsForm button[type="submit"]').click();
    await page.locator('#closeCardDialog').click();
    await page.locator('#collectionList .card-name-button').first().click();
    assert.equal(await page.locator('#collectionDetailsForm [name="quantity"]').inputValue(), '2');
    await page.locator('#closeCardDialog').click();

    await page.locator('[data-view="cards"]').click();
    await page.locator('#clearFilters').click();
    await page.locator('#globalSearch').fill('unlikely-nonexistent-card-zzzz');
    assert.equal(await page.locator('#resultCount').innerText(), '0 cards');
    await page.locator('#clearFilters').click();
    assert.notEqual(await page.locator('#resultCount').innerText(), '0 cards');
    const downloadPromise = page.waitForEvent('download');
    await page.locator('#backupButton').click();
    assert.match((await downloadPromise).suggestedFilename(), /^ringvault-backup-.*\.json$/);
    await page.locator('#authButton').click();
    assert.equal(await page.locator('#authDialog').isVisible(), true);
    await page.locator('#authSignUpTab').click();
    assert.equal(await page.locator('#authSubmit').innerText(), 'Create account');
    await page.locator('#closeAuthDialog').click();

    await page.locator('[data-view="dashboard"]').click();
    await page.setViewportSize({ width: 390, height: 844 });
    assert.equal(await page.locator('#menuButton').isVisible(), true);
    await page.locator('#menuButton').click();
    assert.equal(await page.locator('.sidebar').evaluate(el => el.classList.contains('open')), true);
    await page.locator('[data-view="sets"]').click();
    assert.equal(await page.locator('#setsView').isVisible(), true);
    assert.equal(await page.locator('.sidebar').evaluate(el => el.classList.contains('open')), false);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true);
    assert.deepEqual(errors, []);
    console.log('PASS: catalogue, progress, sets, owned persistence, details, search, backup, auth UI, and mobile navigation');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
