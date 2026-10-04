# GrailRoster handover

Read this first; inspect only files needed for the current task.

## Current state — 4 October 2026

- Production: https://grailroster.com ; GitHub: JoshY95/GrailRoster, main.
- Catalogue published at commit 8f1fdd8 (PR #4); Pages deployment succeeded. Live set library and published data files verified.
- Production/local/database catalogue: 23 sets, 10,359 identities. All completed lists are uploaded, including National Treasures (718 identities, 21 subsets, 3,550 numbered versions), annual 2025/2026 Topps NOW and the WBC crossover.
- Supabase Sydney project: jvsvuxgpaqwlcstfuzbd. No credentials belong in this file.
- Obsidian design uses theme.css; preserve all legitimate collection cards and existing user data.
- Branded auth/SMTP, password confirmation, password recovery, email change and account deletion were user-tested successfully.
- Collector Vault is implemented; see docs/COLLECTOR_VAULT.md for behaviour and test limitations. Do not infer all live photo/two-device tests are complete.

## Split catalogue — deployed

- Runtime catalogue: data/catalogue-index.json plus data/sets/<set-id>.json.
- scripts/catalogue_io.py and catalogue_io.js load/save the split format and skip rewriting unchanged files.
- Importers, exporter, app loader and offline service worker now use the split format.
- data/catalogue.json is a frozen pre-split compatibility snapshot, not the current source of truth. Do not read/upload/regenerate it for routine set additions.
- All legitimate card identities remain unchanged; two false heading records were removed in the reviewed 4 October correction. The app still loads all sets for global search; lazy loading is not implemented.
- GitHub CI run 37187099064 passed Chromium browser smoke, Collector Vault and real offline reload tests. Local Chromium remains unavailable; use the verified CI workflow rather than retrying local browser installation.

## Next catalogue task — imports paused

User paused new sets on 4 October 2026. Audit completed: see docs/WWE_2025_2026_COVERAGE_AUDIT.md for all 18 existing 2025/2026 lists, missing 2025 Royal Rumble/WrestleMania/SummerSlam event exclusives, annual 2025/2026 NOW coverage (including HOF/posters), now imported and published, and upcoming Stadium Club. No missing released main boxed product was identified in the sources checked. Royalty and 2026 Sapphire heading/subset errors are now corrected locally and in Sydney: 689 and 496 identities respectively. Two false headings and their identity placeholders were removed; 35 real cards moved to the correct subsets without changing IDs. Collections, unrelated card records and legitimate variant links have identical before/after digests; zero orphan variants. BAPE's four variation records still need card-image verification. Completed-list uploads were subsequently authorised and published. Further new-set research/imports remain paused; wait for user instruction before resuming.

2024 Panini National Treasures WWE is complete locally and in Sydney; see docs/NATIONAL_TREASURES_2024.md. Source-derived variant digest matches all 3,550 stored versions, with zero orphan variants. Existing catalogue and collection digests remain unchanged. All 19 existing split set files are byte-identical; source-backed importer tests and catalogue-split tests passed.

Publication verified: browser smoke, Vault and real offline reload passed in CI. The live set library shows all 23 sets; production index and all newly published/corrected bundles exactly match the verified local files. Public Supabase API matches all 10,359 local card identities. Authenticated cloud/photo/two-device testing is not implied by these guest checks.

Next set: 2024 Panini Three Count WWE, then Select, PhotoGenic, Prizm Premium Factory Set and Prizm (tentative order). Verify actual release dates before confirming order. National Treasures uses provisional December 31, 2024 for sorting; the original GTS schedule said December 13 and no final manufacturer announcement was found.

One set per task. Use authoritative manufacturer/distributor checklists. Keep stable subset/card-number IDs; multi-subject designs are one identity. Never infer missing card numbers or parallel applicability. Record only verified numbered versions. Preserve all pre-existing set/card records and collections. Validate counts, duplicate IDs, variant linkage, idempotency and existing-record preservation.

## Lean workflow

1. Read this file and git status; use targeted searches, not full catalogue dumps.
2. Reuse the importer pattern and catalogue_io helpers. Parse large sources locally; report counts/errors only.
3. One agent. Use tools only for required research, implementation and checks; no repeated attempts at known unavailable tooling.
4. Run focused tests plus regression tests when UI/auth/storage changes warrant them. Distinguish tests actually run from pending checks.
5. Publish only validated work within user authorization; never force-push. Update this handover after each milestone.

User settings: recommend GPT-6.1 Sol, Medium reasoning, Standard speed for routine work; reserve Astra for difficult design/debugging reviews. The user changes these settings, not the agent.

Correction validation: catalogue-split and National Treasures tests passed; repair rerun was byte-identical and all 18 unrelated set files remain unchanged. Reviewed manifest: scripts/catalogue_repairs.json; local repair: scripts/repair_catalogue.py; database transaction: supabase/corrections/2026-10-04-checklist-headings.sql. Corrections are published; browser and offline verification passed.

Topps NOW release-list milestone: docs/WWE_TOPPS_NOW_2025_2026_RELEASE_LIST.md covers all 157 2025 annual cards, 123 2026 annual WWE cards through #104, the separately labelled WBCO crossover and the existing 40-design Vegas checklist. Standalone workbook created with product links, release dates, print runs and published extras. Annual lists and the separately labelled WBC crossover are imported and published; the existing Vegas list is unchanged. Only verified checklist identities were added; advertised extras remain source notes pending variant verification. New-set queue remains paused.

Upload milestone — 4 October 2026: user authorised uploading every completed list. Annual NOW 2025 (157), annual NOW 2026 (123) and separate WBC crossover (1) are imported locally and in Sydney. All prior card and collection digests match; zero orphan variants. Existing Vegas is unchanged. No new research sets authorised. Published website bundle includes National Treasures, Royalty/Sapphire corrections and the split catalogue. Local catalogue, source, idempotency and preservation checks passed. GitHub CI browser smoke, Vault and real offline reload passed; production deployment and file parity verified. Collection digest remains 4a4cedb954d6d44b24667d0d04001d2b; pre-existing card digest remains 746683a59318a70ae53834ad1d4860c5.
