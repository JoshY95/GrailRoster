# 2026 Topps Stadium Club WWE — manufacturer reconciliation

Checked 24 October 2026. Imported locally and synchronized to Sydney after validation. Published via PR #5 and merge 1ec1a2a; GitHub Pages run 40085538149 succeeded.

## Authoritative evidence

- [Manufacturer checklist, 21 pages](https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2026_Topps_Stadium_Club_WWE_-_Checklist.pdf?v=1791221305); SHA-256 `e7fc883049de24ced4f271f75d432f49a4c3ac17155ab0ac12c0116c2940144d`.
- [Manufacturer odds, 3 pages](https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2026_Topps_Stadium_Club_WWE_Odds.pdf?v=1791212522); SHA-256 `714fdd3df3824ec6e2c175a6ab3ae867964e8d12d893a72369f59bb9fe8fb34f`.
- [Topps collector guide](https://ripped.topps.com/2026-topps-stadium-club-wwe-cards-collector-guide/) confirms October 23 release and illustrated numbered editions.
- Normalized rows, original page numbers and all 122 odds entries: `sources/stadium-club-wwe-2026/checklist.json`. Regenerate/check extraction with `python3 scripts/add_2026_stadium_club_wwe.py --verify-pdf /path/to/official.pdf` (pdfplumber). Text-flow extraction preserves subjects whose names overlap the roster column; layout-based extraction garbles several names.

## Reconciliation

**938 printed subject rows − 8 repeated second-signer rows = 930 physical card identities in 25 subsets.** The paper and Chrome 1–200 programmes are separate. Triumvirates numbers remain distinct even when subjects repeat. No separate SP/SSP image-variation or relic checklist is present in this PDF; none was invented.

| Subset | Category | Printed number prefix | PDF pages | Source rows | Unique identities | Notes |
| --- | --- | --- | --- | ---: | ---: | --- |
| BASE CARDS | Base | 1–200 | 1–4 | 200 | 200 |  |
| CHROME BASE CARDS | Base | 1–200 | 5–8 | 200 | 200 |  |
| BEAM TEAM | Insert | BT | 8–9 | 20 | 20 |  |
| INKED | Insert | INK | 9–9 | 25 | 25 |  |
| CONCENTRATION | Insert | C | 9–10 | 25 | 25 |  |
| THE AFTERMATH | Insert | AM | 10–10 | 25 | 25 |  |
| MAIN STAGE | Insert | MS | 10–11 | 25 | 25 |  |
| TRIUMVIRATES | Insert | TV | 11–12 | 60 | 60 |  |
| TRIUMVIRATES NICKNAME | Insert | TVN | 12–13 | 39 | 39 |  |
| BASE CARDS AUTOGRAPH VARIATION | Autograph | SCA | 13–15 | 91 | 91 |  |
| BASE CARDS CHROME AUTOGRAPH VARIATION | Autograph | SCCA | 15–17 | 89 | 89 |  |
| INKED AUTOGRAPHS | Autograph | INK | 17–17 | 17 | 17 |  |
| THE AFTERMATH AUTOGRAPHS | Autograph | AMA | 17–17 | 18 | 18 |  |
| DUAL AUTOGRAPHS | Autograph | DA | 17–18 | 16 | 8 | Two signers per numbered card; combined into one identity. |
| MAIN STAGE AUTOGRAPHS | Autograph | MRA, MSA | 18–18 | 17 | 17 | Source prints MRA-RSV for Rusev; retained literally. |
| ABSTRACT AUTOGRAPHS | Autograph | AA | 18–18 | 15 | 15 |  |
| CONCENTRATION AUTOGRAPHS | Autograph | CA | 18–19 | 14 | 14 |  |
| BASE CARDS AUTOGRAPH VARIATION II | Autograph | SCA | 19–19 | 24 | 24 |  |
| STONE COLD STEVE AUSTIN 30TH ANNIVERSARY AUTOGRAPHS | Autograph | SCA | 19–19 | 2 | 2 |  |
| DUDLEY BOYZ 30TH ANNIVERSARY AUTOGRAPHS | Autograph | DUD | 19–19 | 2 | 2 |  |
| CM PUNK 20TH ANNIVERSARY AUTOGRAPHS | Autograph | CMP | 19–19 | 3 | 3 |  |
| THE ROCK 30TH ANNIVERSARY AUTOGRAPHS | Autograph | TRA | 19–19 | 2 | 2 |  |
| NWO 30TH ANNIVERSARY AUTOGRAPHS | Autograph | NWO | 20–20 | 3 | 3 |  |
| LITA 25TH ANNIVERSARY AUTOGRAPHS | Autograph | LIT | 20–20 | 3 | 3 |  |
| TRISH STRATUS 25TH ANNIVERSARY AUTOGRAPHS | Autograph | TRS | 20–20 | 3 | 3 |  |

## Parallel and edition policy

- 117 odds rows map to known checklist subsets and are stored as subset rules with product-format odds. Pack odds never become serial caps. A null cap means unspecified in this evidence, not a declaration that the issue is unnumbered.
- Topps explicitly warns that a listed subject need not appear in every parallel. Therefore no blanket card-by-parallel Cartesian product was generated. All 930 cards receive an unnumbered checklist-identity placeholder; four card-specific numbered editions below are additionally verified (934 database variant rows).

| Card | Edition | Serial cap | Manufacturer evidence |
| --- | --- | ---: | --- |
| Base autograph SCA-USO — Jey Uso | Gold Rainbow Foilboard | 1 | Guide names Jey Uso’s 1/1 under Base Autographs |
| Inked autograph INK-RBR — Rhea Ripley | Gold Rainbow Foilboard | 1 | Guide explicitly describes pictured 1/1 |
| Abstract autograph AA-LIV — Liv Morgan | Gold Rainbow Foilboard | 1 | Guide explicitly describes pictured 1/1 |
| Dual autograph DA-CA — Charlotte Flair / Alexa Bliss | Purple | 25 | Guide names the duo and states 25 copies |

## Deferred manufacturer ambiguities

- **Base Chrome Autographs II:** five odds rows appear, but no section/card identifiers exist in the full 21-page checklist. Do not copy the 24 paper autograph-II names into Chrome. The last two of these odds rows also omit “II”; retain the source labels and defer all five rather than silently reassign them.
- The guide describes Gold Minted and Pearl White /30 under Chrome Autographs; the odds sheet lists these under unsigned Chrome base, not Chrome autographs. This conflicting applicability is not generated.
- Other serial caps and subject-specific parallel availability require clearer manufacturer evidence. They remain unassigned.
- No card images were downloaded or published. Existing placeholders remain.

## Validation

- All 938 normalized rows compared directly with extraction from the hash-verified manufacturer PDF. Visually inspected PDF pages 17–20 for dual-signer boundaries, MRA-RSV, autograph II and anniversary sections.
- Six focused tests cover source reconciliation, complete number ranges, unique IDs/subset-number pairs, rookie/name preservation, rejected malformed input, stable existing records, byte-identical reruns, conflict refusal and variant linkage.
- Catalogue-split regression passes at 24 sets / 11,298 identities, including loader failure handling and every-set offline cache inclusion.
- Combined SQL dry run reached 11,298 cards / 32,568 variants with 30 collections; all preservation guards passed, then transaction rolled back. Committed apply then succeeded, and a second apply changed no table digest. Database/runtime row parity passed for both sets; collection digest stayed 6648329147d88b88ed9e52eaac40cfa9. GitHub CI run 40085112389 passed guest, Vault and real offline reload. Final-head CI run 40085394150 also passed. Production index, every set bundle and sw.js match validated bytes. The guest UI opens the 930-card set and returns a single combined DA-RH identity. Receipt: docs/CATALOGUE_UPDATE_2026_10_24_VERIFICATION.json.
- `sw.js` cache version advanced to v23 so existing installations can refresh the new catalogue.
