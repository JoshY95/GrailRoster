# 2026 Topps Stadium Club WWE — release and checklist audit
Checked 24 October 2026. Research only — NOT imported into the GrailRoster catalogue or Sydney Supabase database.

## Manufacturer sources
- Official Topps collector guide: https://ripped.topps.com/2026-topps-stadium-club-wwe-cards-collector-guide/
- Official Topps checklist PDF (21 pages): https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2026_Topps_Stadium_Club_WWE_-_Checklist.pdf
- Official Topps product page: https://www.topps.com/pages/topps-stadium-club-wwe
- Release date: 2026-10-23. First Stadium Club-branded WWE product.
- Base: 200 numbered cards. Chrome base: separate 200-card subset with matching subjects and numbers, distinct card identities.
- Other checklists include Beam Team, Inked, Concentration, The Aftermath, Main Stage, Triumvirates, Triumvirates Nickname, multiple autograph series and anniversary autographs.
- Hobby box: 16 packs x 8 cards, 2 autos.

## Reconciliation blocker / required next validation
Community indexes disagree: 930, 938 and 955 identities depending on subset inclusion, repeated dual-signature source rows, and apparently incomplete checklist sections. They are **not** accepted as final import counts.
The official manufacturer PDF must be parsed by section, treating a multi-signature card sharing the same subset/card number as **one** physical card identity. Confirm every subset, card ID, category, rookie marker and multi-subject display name before creating data/sets/2026-topps-stadium-club-wwe.json.
Check whether the published Base Chrome Autographs II checklist is outstanding. Do not invent entries from odds-only evidence or copy missing subjects from Base Chrome Autographs I.
Use manufacturer pack odds to attach only verified numbered parallel rules, keeping unnumbered effects separate and no guessed /N applicability.
Validate no duplicate ID or subset/number pairs, every 1-200 base and chrome number, contiguous checklist_order, stable pre-existing records and variant linkage.
After passing local tests and source review, create one set file and a catalogue-index entry, then apply a guarded Sydney database transaction and confirm guest catalogue and deployment parity. Preserve user collections. No new set has been published from this research.
