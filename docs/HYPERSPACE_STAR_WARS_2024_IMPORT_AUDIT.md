# 2024 Topps Star Wars Hyperspace — import audit

Status: imported and published via PR #18. Browser CI 40264087061 and Pages 40264240888 succeeded.

## Manufacturer reconciliation

The official ten-page checklist contains **326 numbered identities /10 subsets**. All rows, five sketch planet themes, 106 artist entries and 61 odds rows independently matched Poppler in source order, ignoring whitespace only. Some long subjects overlap the planet column in rendered layout; the PDF text cells and independent raw extraction retain the full subject and separate planet. Checklist page 6 and the first odds page were visually inspected.

| Subset | Identities |
|---|---:|
| BASE CARDS | 100 |
| BASE CARDS PLANETARY VARIATIONS I | 100 |
| JUMP TO HYPERSPACE | 5 |
| THERES ALWAYS A BIGGER FISH | 15 |
| FIRST ARRIVAL | 15 |
| GALACTIC ERAS | 25 |
| STAR WARS REFLECTIONS | 5 |
| PLANETARY VIEWS | 5 |
| GALACTIC ORIGINS | 10 |
| STAR WARS AUTOGRAPH VARIATION | 46 |

Totals: 100 base, 100 separately numbered Planetary Variations, 80 inserts and 46 autograph designs. Reflections begins at R-6 and ends R-10; no earlier numbers are invented. Planetary Views is PV-1–5. This release does not inherit 2025-only Shadowbox, Widevision or Art of Tatooine designs.

## Identity and source differences

Namespace: `2024-TSWH-<subset>-<printed number>`, separate from 2025 Hyperspace. Both BASE #1 and BPV-1 are explicit designs. Planet metadata remains in the runtime/database roster field and is searchable. The BPV heading retains its printed terminal I.

Source differences are preserved rather than silently corrected: base #8 Mylaya versus BPV-8 Mylayas, base #86 Maximillian Veers versus BPV-86 Maximilian Veers, base #54 Kashyyyk versus BPV-54 Naboo, and base #56 Hoth versus BPV-56 Bespin. Base/BPV planets have distributions Naboo 41/42, Kashyyyk 17/16, Hoth 20/19, Bespin 8/9, Mustafar 14/14. The full underlying GE-4 title remains Obi-Wan Kenobi vs Anakin Skywalker even where layout extraction clips the final word. No factual or spelling repair is inferred.

The five unnumbered sketch themes are Naboo, Kashyyyk, Hoth, Bespin and Mustafar. The artist roster has 106 entries /105 distinct printed names: Brent Scotchmer is listed twice. Both source entries remain evidence; no duplicate card identities or artist-by-planet grid are created. No licensed card images added.

## Odds and date limits

All 61 odds rows are retained. 56 become subset rules, while five sketch-foil rates remain source-only. Aliases reconcile Reflections/Star Wars Reflections and the repeated Bigger a Bigger Fish wording. The source label Superfractor Refractor is retained. Pack rates do not establish serial caps or every subject/parallel combination. All 326 variant records are checklist identity placeholders and all serial caps remain null. Five planet-labelled BPV rules describe their source groups without being expanded across every subject.

Topps' product title is 2024, while Available From is **19 February 2025** and generic Product Year metadata says 2025. Keep the title year and actual release date without creating another annual product.

## Preservation and tests

All previous 34 metadata records, set bundles and stable IDs, plus the frozen compatibility snapshot, remain unchanged against 6bf9fcd11e6db774c3798cb954c956313950935b. Totals: 35 sets /17,483 cards; Star Wars 11 /6,185; WWE unchanged 24 /11,298. Reruns are byte-identical and conflicts are rejected.

Five focused tests and all ten existing Star Wars source/import suites, Stadium Club, split catalogue, category import and real-page category DOM checks passed locally. Earlier 2024 Masterwork totals now permit additive future sets while retaining full prior metadata/byte preservation checks. Browser coverage adds independent 2024/2025 Hyperspace ownership, base/BPV separation, 100 variation /80 insert /46 autograph filters, BPV-54 Naboo, R-6 Lord Vader and Ewan McGregor search. Existing guest, Vault, real offline reload and responsive checks remain enabled. Known unavailable local Chromium was not retried; browser CI passed.

Guarded SQL `supabase/corrections/2026-10-26-star-wars-hyperspace-2024.sql` passed rolled-back dry run, committed import and identical second application across all eight full-row digests. Database: 35 sets /17,483 cards /38,844 variants /597 subsets /2,074 rules /98 sources. All 30 collections retain 6648329147d88b88ed9e52eaac40cfa9; images remain empty. No collector, image, auth, RLS or schema writes. Authenticated private-photo/two-device checks not rerun.

## Sources

- [Official product](https://www.topps.com/products/2024-star-wars-hyperspace-hobby-box) — 2024 title and 19 February 2025 availability.
- [Official checklist](https://cdn.shopify.com/s/files/1/0662/9749/5709/files/STW2488-CheckList_24SWRS.pdf?v=1787937372) — SHA-256 `ed5dd0d7031e826e683a72f27d2c9c4bad2ed09081ffb63a0f18550f78fd8ac5`.
- [Official odds](https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2024_Star_Wars_Hyperspace_Odds.pdf?v=1787937372) — SHA-256 `22cc1620c185ce7c18db3c22ed9438836d3cd880382f4ad242441c07e10098d4`.

Next: SW-017 — 2024 Topps Star Wars Galactic Antiquities. Topps' official product records Available From 5 February 2025: https://www.topps.com/products/2024-topps-star-wars-galactic-antiquities .

## Published verification

Feature c4b93760ae4c9bbf841a9bd856b74c523f693b18 passed CI 40264087061: all source/catalogue/category checks, guest, Vault, real offline reload, eleven-set ownership isolation, separate 2024/2025 Hyperspace ownership, base/BPV separation, filters, printed-number and signer searches, and responsive widths. PR #18 merged as dfb5de2b6a792e43975bacf2bf72d5c9a097a2e2. Pages 40264240888 succeeded. All 48 live runtime/index/set assets match validated source byte-for-byte. Live guest UI was not separately rerun; browser CI exercised identical deployed runtime assets. Receipt: docs/HYPERSPACE_STAR_WARS_2024_RELEASE.json. Authenticated private-photo/two-device flows remain unrerun.
