"""Compact, guarded atomic additive import; no existing row or collector writes."""
import json,re
from pathlib import Path
from wwe_2024_batch import CONFIGS,tables
from prepare_star_wars_2024_batch_import import generate as atomic
OUT=Path(__file__).resolve().parents[1]/'supabase/corrections/2026-10-26-wwe-2024-batch.sql'
def literal(value):return "'"+json.dumps(value,ensure_ascii=False,separators=(',',':')).replace("'","''")+"'::jsonb"
def packed(table,rows):
 columns=list(rows[0]);values=[];lookup={};arrays=[]
 for row in rows:
  refs=[]
  for col in columns:
   v=row[col];k=json.dumps(v,ensure_ascii=False)
   if k not in lookup:lookup[k]=len(values);values.append(v)
   refs.append(lookup[k])
  arrays.append(refs)
 payload=literal(dict(c=columns,v=values,r=arrays))
 return f"create temporary table desired_{table} on commit drop as select (jsonb_populate_record(null::public.{table},(select jsonb_object_agg(k.value,p->'v'->((r.value->>(k.ordinality::int-1))::int)) from jsonb_array_elements_text(p->'c') with ordinality k(value,ordinality)))).* from (select {payload} p) d cross join lateral jsonb_array_elements(p->'r') r(value);"
def variants(rows):
 cards=list(dict.fromkeys(r['card_id'] for r in rows));cardmap={c:i for i,c in enumerate(cards)}
 parallels=list(dict.fromkeys(r['parallel'] for r in rows));pm={p:i for i,p in enumerate(parallels)}
 payload=literal(dict(c=cards,p=parallels,r=[[cardmap[r['card_id']],pm[r['parallel']],r['serial_cap'],r['variant_order']] for r in rows]))
 note=literal(rows[0]['numbering_note']);status=literal(rows[0]['verification_status'])
 return f"""create temporary table desired_catalogue_variants on commit drop as
 with packed as(select {payload} p),expanded as(select c.*,p->'p'->>(r->>1)::int as parallel,(r->>2)::int as cap,(r->>3)::int as vorder
 from packed cross join lateral jsonb_array_elements(p->'r') rowdata(r) join desired_catalogue_cards c on c.id=p->'c'->>(r->>0)::int)
 select id||'-'||trim(both '-' from regexp_replace(upper(parallel),'[^A-Z0-9]+','-','g')) as id,set_id,id as card_id,vorder as variant_order,
 s.name as subset,card_number,display_name,parallel,cap as serial_cap,
 case when cap=1 then '1/1' when cap is not null then '/'||cap::text else null end as serial_exact,
 case when parallel like '%FOTL%' then 'First Off the Line' else null end as exclusive_note,
 {note}#>>'{{}}' as numbering_note,{status}#>>'{{}}' as verification_status
 from expanded e join desired_catalogue_subsets s on s.set_id=e.set_id and s.subset_code=e.subset_code;""".replace("select id||", "select e.id||").replace("as id,set_id,id as card_id", "as id,e.set_id,e.id as card_id")
def generate():
 parts=[tables(k) for k in CONFIGS];sql=atomic(parts,baseline_sets=42,baseline_cards=20616)
 for table in parts[0]:
  rows=[r for part in parts for r in part[table]]
  marker=f'create temporary table desired_{table} on commit drop as '
  start=sql.index(marker);end=sql.index(';\ndo $$ begin',start)+1
  replacement=variants(rows) if table=='catalogue_variants' else packed(table,rows)
  sql=sql[:start]+replacement+sql[end:]
 return sql
if __name__=='__main__':OUT.write_text(generate());print('Guarded compact SQL',OUT.stat().st_size,'bytes')
