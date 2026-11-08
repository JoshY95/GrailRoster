"""Add official 2026 Topps NOW #114–116 without renumbering existing cards."""
import json
from pathlib import Path
from catalogue_io import load_catalogue, save_catalogue
from prepare_october_catalogue_update import insert_guarded

ROOT = Path(__file__).resolve().parents[1]
SID = '2026-topps-now-wwe'
SRC = ROOT / 'sources/topps-now-2025-2026/2026-11-09-now-114-116.json'
SQL = ROOT / 'supabase/corrections/2026-11-09-now-114-116.sql'


def records():
    evidence = json.loads(SRC.read_text())
    cards, variants, sources = [], [], []
    for i, item in enumerate(evidence):
        number, name = item['number'], item['subject']
        cid = f'2026-TNWWE-BASE-{number}'
        order = 138 + i
        notes = (f"US sale window {item['releaseDate']} to {item['saleEnd']}. Official product number {number}; "
                 "physical back not independently inspected. Final print run pending. "
                 "Conditional Chrome/Opal editions excluded. " + item['variationNote'])
        cards.append(dict(id=cid, set_id=SID, checklist_order=order, category='Base', subset_code='BASE',
                          card_number=number, display_name=name, subject_1=name, subject_2=None,
                          roster=item['roster'], rookie=False, parallel_group='BASE', image_status='Missing',
                          pricing_status='Unpriced', source_url=item['source'], notes=notes))
        edition_rows = [('IDENTITY', 'Checklist identity', None, None)] + [
            (v['parallel'].upper().replace(' ', '-'), v['parallel'], v['serialCap'], None)
            for v in item['publishedEditions']]
        edition_rows += [(f'IMAGE-VARIATION-{v.upper().replace(" ", "-")}',
                          f'{v} Image Variation Short Print', None, v)
                         for v in item['imageVariations']]
        for j, (suffix, parallel, cap, variation) in enumerate(edition_rows):
            variants.append(dict(id=f'{cid}-{suffix}', set_id=SID, card_id=cid,
                                 variant_order=187 + len(variants), subset='Regular', card_number=number,
                                 display_name=name, parallel=parallel, serial_cap=cap,
                                 serial_exact=('1/1' if cap == 1 else f'/{cap}') if cap else None,
                                 exclusive_note=None,
                                 numbering_note=('Topps advertises this named image variation; quantity and printed code unverified.'
                                                 if variation else 'Unnumbered checklist identity; print run is not a serial cap.'
                                                 if cap is None else 'Card-specific Topps product listing names this foil and serial cap.'),
                                 verification_status='Official Topps product listing'))
        sources.append(dict(id=cid+'-SOURCE', set_id=SID, source='Topps official product page',
                            purpose=f'Card {number} identity and advertised editions', url=item['source'], notes=notes))
    return cards, variants, sources


def generate_sql():
    cards, variants, sources = records()
    assert len(cards) == 3 and len(variants) == 23 and len(sources) == 3
    tables = ['catalogue_sets', 'catalogue_subsets', 'catalogue_cards', 'catalogue_variants',
              'catalogue_sources', 'catalogue_parallel_rules', 'collection_items', 'reference_images']
    def projection(table):
        if table == 'catalogue_sets':
            return f"case when t.id='{SID}' then to_jsonb(t)-'card_count'-'variant_count'-'updated_at' else to_jsonb(t) end"
        if table == 'catalogue_subsets':
            return f"case when t.set_id='{SID}' and t.subset_code='BASE' then to_jsonb(t)-'card_count' else to_jsonb(t) end"
        return 'to_jsonb(t)'
    sql = ["begin; set local lock_timeout='5s';",
           'lock table '+','.join('public.'+t for t in tables)+' in share row exclusive mode;']
    for table in tables:
        sql.append(f'create temporary table before_{table} on commit drop as select {projection(table)} as row from public.{table} t;')
    sql.append(f"""do $$ begin
      if (select count(*) from public.catalogue_cards where set_id='{SID}') not in (137,140)
      or (select count(*) from public.catalogue_variants where set_id='{SID}') not in (186,209)
      or exists(select 1 from public.catalogue_cards where set_id='{SID}' and card_number in ('114','115','116') and id<>'2026-TNWWE-BASE-'||card_number)
      or exists(select 1 from public.catalogue_cards where set_id='{SID}' and checklist_order between 138 and 140 and id not in ('2026-TNWWE-BASE-114','2026-TNWWE-BASE-115','2026-TNWWE-BASE-116'))
      or exists(select 1 from public.catalogue_variants where set_id='{SID}' and variant_order between 187 and 209 and card_id not in ('2026-TNWWE-BASE-114','2026-TNWWE-BASE-115','2026-TNWWE-BASE-116'))
      then raise exception 'Unexpected annual baseline'; end if;
    end $$;""")
    for table, rows in [('catalogue_cards', cards), ('catalogue_variants', variants), ('catalogue_sources', sources)]:
        sql.append(insert_guarded(table, rows))
    sql.append(f"""update public.catalogue_subsets set card_count=118 where set_id='{SID}' and subset_code='BASE' and card_count=115;
    update public.catalogue_sets set card_count=140,variant_count=209,updated_at=now() where id='{SID}' and (card_count,variant_count)=(137,186);
    do $$ begin
      if (select count(*) from public.catalogue_cards where set_id='{SID}')<>140
      or (select count(*) from public.catalogue_variants where set_id='{SID}')<>209
      or (select count(*) from public.catalogue_cards where set_id='{SID}' and subset_code='BASE')<>118
      or not exists(select 1 from public.catalogue_subsets where set_id='{SID}' and subset_code='BASE' and card_count=118)
      or not exists(select 1 from public.catalogue_sets where id='{SID}' and card_count=140 and variant_count=209)
      then raise exception 'Annual count validation failed'; end if;
    end $$;""")
    for table in tables:
        proj = projection(table)
        sql.append(f"do $$ begin if exists(select row from before_{table} except all select {proj} from public.{table} t) then raise exception 'Existing {table} rows changed'; end if; end $$;")
        if table in ('catalogue_sets','catalogue_subsets','catalogue_parallel_rules','collection_items','reference_images'):
            sql.append(f"do $$ begin if exists(select {proj} from public.{table} t except all select row from before_{table}) then raise exception 'Unexpected {table} rows'; end if; end $$;")
    sql.append("select 'NOW 114-116 verified' as result,(select count(*) from public.catalogue_cards) as cards,(select count(*) from public.collection_items) as collections;\ncommit;")
    return '\n'.join(sql)+'\n'


def main():
    catalogue = load_catalogue()
    cards, variants, _ = records()
    existing = {c['id'] for c in catalogue['cards']}
    if any(c['id'] in existing for c in cards):
        raise ValueError('Already imported; refusing duplicate append')
    item = next(s for s in catalogue['sets'] if s['id'] == SID)
    assert item['cardCount'] == 137 and catalogue['cardCount'] == 25290
    assert [(c['number'], c['order']) for c in catalogue['cards'] if c['setId'] == SID][-1] == ('CJ26', 137)
    catalogue['cards'].extend(dict(id=c['id'], setId=SID, order=c['checklist_order'], number=c['card_number'],
                                   name=c['display_name'], subject2=None, category='Base', subset='Regular',
                                   subsetCode='BASE', roster=c['roster'], rookie='No', parallelGroup='BASE') for c in cards)
    item['cardCount'] += len(cards)
    next(s for s in item['subsets'] if s['code'] == 'BASE')['count'] += len(cards)
    save_catalogue(catalogue)
    SQL.write_text('-- Official Topps NOW #114–116; guarded catalogue-only append.\n'+generate_sql())
    print(f'Added {len(cards)} identities, {len(variants)} editions; catalogue {catalogue["cardCount"]+len(cards)} cards.')


if __name__ == '__main__':
    main()
