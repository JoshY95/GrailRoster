#!/usr/bin/env python3
from pathlib import Path
from add_2024_topps_star_wars_galactic_antiquities import tables, SET_ID
from prepare_star_wars_chrome_import import generate as additive
OUT = Path(__file__).resolve().parents[1] / 'supabase/corrections/2026-10-26-star-wars-galactic-antiquities-2024.sql'
def generate():
    return additive(tables(), set_id=SET_ID, baseline_sets=35, baseline_cards=17483)
if __name__ == '__main__':
    OUT.write_text(generate())
    print('Generated guarded Galactic Antiquities import', OUT.stat().st_size, 'bytes')
