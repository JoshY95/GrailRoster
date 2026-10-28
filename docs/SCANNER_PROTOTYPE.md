# WWE scanner prototype

Open `https://grailroster.com/#scanner` after publication, or `/#scanner` on a local static server.

## What works

- Take/upload a front photo and optionally the back; rotate or remove either side.
- Read visible text with pinned Tesseract.js 6.0.1 (English, sparse-text mode) on the device.
- Search only verified WWE identities already in the current runtime catalogue. Name, printed card number, product, year and subset text rank possible matches. An optional set hint narrows the search. A single incomplete first name does not qualify a multi-word name; one-character OCR mistakes can qualify as a similar-name candidate.
- Review/correct OCR text, reject matches, select a checklist identity and confirm optional parallel/serial information. Serial denominators and copyright years are not treated as standalone checklist numbers.
- Save to a separate device-local test collection, never `collection_items`, the guest Vault or signed-in collection. No photos are uploaded, persisted or included in exports.
- Simulate 25 successful confirmed cards per device-local calendar month. Front/back count together; failed, rejected and cancelled attempts consume no credit. Reset is explicitly a test-only action, not a paid plan bypass.
- Export JSON with original/reviewed OCR text, candidate IDs, selected rank, confirmed identity, optional edition details, corrections, elapsed recognition time and zero paid-API recognition cost. Attempts retain the latest 200 entries, test collection up to 500 items, and the screen displays the latest 20 items. Excludes development, device, hosting and bandwidth costs.

## Boundaries

This is a real OCR prototype, not generative vision or artwork recognition. It cannot establish a foil colour, autograph authenticity, grade or exact edition from artwork. The current runtime exposes checklist identities rather than the full verified variant catalogue. It never invents a parallel or silently writes an AI guess into the database. Use clear upright close photos, especially card backs. Support includes JPEG/PNG/WebP/AVIF up to 12 MB /40 MP, resized on device to a maximum dimension of 2000 pixels. HEIC must be converted first.

No Gemini or other paid recognition key is configured; no recognition backend, database schema, account/auth rules, payments or subscriptions are changed. Real AI image understanding can be added later behind an authenticated server endpoint with provider credentials, server-enforced usage and a spending limit. This local allowance is not suitable for paid billing.

On first use the browser downloads the integrity-checked Tesseract script, pinned worker/core and English model. Internet is required for those downloads; offline recognition is not guaranteed. Assets are requested from jsDelivr and tessdata.projectnaptha.com; card pixels are processed locally. Cancellation invalidates the job and terminates an active worker; a 90-second timeout stops a stalled attempt. Blocked/full storage keeps the session usable with an explicit export warning.

## Acceptance test

1. Open Scan a card from the sidebar or Overview. Choose a front photo and optionally back. Select a set if known.
2. Find my card → inspect the candidates, exact year/product/card number/subset. Choose a candidate; confirm parallel/serial only if known.
3. Tick the review box and Add to test collection. Expect 24/25 scans and one test card. Real Owned cards/Vault must not change.
4. Retry a poor or unsupported photo; expect no credit deduction. Review OCR text to learn why a match failed.
5. Download results before resetting or changing device.

For real accuracy evaluation, independently label 100–200 supported and unsupported real collector cards, include similar-looking products/variants, sleeves/slabs, glare and blurred photos. Measure correct identity at rank 1 and within the shown candidates, false matches, no-match rate, corrections, median/tail time, and end-to-end time versus search. A user confirming a suggestion is not independent ground truth. Synthetic OCR tests establish wiring, not real-card identification accuracy.

## Automated checks

- `node tests/scanner-match.cjs`: current catalogue ranking, one-character errors, ambiguity, serial/year isolation, category boundaries, monthly rollover/corrupt state and catalogue immutability.
- `node tests/run.cjs tests/scanner-browser.cjs`: Chromium real Tesseract front/back recognition on synthetic text fixtures, confirmed test-only save, export/reload, then injected OCR responses for failure/cancel/correction/quota/reset/storage branches, responsive widths 320–1440px and unchanged collection/catalogue. No real collector or account writes.
- Existing catalogue/category, guest/Vault, cloud-mock and offline suites remain in CI.
