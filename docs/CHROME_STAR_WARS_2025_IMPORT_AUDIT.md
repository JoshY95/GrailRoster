# 2025 Topps Chrome Star Wars — import audit

Status: prepared; local checks passed. Browser CI, database application and publication pending.

## Manufacturer reconciliation

Topps product metadata confirms release **20 August 2025**. The official 16-page checklist has **1,272 numbered source rows** across 20 subsets. Thirty duo signer rows become 15 cards; 33 trio signer rows become 11 cards, removing 37 repeated signature rows: **1,235 design identities** (200 base, 840 inserts, 195 autographs).

All numbered rows, all 281 attached DEBUT flags and all 95 five-format odds rows independently matched Poppler text in source sequence after whitespace normalization. Autograph checklist page 12 and the complete odds sheet were visually inspected. DEBUT appears on 65 rows in each of Characters, Printing Plate Book, Hothfractor and Aurebesh, plus 21 single-autograph rows. All flags are preserved in normalized evidence and database notes; none is inferred to be an athlete rookie. The 188 sketch artists remain a roster, not invented card identities.

## Enumerated subsets

| Subset | Category | Identities |
|---|---|---:|
| CHARACTERS | Base | 200 |
| PRINTING PLATE BOOK CARD | Insert | 200 |
| HOTHFRACTOR SHORT PRINT | Insert | 200 |
| AUREBESH SHORT PRINT | Insert | 200 |
| 1975 TRIBUTE | Insert | 50 |
| SKELETON CREW | Insert | 25 |
| ACOLYTE | Insert | 25 |
| UNDERWORLD ODDITIES | Insert | 25 |
| STAR WARS BY THE NUMBER | Insert | 24 |
| GALACTIC GRAFITTI | Insert | 21 |
| BONUS STAGE | Insert | 10 |
| KYBER LIGHT | Insert | 20 |
| REFLECTIONS | Insert | 5 |
| COMICFRACTOR | Insert | 5 |
| ONE WITH THE FORCE | Insert | 5 |
| DOUBLE VISION | Insert | 25 |
| AUTOGRAPH CARDS | Autograph | 122 |
| DUO AUTOGRAPHS | Autograph | 15 |
| TRIO AUTOGRAPHS | Autograph | 11 |
| 1975 TRIBUTE AUTOGRAPH VARIATION | Autograph | 47 |

## Design boundaries

The base, printing-plate book, Hothfractor and Aurebesh programmes each have all 200 manufacturer-listed designs and their own IDs. A printing-plate book is one checklist identity per BC number; it is not expanded into four unenumerated printing-colour cards. The 50 1975 Tribute designs and 47 Tribute autograph designs stay separate. Repeated names with distinct source numbers are retained. Multi-subject insert titles remain one design, and duo/trio signer repeats combine only within the same subset and printed number.

The `2025-TCSW-<subset>-<number>` namespace is separate from Sapphire, Galaxy and 2026 Chrome. DA-MJj retains its exact source case. Regular Chrome's 21 autograph DEBUT flags are source-specific; existing Sapphire data is unchanged. Original wording and spelling, including apparent source errors, are preserved. The new short name includes 2025 to distinguish both Chrome years in filters.

## Five-format odds and unresolved cells

All 95 manufacturer rows retain Hobby, Breaker, Value Box SE, Value Box EA and Value Box CEE cells, including dashes. Ninety-one subset rules map to numbered designs; four sketch-format rows remain source evidence without fabricated subject lists. Odds heading Outerworld Oddities is mapped to the checklist's Underworld Oddities, and Star Wars By The Numbers maps to the singular checklist heading. Exact raw labels remain in normalized evidence.

Five malformed cells remain unresolved and are never silently corrected:

| Odds label | Format | Printed rate |
|---|---|---|
| Characters Kamino Purple Refractor Parallel | Value Box SE | 1::590 |
| Kyber Light Superfractor Refractor Parallel | Value Box SE | 1:1,942400 |
| Single Autographs Superfractor Refractor Parallel | Value Box EA | 1:38,4384 |
| Trio Autographs | Value Box EA | 1:38,4384 |
| Tribute to '75 Autograph Variation Superfractor Refractor Parallel | Value Box EA | 1:38,4384 |

Other rates, including unusual ungrouped digits, remain exactly as printed. Syntax validation is not a claim that the manufacturer's numerical values are correct. There are 1,235 identity placeholder variant records. No serial caps, plate-book print runs or card-specific subject/parallel grids are inferred from odds. No licensed reference images are added.

## Preservation and validation

All previous 30 metadata records and set bundles, stable IDs and frozen compatibility snapshot are unchanged against baseline fd8235e6fc2cc5238a9619247147918b58c7c695. New totals: 31 sets /16,206 identities; Star Wars seven sets /4,908, WWE unchanged 24 /11,298. Importer reruns are byte-identical and refuse existing conflicting identities.

Focused source/programme/odds/preservation tests and all existing source/catalogue/category regressions passed locally. New browser checks add independent regular Chrome ownership alongside Sapphire, all 840 inserts, Hothfractor HF-200, Carrie Fisher's Tribute autograph and a single dual-signer identity. Existing guest, Vault, offline and responsive checks remain enabled. Local Chromium is known unavailable; use CI. Guarded SQL baseline is 30 sets /14,971 cards and protects all earlier catalogue, collection and image rows. No schema, auth, RLS or collector-data writes. Authenticated private-photo/two-device flows are not implied by guest checks.

## Sources

- [Official product](https://www.topps.com/products/2025-topps-chrome-star-wars-hobby-box).
- [Official checklist](https://cdn.shopify.com/s/files/1/0662/9749/5709/files/Checklist_-_2025_Topps_Chrome_Star_Wars_cbb6bdaf-a6f0-4435-9bcc-59f4b3497263.pdf?v=1787946290) — SHA-256 `6d57e25e73ae7762f7fbf425a580723c74efb628e4e727675f2db02696f04b28`.
- [Official odds](https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2025_Topps_Chrome_Star_Wars_Odds.pdf?v=1787948202) — SHA-256 `2871e2380c61e5e6eacce1b5e723fcccb5f4991dfbb3c7be9290e7d7d9eb7527`.
