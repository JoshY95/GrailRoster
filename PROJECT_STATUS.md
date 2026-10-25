# GrailRoster handover

Read this first; inspect only files needed for the current task.

## Star Wars Galaxy — 25 October 2026 (published)

- Next authorised set: 2026 Topps Chrome Star Wars Galaxy, official release 12 August 2026. Built 323 identities / 14 subsets: 100 base, 137 inserts, 86 autographs. All 366 manufacturer rows independently matched Poppler; dual/triple/quad signer repeats combine into one identity per printed card. The 218 sketch artists remain a roster, not invented card identities.
- Retained all 110 odds rows, imported 107 subset rules with no inferred serial caps or subject/parallel grids. Source artwork titles and artist credits retained. Audit: docs/CHROME_STAR_WARS_GALAXY_2026_IMPORT_AUDIT.md.
- Local catalogue: 26 sets / 12,925 identities; Star Wars 2 / 1,627, WWE unchanged 24 / 11,298. All 25 prior metadata/set files and frozen snapshot preserved against baseline 109ff57850cdb470a1e05ae4bc25bc6a685b42b9.
- Local focused source/import and existing regressions passed. Browser CI 40194538371 passed guest, Vault, offline reload, responsive layouts and independent ownership of real Chrome/Galaxy #1 cards. The guarded SQL passed a rolled-back dry run, committed successfully and a second committed run left complete-row digests unchanged across all eight tables. Collections remain 30, digest 6648329147d88b88ed9e52eaac40cfa9; images remain empty. No collector writes occurred. Shared additive generator defaults still reproduce the previous Chrome SQL byte-for-byte.
- Published via PR #8, feature e0867d1d44932378b18efbb07ef3904b60c449e9, merge e47a3a33ccc4703a0912fc283821de9f9b40c9ff. Pages 40194738478 succeeded; all 39 runtime/index/set assets are byte-identical to validated source. Live guest UI showed two Star Wars sets / 1,627 cards, Galaxy 323 / 14 subsets, and Q-ANDOR as one card with four signers. The old offline cache refreshed after one normal reload. Receipt: docs/CHROME_STAR_WARS_GALAXY_2026_RELEASE.json. Authenticated two-device/private-photo flows were not rerun.
- Next: 2025 Topps Star Wars Masterwork, then 2025 Smugglers Outpost, following the master register. Do one set per task.


## First Star Wars set — 25 October 2026 (published)

- User authorised starting with the newest Star Wars set and working backwards. One set per task remains the workflow.
- 2026 Topps Chrome Star Wars: 1,304 identities / 27 subsets, explicit star-wars category. All 1,369 source rows independently matched Poppler; 44 duo + 57 triple signature rows combine into 41 cards. Five Sapphire-only Hidden Gems identities deferred.
- Retained all 186 combined odds rows; 151 Chrome subset rules imported. No invented Superbox design subjects, sketch identities, card-specific parallel grids or serial caps. Only the Topps guide supports a subset Logofractor /77 rule. Audit: docs/CHROME_STAR_WARS_2026_IMPORT_AUDIT.md.
- Local catalogue now 25 sets / 12,602 identities: WWE remains 24 / 11,298; Star Wars 1 / 1,304; Marvel empty. All pre-existing set files, metadata, card IDs and frozen snapshot are byte-identical to the published main baseline b579bc05bf19229b87ab9437a2394ee19d5bf10f.
- Local focused import/source tests and existing catalogue/category regressions passed. Browser CI 40192755992 passed guest, Vault, real offline reload and category ownership/isolation at 320–1440px. Guarded SQL supabase/corrections/2026-10-25-chrome-star-wars.sql passed a rolled-back dry run, committed successfully, and a second committed run left all eight table digests unchanged. Collections remain 30, digest 6648329147d88b88ed9e52eaac40cfa9; images remain empty. No collector writes occurred.
- Published via PR #7, feature a77d068500eda96c933b6bdb4c00891dec798049, merge ef70dc60d6db27f5ae7254e78dad593bc3acee9c. Pages 40192984799 succeeded. All 38 runtime/index/set assets match validated local bytes. Live guest UI verified WWE 24 / 11,298, Star Wars 1 / 1,304 and Ewan McGregor signer search returning two autograph identities. Receipt: docs/CHROME_STAR_WARS_2026_RELEASE.json. Authenticated two-device/private-photo checks were not rerun.
- Next set: 2026 Topps Chrome Star Wars Galaxy. 2026 Sapphire is announced for 28 October UTC / 29 October Melbourne, and is not part of this import.


## Multi-category release — 25 October 2026 (published)

- User approved clean separation for WWE, Star Wars and Marvel after reviewing the
  design preview. Published through PR #6; no new sets imported.
- Every existing set has explicit `categoryId: wwe` metadata. `categories.js` validates
  franchise membership and scopes every view/search/statistic/Vault summary. Unimported
  categories show Coming soon; selected category persists separately from collector data.
- Full collection sync and backup retain all categories together; IDs/storage/auth and
  all 24 per-set bundles/frozen compatibility snapshot are preserved. Cloud classification
  uses the reviewed index mapping; no schema or database writes are needed.
- Focused catalogue, import, category contract and real-page DOM tests passed. Read-only
  database checks showed 30 unchanged collection rows with full-row digest
  `820fb924a7559fe022be70620b24bcef`. See docs/MULTI_CATEGORY.md for contract and limits.
- Feature commit daa1e205da8ee3d00646afd13ee304be3ae4e707 passed CI run 40179641739:
  six Stadium Club checks, split catalogue, category DOM/import contract, Chromium guest,
  Vault, real offline reload, category switching and responsive widths 320–1440px.
- Merged as 2256dcb4dc4811231ad099ac3c2420c7345ee9d5; Pages run 40179804636 succeeded.
  All 36 checked live runtime/index/set assets match validated source byte-for-byte.
  Live guest browser verified WWE 24 sets / 11,298 cards and separate Star Wars/Marvel
  Coming soon screens, then returned to WWE. Authenticated two-device/photo tests were
  not rerun. Receipt: docs/CATEGORY_RELEASE_2026_10_25.json. No database writes occurred.

## Published catalogue update — 24 October 2026

- NOW #107–112 reverified against all six official pages: 132 annual identities (112 regular, 6 HOF, 14 posters). Archive newest is #112; active WWE NOW page has no releases. #112 is officially titled “946”; preserved. Six new cards have 30 explicitly listed numbered foil variants; autograph redemption extras remain notes without invented checklist IDs.
- Stadium Club: manufacturer PDF reconciled to 930 identities / 25 subsets (938 rows minus eight repeated dual-signer rows). Both 200-card base programmes are complete. See docs/STADIUM_CLUB_WWE_2026_IMPORT_AUDIT.md for subset table, source hashes, confirmed editions and deferred Chrome autograph-II entries.
- Local split catalogue: 24 sets / 11,298 identities. Stadium Club has 930 identity placeholders + four explicitly confirmed editions; 117 subset odds rules. Unrelated set files and frozen catalogue.json are byte-identical to main. Existing NOW IDs and metadata unchanged; 20 HOF/poster display positions shift by six.
- Six focused source/preservation/idempotency tests and catalogue-split regression passed. All six archive pages reconcile 135 products to 132 identities plus the duplicate #106, Vegas box and WBCO. GitHub CI run 40085112389 passed guest browser smoke, Collector Vault and real offline reload. The combined SQL was applied successfully after a rolled-back dry run: Sydney now has 24 sets / 11,298 cards / 32,568 variants / 414 subsets. Zero orphan variants. Runtime data and database rows match exactly for both affected sets. A second committed application was a byte-for-byte no-op across all eight catalogue/collection/image tables.
- Execute only supabase/corrections/2026-10-24-now-stadium-club.sql (generated by scripts/prepare_october_catalogue_update.py). Earlier six-card SQL is superseded. This transaction rejects conflicts, snapshots every existing catalogue row and collection/image records, validates counts/linkage and preserves old rows. Reapplication must be a no-op.
- Published via PR #5, merge 1ec1a2ae643eb4caacb1124159407fec97bb15c6. Final-head CI run 40085394150 passed all six focused tests, catalogue-split checks, Chromium guest smoke, Collector Vault and real offline reload. GitHub Pages deployment run 40085538149 succeeded. Production index, all 24 set bundles and sw.js are byte-identical to validated source. Live guest UI shows 24 sets / 11,298 cards, Stadium Club 930, dual DA-RH as one Triple H / The Rock card, and NOW #112 “946”. Full verification receipt: docs/CATALOGUE_UPDATE_2026_10_24_VERIFICATION.json. Authenticated cloud/photo/two-device tests have not been rerun. PR #5 is the existing work item. Collection rows remain 30; complete collection digest before/after is 6648329147d88b88ed9e52eaac40cfa9. Images remain empty/unchanged. The transaction’s complete-row guards preserved all old catalogue rows, allowing only the documented NOW ordering/count changes. New-set research outside this requested update remains paused.

## Current state — 4 October 2026

- Production: https://grailroster.com ; GitHub: JoshY95/GrailRoster, main.
- Catalogue published at commit 8f1fdd8 (PR #4); Pages deployment succeeded. Live set library and published data files verified.
- Production/local/database catalogue: 23 sets, 10,359 identities. All completed lists are uploaded, including National Treasures (718 identities, 21 subsets, 3,550 numbered versions), annual 2025/2026 Topps NOW and the WBC crossover.
- Supabase Sydney project: jvsvuxgpaqwlcstfuzbd. No credentials belong in this file.
- Obsidian design uses theme.css; preserve all legitimate collection cards and existing user data.
- Branded auth/SMTP, password confirmation, password recovery, email change and account deletion were user-tested successfully.
- Collector Vault is implemented; see docs/COLLECTOR_VAULT.md for behaviour and test limitations. Do not infer all live photo/two-device tests are complete.

## Split catalogue — deployed

- Runtime catalogue: data/catalogue-index.json plus data/sets/<set-id>.json.
- scripts/catalogue_io.py and catalogue_io.js load/save the split format and skip rewriting unchanged files.
- Importers, exporter, app loader and offline service worker now use the split format.
- data/catalogue.json is a frozen pre-split compatibility snapshot, not the current source of truth. Do not read/upload/regenerate it for routine set additions.
- All legitimate card identities remain unchanged; two false heading records were removed in the reviewed 4 October correction. The app still loads all sets for global search; lazy loading is not implemented.
- GitHub CI run 37187099064 passed Chromium browser smoke, Collector Vault and real offline reload tests. Local Chromium remains unavailable; use the verified CI workflow rather than retrying local browser installation.

## Topps NOW catalogue addition — 12 October 2026

Three newly confirmed identities were added to the existing 2026 annual WWE set: regular #105 Blake Monroe, #106 Wren Sinclair, and MITB event poster. The set now has 126 cards (106 regular, 6 Hall of Fame, 14 posters); global catalogue count is 10,362 across 23 sets. Topps reports #105 base print run 1,626. The release list records official links and explicit foil details; #106 and MITB print runs remain pending. Existing IDs and unrelated set files remain unchanged. Sydney catalogue tables now match: 126 cards and 126 identity variant rows for the set, 10,362 cards globally, with no orphan variants. The live guest card catalogue displayed all three identities and 10,362 cards. The applied one-time SQL is recorded in supabase/corrections/2026-10-12-topps-now-105-106-mitb.sql; authenticated collection sync was not retested.

## Next catalogue task — imports paused

User paused new sets on 4 October 2026. Audit completed: see docs/WWE_2025_2026_COVERAGE_AUDIT.md for all 18 existing 2025/2026 lists, missing 2025 Royal Rumble/WrestleMania/SummerSlam event exclusives, annual 2025/2026 NOW coverage (including HOF/posters), now imported and published, and upcoming Stadium Club. No missing released main boxed product was identified in the sources checked. Royalty and 2026 Sapphire heading/subset errors are now corrected locally and in Sydney: 689 and 496 identities respectively. Two false headings and their identity placeholders were removed; 35 real cards moved to the correct subsets without changing IDs. Collections, unrelated card records and legitimate variant links have identical before/after digests; zero orphan variants. BAPE's four variation records still need card-image verification. Completed-list uploads were subsequently authorised and published. Further new-set research/imports remain paused; wait for user instruction before resuming.

2024 Panini National Treasures WWE is complete locally and in Sydney; see docs/NATIONAL_TREASURES_2024.md. Source-derived variant digest matches all 3,550 stored versions, with zero orphan variants. Existing catalogue and collection digests remain unchanged. All 19 existing split set files are byte-identical; source-backed importer tests and catalogue-split tests passed.

Publication verified: browser smoke, Vault and real offline reload passed in CI. The live set library shows all 23 sets; production index and all newly published/corrected bundles exactly match the verified local files. Public Supabase API matches all 10,359 local card identities. Authenticated cloud/photo/two-device testing is not implied by these guest checks.

Next set: 2024 Panini Three Count WWE, then Select, PhotoGenic, Prizm Premium Factory Set and Prizm (tentative order). Verify actual release dates before confirming order. National Treasures uses provisional December 31, 2024 for sorting; the original GTS schedule said December 13 and no final manufacturer announcement was found.

One set per task. Use authoritative manufacturer/distributor checklists. Keep stable subset/card-number IDs; multi-subject designs are one identity. Never infer missing card numbers or parallel applicability. Record only verified numbered versions. Preserve all pre-existing set/card records and collections. Validate counts, duplicate IDs, variant linkage, idempotency and existing-record preservation.

## Lean workflow

1. Read this file and git status; use targeted searches, not full catalogue dumps.
2. Reuse the importer pattern and catalogue_io helpers. Parse large sources locally; report counts/errors only.
3. One agent. Use tools only for required research, implementation and checks; no repeated attempts at known unavailable tooling.
4. Run focused tests plus regression tests when UI/auth/storage changes warrant them. Distinguish tests actually run from pending checks.
5. Publish only validated work within user authorization; never force-push. Update this handover after each milestone.

User settings: recommend GPT-6.1 Sol, Medium reasoning, Standard speed for routine work; reserve Astra for difficult design/debugging reviews. The user changes these settings, not the agent.

Correction validation: catalogue-split and National Treasures tests passed; repair rerun was byte-identical and all 18 unrelated set files remain unchanged. Reviewed manifest: scripts/catalogue_repairs.json; local repair: scripts/repair_catalogue.py; database transaction: supabase/corrections/2026-10-04-checklist-headings.sql. Corrections are published; browser and offline verification passed.

Topps NOW release-list milestone: docs/WWE_TOPPS_NOW_2025_2026_RELEASE_LIST.md covers all 157 2025 annual cards, 123 2026 annual WWE cards through #104, the separately labelled WBCO crossover and the existing 40-design Vegas checklist. Standalone workbook created with product links, release dates, print runs and published extras. Annual lists and the separately labelled WBC crossover are imported and published; the existing Vegas list is unchanged. Only verified checklist identities were added; advertised extras remain source notes pending variant verification. New-set queue remains paused.

Upload milestone — 4 October 2026: user authorised uploading every completed list. Annual NOW 2025 (157), annual NOW 2026 (123) and separate WBC crossover (1) are imported locally and in Sydney. All prior card and collection digests match; zero orphan variants. Existing Vegas is unchanged. No new research sets authorised. Published website bundle includes National Treasures, Royalty/Sapphire corrections and the split catalogue. Local catalogue, source, idempotency and preservation checks passed. GitHub CI browser smoke, Vault and real offline reload passed; production deployment and file parity verified. Collection digest remains 4a4cedb954d6d44b24667d0d04001d2b; pre-existing card digest remains 746683a59318a70ae53834ad1d4860c5.
