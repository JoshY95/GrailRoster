#!/usr/bin/env python3
from pathlib import Path
from add_2024_topps_star_wars_masterwork import tables,SET_ID
from prepare_star_wars_chrome_import import generate as additive
OUT=Path(__file__).resolve().parents[1]/'supabase/corrections/2026-10-26-star-wars-masterwork-2024.sql'
def generate():return additive(tables(),set_id=SET_ID,baseline_sets=33,baseline_cards=16820)
if __name__=='__main__':OUT.write_text(generate());print('Generated guarded Masterwork 2024 import',OUT.stat().st_size,'bytes')
