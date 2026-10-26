# WWE 2024 catalogue gap audit and three-set import

Prepared 26 October 2026 (Australia/Melbourne). User authorised auditing the 2024 gaps and completing the next three missing WWE sets, including Panini. Baseline: `181191c8139e31b7c5913cf7ec1dafae8aebd4e5`.

## Scope and counts

| Product | Release date used | Identities | Subsets | Listed versions | Explicitly numbered versions |
|---|---|---:|---:|---:|---:|
| 2024 Panini Three Count WWE | 6 December 2024 | 415 | 13 | 3,333 | 3,313 |
| 2024 Panini Select WWE | 8 November 2024 | 789 | 21 | 11,234 | 7,240 |
| 2024 Panini PhotoGenic WWE | 25 September 2024 | 395 | 12 | 2,924 | 2,544 |
| Total | | 1,599 | 46 | 17,491 | 13,097 |

Resulting catalogue: 45 sets /22,215 identities. WWE 27 /12,897; Star Wars remains 18 /9,318. All 42 pre-existing set metadata records, set bundles, stable card IDs and frozen compatibility snapshot remain unchanged.

## Checklist provenance and limits

The `sources/wwe-2024-batch/` folder retains two independently hosted workbook copies for each product, plus normalized primary rows with source URLs and SHA-256 hashes. Primary workbooks are the five-column Panini-format checklists published by Checklist Insider; comparison copies come from Checklist Center. Every edition, subject, number and printed sequence is reconciled across those two copies. PhotoGenic comparison combines separate dual-signer rows, normalizes signer order and repeated Progressions subjects (including Bray Wyatt's Fiend persona); complete original primary wording remains in the normalized evidence.

Original GTS distributor workbooks were recovered for Three Count (3,333 rows) and Select (11,234 rows). All rows reconcile with the mirrored workbooks after repairing one malformed Seth “Freakin” Rollins nickname string in the original exports: 35 occurrences in Three Count and 63 in Select. Original bytes, unmodified rows and SHA-256 hashes are retained. PhotoGenic remains reconciled between two published workbook mirrors; its direct-origin manufacturer/distributor workbook was not recovered. Panini historical product pages no longer supply complete historical content. No direct-origin hash match is claimed for PhotoGenic, and images have not certified every physical card.

- [GTS Three Count distributor checklist](https://gogts.net/2024-panini-three-count-wwe-trading-cards-checklist/)
- [GTS Select distributor checklist](https://gogts.net/2024-panini-select-wwe-trading-cards-checklist/)
- [Panini manufacturer checklist index](https://www.paniniamerica.net/checklist.html)
- [Three Count published workbook](https://xcdn.checklistinsider.com/public/2024/11/2024-Panini-Three-Count-WWE-Wrestling-Checklist-Downloads-Excel-spreadsheet.xlsx)
- [Select published workbook](https://xcdn.checklistinsider.com/public/2024/10/2024-Panini-Select-WWE-Wrestling-Checklist-Downloads-Excel-spreadsheet.xlsx)
- [PhotoGenic published workbook](https://xcdn.checklistinsider.com/public/2024/09/2024-Panini-PhotoGenic-WWE-Wrestling-Checklist-Downloads-Excel-spreadsheet.xlsx)
- Comparison pages: [Three Count](https://www.checklistcenter.com/2024-panini-three-count-wwe-wrestling-card-checklist/), [Select](https://www.checklistcenter.com/2024-panini-select-wwe-wrestling-card-checklist/), [PhotoGenic](https://www.checklistcenter.com/2024-panini-photogenic-wwe-wrestling-card-checklist/).

Final guide dates are used above. GTS's preliminary Three Count schedule says 22 November 2024; the later Checklist Insider and Beckett guides report 6 December. No existing National Treasures release-date metadata is changed by this audit.

## Decisions and unresolved source anomalies

- Identity is the union of actual listed editions, not just the unsuffixed issue. Parallel-only autograph subjects remain collectible; no missing base versions are invented. Three Count therefore has 415 identities, including 30 Legendary Autographs, rather than just the 28 unsuffixed rows. Select Signature Selections has 94 identities across its editions.
- PhotoGenic base horizontal is 100 designs (#1–100); vertical has 101 source subject identities across #101–200. Both mirrors assign base #175 to Triple H and parallel #175 to Beth Phoenix. These conflicting subject entries have distinct internal suffixes (`-TRIPLE-H`, `-BETH-PHOENIX`); the printed source number is retained. Triple H has only the listed base version; Beth Phoenix has only the listed parallels. Physical card numbering remains unresolved. Neither a missing Beth base nor Triple H parallels are manufactured.
- PhotoGenic Dual Autographs is ten card designs, rather than twenty signer identities. Progressions retains three-image/subject source wording on one card. FOTL-only subjects account for 37 Picture Perfect Signatures and 47 Superstar Signatures designs.
- Select's `Red and Blue` and `Red and Blue Prizms` are distinct published row labels with unannounced sequences. Both labels are preserved as source-listed versions. Whether these are a physical alias is unresolved; no duplicate card identity is created, and no print run is inferred.
- Blank SEQ values remain unknown. They never imply an unlimited print run or 1/1. Caps come only from actual subject/edition rows, with no extrapolated parallel grids. The 409 subset rules are explicitly restricted to exact variant rows.
- No artwork, inventory, auth, storage or collector data is changed.

## 2024 gap register — updated after the Prizm follow-up

| Release/programme | State / next action |
|---|---|
| Panini Flawless WWE | Already published; unchanged |
| Panini National Treasures WWE | Already published; unchanged |
| Panini Three Count WWE | Added in this batch |
| Panini Select WWE | Added in this batch |
| Panini PhotoGenic WWE | Added in this batch |
| Panini Prizm WWE, including Premium Factory Set editions | Published in the Prizm follow-up: one parent, 516 identities /16 subsets and 9,270 listed versions, including 400 Premium editions across the same 200 base IDs. See [Prizm audit](PRIZM_WWE_2024_IMPORT_AUDIT.md). Premium does not create a duplicate parent. |
| Panini Instant WWE 2024 | Continuing online programme; missing historical coverage. Enumerate releases separately before claiming completeness. |
| Panini Adrenalyn XL WWE 2024 | Regional/game-format candidate; not covered by the main hobby import. Verify physical edition, region and checklist. |
| Promotions/event exclusives | Open title audit; no worldwide completeness claim. Digital blockchain releases excluded. |

Sources: [2024 wrestling release index](https://wrestlingtradingcards.com/2024-checklists/), [GTS Prizm checklist](https://gogts.net/2024-panini-prizm-wwe-trading-cards-checklist/), [Premium Factory Set guide](https://www.checklistinsider.com/2024-panini-prizm-premium-wwe-factory-set).

## Verification and publication

- Six new focused tests cover both complete workbook comparisons, identity/edition counts, exact subject/cap applicability, parallel-only subjects, multi-subject handling, #175 separation, all 42 previous sets, repeat import and conflict refusal.
- Existing catalogue split, category, Stadium Club and fourteen Star Wars import suites are retained. Three historical tests now permit additive sets; the new batch suite checks exact current totals and full baseline preservation.
- `prepare_wwe_2024_batch_import.py` generates a compact, single atomic transaction. It expands only source-listed versions, refuses existing-ID conflicts, validates counts/linkage, and compares every pre-existing catalogue row plus both complete collector/image tables before commit. Reapplication must be a no-op. No mutations target `collection_items` or `reference_images`.
- Rolled-back database dry run passes: 45 sets /22,215 cards /30 collection records. Baseline collection digest: `6648329147d88b88ed9e52eaac40cfa9`; reference images empty.
- Chromium guest/Vault/offline and batch-specific ownership/responsive checks run through GitHub CI; known unavailable local Chromium is not retried. Authenticated cloud/private-photo/two-device flows are outside this catalogue-only check.
- Final publication result and database parity are recorded in `docs/WWE_2024_BATCH_RELEASE.json` once completed.

Published through [PR #22](https://github.com/JoshY95/GrailRoster/pull/22), feature `9d0a8d5f7550855fc03ea1635937ed65b84a3975`, merge `65e54811920ba9bb18f266b85e7c80e1dea82691`. Browser CI `40317317513` and Pages `40317675403` succeeded. All 58 production runtime/index/set assets match tested bytes. The committed database matches all six generated catalogue tables exactly; an identical committed repeat preserves every full-row digest across all eight watched tables. All 30 collections retain digest `6648329147d88b88ed9e52eaac40cfa9`; images remain empty. Live guest UI was not separately rerun; CI exercised identical published assets. Full receipt: `docs/WWE_2024_BATCH_RELEASE.json`.
