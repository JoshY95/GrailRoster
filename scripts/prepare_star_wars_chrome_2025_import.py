#!/usr/bin/env python3
"""Guarded additive 2025 regular Chrome import."""
from pathlib import Path
from add_2025_topps_chrome_star_wars import tables,SET_ID
from prepare_star_wars_chrome_import import generate as generate_additive
OUT=Path(__file__).resolve().parents[1]/'supabase/corrections/2026-10-26-star-wars-chrome-2025.sql'
def generate():
 return generate_additive(tables(),set_id=SET_ID,baseline_sets=30,baseline_cards=14971)
if __name__=='__main__':
 OUT.write_text(generate());print(f'Generated guarded import: {OUT.stat().st_size} bytes')
