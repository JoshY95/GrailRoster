# GrailRoster

GrailRoster is a WWE trading card collection tracker built from verified master catalogues.

Production: <https://grailroster.com/>

## MVP features

- Browse 10,359 card identities across 23 sets
- Search by wrestler, card number, subset, code or roster
- Filter by set, category and collection status
- Mark cards as owned or wanted
- See progress by set and across the full catalogue
- Use the app in local guest mode or sign in with email/password for cross-device cloud sync
- Create test accounts in-app, with one-time email links retained as a backup sign-in method
- Merge an existing on-device collection into a signed-in account
- Back up and restore collection data
- Installable, responsive and available offline after the first visit
- Rights-aware card and sealed-product image support with lazy loading and placeholders

Guest collection progress is stored in the browser. Signed-in collection progress is protected by Supabase Row Level Security and synchronized with the GrailRoster backend.

The active backend project is in Supabase region `ap-southeast-2` (project reference `jvsvuxgpaqwlcstfuzbd`).

## Reference images

The app loads approved card and sealed-product images from `data/images.json`. Until an asset is approved, GrailRoster displays a generated placeholder. See `docs/IMAGE_LIBRARY.md` for the Supabase storage layout, rights register and bulk-manifest workflow.

## Run locally

Serve the repository with any static web server, for example:

```bash
python -m http.server 8080
```

Then open `http://localhost:8080`.

## Catalogue source files

Read `PROJECT_STATUS.md` for the compact project handover. The runtime catalogue is
`data/catalogue-index.json` plus one file per set in `data/sets/`. Importers use
`scripts/catalogue_io.py` / `catalogue_io.js`, which do not rewrite unchanged sets.
`data/catalogue.json` is retained only as a frozen pre-split compatibility snapshot.
Run `node tests/catalogue-split.cjs` to verify the migration and loader/cache logic.

The generated app dataset currently includes:

- 2025 Topps Universe WWE
- 2025 Topps WWE x BAPE
- 2025 Topps Finest WWE
- 2025 Topps Chrome WWE x Cactus Jack
- 2025 Topps Chrome WWE Cactus Jack x WrestleMania
- 2025 Topps Chrome Sapphire WWE
- 2025 Topps Chrome WWE
- 2024 Panini Flawless WWE
- 2025 Topps John Cena Commemorative Collection
- 2025 Topps Exalted WWE
- 2026 Topps Chrome WWE
- 2026 Topps Now WrestleMania Vegas
- 2026 Topps Chrome LogoFractor WWE
- 2025 Topps Royalty WWE
- 2026 Topps Chrome Sapphire WWE
- 2026 Topps Cosmic Chrome WWE
- 2026 Topps Decades WWE - '90s Edition
- 2026 Topps Universe WWE
- 2026 Topps NSCC Collection - WWE

The NSCC WWE set is sourced from Topps' official 2026 NSCC checklist: 50 National
Refractors, 46 National Refractors Autograph Parallel cards, 5 National Collection
inserts and 4 National Collection Autograph Parallel cards. The `/26` NSCC Annual
Refractor is recorded as a set-level rule only; card-level variants remain unlisted
until Topps confirms applicability. To re-parse the official checklist, run
`node scripts/add_nscc_wwe.js /path/to/official-checklist.pdf --sql` to validate
the bundled data and print the Sydney database seed SQL.

The 2025 Topps Chrome WWE flagship set is sourced from Topps' official 27-page
checklist. It contains 1,039 stable checklist identities across 33 sections. The
200 Frozenfractor entries reuse the base-card identities and are stored as verified
variants instead of being incorrectly counted as additional checklist cards. Run
`node scripts/add_2025_topps_chrome_wwe.js /path/to/WWE2502-CheckList_25CWWE.pdf
--sql-dir supabase/generated/2025-topps-chrome-wwe` to validate the source PDF,
refresh the bundled catalogue, and generate idempotent Sydney database seed batches.

The 2024 Panini Flawless WWE set is sourced from the published Panini checklist
workbook. Its 3,356 printed rows normalize to 652 stable card identities across 25
subsets. Every numbered base issue and parallel remains attached as an exact verified
variant, including the Bronze FOTL cards and the three identities with no base issue.
Run `python scripts/add_2024_panini_flawless_wwe.py /path/to/checklist.xls --sql-dir
supabase/generated/2024-panini-flawless-wwe` to validate the workbook and regenerate
the idempotent Sydney database batches.

2024 Panini National Treasures WWE adds 718 identities across 21 subsets and
3,550 exact numbered versions from the published Panini workbook. The original
source is retained under `sources/2024-panini-national-treasures-wwe/`. Run
`python scripts/add_2024_panini_national_treasures_wwe.py
sources/2024-panini-national-treasures-wwe/checklist.xls --sql-dir
supabase/generated/2024-panini-national-treasures-wwe` to rebuild its split
catalogue file and database batches. See `docs/NATIONAL_TREASURES_2024.md` for
source coverage, provisional release date and verification details.

The ten post-Universe source workbooks and their original checklist files are stored under `sources/new_sets/`. Run `scripts/extract_new_catalogues.py` to re-normalize those checklists, then rebuild the workbooks and run `scripts/build_catalogue.py` to regenerate `data/catalogue.json` and the Supabase SQL batches.

## Authentication setup

The browser uses the public Supabase publishable key in `config.js`; no server secret is shipped to the client. Before production sign-in testing, add every deployed GrailRoster origin to **Authentication → URL Configuration → Redirect URLs** in the GrailRoster Supabase dashboard. Keep localhost entries for local testing and use exact HTTPS deployment URLs in production.

Email/password accounts use Supabase `signUp` and `signInWithPassword`. Hosted projects require email confirmation by default. For closed testing only, confirmation can be temporarily disabled under **Authentication → Providers → Email**. Re-enable confirmation and configure custom SMTP before a public launch.

The production Supabase Site URL and exact redirect URL are both `https://grailroster.com/`. The legacy GitHub Pages redirect remains temporarily allow-listed during the domain migration.

Completed annual Topps NOW lists: 2025 (157 cards), 2026 through 4 October (123 cards) and the separately labelled 2026 WBC/WWE crossover (1 card). See docs/WWE_TOPPS_NOW_2025_2026_RELEASE_LIST.md; run `python scripts/add_topps_now_annual.py` to validate/rebuild the split records and guarded SQL. Printed parallels are not inferred from base print runs.
