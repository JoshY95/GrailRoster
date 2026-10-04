#!/usr/bin/env python3
"""Import 2024 Panini National Treasures WWE from the published Panini checklist workbook.

The workbook lists every printed version as a separate row. This importer keeps one
stable card identity per subset/card number and stores every numbered printing,
including the numbered base issue, as a verified variant.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import OrderedDict
from datetime import UTC, datetime
from pathlib import Path

import xlrd
from catalogue_io import load_catalogue, save_catalogue


ROOT = Path(__file__).resolve().parents[1]
SET_ID = "2024-panini-national-treasures-wwe"
SOURCE = "https://gogts.net/wp-content/uploads/2024/12/2024-Panini-National-Treasures-WWE-Trading-Cards-Checklist.xls"
PRODUCT = "https://www.paniniamerica.net/checklist.html"

PARALLEL_SUFFIXES = (
    "Purple FOTL", "Red FOTL", "Holo Gold", "Holo Silver",
    "Amethyst", "Emerald", "Platinum", "Red",
)

# These are the actual subset/card-number unions present in the source workbook.
# Missing base issues and gaps in printed numbering are intentionally preserved.
SUBSETS = OrderedDict([
    ("Base", ("BASE", "Base", 100)),
    ("Clutch Factor Signatures", ("CFS", "Autograph Relic", 19)),
    ("Colossal Mat Material Signatures", ("CMMS", "Autograph Relic", 19)),
    ("Colossal Mat Materials", ("CMM", "Relic", 29)),
    ("Colossal Materials", ("CM", "Relic", 67)),
    ("Definitive Ink", ("DI", "Autograph", 51)),
    ("Dual Signatures", ("DUAL", "Autograph", 11)),
    ("International Treasures Signatures", ("ITS", "Autograph", 17)),
    ("Legendary Signatures", ("LS", "Autograph", 44)),
    ("Material Treasures", ("MT", "Relic", 50)),
    ("Peerless Signatures", ("PS", "Autograph", 26)),
    ("Retro Materials", ("RM", "Relic", 29)),
    ("Superstar Material Signatures", ("SMS", "Autograph Relic", 41)),
    ("Superstar Signature Jumbo Material Booklet", ("SSJMB", "Autograph Relic", 10)),
    ("Tag Team Material Signature Booklet", ("TTMSB", "Autograph Relic", 1)),
    ("Timeline Materials", ("TM", "Relic", 68)),
    ("Treasured Threads", ("TT", "Relic", 50)),
    ("Treasures of WWE Signatures", ("TWS", "Autograph", 45)),
    ("Triple Signatures", ("TRIPLE", "Autograph", 2)),
    ("Viewpoint Signatures", ("VS", "Autograph", 24)),
    ("WWE's Greatest Signatures", ("WGS", "Autograph", 15)),
])


def clean(value) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def number(value) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return clean(value)


def split_set_name(card_set: str) -> tuple[str, str]:
    for suffix in PARALLEL_SUFFIXES:
        marker = f" {suffix}"
        if card_set.endswith(marker):
            return card_set.removesuffix(marker), suffix
    return card_set, "Base"


def slug(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "-", value.upper()).strip("-")


def sql_literal(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def values(rows) -> str:
    return ",\n".join("(" + ",".join(sql_literal(value) for value in row) + ")" for row in rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--sql-dir", type=Path)
    args = parser.parse_args()

    sheet = xlrd.open_workbook(args.workbook).sheet_by_index(0)
    headers = [clean(sheet.cell_value(2, column)) for column in range(sheet.ncols)]
    if headers != ["CARD #", "CARD SET", "ATHLETE", "TEAM", "SEQUENCE"]:
        raise ValueError(f"Unexpected workbook columns: {headers}")

    rows = []
    for row_index in range(3, sheet.nrows):
        card_number = number(sheet.cell_value(row_index, 0))
        card_set = clean(sheet.cell_value(row_index, 1))
        athlete = clean(sheet.cell_value(row_index, 2))
        team = clean(sheet.cell_value(row_index, 3))
        sequence_value = sheet.cell_value(row_index, 4)
        if not all((card_number, card_set, athlete, sequence_value)):
            raise ValueError(f"Blank required value in workbook row {row_index + 1}")
        if not isinstance(sequence_value, (int, float)) or int(sequence_value) != sequence_value or sequence_value < 1:
            raise ValueError(f"Invalid sequence in workbook row {row_index + 1}: {sequence_value}")
        family, parallel = split_set_name(card_set)
        if family not in SUBSETS:
            raise ValueError(f"Unmapped card set in workbook row {row_index + 1}: {card_set}")
        rows.append({
            "number": card_number,
            "card_set": card_set,
            "family": family,
            "parallel": parallel,
            "athlete": athlete,
            "team": team or None,
            "sequence": int(sequence_value),
        })

    if len(rows) != 3550:
        raise ValueError(f"Unexpected printed-version count: {len(rows)}; expected 3550")
    observed_card_sets = {row["card_set"] for row in rows}
    expected_card_sets = {
        family + (f" {suffix}" if suffix else "")
        for family in SUBSETS
        for suffix in ("", *PARALLEL_SUFFIXES)
        if any(row["card_set"] == family + (f" {suffix}" if suffix else "") for row in rows)
    }
    if observed_card_sets != expected_card_sets:
        raise ValueError("A checklist card-set label was not classified exactly")

    # Prefer the unsuffixed issue as the canonical name. Parallel-only identities
    # use their first published printing; never fabricate an absent base version.
    identity_rows = OrderedDict()
    for row in rows:
        key = (row["family"], row["number"])
        if key not in identity_rows or row["parallel"] == "Base":
            identity_rows[key] = row

    # Subject order changes on eight multi-signed designs, but the people must agree.
    for row in rows:
        canonical = identity_rows[(row["family"], row["number"])]
        if sorted(map(clean, row["athlete"].split("/"))) != sorted(map(clean, canonical["athlete"].split("/"))):
            raise ValueError(f"Conflicting subjects for {row['family']} #{row['number']}")

    observed_counts = {family: 0 for family in SUBSETS}
    for family, _ in identity_rows:
        observed_counts[family] += 1
    expected_counts = {family: config[2] for family, config in SUBSETS.items()}
    if observed_counts != expected_counts:
        raise ValueError(f"Unexpected identity counts: {observed_counts}")

    cards = []
    card_by_key = {}
    for order, ((family, card_number), row) in enumerate(identity_rows.items(), 1):
        code, category, _ = SUBSETS[family]
        subjects = [part.strip() for part in row["athlete"].split("/")]
        card = {
            "id": f"2024-PNTWWE-{code}-{card_number}",
            "setId": SET_ID,
            "order": order,
            "number": card_number,
            "name": " / ".join(subjects),
            "subject1": subjects[0],
            "subject2": " / ".join(subjects[1:]) if len(subjects) > 1 else None,
            "category": category,
            "subset": family,
            "subsetCode": code,
            "roster": row["team"],
            "rookie": "No",
            "parallelGroup": code,
        }
        cards.append(card)
        card_by_key[(family, card_number)] = card

    if len(cards) != 718 or len({card["id"] for card in cards}) != 718:
        raise ValueError("Expected 718 unique stable card identities")

    variants = []
    seen_variant_ids = set()
    for order, row in enumerate(rows, 1):
        card = card_by_key[(row["family"], row["number"])]
        variant_id = f'{card["id"]}-{slug(row["parallel"])}'
        if variant_id in seen_variant_ids:
            raise ValueError(f"Duplicate variant: {variant_id}")
        seen_variant_ids.add(variant_id)
        variants.append({
            "id": variant_id,
            "cardId": card["id"],
            "order": order,
            "subset": row["family"],
            "number": row["number"],
            "name": card["name"],
            "parallel": row["parallel"],
            "serialCap": row["sequence"],
            "serialExact": "1/1" if row["sequence"] == 1 else f'/{row["sequence"]}',
            "exclusiveNote": "First Off the Line exclusive" if row["parallel"].endswith(" FOTL") else None,
        })

    set_record = {
        "id": SET_ID,
        "name": "2024 Panini National Treasures WWE",
        "shortName": "National Treasures WWE 2024",
        "accent": "#d4af37",
        "year": 2024,
        "manufacturer": "Panini",
        "releaseDate": "2024-12-31",
        "cardCount": len(cards),
        "subsetCount": len(SUBSETS),
        "subsets": [
            {"category": category, "name": family, "code": code, "count": expected_count}
            for family, (code, category, expected_count) in SUBSETS.items()
        ],
    }

    catalogue = load_catalogue()
    existing_cards = [card for card in catalogue["cards"] if card["setId"] == SET_ID]
    existing_sets = [item for item in catalogue["sets"] if item["id"] == SET_ID]
    generated_cards = [{key: value for key, value in card.items() if key != "subject1"} for card in cards]
    if existing_sets or existing_cards:
        if existing_sets != [set_record] or existing_cards != generated_cards:
            raise ValueError("Existing National Treasures data differs from the source workbook")
    else:
        catalogue["sets"].append(set_record)
        catalogue["cards"].extend({key: value for key, value in card.items() if key != "subject1"} for card in cards)
        catalogue["sets"].sort(key=lambda item: (item.get("releaseDate") or "", item["name"]), reverse=True)
        set_order = {item["id"]: index for index, item in enumerate(catalogue["sets"])}
        catalogue["cards"].sort(key=lambda card: (set_order[card["setId"]], card["order"]))
        catalogue["setCount"] = len(catalogue["sets"])
        catalogue["cardCount"] = len(catalogue["cards"])
        catalogue["generatedAt"] = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        save_catalogue(catalogue)

    if args.sql_dir:
        args.sql_dir.mkdir(parents=True, exist_ok=True)
        for old_file in args.sql_dir.glob("*.sql"):
            old_file.unlink()

        statements = []
        statements.append(
            "insert into public.catalogue_sets "
            "(id,name,short_name,year,manufacturer,release_date,source_file,accent,card_count,subset_count,variant_count) values "
            + values([[
                SET_ID, set_record["name"], set_record["shortName"], 2024, "Panini",
                set_record["releaseDate"], SOURCE, set_record["accent"], len(cards), len(SUBSETS), len(variants),
            ]])
            + " on conflict (id) do update set name=excluded.name,short_name=excluded.short_name,release_date=excluded.release_date,"
              "source_file=excluded.source_file,accent=excluded.accent,card_count=excluded.card_count,"
              "subset_count=excluded.subset_count,variant_count=excluded.variant_count;"
        )
        statements.append(
            "insert into public.catalogue_subsets "
            "(set_id,subset_code,category,name,card_count,parallel_group,source_url) values "
            + values([[SET_ID, code, category, family, expected_count, code, SOURCE]
                      for family, (code, category, expected_count) in SUBSETS.items()])
            + " on conflict (set_id,subset_code) do update set category=excluded.category,name=excluded.name,"
              "card_count=excluded.card_count,parallel_group=excluded.parallel_group,source_url=excluded.source_url;"
        )
        for start in range(0, len(cards), 200):
            batch = cards[start:start + 200]
            statements.append(
                "insert into public.catalogue_cards "
                "(id,set_id,checklist_order,category,subset_code,card_number,display_name,subject_1,subject_2,roster,rookie,parallel_group,image_status,pricing_status,source_url,notes) values "
                + values([[card["id"], SET_ID, card["order"], card["category"], card["subsetCode"], card["number"],
                           card["name"], card["subject1"], card["subject2"], card["roster"], False,
                           card["parallelGroup"], "Missing", "Unpriced", SOURCE,
                           "Published Panini 2024 National Treasures WWE checklist workbook"] for card in batch])
                + " on conflict (id) do update set checklist_order=excluded.checklist_order,category=excluded.category,"
                  "subset_code=excluded.subset_code,card_number=excluded.card_number,display_name=excluded.display_name,"
                  "subject_1=excluded.subject_1,subject_2=excluded.subject_2,roster=excluded.roster,"
                  "parallel_group=excluded.parallel_group,source_url=excluded.source_url,notes=excluded.notes;"
            )
        for start in range(0, len(variants), 200):
            batch = variants[start:start + 200]
            statements.append(
                "insert into public.catalogue_variants "
                "(id,set_id,card_id,variant_order,subset,card_number,display_name,parallel,serial_cap,serial_exact,exclusive_note,numbering_note,verification_status) values "
                + values([[variant["id"], SET_ID, variant["cardId"], variant["order"], variant["subset"],
                           variant["number"], variant["name"], variant["parallel"], variant["serialCap"],
                           variant["serialExact"], variant["exclusiveNote"],
                           "Exact sequence from the published checklist workbook", "Official checklist verified"]
                          for variant in batch])
                + " on conflict (id) do update set card_id=excluded.card_id,variant_order=excluded.variant_order,"
                  "display_name=excluded.display_name,parallel=excluded.parallel,serial_cap=excluded.serial_cap,"
                  "serial_exact=excluded.serial_exact,exclusive_note=excluded.exclusive_note,"
                  "numbering_note=excluded.numbering_note,verification_status=excluded.verification_status;"
            )

        rule_rows = []
        seen_rules = set()
        for row in rows:
            code = SUBSETS[row["family"]][0]
            rule_key = (row["family"], row["parallel"], row["sequence"])
            if rule_key in seen_rules:
                continue
            seen_rules.add(rule_key)
            rule_rows.append([
                f'2024-panini-national-treasures-wwe-{slug(code).lower()}-{slug(row["parallel"]).lower()}-{row["sequence"]}',
                SET_ID, code, row["family"], row["parallel"], row["sequence"],
                "1/1" if row["sequence"] == 1 else f'/{row["sequence"]}',
                "First Off the Line exclusive" if row["parallel"].endswith(" FOTL") else None,
                "Applies only to card numbers explicitly present in the checklist workbook",
                "Official checklist verified",
            ])
        statements.append(
            "insert into public.catalogue_parallel_rules "
            "(id,set_id,parallel_group,applies_to,parallel,serial_cap,serial_exact,exclusive_note,numbering_note,verification_status) values "
            + values(rule_rows)
            + " on conflict (id) do update set serial_cap=excluded.serial_cap,serial_exact=excluded.serial_exact,"
              "exclusive_note=excluded.exclusive_note,numbering_note=excluded.numbering_note,"
              "verification_status=excluded.verification_status;"
        )
        statements.append(
            "insert into public.catalogue_sources (id,set_id,source,purpose,url,notes) values "
            + values([
                ["2024-panini-national-treasures-wwe-checklist", SET_ID, "GTS Distribution / Panini", "Checklist", SOURCE,
                 "Published Panini workbook with 3,550 exact printed versions; original scheduled release Dec 13, 2024; current hobby guides report Dec 31, 2024"],
                ["2024-panini-national-treasures-wwe-panini", SET_ID, "Panini America", "Checklist index", PRODUCT,
                 "Official manufacturer checklist search"],
            ])
            + " on conflict (id) do update set url=excluded.url,notes=excluded.notes;"
        )
        for index, statement in enumerate(statements, 1):
            (args.sql_dir / f"{index:02d}.sql").write_text(f"begin;\n{statement}\ncommit;\n", encoding="utf-8")

    print(
        f"Validated {len(cards)} stable identities across {len(SUBSETS)} subsets "
        f"and {len(variants)} exact numbered versions."
    )


if __name__ == "__main__":
    main()
