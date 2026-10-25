# Multiple collection categories

Prepared 25 October 2026. User approved the preview and publication after browser
checks. No new Star Wars or Marvel catalogue cards are included.

## User experience

- A persistent WWE / Star Wars / Marvel switch sits above every collection view.
- WWE is the initial selection for existing users; selection is remembered on the device.
- Each category owns its overview, catalogue totals, completion denominator, set library,
  set filters, global search, owned cards, wanted list, recent additions and Vault cost,
  value and sold/traded summaries. There is no implicit combined collection view.
- Switching clears searches, set/card-type/status filters, pagination and personal sort.
  A modal editor must finish its save/discard flow before switching.
- Categories without imported sets show one Coming soon screen across navigation.
  No speculative sets, sample ownership or fake completion percentages are imported.
- Card type (Base, Insert, Autograph, etc.) remains separate from franchise category.
- One account syncs the complete collection; backup explicitly covers all categories.

## Classification and identity contract

`categories.js` defines the allowed stable category IDs: `wwe`, `star-wars`, `marvel`.
Every set in `data/catalogue-index.json` has an explicit `categoryId`. All 24 reviewed
existing sets, including the WWE NOW crossover, retain WWE membership. Card records
derive membership through their stable parent `setId`. Names/numbers are never used
to infer membership or merge ownership.

The bundled index is the authoritative franchise mapping for both bundled and cloud
catalogues. The cloud loader maps exact set IDs back to that index and validates
all card/set IDs. An unmapped cloud set, duplicate card ID or missing bundled identity
causes fallback to the complete validated bundle. This deliberately requires publishing
reviewed set metadata with future database imports; cloud-only sets stay unpublished.

This preparation needs no database schema migration. Auth, policies, collection keys,
card IDs and cloud collection operations retain their existing contracts. Category
selection is a presentation preference, not authorization or a separate user account.

The catalogue IO helper preserves existing category metadata when an older exporter
omits it. New sets must explicitly supply a supported category; an importer cannot
silently reassign an existing set. Validation occurs before any file writes. Existing
WWE importers now declare WWE membership so repeat imports remain supported.

## Importing Star Wars and Marvel later

1. Verify manufacturer checklist identities, subsets and parallel applicability.
2. Assign `categoryId` explicitly and use globally unique stable set/card IDs.
3. Keep Comics and Studios as distinct Marvel sets; preserve the exact product identity.
4. Import database rows using existing catalogue conventions and publish matching split
   bundles/index in the same release. No catalogue image permission is assumed.
5. Test category isolation, ownership, Vault summaries, sync, backup/restore and offline
   reload before announcing availability. A category becomes usable when it has sets.

## Verification performed

- `node tests/catalogue-split.cjs`: catalogue loader, stable identities, unchanged set
  files, repeat-save behavior, failed chunk handling and service worker asset list.
- `python3 tests/stadium-club-2026.py`: six existing source/import preservation checks.
- `python3 tests/national-treasures.py`: source counts, preservation, repeat import and
  conflict refusal.
- `python3 tests/category-imports.py`: explicit category assignment, retained metadata,
  reclassification refusal and pre-write failure behavior.
- `node tests/categories.cjs` with pinned `linkedom@0.18.12`: actual page/script DOM
  initialization, click switching and remembered selection, all views, cleared filters,
  future-category activation, separate Vault costs, same-number/name identity isolation,
  complete backup and unchanged saved entries. Fixtures are isolated and never uploaded.
- Read-only connected database check: 30 collection rows; complete-row digest
  `820fb924a7559fe022be70620b24bcef` before/after. No database writes were performed.

## Pending before publication

Chromium is unavailable in this environment. Browser layout, actual service worker
offline reload, existing guest/Vault browser flows and authenticated two-device/photo
checks have not run for this change. The existing CI workflow includes the new DOM and
import checks; the browser category regression is included in its browser run.

The user approved publication on 25 October 2026 after reviewing the preview. Submit
through the connected GitHub account, run all browser checks, inspect responsive
layouts, and publish only after they pass. Command-line Git lacks login credentials
in this workspace; use the connected account rather than starting another login flow.
