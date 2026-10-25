#!/usr/bin/env python3
"""Use the reviewed additive transaction with Galaxy's baseline and exact rows."""
from pathlib import Path
from add_2026_topps_chrome_star_wars_galaxy import tables,SET_ID
from prepare_star_wars_chrome_import import generate as generate_additive

OUT=Path(__file__).resolve().parents[1]/'supabase/corrections/2026-10-25-chrome-star-wars-galaxy.sql'


def generate():
    return generate_additive(tables(),set_id=SET_ID,baseline_sets=25,baseline_cards=12602)


if __name__=='__main__':
    OUT.write_text(generate())
    print(f'Generated guarded Galaxy import: {OUT.stat().st_size} bytes')
