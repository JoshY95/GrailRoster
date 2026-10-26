# WWE 2023 Immaculate, Chronicles and Impeccable import

Prepared 27 October 2026 (Australia/Melbourne). User authorised all three sets. Baseline: `b3c7cbb6a66807c795eb94e60cdf84a5eda03601` (46 sets /22,731 identities).

| Product | Actual hobby release used | Identities | Subsets | Explicit source editions | Editions with printed sequence |
|---|---|---:|---:|---:|---:|
| 2023 Panini Immaculate Collection WWE | 19 June 2024 | 1,047 | 35 | 3,362 | 3,362 |
| 2023 Panini Chronicles WWE | 24 May 2024 | 843 | 34 | 5,862 | 4,518 |
| 2023 Panini Impeccable WWE | 3 April 2024 | 664 | 24 | 2,335 | 2,335 |
| Total | | 2,554 | 93 | 11,559 | 10,215 |

Resulting catalogue: 49 sets /25,285 identities; WWE 31 /15,967; Star Wars unchanged at 18 /9,318. All previous 46 metadata records, set bundles and frozen compatibility snapshot are preserved. No collector, ownership, photo, auth or storage-policy writes are part of this import.

## Sources and reconciliation

The `sources/wwe-2023-batch/` directory retains original downloaded workbooks, normalized rows with SHA-256 hashes, explicit family/count/category mappings, and independently captured factual checklist sections. The importer re-extracts and validates them without network access. Workbooks remain unchanged.

- **Immaculate:** the updated [published Panini-format workbook](https://xcdn.checklistinsider.com/public/2024/06/2023-Panini-Immaculate-Collection-WWE-Wrestling-Checklist-Downloads-Excel-spreadsheet-new.xlsx) contains 3,362 edition rows. All 2,516 rows in the [original GTS export](https://gogts.net/wp-content/uploads/2024/06/2023-Panini-Immaculate-WWE-Trading-Cards-Checklist.xls) reconcile after one documented Seth nickname encoding repair, nickname quotation formatting, signer order and repeated subject normalization. The original export lacks four later memorabilia sections: Remarkable Memorabilia (99 subjects), Standout Memorabilia (40), Superstar Swatches (60) and The Immaculate Standard (50). All 249 additional numbered subjects, their caps and explicitly declared parallel statements independently match [WrestlingTradingCards](https://wrestlingtradingcards.com/2023-wwe-panini-immaculate-collection-panini/), accounting for exactly 846 additional edition rows. No editions are extrapolated beyond those matched lists.
- The older [Checklist Center Immaculate workbook](https://www.checklistcenter.com/wp-content/uploads/2024/06/2023-Panini-Immaculate-Collection-WWE.xlsx) lists multi-signers on separate rows. Combining them gives 2,516 designs/editions for comparison, but Quad Autographs #3 and its Platinum edition incorrectly repeat Rob Van Dam instead of The Sandman. Both original GTS and updated source agree on Rob Van Dam, Bubba Ray Dudley, The Sandman and D-Von Dudley. The discrepancy is explicitly retained in the evidence, not treated as an exact full-file match.
- **Chronicles:** all 5,862 rows of the [published workbook](https://xcdn.checklistinsider.com/public/2024/05/2023-Panini-Chronicles-WWE-Wrestling-Checklist-Downloads-Excel-Spreadsheet.xlsx) reconcile to the [independent workbook](https://www.checklistcenter.com/wp-content/uploads/2024/05/2023-Panini-Chronicles-WWE.xlsx). Three quote-format differences in Tools of the Trade Signatures #5 are normalized only for comparison. The GTS page points to an updated XLS file, but that download did not complete; no original distributor-byte comparison is claimed for Chronicles.
- **Impeccable:** all 2,335 rows of the [original distributor XLS](https://gogts.net/wp-content/uploads/2024/03/2023-Panini-Impeccable-WWE-Trading-Cards-Checklist.xls) reconcile with the [published mirror](https://xcdn.checklistinsider.com/public/2024/03/2023-Panini-Impeccable-WWE-Wrestling-Checklist-Downloads-Excel-spreadsheet-checklist.xlsx), after 19 occurrences of one malformed Seth nickname string and quote formatting are normalized. The source's POSITION column is not a rookie designation; no rookie flags are inferred.

Checklist numbering is the numeric numbering in the retained Panini-format worksheets. Physical cards can use alphanumeric codes. This import does not invent physical aliases or imply that every worksheet number is printed on the card.

Release dates: [Immaculate guide](https://www.checklistinsider.com/2023-panini-immaculate-collection-wwe), [Chronicles guide](https://www.checklistinsider.com/2023-panini-chronicles-wwe-wrestling), [Impeccable final GTS calendar](https://gogts.net/hot-in-the-shop-week-of-april-1-2024-phenomenal-multi-sport-week/). The final 3 April Impeccable calendar supersedes its preliminary 29 March checklist-page schedule. All retain the official 2023 product year.

## Identity and edition decisions

- Identities are the union of actual listed editions, including parallel-only subjects. Unlisted base editions are never added. All 11,559 variants link only to their explicitly listed subject/design; blank sequence cells remain unknown.
- Chronicles' sixteen numbered base brands contain 394 designs, rather than the advertised round 400. Original numbering gaps remain: Chronicles #14 and other brand-specific gaps are not filled. Premium Gala Rookies, National Treasures, Noir and Timeless Treasures retain their separate source families under the same Chronicles product.
- Impeccable Base has 99 source identities; #36 is absent. Indelible Ink has 39 identities across its editions: Nova has no unsuffixed/base edition in these sources. Jerry Sags' missing Platinum edition is not invented. Gold and Silver WWE Logo and Legends Logo programmes remain source-distinct subsets, rather than silently conflating their materials.
- Immaculate Memorabilia Autographs includes its FOTL-only subject as the same source-defined family. The Attitude Era is one eight-signer design. Duals, triples and quads are one card per family/number, retaining all signers. Repeated exact names on a two-image Past and Present design do not create separate cards.
- Subject order, nickname formatting, encoding repairs and the known older-mirror error are documented comparison operations. Original rows remain available. No licensed artwork or new reference images are added.

## Implementation and validation

- `scripts/wwe_2023_batch.py` loads explicit reviewed family manifests, reconciles retained evidence, builds stable family/number IDs and refuses overwriting any conflicting existing identity. `catalogue_io` changes only the three new bundles and the index; the old 46 set bundles and frozen snapshot are byte-identical to baseline. Reapplication is byte-identical.
- `scripts/prepare_wwe_2023_batch_import.py` builds one compact atomic additive transaction. It validates every existing-ID match, all new table counts, subset membership and variant linkage; full-row snapshots guard all six catalogue tables plus complete collector and reference-image tables. No SQL targets collector/image writes. A rolled-back dry run and an identical committed repeat are required before declaring publication complete.
- Five focused tests cover independent source reconciliation, all exact edition/cap applicability, numbering gaps, parallel-only subjects, the corrected quad/eight-signer book, all prior metadata/bundles, idempotency, conflict refusal and SQL guards. The older Prizm test now accepts additive catalogue totals while retaining every prior-record preservation check.
- GitHub CI adds batch-specific browser coverage alongside existing catalogue preservation, guest, Vault and real offline reload suites. The new browser checks cover all three set counts, ownership/category separation, preserved prior guest entries, the Nova source identity, corrected multi-signer designs, numbering gaps, persistence and widths 320–1440. Known unavailable local Chromium is not retried.
- Authenticated cloud sync, private-photo/privacy and two-device flows are not rerun by this catalogue-only task. Do not equate guest/Vault/offline CI with those checks.

Publication milestones and final run/merge/database/production evidence will be recorded in `docs/WWE_2023_BATCH_RELEASE.json` when completed.
