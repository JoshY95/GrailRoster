# 2026 Topps Chrome Star Wars Galaxy — import audit

Status: built and locally validated; browser CI, database application and publication pending.

## Reconciliation

- Updated official checklist: 17 pages, 366 numbered artwork/signature rows in 14 sections; 218 sketch artist roster entries are retained separately.
- Repeated autograph rows combine by subset and printed number: 20 dual rows → 10 cards; 27 triple rows → 9 cards; 20 quad rows → 5 cards.
- Result: **323 identities**: 100 base cards, 137 inserts and 86 autograph cards.
- All 366 normalized rows independently matched Poppler text extraction, including long overlapping titles and the overlaid GA-BDH addition.
- All 110 official odds rows are retained; 107 numbered-subset rules are imported. Three sketch foil rules remain source evidence because the artist roster does not enumerate finite card identities.
- One identity placeholder per card; no serial caps or card/parallel cross product inferred from pack odds.

## Subsets

| Subset | Identities |
|---|---:|
| BASE CARDS | 100 |
| DUEL ON CLOUD CITY | 15 |
| ART OF ROGUE ONE | 15 |
| ART OF THE DARK SIDE | 15 |
| GALACTIC ANTHOLOGY | 15 |
| ART OF KNIGHTS OF THE REPUBLIC | 15 |
| TOPPS CHROME LAYERS ORIGINAL ART | 11 |
| COMICFRACTOR | 5 |
| ORIGINAL ART PUZZLE CARDS | 36 |
| FORCE ENERGY | 10 |
| GALAXY AUTOGRAPHS | 62 |
| DUAL AUTOGRAPHS | 10 |
| TRIPLE AUTOGRAPHS | 9 |
| QUAD AUTOGRAPHS | 5 |

## Source and identity decisions

- Checklist: https://cdn.shopify.com/s/files/1/0662/9749/5709/files/26SWCGCHECKLISTUPDATE.pdf?v=1786632392
- SHA-256: 5f1188e5b9569d16b86616b8d61771e1cfbeb5b503743dd99df9304db5585e3e
- Odds: https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2026_Stars_Wars_Chrome_Galaxy.pdf?v=1786638023
- SHA-256: 81c612e3b2ba9164c990abdf2ee91d7fa21661c3253aba34d6054be6b996b7ea
- Official release metadata: https://www.topps.com/products/2026-star-wars-chrome%C2%AE-galaxy-hobby-box

Topps product metadata gives 12 August 2026. Preserve exact product identity separately from 2026 Chrome Star Wars. Source artwork titles and artist credits are retained in normalized JSON; database card notes also retain the artist credit. Display names use the artwork title, or character plus signer for autographs. No sports roster or rookie label is inferred.

The checklist heading omits “Old” from ART OF KNIGHTS OF THE REPUBLIC while the odds sheet uses Art of Knights of the Old Republic. These are reconciled to one subset, retaining source spelling. The source artist credits include “Chrstian Benavides” and “Doug Chaing”; they are not silently rewritten. GA-BDH lists Bryce Dallas Howard with subject “Director”; preserve that literal role rather than inventing a character. The overlaid GA-BDH Form XObject yields duplicate text callbacks, which are deduplicated at rendered-cell level and independently checked against Poppler.

The 36 Original Art Puzzle Cards keep their printed prefixes and numbers within one subset. Artists and repeated artwork titles do not collapse distinct numbers. VC-16–20 overlap regular 2026 Chrome numbering; globally unique 2026-TCSWG IDs and distinct set IDs prevent ownership crossover. Multi-autograph cards retain one collection identity for all signers. Sketch art remains an explicitly unenumerated scope, not one fabricated card per artist.

## Validation and preservation

The 25 existing set bundles, metadata, all 12,602 prior card identities and frozen data/catalogue.json are preserved byte-for-byte. Local source/import, old Chrome/Stadium Club regression, category metadata and real-page DOM checks passed. Browser CI will verify the two actual Star Wars #1 cards retain separate ownership, filtering shows 323 Galaxy cards, category isolation and offline reload. Guarded data-only SQL snapshots existing catalogue and collector/image rows; browser CI, rolled-back dry run, committed import and live verification are pending. Authenticated two-device/private-photo tests are not implied.

Next set: 2025 Topps Star Wars Masterwork (2025 product label, released in 2026). Future 2026 Sapphire remains separate.
