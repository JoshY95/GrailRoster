# 2025 Topps Chrome Star Wars Galaxy — import audit

Status: imported and published via PR #11. Browser CI 40201920499 and Pages 40202136681 succeeded.

## Manufacturer reconciliation

Topps product metadata confirms release **10 December 2025**. The 11-page official checklist has 325 numbered source rows. Twenty dual signer rows become ten cards, 15 triple rows become five cards, and 16 quad rows become four cards, removing 32 repeated signer rows: **293 identities / 15 subsets** (100 base, 103 inserts, 20 McQuarrie buybacks, 70 autographs including two autograph buybacks).

All 325 source rows and all 93 odds rows independently matched Poppler text in source sequence after whitespace normalization. PDF page 5 was visually inspected for puzzle credits and buyback references, and the complete odds sheet was inspected. The 154 sketch artists and seven Blank Canvas artists remain separate rosters, not invented cards. Original titles, spelling and credits are retained, including Chrstian Benavides and source archive credits.

## Enumerated subsets

| Subset | Category | Identities |
|---|---|---:|
| BASE CARDS | Base | 100 |
| GALACTIC INSPIRATIONS | Insert | 15 |
| DUEL ON MUSTAFAR | Insert | 15 |
| POWER OF THE FORCE | Insert | 15 |
| FEAR THE DARKSIDE | Insert | 15 |
| TOPPS CHROME LAYERS RALPH MCQUARRIE ORIGINAL CONCEPT ART | Insert | 15 |
| COMICFRACTOR | Insert | 5 |
| ONE WITH THE FORCE | Insert | 5 |
| ORIGINAL ART PUZZLE CARDS | Insert | 18 |
| STAR WARS GALAXY RALPH MCQUARRIE BUYBACKS | Buyback | 20 |
| GALAXY AUTOGRAPHS | Autograph | 49 |
| DUAL AUTOGRAPHS | Autograph | 10 |
| TRIPLE AUTOGRAPHS | Autograph | 5 |
| QUAD AUTOGRAPHS | Autograph | 4 |
| AUTOGRAPH BUYBACKS | Autograph | 2 |

## Identity boundaries and source gaps

Buyback rows explicitly supply new MCQ/AB checklist codes and the original year, series and printed number. Both fields are joined as a source reference (e.g. `1993 Star Wars Galaxy Series 1 #15`); the original number is not treated as an artist or actor. MCQ-1 and AB-15 are separate editions with separate stable IDs. No original artwork title, autograph signer or serial cap is inferred. Three source columns are mandatory for base/credited art/autograph rows; two for uncredited Layers/Comicfractor/One With The Force rows. Raw fields and page evidence are retained in normalized source.

IDs use `2025-TCSWG-<subset>-<printed-number>` and cannot collide with the 2026 Galaxy or other Star Wars sets. The new short name includes 2025 so both Galaxy years are clear in filters. Existing set names and IDs remain unchanged.

All 93 manufacturer odds rows are retained; 88 subset rules map to enumerated designs, with five unenumerated Sketch/Blank Canvas formats left as source evidence. `BASE. ATOMIC REFRACTOR` maps to Base Cards with its printed label retained. The final Layers row repeats `TOPPS CHROME LAYERS ORIGINAL ART` at 1:49,018 after the first unsuffixed row at 1:432. The later row is explicitly marked **Unspecified edition / unresolved**, not assumed to mean Superfractor or base. `SKETCH CARDS BLACK FOIL` prints `1;11,140`; the malformed rate remains unresolved, without replacing the semicolon or interpreting it as a valid pack rate. Other original label spelling is retained.

There are 293 identity placeholder variant records. No subject/parallel grids or serial caps are inferred from odds. Missing odds for checklist-only designs do not invent pack rates. No licensed reference images are added.

## Preservation and validation

All 28 earlier set metadata records, set bundles and stable IDs, and the frozen compatibility snapshot are unchanged against baseline d267bd9e7d490f75246c9fd03ee5742e36186d9c. New totals: 29 sets / 14,613 identities; Star Wars five sets / 3,315, WWE 24 / 11,298 unchanged. Importer reruns are byte-identical and refuse conflicting existing rows.

Focused source/identity/odds/preservation tests and all existing source/catalogue/category regressions passed locally. New browser checks cover a separately owned 2025 Galaxy #1 alongside 2026 #1, the 20-card buyback filter and Q-JNJF as one four-signer card. Existing responsive, guest, Vault and offline checks remain enabled. Local Chromium is unavailable; CI is required. Guarded SQL baseline is 28 sets / 14,320 cards and protects every previous catalogue, collection and image row. No schema/auth/RLS or collector-data writes. Authenticated two-device/private-photo flows are not implied by guest checks.

## Sources

- [Official product](https://www.topps.com/products/2025-star-wars-chrome%C2%AE-galaxy-hobby-box).
- [Official checklist](https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2025_Star_Wars_Chrome_Galaxy_Checklist.pdf?v=1787955654) — SHA-256 `d1e6218b693137bfd7ecff80278b7af5d713786eff7bff7d7336f47106a130a4`.
- [Official odds](https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2025_Star_Wars_Chrome_Galaxy_Odds.pdf?v=1787955654) — SHA-256 `337cee9d893df3768b263a001af37fc9f99d1f9eb5d8b48695f793c0c10cd1b2`.

## Published verification

Guarded SQL passed a rolled-back dry run and committed successfully. A second committed import left complete-row digests identical across all eight catalogue/collection/image tables. Collections remain 30 with digest `6648329147d88b88ed9e52eaac40cfa9`; images remain empty. Browser CI passed all source/category, guest, Vault, offline, five-set ownership and responsive checks. PR #11 feature `fa2134a1e55b58dac2e2497886c7403bbbbdd80f` merged as `fcaba490bcbcf3de3e373829c69cf556f1551617`. All 42 live runtime/index/set files match validated source bytes. Live guest UI confirmed five sets / 3,315 cards, 2025 Galaxy 293 / 15, Q-JNJF as one four-signer card and AB-15 preserving the 1993 Series 1 #15 reference. Existing cache refreshed after activation and a normal reload. Receipt: `docs/CHROME_STAR_WARS_GALAXY_2025_RELEASE.json`.
