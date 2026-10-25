# 2025 Topps Star Wars Hyperspace — import audit

Status: imported; browser CI and publication pending.

## Manufacturer reconciliation

Topps product metadata confirms release **30 December 2025**. The 14-page checklist contains **347 numbered designs across 12 subsets**. All 347 rows, five panoramic planet themes, 18 panoramic artists, 144 regular sketch artists and all 77 odds rows independently matched Poppler after whitespace normalization. Checklist page 8 and odds page 2 were visually inspected. The Japanese artist ジェイソン (Jason) is one line split across two PDF text spans and remains one artist.

| Subset | Identities |
|---|---:|
| BASE CARDS | 100 |
| BASE CARDS PLANETARY VARIATIONS | 100 |
| MOON OF MANDALORE | 10 |
| THERES ALWAYS A BIGGER FISH | 15 |
| GALACTIC ERAS | 25 |
| ART OF TATOOINE | 15 |
| STAR WARS REFLECTIONS | 5 |
| PLANETARY VIEWS | 5 |
| GALACTIC ORIGINS | 10 |
| HYPERSPACE SHADOWBOX | 20 |
| OVERSIZED WIDEVISION CHROME CARDS | 5 |
| STAR WARS AUTOGRAPH VARIATION | 37 |

Totals: 100 base, 100 separately numbered Planetary Variations, 110 inserts and 37 autographs. BPV-1–100 are separate numbered designs under this parent. Five WIDE cards are numbered oversized inserts; no second product is created for box formats.

## Identity and source limits

Stable namespace: `2025-TSWH-<subset>-<printed number>`. Reflections R-16–20 and Planetary Views PV-6–10 retain their non-starting printed numbering. AV-LJj keeps mixed case. All source subjects, signers and artist credits are retained; planet metadata is stored in the runtime/database roster field and is searchable. Artist credits remain normalized source and database notes, consistent with existing imports. No new images.

Five unnumbered panoramic sketch planet themes and the two artist rosters do not create fake card identities or an artist-by-planet grid. No unique original sketch enumeration is claimed. The manufacturer product description calls this a debut despite the earlier 2024-labelled release; keep the annual products distinct.

77 odds rows are retained, yielding 71 numbered-subset rules. Five sketch foil rows and one panoramic sketch row remain source-only. The repeated wording `Bigger a Bigger Fish`, `Superfractor Refractor`, `Panaromic` and spacing/hyphen differences remain in raw evidence. Explicit aliases map these labels to the existing checklist sections. The five BPV planet rules describe their source planet groups and are not expanded across all 100 subjects. No serial caps or subject/parallel grids are inferred from pack odds. All 347 variant records are identity placeholders.

## Preservation and validation

All previous 31 metadata records, set bundles, stable IDs and frozen compatibility snapshot remain unchanged against baseline 286e5b1226833a41f5f727ea15517e599a1e5d3d. New totals: 32 sets /16,553 identities; Star Wars eight sets /5,255; WWE unchanged 24 /11,298. Importer reruns are byte-identical; conflicts are rejected.

Five focused tests, all eight existing Star Wars source/import suites, Stadium Club, split catalogue, category import and category DOM tests passed locally. The previous Chrome test now permits additive future sets while retaining all prior-row and byte-preservation checks. Browser coverage adds Hyperspace base/BPV ownership isolation, 100 variation and 110 insert filters, WIDE-5 and R-16 searches, mixed-case AV-LJj signer search, offline persistence and existing responsive checks. Known unavailable local Chromium was not retried; CI pending.

Guarded transaction `supabase/corrections/2026-10-26-star-wars-hyperspace-2025.sql` passed rolled-back dry run, committed import and a second committed application. The repeat was identical across all eight complete-row table digests. Database: 32 sets /16,553 cards /37,914 variants /549 subsets /1,855 parallel rules /88 sources. All 30 collection rows retain digest 6648329147d88b88ed9e52eaac40cfa9; images remain empty. No schema, auth, RLS, collection or image writes occurred. Authenticated private-photo/two-device flows have not been rerun.

## Sources

- [Official product](https://www.topps.com/products/2025-star-wars-hyperspace-hobby-box).
- [Official checklist](https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2025_Star_Wars_Hyperpsace_Checklist.pdf?v=1787957644) — SHA-256 `9e31cb8d1889575264e05b67133da6de7e462fb3c92739799a987b60b9ea1cfb`.
- [Official odds](https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2025_Star_Wars_Hyperspace_Odds.pdf?v=1787957644) — SHA-256 `2c64da7972a2b8d9d3ec0056109b29605fa3a0c56bd58fadd7d9e7507d2862e1`.
