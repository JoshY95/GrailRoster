# 2025 Topps Star Wars Meiyo — import audit

Status: imported; browser CI and publication pending.

## Verified designs and sources

The official eight-page Hobby checklist contains 280 subject/signer rows and 13 centered dual labels, forming **267 identities across 22 subsets**. The 13 dual labels occur at the end of PDF object order and are associated with their two signer rows using their vertical coordinates, never object order. Every row and all 13 label-to-pair mappings independently matched Poppler layout text. The 25 sketch artist names and 99 two-format odds rows also independently matched. Checklist page 6 and odds page 2 were visually inspected.

| Subset | Identities |
|---|---:|
| REBEL ALLIANCE BASE | 25 |
| GALACTIC EMPIRE BASE | 25 |
| THE RESISTANCE BASE | 25 |
| FIRST ORDER BASE | 25 |
| REBEL HONOR | 10 |
| IMPERIAL HONOR | 10 |
| RESISTANCE HONOR | 10 |
| FIRST ORDER HONOR | 10 |
| REBEL HONOR DIECUT VARIATION | 10 |
| IMPERIAL HONOR DIECUT VARIATION | 10 |
| RESISTANCE HONOR DIECUT VARIATION | 10 |
| FIRST ORDER HONOR DIECUT VARIATION | 10 |
| CHROME STICKERS | 10 |
| STAR WARS JAPANESE POSTER VARIANTS | 10 |
| UKIYO E | 4 |
| MEDAL OF YAVIN DIECUT | 3 |
| CHROME AUTOGRAPHS | 22 |
| CHROME DUAL AUTOGRAPHS | 13 |
| REBEL HONOR DIECUT AUTOGRAPH VARIATION | 6 |
| IMPERIAL HONOR DIECUT AUTOGRAPH VARIATION | 5 |
| RESISTANCE HONOR DIECUT AUTOGRAPH VARIATION | 7 |
| FIRST ORDER HONOR DIECUT AUTOGRAPH VARIATION | 7 |

Totals: 100 base, 40 separately numbered die-cut variations, 67 inserts and 60 autograph designs. Each base faction has 25 cards. Repeated poster titles at distinct MP numbers remain distinct designs. Manufacturer spelling is retained, including C-3P0, Obi Wan-Kenobi, Wicket W. Warrick, Domnhall Gleeson and BLACK RREFRACTOR. Runtime/database namespace: `2025-TSWM-<subset>-<printed number>`. Base faction metadata is retained in roster; signers remain searchable.

## Format, date and completeness limits

This import includes all identities in the official Hobby checklist. Ukiyo E is Hobby/online-exclusive. The official combined odds/guide confirms Celebration-exclusive Manga Madness, but Topps' current index, product and brand links all expose the Hobby checklist without its card-by-card Manga list. No authoritative manufacturer/distributor Manga identity list was located. Secondary candidates exist but remain unimported. Four Manga odds rows are retained as source-only. This release is **not certified as a complete Celebration checklist**. No fake IDs, guessed Manga subjects or caps are created. Original sketches remain an artist roster.

The catalogue releaseDate is **4 May 2025**, explicitly shown as Available From on Topps' Hobby product. Earlier Celebration availability is described in the official brand history/guide without using a guessed convention release day. This is the general-public release sorting date, not a claim that May 4 was the first card sold anywhere. Hobby and Celebration packaging do not duplicate shared identities into separate sets.

All 99 odds rows retain both format columns and dashes. 91 become subset rules; four sketch and four Manga rows remain source-only. The Topps collector guide explicitly confirms the base ladder: Purple /99, Black /75, Blue /50, Green /25, Red /10, Foilfractor 1/1. These are 24 base subset rules across four factions. All remaining caps are null, and all 267 variant rows are checklist identity placeholders. No per-card applicability grids or autograph caps are inferred.

## Preservation and checks

All previous 32 metadata records and set bundles, stable IDs and frozen compatibility snapshot remain unchanged against 502153f024e72fbb84531b3de81d04a6ad3a99a4. Totals: 33 sets /16,820 cards; Star Wars nine sets /5,522; WWE unchanged 24 /11,298. Conflicting identities are rejected; reruns leave existing bytes unchanged.

Four focused tests and all eight existing Star Wars source/import suites, Stadium Club, split catalogue, category import and real-page category DOM regressions passed locally. Earlier Hyperspace total assertions now permit additive future sets while retaining full prior metadata/byte-preservation checks. Browser coverage adds independent Meiyo faction ownership, 40 variation/67 insert/60 autograph filters, UK-4 Grogu and the correctly paired DA-H dual; existing guest, Vault, offline and responsive checks remain. Known unavailable local Chromium was not retried; CI pending.

Guarded SQL `supabase/corrections/2026-10-26-star-wars-meiyo-2025.sql` passed rolled-back dry run, committed import and an identical second application across all eight full-row digests. Database totals: 33 sets /16,820 cards /38,181 variants /571 subsets /1,946 rules /92 sources. All 30 collection rows retain 6648329147d88b88ed9e52eaac40cfa9; images remain empty. No collector, image, auth, RLS or schema writes. Authenticated private-photo/two-device checks were not rerun.

## Sources

- [Official Hobby product](https://www.topps.com/products/2025-topps-star-wars-meiyo-hobby-box) — May 4, 2025 general-public date.
- [Official checklist](https://cdn.shopify.com/s/files/1/0662/9749/5709/files/STW2566-2025StarWarsMeiyoChecklist_Hobby.pdf?v=1787940399) — SHA-256 `e51c7fe9a1f83854fd050ca201ec3a4839f473d76170b3b093a90c74b669dfc9`.
- [Official two-format odds](https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2025StarWarsMeiyoOdds.pdf?v=1787940399) — SHA-256 `945e239b4f7c46498c1120766fc55f1ef6162633c91605e69c19d28f2feb1d96`.
- [Official collector guide](https://ripped.topps.com/how-to-collect-2025-star-wars-meiyo-product/) — base caps and format exclusives.
- [Official brand history](https://ripped.topps.com/brand-history-topps-star-wars-meiyo-product/) — earlier Celebration availability.

Next: SW-014 — 2024 Topps Star Wars Masterwork (Topps UK product Available From 16 April 2025), before the earlier 2024-labelled Hyperspace and Galactic Antiquities. Verify the rest of the 2024 queue by actual release dates when that work begins.
