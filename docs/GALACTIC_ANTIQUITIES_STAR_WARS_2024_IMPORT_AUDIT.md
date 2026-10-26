# 2024 Topps Star Wars Galactic Antiquities — import audit

Status: imported and published via PR #19. Browser CI 40295521725 and Pages 40295773056 succeeded.

## Manufacturer reconciliation

The official five-page checklist contains **177 subject/signer rows forming 165 numbered designs /10 subsets**. Every printed number and source field, all 47 artist names and all 47 odds labels/rates independently match Poppler extraction in source order, ignoring whitespace only. The checklist's third page and odds pages 1 and 3 were visually inspected. Long Stephen "Thundercat" Bruner rows wrap in Poppler layout extraction; the complete name and The Modifier subject are preserved.

| Printed subset heading | Identities |
|---|---:|
| CHARACTERS | 60 |
| METAL CHARACTERS | 30 |
| PREQUEL TRILOGY AUTOGRAPHS | 8 |
| ORIGINAL TRILOGY AUTOGRAPHS | 8 |
| SEQUEL TRILOGY AUTOGRAPHS | 10 |
| FRAMED AUTOGRAPHS | 11 |
| AUTOGRAPH BOOK CARD | 2 |
| WOOD AUTOGRAPHS | 11 |
| BESKAR METAL AUTOGRAPHS | 8 |
| 1977 STAR WARS SERIES 1 TRIBUTE AUTOGRAPHS | 17 |

Totals: 90 base designs and 75 autograph designs. Characters #1–60 and Metal Characters #1–30 are separate numbering programmes. The two books BC-O and BC-X each have seven signer rows, combined into one identity per printed number. Namespace `2024-TSWGA-<subset>-<printed number>` prevents collisions across subsets, years and existing releases. Screen titles remain searchable in the runtime/database roster field. All 47 oversized original-art names remain an artist roster; no unnumbered sketch identities are invented. No licensed card images added.

## Source anomalies and limits

The manufacturer's trilogy headings do not match the expected film affiliations of their subjects: PREQUEL includes Andy Serkis / Supreme Leader Snoke, ORIGINAL includes Ahmed Best / Jar Jar Binks, and SEQUEL includes Freddie Prinze Jr. / Kanan Jarrus. Printed headings, subjects, signers, spelling and numbers are retained without factual reassignment. Base #46 is Q’ira; autograph Qi'ra spellings remain as printed.

The four-page odds PDF separates **47 labels on pages 1–2** from **47 corresponding Hobby rates on pages 3–4**. Both columns match independently and pair by ordered rows. All 47 pairs remain normalized evidence. The 15 AUTOGRAPHS A/B/C DESIGN rows are source-only because the manufacturer does not explicitly map these labels to the trilogy checklist headings. One oversized sketch rate is also source-only. The other 31 rows become verified subset rules. The book Gold rate is 1:1,009. Pack rates do not establish serial caps or every subject/parallel combination; all 165 variants are checklist identity placeholders with null caps.

Topps uses a 2024 title, generic Product Year 2025 and **Available From 5 February 2025**. Keep the title year and actual date, without creating another annual product.

## Preservation and validation

All previous 35 set metadata records, bundles and IDs plus the frozen compatibility snapshot remain unchanged against `4543c5cef7fcc6339cf6c06b5fa2872afedacd8d`. Local totals: 36 sets /17,648 cards; Star Wars 12 /6,350; WWE unchanged 24 /11,298. Reruns are byte-identical; conflicts and missing source rows are rejected.

Five focused checks pass and cover complete identities, seven-signer books, independent base numbering, source anomalies, exact odds pairing, deferred design mapping, no inferred caps, preservation, idempotency and guarded SQL. All eleven existing Star Wars suites, Stadium Club, catalogue split, category import and DOM regressions passed locally. Browser coverage adds separate regular/metal ownership, 90 base /75 autograph filters, printed trilogy headings, signer searches, both seven-signer books and 320–1440px layout. Guest, Vault and real offline reload remain enabled. Known unavailable local Chromium was not retried; browser CI passed before merge. Authenticated private-photo/two-device flows are not rerun.

The generated SQL `supabase/corrections/2026-10-26-star-wars-galactic-antiquities-2024.sql` uses the shared additive transaction with a 35-set /17,483-card baseline. It snapshots all eight catalogue/collection/image tables, rejects conflicts, and verifies counts, linkage and complete prior-row preservation. It performs no collector, image, auth, RLS or schema writes.

## Sources

- [Official product](https://www.topps.com/products/2024-topps-star-wars-galactic-antiquities) — title and availability.
- [Official checklist](https://cdn.shopify.com/s/files/1/0662/9749/5709/files/STW2384-2024StarWarsGalacticAntiquitiesChecklist.pdf?v=1787936593) — SHA-256 recorded in normalized source evidence.
- [Official odds](https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2024StarWarsGalacticAntiquitiesOdds_d1b92e48-e844-45cf-8291-80b194aa931a.pdf?v=1787936593) — SHA-256 recorded in normalized source evidence.

Next: SW-015 — 2024 Topps Star Wars High-Tek, official Available From 8 January 2025: https://www.topps.com/products/2024-topps-star-wars-high-tek-hobby-box .

Database dry run passed and rolled back with all eight baseline digests unchanged. The committed import and a second committed application passed; every full-row digest was identical on repeat. Totals: 36 sets /17,648 cards /39,009 variants /607 subsets /2,105 rules /101 sources. All 30 collections retain digest `6648329147d88b88ed9e52eaac40cfa9`; reference images remain empty.

## Published verification

Feature `eb49a838182ad17fc01bf9dcb1aebb7414fe38c7` passed CI 40295521725 (job 121480523223): all source/catalogue/category checks, guest, Vault, real offline reload, twelve-set ownership isolation, separate regular/metal ownership, filters, printed headings, signer searches, both seven-signer books and responsive widths. PR #19 merged as `adf21b2c4570f5b965cbe576371e7ccce2e1ca8a`. Pages 40295773056 succeeded. All 49 live runtime/index/set assets match tested source byte-for-byte. Live guest UI was not separately rerun; browser CI exercised identical deployed runtime assets. Receipt: docs/GALACTIC_ANTIQUITIES_STAR_WARS_2024_RELEASE.json. Authenticated private-photo/two-device flows remain unrerun.
