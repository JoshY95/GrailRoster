# 2025 Topps Star Wars Masterwork — import audit

Status: imported and published via PR #9. Browser CI 40196453340 and Pages 40196643494 succeeded.

## Manufacturer reconciliation

- 18-page official checklist: 660 numbered subject/signature rows in 19 enumerated subsets; 209 sketch artists retained separately.
- 20 duo rows → 10 cards; 15 trio rows → 5 cards; 20 quad rows → 5 cards; 40 Ultimate Book signer rows → 4 ten-signer cards. These remove 71 repeated signature rows from the identity total.
- **589 identities**: 100 base, 119 inserts, 120 autographs, 113 relics and 137 autograph relics.
- All 660 source rows independently matched Poppler after whitespace normalization. All source cells, including repeated actor-name columns, remain in normalized evidence.
- 680 database variants: 589 identity placeholders plus 91 manufacturer-confirmed non-autograph ROTJ film cel 1/1 editions. Topps explicitly describes those film cels as all 1/1; no caps are extrapolated to the separate autograph relics or other parallels.
- 90 odds rows retained; 84 subset-label rules, of which 83 have well-formed published pack rates and one has an unresolved manufacturer rate. Two buyback programmes and four sketch-format rows remain source evidence, without fabricated finite checklist identities.

## Enumerated subsets

| Subset | Category | Identities |
|---|---|---:|
| CHARACTERS | Base | 100 |
| UNDER DISGUISE | Insert | 26 |
| FALL OF THE CHOSEN ONE | Insert | 24 |
| GALACTIC DIE CUT PODS | Insert | 24 |
| SHORT CIRCUIT | Insert | 26 |
| BB-8 | Insert | 10 |
| LOTHAL JEDI TEMPLE MORTIS GODS PAINTING PUZZLE | Insert | 9 |
| 2025 MASTERWORKS ON CARD AUTOGRAPHS | Autograph | 96 |
| DUO AUTOGRAPHS | Autograph | 10 |
| TRIO AUTOGRAPHS | Autograph | 5 |
| QUAD AUTOGRAPHS | Autograph | 5 |
| ULTIMATE BOOK CARD AUTOGRAPHS | Autograph | 4 |
| SKELETON CREW RELIC | Relic | 10 |
| RELIC CARDS | Relic | 12 |
| ROTJ FILM CEL | Relic | 91 |
| SKELETON CREW AUTOGRAPH RELIC | Autograph Relic | 9 |
| AUTOGRAPH RELIC CARDS | Autograph Relic | 11 |
| ROTJ FILM CEL AUTOGRAPH RELIC | Autograph Relic | 32 |
| PEN AUTOGRAPH RELIC | Autograph Relic | 85 |

## Sources and dates

- Checklist: https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2025_Star_Wars_Masterwork_Checklist.pdf?v=1777400855
- SHA-256: 5369458990a683f342c3983cf517f7820d1b8339c3a76cde03c99456f2904ace
- Odds: https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2025_Star_Wars_Masterwork_Odds.pdf?v=1777320886
- SHA-256: 01f6753be19d9c786158a857563de829eb67d41eabf5e819140f08c8cb9fce2e
- Product/release metadata: https://www.topps.com/products/2025-star-wars-masterwork-hobby-box
- Film cel numbering and scope: https://www.topps.com/pages/topps-masterwork-star-wars

The official product title is 2025 Star Wars Masterwork. The product page states release 3 June 2026 and generic Product Year 2026. Preserve title year 2025 and actual releaseDate 2026-06-03; do not create a second 2026 Masterwork set from the metadata conflict.

## Source decisions and limits

- Skeleton Crew Auto Relic Black has pack odds printed as **1,249**, without a colon. The raw cells and malformed-rate flag remain in evidence; the rule explicitly says unresolved, and no numeric interpretation is asserted.
- The Mortis painting-puzzle odds label is clipped in the visible table. The full checklist heading and underlying text identify it; the visible pack rate is 1:160. Raw cells are retained alongside the reconciliation.
- ROTJ film-cel autograph relic rows repeat the actor name in both columns. Keep the actor-only display name and each original RAR number; do not invent a character or merge several different numbers belonging to the same actor.
- Plain autograph and pen-autograph relic cards can reuse A-AA and other numbers. Distinct subset namespaces keep these as separate collectible identities. All 91 ROC film-cel design numbers remain distinct even when their character names repeat; no additional per-frame identities are invented.
- The four UBC numbers each identify one ten-signer book, including source rows split across pages. No extra identity is created per signer.
- The 10 Years of Masterworks Buybacks and Harrison Ford Buyback On Card Autos headings have no enumerated cards. Sketch names are an artist roster, not a finite design checklist. These remain documented scope gaps.
- Relic material/production attribution is retained in normalized source and database notes, including manufacturer spellings such as Missle: Andor. No images, pricing or additional likeness rights are assumed.

## Preservation and verification

All 26 prior metadata records, per-set bundle bytes, 12,925 card identities and frozen data/catalogue.json remain unchanged against baseline f16adeee60e5cab1d5c1f2934bfa6d4dd2378e21. Focused source/import and existing category/catalogue regressions passed locally. Browser CI passed Masterwork ownership, autograph-relic filtering, repeated actor-name designs, ten-signer book rendering at 320–1440px and offline/category isolation. Guarded SQL passed a rolled-back dry run, committed successfully and a second committed run left all eight complete-row digests unchanged. All 30 collections retain digest 6648329147d88b88ed9e52eaac40cfa9; images remain empty. All 40 production assets match validated source. Live guest UI confirmed three Star Wars sets / 2,216 cards, Masterwork 589 / 19 subsets and one UBC-456 identity with ten signers, after one normal reload of the old cached session. Authenticated two-device/private-photo flows were not rerun. Receipt: docs/MASTERWORK_STAR_WARS_2025_RELEASE.json.

Next set: 2025 Topps Star Wars Smugglers Outpost.
