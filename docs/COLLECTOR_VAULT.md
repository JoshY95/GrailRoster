# Collector Vault

Feature branch: `feature/collector-vault`.

## Behaviour

- Open a card and choose **Set up physical copies**. Conversion is explicit and per card.
- A legacy quantity becomes that many independently identified copy records. Existing price/date/notes stay on the first copy only; this avoids inventing acquisition costs for duplicates. The legacy fields remain in the parent record as well.
- Each copy records parallel, printed serial, raw/graded format, grading company, grade, certification, condition, purchase cost/date/source, currency, storage, notes, manual valuation/date, sale price/date/fees and private front/back photos.
- Sold/traded copies stay in history but do not count as owned. Unique-card completion remains unchanged by duplicate quantities.
- Currency totals are separate. Values are user-entered estimates; there is no market feed.
- Guest records use browser storage. Signed-in writes are cloud-first and check the previous update timestamp; conflicts and network failures leave the editor available for correction/retry.
- Photos require sign-in, accept JPEG/PNG/WebP up to 10 MB and are converted to JPEG with a 1600px maximum side. The private bucket has a 5 MB object limit. Paths begin with the owner UUID; signed viewing links expire after 120 seconds.
- JSON backups include copy data and photo paths, not image files. A restore does not overwrite existing cloud Vault records. Conflicting guest data is retained in guest mode.
- Account deletion removes the user's private photo objects before calling the existing account-deletion function. If the later account-deletion call fails, those photographs may already have been removed.

## Data design

`collection_items.vault_copies` is an optional JSONB aggregate. Null means the existing checklist mode. Each array element has a stable UUID. Copies and the parent quantity update atomically, using the existing owner RLS. This avoids introducing two independently synchronised sources of ownership truth. The limit is 999 records per card design; a future large-scale reporting feature may warrant normalising copies into a separate table.

The additive migration does not convert or delete existing user records. A validation function checks types, bounds, dates, IDs and sale/grade requirements. A trigger derives quantity and protects Vault history from old clients' null replacements and authenticated row deletion. There are no security-definer functions.

## Verification

- `tests/smoke.cjs`: existing catalogue, checklist, persistence, search, backup, auth UI and responsive navigation.
- `tests/vault.cjs`: legacy conversion, independent copy editing, grading, serials, gains/losses, sold/traded history, quantities, reload, add/delete and viewport widths 320–1440px.
- `tests/vault-cloud.cjs`: simulated cloud conflict/write failures, owner filter, actual browser image conversion, failed-write photo cleanup, stale open-editor detection and account-view cleanup. Network calls in this suite are mocked.
- Live PostgreSQL transaction test: validation, derived quantity, legacy overwrite/deletion guards, owner photo access, cross-user read/upload denial. All fixture writes rolled back; 30 existing records, zero converted.
- Security advisor: no new database findings. Existing warning: leaked-password protection disabled.

Before production UI release, finish a real authenticated photo upload/read/replace/delete and two-device save/reload check. The database migration has been applied; the UI remains on the feature branch until release.

Run browser suites with Playwright available in NODE_PATH and CHROMIUM_EXECUTABLE_PATH set as needed:

```sh
node tests/run.cjs tests/vault.cjs tests/vault-cloud.cjs tests/smoke.cjs
```
