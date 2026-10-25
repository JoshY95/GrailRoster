# 2026 Topps Chrome Star Wars — import audit

Status: built and locally validated; browser CI and production publication pending.

## Reconciliation

- Official checklist: 31 pages, 1,369 printed card/signature rows in 28 sections, plus 134 artist roster entries.
- Combine 44 duo rows into 22 identities and 57 triple rows into 19 identities.
- Hold five Hidden Gems identities: the combined odds show only Sapphire availability.
- Result: **1,304 Chrome card identities across 27 subsets** (200 base, 857 inserts and 247 autographs).
- Retain 186 odds rows (49 + 49 + 49 + 39), including the final Trio Sapphire entry whose dash cells spill onto page 5.
- Import 151 Chrome subset rules; hold 22 Sapphire-only rows, 10 unenumerated design-variation rows and 3 sketch rules. No subject/parallel Cartesian product.
- One checklist-identity variant per imported card. No card-specific serial numbers are inferred; the Topps box guide supports a subset-level Logofractor /77 rule.

## Imported subsets

| Subset | Card identities |
|---|---:|
| CHARACTERS | 200 |
| CHARACTERS HOTHFRACTOR | 200 |
| CHARACTERS AUREBESH | 200 |
| ANDOR SEASON 2 CHARACTERS | 17 |
| ANDOR SEASON 2 MOMENTS | 12 |
| VISIONS SEASON 3 CHARACTERS | 14 |
| VISIONS SEASON 3 MOMENTS | 9 |
| MANDO AND GROGU CHARACTERS | 26 |
| MANDO AND GROGU MOMENTS | 17 |
| OBLIVION | 16 |
| STORMTROOPER COMMAND | 20 |
| GALAXYS CUTEST | 15 |
| GALATIC MAXIMALISTS | 10 |
| FACTIONS | 10 |
| COSMIC CRYSTALS | 50 |
| BONUS STAGE | 12 |
| KYBER LIGHT | 10 |
| ERAS | 9 |
| REFLECTIONS | 5 |
| COMICFRACTOR | 5 |
| BASE PRINTING PLATE BOOK CARDS I | 200 |
| CHARACTERS AUTOGRAPHS | 182 |
| ANDOR SEASON 2 CHARACTERS AUTOGRAPHS | 14 |
| MANDO AND GROGU CHARACTERS AUTOGRAPHS | 5 |
| VISIONS SEASON 3 CHARACTERS AUTOGRAPHS | 5 |
| DUO AUTOGRAPHS | 22 |
| TRIPLE AUTOGRAPHS | 19 |

## Source handling and limits

Both source PDFs were downloaded from links on the official Topps product page. PDF hashes and all page-addressed normalized rows are retained in sources/chrome-star-wars-2026/checklist.json. Re-fetch the exact URLs to run --verify-pdf; binary PDFs are not part of the runtime bundle. An independent Poppler extraction matched all 1,369 normalized rows after whitespace normalization.

- Checklist: https://cdn.shopify.com/s/files/1/0662/9749/5709/files/CheckList_26SWCM4.pdf?v=1790785945
- SHA-256: c4181d0e48d353b28dbb68a5b9fa5b6ec7b8720b97f428e5491970575bb1e6a8
- Odds: https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2026-09-29_2026-Topps-Chrome-Star-Wars_Odds-2.pdf?v=1790777195
- SHA-256: 3304c072fa00eb23ba6e034d7f047c0be62ca894a99f879e0888741cb7ca9e25
- Release/box guide: https://ripped.topps.com/2026-topps-chrome-star-wars-box-guide/

Preserve printed manufacturer spellings and apparent errors, including PALTE-194, mixed MAG/MAGR autograph prefixes, repeated character names and autograph/base numbering disagreements. The main autograph #114 lists Bronte Carmichael as both signer and character; it remains literal pending a manufacturer correction or card evidence. Do not silently remap it to another numbered card. DEBUT is retained in normalized evidence and does not become a sports rookie flag.

Autograph display names include characters and signers so either can be searched. Repeated multi-signer rows share one identity and one collection key. Card IDs are namespaced 2026-TCSW-<subset>-<printed number>; set categoryId is explicitly star-wars.

Superbox Characters Design Variation and design autograph subjects are not enumerated by this PDF. Sketch artists are a roster, not a finite subject/card checklist. These are documented gaps; do not invent 200 design-variation subjects or one card per artist. Hidden Gems and Kyber Carvings belong to the separate Sapphire review. Pack odds do not certify serial caps or guarantee any subject in every parallel.

Release date: 30 September 2026, explicitly stated by Topps. Hobby, Breaker Delight, Value and Superbox remain formats of this set. 2026 Chrome Galaxy is the next work item.

## Preservation and validation

All 24 existing WWE metadata records, per-set JSON bytes, 11,298 card identities and the frozen compatibility snapshot remain unchanged. One local renderer fallback now uses the parent franchise name instead of labelling a card with no roster as WWE. The new cache version refreshes the category index offline.

Local checks passed: four source/import/SQL tests, six existing Stadium Club tests, catalogue loader/preservation/offline asset-list regression, real-page category DOM tests and import-category contract. Failed intermediate assertions were corrected before this milestone. Full browser CI, database dry-run/commit and live checks are pending. No private collector/photo changes are part of the import.
