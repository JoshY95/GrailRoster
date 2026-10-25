# 2025 Topps Star Wars Smugglers Outpost — import audit

Status: prepared; local validation passed. Browser CI, guarded database application and publication pending.

## Manufacturer reconciliation

The official product title is 2025, with an actual release of 18 March 2026 (Topps Available From). Generic product-year metadata says 2026; it does not create another set.

The 29-page checklist contains 881 numbered subject/signature rows. Twenty-four trio rows become eight cards, 28 quad rows become seven cards, and 40 book rows become two twenty-signer cards. This removes 75 repeated signature rows: **806 design identities / 23 subsets** — 200 base, 260 inserts, 221 autographs (including 39 numbered Sketchagraphs), and 125 numbered sketch designs. The 216 artists remain a separate roster; no artist/subject combinations or unique frames are invented.

All 881 rows matched an independent Poppler extraction in source sequence after whitespace normalization. Source field counts are strict. Original spelling and case, including SCA-LJj, are retained. PDF pages 19 and 23 were visually inspected for book/signature and numbered sketch boundaries.

## Numbering discrepancy

On checklist page 6, ARS-25 is printed for **both Jar Jar Binks and Darth Vader**, and ARS-23 is absent. These are separate named subjects, not repeated signers. Both are retained with their published number. Internal IDs use reviewed subject suffixes `2025-TSWSO-ROTS-ARS-25-JAR-JAR-BINKS` and `2025-TSWSO-ROTS-ARS-25-DARTH-VADER`. No ARS-23 or inferred correction is created. Both database notes flag the conflict; physical-card numbering remains unverified. The importer refuses unreviewed changes to this exceptional sequence.

## Enumerated subsets

| Subset | Category | Identities |
|---|---|---:|
| Finest Base Set | Base | 75 |
| Chrome Black Base Set | Base | 75 |
| Galactic Antiquities Base Set | Base | 50 |
| 20th Anniversary of Revenge of the Sith | Insert | 25 |
| Power of the Force | Insert | 25 |
| Finest Jedi Knights | Insert | 25 |
| Stellar Signatures Art Reproduction | Insert | 100 |
| Galactic Funk | Insert | 15 |
| Cortosis Metal | Insert | 20 |
| Droid Shadowbox | Insert | 20 |
| Lightsaber Shadowbox | Insert | 20 |
| Civilized Age Art | Insert | 10 |
| Chrome Black Autograph | Autograph | 51 |
| Finest Autograph | Autograph | 49 |
| Stellar Signatures Autograph | Autograph | 54 |
| Cortosis Metal Autograph | Autograph | 11 |
| Trio Autograph | Autograph | 8 |
| Quad Autograph | Autograph | 7 |
| Light Side Ultimate Autograph Book Card | Autograph | 1 |
| Dark Side Ultimate Autograph Book Card | Autograph | 1 |
| Sketchagraphs | Autograph | 39 |
| Stellar Signatures Art Cards | Sketch | 100 |
| Triptych Sketch Cards | Sketch | 25 |

## Odds and variant limits

All 127 rows from the 7-page manufacturer odds PDF are retained. All pack rates are well formed. The 124 rules map only to enumerated subsets. Three general Sketch Card format rows remain evidence without a fabricated finite subject list. Stellar Signatures Sketch Card maps to the checklist's Stellar Signatures Art Cards; Triptych Sketch Card maps to Triptych Sketch Cards. Sketchagraphs remain an autograph category with an explicit subset name.

There are 806 identity placeholder variant records. Pack odds establish no serial cap or universal subject/parallel applicability; no parallel grids or caps are inferred. Printed-card verification and a manufacturer serial-number source can support later variant additions. Art originals and reproductions have different subset IDs. No licensed card images are added.

## Preservation and verification

All 27 earlier metadata records and per-set files, stable IDs and the frozen catalogue.json are unchanged against baseline edcb8f60034b2dec0b5425535b989849e9e3efe7. New totals: 28 sets / 14,320 identities; Star Wars four sets / 3,022; WWE 24 / 11,298 unchanged. The importer is byte-idempotent and rejects conflicting existing identities.

The guarded data-only SQL uses baseline 27 / 13,514, locks catalogue tables, snapshots full catalogue/collection/image rows, refuses conflicts, verifies counts and parent links, and preserves every earlier row. There are no auth, schema, RLS or collector-data writes. The older Masterwork test now asserts its own set count so future additive imports are allowed. Existing Chrome/Galaxy/WWE and category regressions passed locally. New browser coverage checks 806 cards, 125 sketches, two distinct ARS-25 subjects, independent ownership and twenty-signer layout at 320–1440px. Browser results pending. Authenticated private-photo and two-device flows are not implied by guest tests.

## Sources

- [Official product](https://www.topps.com/products/2025-topps-star-wars-smugglers-outpost-hobby-box) — release and title verified.
- [Official checklist](https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2025_Star_Wars_Smugglers_Outpost_Checklist.pdf?v=1787961928) — SHA-256 `6b73423d85bd1735f08b2a10db13833ec5646e48b2e1834a5cb7ca739f5724d6`.
- [Official odds](https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2025_Star_Wars_Smugglers_Outpost_Odds.pdf?v=1787961928) — SHA-256 `96a09d1649f79dff235af447ff10b0545d1a6cd33e823c355ddaa9b7f9da8f79`.
