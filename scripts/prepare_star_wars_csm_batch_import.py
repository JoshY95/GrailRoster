#!/usr/bin/env python3
from pathlib import Path
from star_wars_csm_batch import CONFIGS,tables
from prepare_star_wars_2024_batch_import import generate as atomic
OUT=Path(__file__).resolve().parents[1]/'supabase/corrections/2026-10-26-star-wars-chrome-sapphire-masterwork-batch.sql'
def generate():return atomic([tables(k) for k in CONFIGS],baseline_sets=39,baseline_cards=19219)
if __name__=='__main__':OUT.write_text(generate());print('Generated guarded CSM batch',OUT.stat().st_size,'bytes')
