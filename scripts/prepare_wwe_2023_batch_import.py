"""Compact atomic additive transaction, preserving all prior rows and collector data."""
from pathlib import Path
from wwe_2023_batch import configs,tables
from prepare_star_wars_2024_batch_import import generate as atomic
from prepare_wwe_2024_batch_import import packed,variants
OUT=Path(__file__).resolve().parents[1]/'supabase/corrections/2026-10-27-wwe-2023-batch.sql'
def generate():
 parts=[tables(k) for k in configs()];sql=atomic(parts,baseline_sets=46,baseline_cards=22731)
 for table in parts[0]:
  rows=[r for part in parts for r in part[table]]
  marker=f'create temporary table desired_{table} on commit drop as '
  start=sql.index(marker);end=sql.index(';\ndo $$ begin',start)+1
  replacement=variants(rows) if table=='catalogue_variants' else packed(table,rows)
  sql=sql[:start]+replacement+sql[end:]
 return sql
if __name__=='__main__':OUT.write_text(generate());print('Guarded SQL',OUT.stat().st_size,'bytes')
