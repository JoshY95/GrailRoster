"""One guarded Prizm parent import with exact published editions."""
from pathlib import Path
from prizm_wwe_2024 import tables
from prepare_star_wars_2024_batch_import import generate as atomic
from prepare_wwe_2024_batch_import import packed,variants
OUT=Path(__file__).resolve().parents[1]/'supabase/corrections/2026-10-26-prizm-wwe-2024.sql'
def generate():
 data=tables();sql=atomic([data],baseline_sets=45,baseline_cards=22215)
 for table,rows in data.items():
  start=sql.index(f'create temporary table desired_{table} on commit drop as ');end=sql.index(';\ndo $$ begin',start)+1
  replacement=variants(rows) if table=='catalogue_variants' else packed(table,rows)
  if table=='catalogue_variants':replacement=replacement.replace("then 'First Off the Line' else null", "then 'First Off the Line' when parallel like '%Premium Box Set%' then 'Premium Factory Set exclusive' else null")
  sql=sql[:start]+replacement+sql[end:]
 return sql
if __name__=='__main__':OUT.write_text(generate());print('Guarded SQL',OUT.stat().st_size,'bytes')
