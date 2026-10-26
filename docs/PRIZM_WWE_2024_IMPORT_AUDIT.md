# 2024 Panini Prizm WWE import and Premium Factory Set review

Prepared 26 October 2026, Australia/Melbourne. Baseline `0cab343bf369f3fa4454b500cc77044d318df35c`. Scope: complete the missing 2024 Prizm parent, verify Premium edition relationship, import, test and publish without changing existing collector data.

## Result

- One new parent: `2024-panini-prizm-wwe`, Hobby release 9 August 2024. GTS separately schedules Under Card for 23 August; the Premium guide estimates 27 August. These are format/edition dates, not three separate design sets.
- **516 identities /16 subsets /9,270 explicitly listed versions.** Includes 200 regular base designs, 20 separately enumerated Under Card variation designs, 112 inserts and 184 autograph designs. Ten dual autograph designs remain ten cards, with two signers each.
- 6,770 source-backed serial-cap records. 2,500 unknown-cap records, including 200 deliberately unresolved base White Sparkle caps. No inferred parallel grids or absent numbered designs.
- Resulting catalogue: **46 sets /22,731 identities**; WWE **28 /13,413**, Star Wars unchanged **18 /9,318**. All previous 45 metadata records and bundles, frozen compatibility snapshot and collector IDs remain unchanged.

## Sources and full reconciliation

[Original Panini-format distributor XLS](https://gogts.net/wp-content/uploads/2024/07/2024-Panini-Prizm-WWE-Trading-Cards-Checklist.xls) and [independent updated workbook](https://xcdn.checklistinsider.com/public/2024/07/2024-Panini-Prizm-WWE-Wrestling-Checklist-Downloads-Excel-spreadsheet-updates.xlsx) are retained with SHA-256 hashes in `sources/2024-panini-prizm-wwe/checklist.json`. All 9,270 rows reconcile: label, number, subjects, roster and sequence. The original has 59 occurrences of the same malformed Seth nickname string; only that known encoding issue is repaired for comparison/display. Original workbook bytes retain the literal values. Signer order is normalized only for comparison, never for assigning a different design.

Release source: [GTS distributor guide](https://gogts.net/2024-panini-prizm-wwe-trading-cards-checklist/). Premium relationship/date source: [Premium Factory Set guide](https://www.checklistinsider.com/2024-panini-prizm-premium-wwe-factory-set). Final source limits are explicit; source publication does not imply every physical edition was image-verified.

## Premium Factory Set decision

Premium uses the same 200 base designs and printed numbers. The original distributor workbook individually enumerates:

| Edition | Verified subjects | Printed cap |
|---|---:|---:|
| Base Horizontal Prizms Premium Box Set | 100 | /199 |
| Base Vertical Prizms Premium Box Set | 100 | /199 |
| Base Horizontal Prizms Premium Box Set Gold | 100 | /5 |
| Base Vertical Prizms Premium Box Set Gold | 100 | /5 |

All 400 versions link to the same 200 base card IDs. No Premium parent, duplicate base card, Premium autograph or Premium Under Card variation is invented. Each Premium version is labelled a Factory Set exclusive. Owning an Under Card image variation never owns the standard base card automatically.

## Subsets

| Subset | Identities |
|---|---:|
| Base Horizontal | 100 |
| Base Vertical | 100 |
| Horizontal Under Card Variation | 10 |
| Vertical Under Card Variation | 10 |
| Black Color Blast | 5 |
| Color Blast | 10 |
| Emergent | 20 |
| Prizmatic Entrances | 20 |
| Rumble Performances | 20 |
| WrestleMania Moments | 37 |
| Champion Signatures | 10 |
| Iconic Rivals Dual Autographs | 10 |
| Legendary Signatures | 19 |
| Sensational Signatures | 100 |
| Superstar Autographs | 35 |
| Throwback Signatures | 10 |

WrestleMania Moments numbers 3, 20 and 30 are absent from both complete workbooks; gaps remain unfilled. Each of the 20 Under Card variations has only its listed regular and Gold /10 edition. Same-name variations still retain separate IDs because the manufacturer enumerates a distinct variation design. Persona changes such as Steve Austin/The Ringmaster, Kane/Isaac Yankem and Dude Love/Mick Foley are preserved.

## White Sparkle exception

The original XLS and comparison workbook both print SEQUENCE=1 for all 200 non-autograph base White Sparkle rows. [Beckett's base checklist](https://www.beckett.com/news/2024-panini-prizm-wwe-wrestling-cards/) and [Checklist Center's base guide](https://www.checklistcenter.com/2024-panini-prizm-wwe-wrestling-card-checklist/) instead leave base White Sparkle unnumbered, while explicitly identifying autograph White Sparkle as 1/1. This is an unresolved source conflict. The 200 base versions remain available but have **null serial_cap and serial_exact**. Their literal SEQUENCE=1 cells remain in source evidence; no different print run is guessed. The 174 autograph White Sparkle source rows retain their 1/1 caps. Manufacturer clarification or physical evidence is still required to settle the base cap claim.

## Verification and publication

Seven focused tests cover complete independent source reconciliation, all exact version mappings, parent/Premium identities, variation ownership IDs, duals, printed numbering gaps, the cap exception, all 45 prior files/metadata, repeat/idempotent import and conflict refusal. Existing split/category checks and the prior WWE batch suite also pass locally. Shared SQL helpers must reproduce the previous three-set transaction byte-for-byte.

The compact atomic transaction in `supabase/corrections/2026-10-26-prizm-wwe-2024.sql` rejects existing-ID conflicts, enforces row counts and linkage, preserves every old catalogue row, and verifies both complete collector/image tables. Rolled-back dry run passes, including exact six-table content digests matching generated data. No writes target collection or image tables.

Browser CI checks guest, Vault, real offline reload, one Prizm parent, variation/base ownership separation, signer search, cross-franchise isolation, persistence and responsive widths. Local Chromium remains known unavailable and is not retried. Authenticated cloud/private-photo/two-device flows are not implied. Final deployment, repeat import and live parity are recorded in `docs/PRIZM_WWE_2024_RELEASE.json` after publication.

## Next WWE work

The six audited main 2024 hobby parents are now represented: Flawless, National Treasures, Three Count, Select, PhotoGenic and Prizm. Premium Factory Set is covered as Prizm editions. This does not certify complete worldwide 2024 coverage: Panini Instant and regional Adrenalyn XL remain separate gaps, and promotional issues remain an open title audit. Next backwards main-set work is a **2023 WWE release-date and coverage audit**, then the next verified missing main releases. Do not assume product-year labels are actual release dates or import continuing programmes without enumerating them.
