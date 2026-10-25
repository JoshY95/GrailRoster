# 2025 Topps Chrome Star Wars — import audit

Status: built and locally validated; browser CI and production import/publication pending.

## Manufacturer reconciliation

Topps product metadata confirms release **20 August 2025**. The official 16-page checklist contains 1,272 numbered subject/signer rows, reconciling to **1,235 identities across 20 subsets**. Thirty duo rows become 15 cards; 33 trio rows become 11 cards. All 1,272 rows, 281 attached DEBUT marks, 188 sketch artist names and all 95 odds rows independently matched Poppler text in source order after whitespace normalization. Checklist page 13 and the full odds sheet were visually inspected.

| Subset | Identities |
|---|---:|
| CHARACTERS | 200 |
| PRINTING PLATE BOOK CARD | 200 |
| HOTHFRACTOR SHORT PRINT | 200 |
| AUREBESH SHORT PRINT | 200 |
| 1975 TRIBUTE | 50 |
| SKELETON CREW | 25 |
| ACOLYTE | 25 |
| UNDERWORLD ODDITIES | 25 |
| STAR WARS BY THE NUMBER | 24 |
| GALACTIC GRAFITTI | 21 |
| BONUS STAGE | 10 |
| KYBER LIGHT | 20 |
| REFLECTIONS | 5 |
| COMICFRACTOR | 5 |
| ONE WITH THE FORCE | 5 |
| DOUBLE VISION | 25 |
| AUTOGRAPH CARDS | 122 |
| DUO AUTOGRAPHS | 15 |
| TRIO AUTOGRAPHS | 11 |
| 1975 TRIBUTE AUTOGRAPH VARIATION | 47 |

Totals: 200 base, 840 inserts and 195 autograph designs. The printing-plate book, Hothfractor and Aurebesh programmes have their own printed checklist numbers and remain separately identifiable under this regular Chrome parent. No additional product sets are created for packaging formats.

## Identity and source limits

Stable namespace: `2025-TCSW-<subset>-<printed number>`. Regular Chrome remains separate from Sapphire, Galaxy and convention issues. Repeated character names with distinct printed numbers remain separate designs. Mixed-case DA-MJj is retained; duo/trio signer rows combine by subset and printed number only. Reflections starts at R-11, Comicfractor at VC-6 and One With The Force at OF-6; no missing earlier numbers are inferred. Manufacturer spelling, including GALACTIC GRAFITTI and C-3P0, is preserved.

281 attached DEBUT marks remain source metadata and database notes, without converting fictional-character debut marks into athlete rookie flags. The 188 sketch artists remain a roster; unenumerated original sketches are not invented as checklist identities.

All 95 odds rows are retained in normalized source. 91 become subset rules, while four sketch rows remain source-only. The odds label Outerworld Oddities maps to checklist UNDERWORLD ODDITIES; Hoth Ice Blue Frozenfractor Variation maps to HOTHFRACTOR SHORT PRINT. These aliases are documented rather than spawning duplicate identities. Malformed printed rates such as `1::590`, `1:1,942400` and `1:38,4384` are preserved without interpreting or silently repairing them. Pack rates do not establish serial caps or every subject/parallel combination. There are 1,235 identity placeholder variant records. No card images added.

## Preservation and validation

All previous 30 set metadata records and bundles, stable IDs and frozen compatibility snapshot remain unchanged against baseline fd8235e. New totals: 31 sets /16,206 identities; Star Wars seven sets /4,908; WWE unchanged 24 /11,298. Importer reruns are byte-identical and conflicting existing identities are rejected.

Four focused tests and all existing source/catalogue/category import regressions passed locally. Category DOM regression passed locally. Browser coverage adds independent regular Chrome #1 ownership, 840 insert filtering, Hothfractor and R-11 searches, mixed-case duo and a trio design; existing guest/Vault/offline and responsive checks remain enabled. Known unavailable local Chromium was not retried. Guarded SQL baseline is 30 sets /14,971 cards; rolled-back dry run passed count, linkage and full old-row preservation guards. No schema, auth, RLS, collection or image changes. Authenticated private-photo/two-device flows are not implied by guest checks.

## Sources

- [Official product](https://www.topps.com/products/2025-topps-chrome-star-wars-hobby-box).
- [Official checklist](https://cdn.shopify.com/s/files/1/0662/9749/5709/files/Checklist_-_2025_Topps_Chrome_Star_Wars_cbb6bdaf-a6f0-4435-9bcc-59f4b3497263.pdf?v=1787946290) — SHA-256 `6d57e25e73ae7762f7fbf425a580723c74efb628e4e727675f2db02696f04b28`.
- [Official odds](https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2025_Topps_Chrome_Star_Wars_Odds.pdf?v=1787948202) — SHA-256 `2871e2380c61e5e6eacce1b5e723fcccb5f4991dfbb3c7be9290e7d7d9eb7527`.
