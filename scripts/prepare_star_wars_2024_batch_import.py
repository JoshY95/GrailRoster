#!/usr/bin/env python3
"""Atomic three-set additive transaction; all previous catalogue/collector rows immutable."""
import json
from collections import OrderedDict
from pathlib import Path
from star_wars_2024_batch import CONFIGS, tables
OUT = Path(__file__).resolve().parents[1] / 'supabase/corrections/2026-10-26-star-wars-2024-batch.sql'

def generate():
    parts = [tables(k) for k in CONFIGS]
    data = OrderedDict((t, [r for p in parts for r in p[t]]) for t in parts[0])
    ids = [c['id'] for c in CONFIGS.values()]
    final_cards = 17648 + len(data['catalogue_cards'])
    watched = [*data, 'collection_items', 'reference_images']
    sql = ['-- Generated atomic three-set import; additive catalogue data only.', 'begin;',
           "set local lock_timeout='5s';", 'lock table '+','.join('public.'+t for t in data)+' in share row exclusive mode;']
    for table in watched:
        sql.append(f'create temporary table before_{table} on commit drop as select to_jsonb(t) as row from public.{table} t;')
    quoted_ids = ','.join("'"+sid+"'" for sid in ids)
    sql.append(f"""do $$ begin
 if (select count(*) from public.catalogue_sets) not in (36,39)
 or (select count(*) from public.catalogue_cards) not in (17648,{final_cards})
 or ((select count(*) from public.catalogue_sets)=39 and (select count(*) from public.catalogue_sets where id in ({quoted_ids}))<>3)
 then raise exception 'Catalogue baseline changed; review batch import'; end if;
end $$;""")
    for table, rows in data.items():
        columns = list(rows[0]); desired = 'desired_'+table
        payload = json.dumps(rows,ensure_ascii=False,separators=(',',':')).replace("'","''")
        sql.append(f"create temporary table {desired} on commit drop as select * from jsonb_populate_recordset(null::public.{table},'{payload}'::jsonb);")
        key = 't.set_id=e.set_id and t.subset_code=e.subset_code' if table=='catalogue_subsets' else 't.id=e.id'
        comparison = ' or '.join(f't.{c} is distinct from e.{c}' for c in columns)
        sql.append(f"""do $$ begin
 if exists(select 1 from public.{table} t join {desired} e on {key} where {comparison})
 then raise exception 'Conflicting {table} identity; refusing overwrite'; end if;
end $$;
insert into public.{table}({','.join(columns)}) select {','.join(columns)} from {desired} on conflict do nothing;""")
    conditions = []
    for part,sid in zip(parts,ids):
        for table, rows in part.items():
            key = 'id' if table=='catalogue_sets' else 'set_id'
            conditions.append(f"(select count(*) from public.{table} where {key}='{sid}')<>{len(rows)}")
    conditions += [f'(select count(*) from public.catalogue_sets)<>39', f'(select count(*) from public.catalogue_cards)<>{final_cards}',
        f"exists(select 1 from public.catalogue_variants v left join public.catalogue_cards c on c.id=v.card_id where v.set_id in ({quoted_ids}) and (c.id is null or c.set_id<>v.set_id))",
        f"exists(select 1 from public.catalogue_subsets s where s.set_id in ({quoted_ids}) and s.card_count<>(select count(*) from public.catalogue_cards c where c.set_id=s.set_id and c.subset_code=s.subset_code))"]
    for table in watched:
        conditions.append(f'exists(select row from before_{table} except all select to_jsonb(t) from public.{table} t)')
    for table in ['collection_items','reference_images']:
        conditions.append(f'exists(select to_jsonb(t) from public.{table} t except all select row from before_{table})')
    sql.append('do $$ begin\n if '+'\n or '.join(conditions)+"\n then raise exception 'Count, linkage or preservation check failed'; end if;\nend $$;")
    sql.append("select 'verified' as result,(select count(*) from public.catalogue_cards) as cards,(select count(*) from public.collection_items) as collections;")
    sql.append('commit;')
    return '\n'.join(sql)+'\n'

if __name__=='__main__':
    OUT.write_text(generate()); print('Generated guarded three-set import',OUT.stat().st_size,'bytes')
