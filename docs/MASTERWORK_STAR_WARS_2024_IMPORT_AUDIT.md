# 2024 Topps Star Wars Masterwork — import audit

Status: imported and published via PR #17. Browser CI 40262668991 and Pages 40262846111 succeeded.

## Manufacturer reconciliation

The official 17-page v2 checklist yields **337 identities /16 subsets** from 363 numbered subject/signer rows. All rows, 17 printed multi-signer labels, 182 sketch artists and 76 odds independently matched Poppler layout text. Checklist pages 6–7 and the odds sheet were visually inspected.

| Subset | Identities |
|---|---:|
| BASE CARDS | 100 |
| BEHIND THE NEW SCENES | 23 |
| JOURNEY OF AHSOKA TANO | 20 |
| THE GRAND ADMIRAL | 20 |
| MARVEL COMIC COVERS | 33 |
| FORCE SPIRITS | 6 |
| ARTOO-DETOO | 10 |
| SEE-THREEPIO | 10 |
| ON CARD AUTOGRAPHS | 50 |
| DUAL AUTOGRAPHS | 9 |
| TRIPLE AUTOGRAPHS | 4 |
| QUAD AUTOGRAPH BOOK CARD | 3 |
| PEN AUTOGRAPH RELICS | 31 |
| STORMTROOPER ARMOR AUTOGRAPH VARIATION | 2 |
| STORMTROOPER ARMOR | 8 |
| RISE OF THE RESISTANCE RELICS | 8 |

Totals: 100 base, 122 inserts, 66 autograph designs, 33 autograph relics and 16 relics. Nine duals combine 18 signer rows, four triples combine 12, and three quad books combine 12. Printed labels are stored outside their physical reading order. Their sorted page/vertical positions are checked against the corresponding signer group. DA-HR repeats across pages 6–7, representing one Rosario Dawson /Hayden Christensen card. Its repeated label is not a second identity. QAB-MPPH is one four-signer design.

## Identity, artifacts and source limits

Namespace: `2024-TSWMW-<subset>-<printed number>`. Matching 2024/2025 numbers remain separate stable IDs. All source spelling is preserved, including Oppurtinity, Domnall Gleeson and Richard Grant. Stormtrooper relics S-1/S-2 share the same printed person but have distinct numbers; both remain separate. Printed film/show contexts and Stormtrooper role metadata are retained in source evidence/database notes, without inferring material or autograph status from a person name.

There are 182 actual sketch-artist entries, all unique as printed, on pages 9–12. Pages 13–15 are blank. Pages 16–17 contain 16 detached story-context fragments at negative x coordinates; some are visibly clipped. These are retained as PDF artifacts, never artists or new cards, and are not silently attached to rows with missing context. No original sketch-card enumeration is claimed.

Topps' product title is **2024**, while Available From is **16 April 2025** and generic Product Year metadata says 2025. Keep the title year and actual release date, without creating another annual set.

All 76 single-column odds rows are retained. 72 become numbered-subset rules; four sketch formats remain source-only. Aliases map odds DUO/TRIO to checklist DUAL/TRIPLE, MARVEL COMICS COVERS to MARVEL COMIC COVERS, PEN AUTOGRAPHS RELICS to PEN AUTOGRAPH RELICS and the singular Rise of the Resistance label to its parent. The clipped `BLAC` label remains as printed, without guessing its missing character. That label touches its rate in Poppler extraction; independent comparison ignores whitespace only. All serial caps are null; 337 variant records are checklist identity placeholders. No subject/parallel grid, missing metal edition, sketch ID or card image is invented.

## Preservation and validation

All prior 33 metadata records, set bundles and stable IDs, plus the frozen compatibility snapshot, remain unchanged against 12c336b170e5f5deb09e9794dc7536d307edfc87. Totals: 34 sets /17,157 identities; Star Wars 10 /5,859; WWE unchanged 24 /11,298. Reruns are byte-identical; conflicts are rejected.

Five focused tests and all nine existing Star Wars source/import suites, Stadium Club, split catalogue, category import and category DOM regressions passed locally. Earlier Meiyo totals now permit additive future sets while retaining full byte/metadata preservation checks. Browser coverage adds independent 2024/2025 Masterwork ownership, 33 autograph-relic and 66 autograph filters, cross-page DA-HR pairing and the four-signer QAB-MPPH book. Existing guest, Vault, real offline reload and responsive checks remain enabled. Known unavailable local Chromium was not retried; browser CI passed.

Guarded SQL `supabase/corrections/2026-10-26-star-wars-masterwork-2024.sql` passed rolled-back dry run, committed import and an identical second application across all eight full-row table digests. Database: 34 sets /17,157 cards /38,518 variants /587 subsets /2,018 rules /95 sources. All 30 collection rows retain 6648329147d88b88ed9e52eaac40cfa9; images remain empty. No collector, image, auth, RLS or schema writes occurred. Authenticated private-photo/two-device checks were not rerun.

## Sources

- [Official product](https://uk.topps.com/products/2024-topps%C2%AE-masterwork-star-wars-master-box) — title and release date.
- [Official v2 checklist](https://cdn.shopify.com/s/files/1/0739/2015/1805/files/STW2456-2024StarWarsMasterworkChecklistv2.pdf?v=1787909664) — SHA-256 `932dcd6b76c33386cea162c7b79ad49749e301435210b941c26d7e16c55e14d2`.
- [Official odds](https://cdn.shopify.com/s/files/1/0739/2015/1805/files/2024StarWarsMasterworkOdds.pdf?v=1787909664) — SHA-256 `14398995d3175045f2323d8383122a74ef9b54b7c635e67f03affb34ec88f832`.

Next: SW-016 — 2024 Topps Star Wars Hyperspace. Topps product metadata records 19 February 2025: https://www.topps.com/products/2024-topps-star-wars-hyperspace-hobby-box . Follow with the earlier 2024 Galactic Antiquities release, subject to its own date verification.

## Published verification

Feature 83b2c92fcc645ace22c6bd83612ffe5b5c2369ae passed CI 40262668991: all source/catalogue/category checks, guest, Vault, real offline reload, ten-set ownership isolation, separate 2024/2025 Masterwork ownership, filters, cross-page dual/quad identities and responsive widths. PR #17 merged as 319b1a17ecf2f52d68ce509bf5df5509def3f4df. Pages 40262846111 succeeded. All 47 live runtime/index/set assets match validated source byte-for-byte. Live guest UI was not separately rerun; the deployed runtime assets are identical to those exercised by browser CI. Receipt: docs/MASTERWORK_STAR_WARS_2024_RELEASE.json. Authenticated private-photo/two-device flows remain unrerun.
