# 2024 Panini National Treasures WWE

The published Panini workbook is retained at
`sources/2024-panini-national-treasures-wwe/checklist.xls`.

- Source: https://gogts.net/wp-content/uploads/2024/12/2024-Panini-National-Treasures-WWE-Trading-Cards-Checklist.xls
- Distributor checklist page: https://gogts.net/2024-panini-national-treasures-wwe-trading-cards-checklist/
- SHA256: `4455cfcf4035cc050972e37da62d32ef72b1e79e70bb6024dd6554a0e9d65378`
- 3,550 published printed-version rows normalize to 718 identities in 21 subsets.
- 71 identities have no unsuffixed base printing in this workbook. No missing
  numbers or base versions are synthesized. All parallel applicability and
  numbering come from individual published rows, including Purple and Red FOTL.
- Eight multi-subject designs vary subject order between printings. Each remains
  one subset/card-number identity; all printings must contain the same subjects.
- Checklist coverage is limited to this published workbook. It does not imply
  every planned card number or possible parallel exists.

## Release date

The catalogue uses **2024-12-31** for sorting, corroborated by Checklist Insider
and Cardsmiths Breaks. GTS's original December 3 announcement scheduled December
13. A final manufacturer release announcement was not located, so December 31
is provisional, not represented as manufacturer-confirmed. This discrepancy does
not change its position between Flawless and Three Count.

- https://www.checklistinsider.com/2024-panini-national-treasures-wwe-wrestling
- https://cardsmithsbreaks.com/full-checklist/2024-panini-national-treasures-wwe/

## Rebuild and verification

```sh
python scripts/add_2024_panini_national_treasures_wwe.py sources/2024-panini-national-treasures-wwe/checklist.xls --sql-dir supabase/generated/2024-panini-national-treasures-wwe
python tests/national-treasures.py
node tests/catalogue-split.cjs
```

The importer refuses conflicts with an existing set, uses the split catalogue
helpers and emits upsert-only SQL scoped to this set. No collection writes or
deletions are generated.

Sydney import and readback completed on October 4, 2026: 718 cards, 21 subsets,
3,550 variants, zero orphan variants. The source-derived digest of every variant
ID, parent identity, parallel and serial cap matches the stored rows:
`d0c91bd67dca1d3a4094fa6686761205`.

Before/after digests match for all existing database cards, sets, variants and
30 collection items. All 19 pre-existing split set files remain byte-identical.
The local catalogue now has 20 sets and 10,080 identities. Repeat imports leave
catalogue and generated SQL bytes unchanged.

Website publication remains pending. Actual browser smoke/Vault checks and a
real offline reload of the split catalogue have not run; the automated loader
and service-worker cache-list test does not substitute for those checks.
