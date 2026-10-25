# 2025 Topps Chrome Sapphire Star Wars — import audit

Status: prepared; local checks passed. Browser CI, database application and publication pending.

## Manufacturer reconciliation

Topps product metadata confirms release **17 September 2025**. The official 15-page PDF has numbered source rows on pages 1–8. Pages 9–12 are empty. Pages 13–15 contain 21 unattached DEBUT glyphs without card numbers or subjects; they are retained as source artifacts and never attached to a card. Page 13 was visually inspected, as was the complete odds sheet.

The 395 numbered source rows reconcile to **358 identities / five subsets**: 200 base, 10 Sapphire Selections and 148 autographs. Thirty duo signer rows become 15 cards; 33 trio rows become 11 cards. This removes 37 repeated signer rows. All 395 numbered rows, their 65 attached base DEBUT flags and all 17 odds rows independently matched Poppler text in source sequence after whitespace normalization.

| Subset | Category | Identities |
|---|---|---:|
| CHARACTERS | Base | 200 |
| SAPPHIRE SELECTIONS | Insert | 10 |
| AUTOGRAPH CARDS | Autograph | 122 |
| DUO AUTOGRAPHS | Autograph | 15 |
| TRIO AUTOGRAPHS | Autograph | 11 |

## Identity and source limits

Sapphire has its own manufacturer checklist, set ID and `2025-TCSSW-<subset>-<number>` identity namespace. It is not a relabelled regular Chrome or Galaxy set. Existing identities and ownership remain separate. Different printed numbers with repeated names (Lando Calrissian #78/#79 and Obi-Wan Kenobi #138/#139) remain separate designs. The mixed-case printed duo code DA-MJj is retained exactly, with both Lee Jung-jae and Manny Jacinto on one design. Multi-signer rows combine only by subset and printed card number.

Sixty-five attached DEBUT flags remain in normalized source and database notes. These character debut marks are not silently converted into athlete rookie flags. No DEBUT glyph from trailing artifact pages is assigned to a card. Source spelling, including Kuill, is retained without guessing corrections.

All 17 Sapphire odds rows become subset rules. Original spelling, including Padpradascha, is preserved. There are 358 identity placeholder variant records; no serial caps or subject/parallel grids are inferred from pack odds. No licensed card images are added.

## Preservation and validation

All previous 29 set metadata records and bundles, stable IDs and frozen compatibility snapshot are unchanged against baseline c52c3742a36480e8f3d1d8c89559579cea922db9. New totals: 30 sets / 14,971 identities; Star Wars six sets / 3,673, WWE unchanged 24 / 11,298. The importer is byte-idempotent and rejects conflicting existing identities.

Focused source, DEBUT/artifact, odds and preservation tests and all existing source/catalogue/category regressions passed locally. Browser coverage adds separately owned Sapphire #1, the ten Sapphire Selections, the mixed-case duo and a trio design; existing guest, Vault, offline and responsive checks remain enabled. Known unavailable local Chromium is not retried. Guarded SQL baseline is 29 sets /14,613 cards and preserves every previous catalogue/collection/image row. No schema, auth, RLS or collector-data writes. Authenticated private-photo/two-device flows are not implied by guest checks.

## Sources

- [Official product](https://www.topps.com/products/2025-topps-chrome%C2%AE-sapphire-star-wars-hobby-box).
- [Official checklist](https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2025_Topps_Chrome_Sapphire_Star_Wars_Checklist.pdf?v=1787949354) — SHA-256 `9ca2fe09ad5e04ad727233cd26b9b7f70ba127a0598f60904dfe3a96c5d2edf2`.
- [Official odds](https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2025_Topps_Chrome_Sapphire_Star_Wars_Odds.pdf?v=1787949354) — SHA-256 `b68c3678c6db00824954aa63b2de852ca6623357172dead2312af9c860178b21`.
