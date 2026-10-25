#!/usr/bin/env python3
"""Generate the guarded Masterwork data-only import from the reviewed baseline."""
from pathlib import Path
from add_2025_topps_star_wars_masterwork import tables,SET_ID
from prepare_star_wars_chrome_import import generate as generate_additive

OUT=Path(__file__).resolve().parents[1]/'supabase/corrections/2026-10-25-star-wars-masterwork.sql'


def generate():
 return generate_additive(tables(),set_id=SET_ID,baseline_sets=26,baseline_cards=12925)


if __name__=='__main__':
 OUT.write_text(generate());print(f'Generated guarded Masterwork import: {OUT.stat().st_size} bytes')
