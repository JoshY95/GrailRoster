"""Source reconciliation and preservation tests for the October catalogue update."""
import copy
import importlib.util
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import add_2026_stadium_club_wwe as stadium
from catalogue_io import load_catalogue, save_catalogue
from prepare_october_catalogue_update import now_rows, generate


class CatalogueUpdate(unittest.TestCase):
    def test_manufacturer_rows(self):
        source = json.loads(stadium.SOURCE.read_text())
        record, cards, variants = stadium.build(source)
        self.assertEqual(sum(len(s['rows']) for s in source['subsets']), 938)
        self.assertEqual((len(cards), len(record['subsets'])), (930, 25))
        self.assertEqual(len({c['id'] for c in cards}), 930)
        self.assertEqual(len({(c['subsetCode'], c['number']) for c in cards}), 930)
        self.assertEqual([c['order'] for c in cards], list(range(1, 931)))
        for code in ('BASE', 'CHROME'):
            self.assertEqual({c['number'] for c in cards if c['subsetCode'] == code}, set(map(str, range(1, 201))))
        by_number = {c['number']: c for c in cards if c['subsetCode'] == 'DA'}
        self.assertEqual(len(by_number), 8)
        self.assertEqual(by_number['DA-RH']['name'], 'Triple H / The Rock')
        self.assertEqual(by_number['DA-SB']['name'], 'Becky Lynch / Seth Rollins')
        self.assertEqual(len([c for c in cards if c['subsetCode'] == 'TV' and c['name'] == 'John Cena']), 3)
        self.assertEqual(next(c['name'] for c in cards if c['subsetCode'] == 'MSA' and c['name'] == 'Rusev'), 'Rusev')
        self.assertEqual(next(c['number'] for c in cards if c['subsetCode'] == 'MSA' and c['name'] == 'Rusev'), 'MRA-RSV')
        self.assertEqual(next(c['name'] for c in cards if c['subsetCode'] == 'BASE' and c['number'] == '8'), '"The American Nightmare" Cody Rhodes')
        self.assertEqual(next(c['name'] for c in cards if c['number'] == 'SCA-MDM'), '"Million Dollar Man" Ted DiBiase')
        self.assertEqual(len(variants), 934)
        ids = {c['id'] for c in cards}
        self.assertTrue(all(v['card_id'] in ids for v in variants))
        self.assertEqual([v['serial_cap'] for v in variants if v['serial_cap']], [1, 1, 1, 25])
        self.assertFalse(any('SCCA-II' in c['id'] for c in cards))
        self.assertEqual(len(stadium.tables()['catalogue_parallel_rules']), 117)
        self.assertTrue(all(r['serial_cap'] is None for r in stadium.tables()['catalogue_parallel_rules']))

    def test_malformed_source_rejected(self):
        source = json.loads(stadium.SOURCE.read_text())
        source['subsets'][0]['rows'].pop()
        with self.assertRaises(ValueError):
            stadium.build(source)
        source = json.loads(stadium.SOURCE.read_text())
        source['subsets'][1]['rows'][0]['number'] = '2'
        with self.assertRaises(ValueError):
            stadium.build(source)

    def test_main_preservation(self):
        base = '3823fb0a4e36e115184164bfacf5cde1032cfbb2'
        def old(path):
            return subprocess.check_output(['git', 'show', f'{base}:{path}'], cwd=ROOT)
        index = json.loads(old('data/catalogue-index.json'))
        current = load_catalogue()
        wwe_sets = [s for s in current['sets'] if s['categoryId'] == 'wwe']
        wwe_ids = {s['id'] for s in wwe_sets}
        self.assertGreaterEqual(len(wwe_sets), 24)
        self.assertGreaterEqual(len([c for c in current['cards'] if c['setId'] in wwe_ids]), 11298)
        now_main = None
        for record in index['sets']:
            path = 'data/' + record['file']
            if record['id'] != '2026-topps-now-wwe':
                self.assertEqual((ROOT / path).read_bytes(), old(path), record['id'])
            else:
                now_main = json.loads(old(path))['cards']
        now_new = json.loads((ROOT / 'data/sets/2026-topps-now-wwe.json').read_text())['cards']
        by_id = {c['id']: c for c in now_new}
        self.assertEqual(len(now_new), 132)
        self.assertEqual([c['order'] for c in now_new], list(range(1, 133)))
        for c in now_main:
            expected = dict(c, order=c['order'] + (6 if c['order'] > 106 else 0))
            self.assertEqual(by_id[c['id']], expected)
        self.assertEqual((ROOT / 'data/catalogue.json').read_bytes(), old('data/catalogue.json'))

    def test_idempotence_and_conflict(self):
        catalogue = load_catalogue()
        record, cards, _ = stadium.build()
        before = {p: p.read_bytes() for p in (ROOT / 'data').glob('**/*.json')}
        save_catalogue(stadium.apply(copy.deepcopy(catalogue), record, cards))
        for p, data in before.items():
            self.assertEqual(p.read_bytes(), data)
        altered = copy.deepcopy(catalogue)
        next(c for c in altered['cards'] if c['setId'] == stadium.SET_ID)['name'] = 'bad'
        with self.assertRaises(ValueError):
            stadium.apply(altered, record, cards)

    def test_now_and_sql(self):
        rows = now_rows()
        self.assertEqual(len(rows['catalogue_cards']), 6)
        variants = rows['catalogue_variants']
        self.assertEqual(len(variants), 36)
        self.assertEqual([v['variant_order'] for v in variants[6:]], list(range(133, 163)))
        self.assertEqual(len({v['id'] for v in variants}), 36)
        for number in map(str, range(107, 113)):
            self.assertEqual([v['serial_cap'] for v in variants if v['card_number'] == number and v['serial_cap']], [50, 25, 10, 5, 1])
        sql = generate()
        self.assertEqual(sql, (ROOT / 'supabase/corrections/2026-10-24-now-stadium-club.sql').read_text())
        self.assertNotRegex(sql.lower(), r'(insert into|update|delete from|truncate) public\.(collection_items|reference_images)')
        self.assertTrue(sql.rstrip().endswith('commit;'))

    def test_complete_2026_now_archive(self):
        audit = json.loads((ROOT / 'sources/topps-now-2025-2026/2026-10-24-archive.json').read_text())
        self.assertEqual(len(audit['products']), 135)
        self.assertEqual(len(audit['pages']), 6)
        self.assertEqual(len({p['id'] for p in audit['products']}), 135)
        numbers = []
        other = []
        for product in audit['products']:
            match = re.search(r'2026 WWE Topps NOW. - Card ([A-Za-z0-9]+)', product['title'])
            if match:
                numbers.append(match[1])
            else:
                other.append(product['title'])
        self.assertEqual(len(numbers), 133)  # 132 identities plus duplicate product #106
        self.assertEqual(numbers.count('106'), 2)
        self.assertEqual({int(n) for n in numbers if n.isdigit()}, set(range(1, 113)))
        self.assertEqual({n for n in numbers if n.startswith('HOF')}, {f'HOF{i}' for i in range(1, 7)})
        current = json.loads((ROOT / 'data/sets/2026-topps-now-wwe.json').read_text())['cards']
        self.assertEqual(set(numbers), {c['number'] for c in current})
        self.assertEqual(len(other), 2)
        self.assertTrue(any('Vegas' in title for title in other))
        self.assertTrue(any('WBCO' in title for title in other))


if __name__ == '__main__':
    unittest.main()
