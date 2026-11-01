"""Generate the narrow, idempotent HH01 catalogue transaction."""
import json
from pathlib import Path
from prepare_october_catalogue_update import insert_guarded

ROOT = Path(__file__).resolve().parents[1]
SID = '2026-topps-now-wwe'
CID = '2026-TNWWE-POSTER-HH01'
SOURCE = json.loads((ROOT / 'sources/topps-now-2025-2026/2026-11-02-hh01.json').read_text())

def generate():
    card = dict(id=CID, set_id=SID, checklist_order=133, category='Base', subset_code='POSTER',
        card_number='HH01', display_name='Halloween Havoc', subject_1='Halloween Havoc', subject_2=None,
        roster=None, rookie=False, parallel_group='POSTER', image_status='Missing', pricing_status='Unpriced',
        source_url=SOURCE['source'], notes='Official Topps product title identifies HH01; on sale 2026-10-30. '
        'Physical card-back code not independently inspected. Final base print run and Rainbow quantity unpublished. '
        'Listed expiry 2027-11-02 is an unresolved source anomaly. Conditional Chrome/Opal editions excluded.')
    variants = []
    for order, suffix, parallel, cap in [(163, 'IDENTITY', 'Checklist identity', None),
        (164, 'RAINBOW-FOIL-SHORT-PRINT', 'Rainbow Foil Short Print', None),
        (165, 'GOLD-SUPER-SHORT-PRINT', 'Gold Super Short Print', 26)]:
        variants.append(dict(id=CID+'-'+suffix, set_id=SID, card_id=CID, variant_order=order,
            subset='Event poster', card_number='HH01', display_name='Halloween Havoc', parallel=parallel,
            serial_cap=cap, serial_exact='/26' if cap else None, exclusive_note=None,
            numbering_note='Card-specific Topps product listing; Rainbow quantity and base print run unpublished.',
            verification_status='Official Topps product listing'))
    source = dict(id=CID+'-SOURCE', set_id=SID, source='Topps official product page',
        purpose='HH01 identity and card-specific advertised editions', url=SOURCE['source'],
        notes='Verified 2026-11-02; no separate checklist. Expiry year unresolved; no conditional Chrome/Opal editions inferred.')
    tables = ['catalogue_sets','catalogue_subsets','catalogue_cards','catalogue_variants',
              'catalogue_sources','catalogue_parallel_rules','collection_items','reference_images']
    sql = ["begin; set local lock_timeout='5s';", 'lock table '+','.join('public.'+t for t in tables)+' in share row exclusive mode;']
    def projection(table):
        if table == 'catalogue_sets':
            return f"case when t.id='{SID}' then to_jsonb(t)-'card_count'-'variant_count'-'updated_at' else to_jsonb(t) end"
        if table == 'catalogue_subsets':
            return f"case when t.set_id='{SID}' and t.subset_code='POSTER' then to_jsonb(t)-'card_count' else to_jsonb(t) end"
        return 'to_jsonb(t)'
    for table in tables:
        sql.append(f'create temporary table before_{table} on commit drop as select {projection(table)} as row from public.{table} t;')
    sql.append(f"""do $$ begin
      if (select count(*) from public.catalogue_cards where set_id='{SID}') not in (132,133)
      or (select count(*) from public.catalogue_variants where set_id='{SID}') not in (162,165)
      or exists(select 1 from public.catalogue_cards where set_id='{SID}' and card_number='HH01' and id<>'{CID}')
      or exists(select 1 from public.catalogue_cards where set_id='{SID}' and checklist_order=133 and id<>'{CID}')
      or exists(select 1 from public.catalogue_variants where set_id='{SID}' and variant_order between 163 and 165 and card_id<>'{CID}')
      then raise exception 'Unexpected NOW baseline; refusing import'; end if;
    end $$;""")
    for table, rows in [('catalogue_cards',[card]),('catalogue_variants',variants),('catalogue_sources',[source])]:
        sql.append(insert_guarded(table, rows))
    sql.append(f"""update public.catalogue_subsets set card_count=15 where set_id='{SID}' and subset_code='POSTER' and card_count=14;
    update public.catalogue_sets set card_count=133,variant_count=165,updated_at=now() where id='{SID}' and (card_count<>133 or variant_count<>165);
    do $$ begin
      if (select count(*) from public.catalogue_cards where set_id='{SID}')<>133
      or (select count(*) from public.catalogue_variants where set_id='{SID}')<>165
      or (select card_count from public.catalogue_sets where id='{SID}')<>133
      or (select variant_count from public.catalogue_sets where id='{SID}')<>165
      or (select card_count from public.catalogue_subsets where set_id='{SID}' and subset_code='POSTER')<>15
      or (select count(*) from public.catalogue_cards where set_id='{SID}' and subset_code='POSTER')<>15
      then raise exception 'HH01 count validation failed'; end if;
    end $$;""")
    for table in tables:
        # Existing full rows must survive unchanged, apart from the two reviewed totals.
        sql.append(f"do $$ begin if exists(select row from before_{table} except all select {projection(table)} from public.{table} t) then raise exception 'Existing {table} rows changed'; end if; end $$;")
        if table in ('collection_items','reference_images','catalogue_parallel_rules','catalogue_subsets','catalogue_sets'):
            sql.append(f"do $$ begin if exists(select {projection(table)} from public.{table} t except all select row from before_{table}) then raise exception 'Unexpected {table} rows'; end if; end $$;")
    sql.append("select 'HH01 verified' as result,(select count(*) from public.catalogue_cards) as cards,(select count(*) from public.collection_items) as collections;\ncommit;")
    return '\n'.join(sql)+'\n'

if __name__ == '__main__':
    (ROOT / 'supabase/corrections/2026-11-02-now-hh01.sql').write_text(generate())
