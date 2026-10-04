"""Import reviewed Topps product listings; boxed Vegas identities already exist."""
import json
from pathlib import Path
from catalogue_io import load_catalogue, save_catalogue

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'sources/topps-now-2025-2026/releases.json'
GROUPS = {'Regular': ('BASE', 'Base'), 'Hall of Fame': ('HOF', 'Base'),
          'Event poster': ('POSTER', 'Base'), 'Special card': ('SPECIAL', 'Base'),
          'Crossover (WBC)': ('WBC', 'Base')}

def build():
    source = json.loads(SOURCE.read_text())
    rows = source['annualCards']
    if len(rows) != 281 or len({(r['year'], r['number']) for r in rows}) != 281:
        raise ValueError('Expected 281 unique reviewed releases')
    for year, maximum in ((2025, 140), (2026, 104)):
        if {int(r['number']) for r in rows if r['year'] == year and r['number'].isdigit()} != set(range(1, maximum + 1)):
            raise ValueError('Regular card numbers do not match reviewed source')
    result = []
    for year, crossover in ((2025, False), (2026, False), (2026, True)):
        selected = [r for r in rows if r['year'] == year and (r['group'] == 'Crossover (WBC)') == crossover]
        sid = f'{year}-topps-now-wwe' + ('-crossovers' if crossover else '')
        expected = 1 if crossover else 157 if year == 2025 else 123
        if len(selected) != expected: raise ValueError('Unexpected annual count')
        subsets = []
        for group, (code, category) in GROUPS.items():
            count = sum(r['group'] == group for r in selected)
            if count: subsets.append({'category': category, 'name': group, 'code': code, 'count': count})
        record = {'id': sid, 'name': f'{year} Topps NOW WWE' + (' Crossovers' if crossover else ''),
                  'shortName': 'NOW Crossovers' if crossover else 'Topps NOW', 'accent': '#f59e0b',
                  'year': year, 'manufacturer': 'Topps', 'releaseDate': min(r['releaseDate'] for r in selected),
                  'cardCount': len(selected), 'subsetCount': len(subsets), 'subsets': subsets}
        cards = []
        for order, row in enumerate(selected, 1):
            code, category = GROUPS[row['group']]
            subjects = [s.strip() for s in row['subject'].split('/')]
            cards.append({'id': f'{year}-TNWWE-{code}-{row["number"]}', 'setId': sid, 'order': order,
                          'number': row['number'], 'name': row['subject'], 'subject2': ' / '.join(subjects[1:]) or None,
                          'category': category, 'subset': row['group'], 'subsetCode': code,
                          'roster': None, 'rookie': 'No', 'parallelGroup': code})
        result.append((record, cards, selected))
    return result

def apply(catalogue, additions):
    # Validate every existing imported set before saving any changes.
    for record, cards, _ in additions:
        old_sets = [s for s in catalogue['sets'] if s['id'] == record['id']]
        old_cards = [c for c in catalogue['cards'] if c['setId'] == record['id']]
        if (old_sets or old_cards) and (old_sets != [record] or old_cards != cards):
            raise ValueError('Conflicting existing NOW data; refusing overwrite')
    for record, cards, _ in additions:
        if not any(s['id'] == record['id'] for s in catalogue['sets']):
            catalogue['sets'].append(record); catalogue['cards'].extend(cards)
    catalogue['sets'].sort(key=lambda s: (s.get('releaseDate') or '', s['name']), reverse=True)
    position = {s['id']: i for i, s in enumerate(catalogue['sets'])}
    catalogue['cards'].sort(key=lambda c: (position[c['setId']], c['order']))
    catalogue['setCount'] = len(catalogue['sets']); catalogue['cardCount'] = len(catalogue['cards'])
    return catalogue

def sql(additions):
    tables = {'catalogue_sets': [], 'catalogue_subsets': [], 'catalogue_cards': [], 'catalogue_variants': []}
    archive = 'https://www.topps.com/collections/wwe-topps-now-archive?stock_status=ALL_STOCK'
    for s, cards, rows in additions:
        tables['catalogue_sets'].append(dict(id=s['id'], name=s['name'], short_name=s['shortName'], year=s['year'],
            manufacturer='Topps', release_date=s['releaseDate'], source_file=archive, accent=s['accent'],
            card_count=s['cardCount'], subset_count=s['subsetCount'], variant_count=len(cards)))
        for sub in s['subsets']:
            tables['catalogue_subsets'].append(dict(set_id=s['id'], subset_code=sub['code'], category=sub['category'],
                name=sub['name'], card_count=sub['count'], parallel_group=sub['code'], source_url=archive))
        for c, r in zip(cards, rows):
            tables['catalogue_cards'].append(dict(id=c['id'], set_id=s['id'], checklist_order=c['order'], category=c['category'],
                subset_code=c['subsetCode'], card_number=c['number'], display_name=c['name'], subject_1=c['name'].split('/')[0].strip(),
                subject_2=c['subject2'], roster=None, rookie=False, parallel_group=c['parallelGroup'],
                image_status='Missing', pricing_status='Unpriced', source_url=r['source'],
                notes=f"Topps product listing; available {r['releaseDate']}; base print run: {r['printRun'] if r['printRun'] is not None else 'not yet published'}. Published extras retained in sources/topps-now-2025-2026/releases.json; numbered editions not inferred."))
            tables['catalogue_variants'].append(dict(id=c['id']+'-IDENTITY', set_id=s['id'], card_id=c['id'],
                variant_order=c['order'], subset=c['subset'], card_number=c['number'], display_name=c['name'],
                parallel='Checklist identity', serial_cap=None, serial_exact=None, exclusive_note=None,
                numbering_note='Unnumbered checklist identity; base print run is not a serial cap.', verification_status='Official Topps product listing'))
    statements = ['BEGIN;']
    for table, rows in tables.items():
        payload = json.dumps(rows, ensure_ascii=False).replace("'", "''")
        columns = ','.join(rows[0])
        # Guard conflicts against the same complete preimage, including identity metadata.
        key = 't.set_id=e.set_id AND t.subset_code=e.subset_code' if table == 'catalogue_subsets' else 't.id=e.id'
        comparisons = ' OR '.join(f't.{k} IS DISTINCT FROM e.{k}' for k in rows[0])
        statements.append(f"DO $$ BEGIN IF EXISTS(SELECT 1 FROM public.{table} t JOIN jsonb_populate_recordset(null::public.{table},'{payload}'::jsonb) e ON {key} WHERE {comparisons}) THEN RAISE EXCEPTION 'Conflicting NOW catalogue data'; END IF; END $$;")
        statements.append(f"INSERT INTO public.{table}({columns}) SELECT {columns} FROM jsonb_populate_recordset(null::public.{table},'{payload}'::jsonb) ON CONFLICT DO NOTHING;")
    ids = ','.join("'"+s['id']+"'" for s, _, _ in additions)
    statements.append(f"DO $$ BEGIN IF (SELECT count(*) FROM public.catalogue_cards WHERE set_id IN ({ids})) <> 281 THEN RAISE EXCEPTION 'NOW total mismatch'; END IF; END $$;")
    statements.append('COMMIT;')
    return '\n'.join(statements)+'\n'

if __name__ == '__main__':
    additions = build()
    save_catalogue(apply(load_catalogue(), additions))
    out = ROOT / 'supabase/generated/topps-now-2025-2026.sql'
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text(sql(additions))
    print('Added 157 + 123 + 1 NOW identities; existing Vegas set unchanged.')
