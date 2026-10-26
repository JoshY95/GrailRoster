"""Galactic Antiquities source coverage, book identities and additive preservation."""
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import add_2024_topps_star_wars_galactic_antiquities as s
from catalogue_io import load_catalogue, save_catalogue
from prepare_star_wars_galactic_antiquities_2024_import import generate, OUT

class GalacticAntiquities2024(unittest.TestCase):
    def test_source_coverage_and_numbering(self):
        source = json.loads(s.SOURCE.read_text())
        r, c, v = s.build(source)
        self.assertEqual((len(c), len(r['subsets'])), (165, 10))
        self.assertEqual((r['year'], r['releaseDate'], r['categoryId']), (2024, '2025-02-05', 'star-wars'))
        self.assertEqual(sum(len(x['rows']) for x in source['subsets']), 177)
        self.assertEqual([x['count'] for x in r['subsets']], s.EXPECTED_COUNTS)
        self.assertEqual(len({x['id'] for x in c}), 165)
        self.assertEqual([x['order'] for x in c], list(range(1, 166)))
        self.assertEqual([sum(x['category'] == k for x in c) for k in ['Base', 'Autograph']], [90, 75])
        self.assertEqual(len(v), 165)
        self.assertTrue(all(x['serial_cap'] is None for x in v))

    def test_books_base_and_source_anomalies(self):
        source = json.loads(s.SOURCE.read_text())
        d = {x['id']: x for x in s.build(source)[1]}
        self.assertEqual(d['2024-TSWGA-BASE-1']['name'], 'Admiral Motti')
        self.assertEqual(d['2024-TSWGA-METAL-1']['name'], 'Admiral Ackbar')
        self.assertEqual(d['2024-TSWGA-BASE-46']['name'], 'Q’ira')
        self.assertEqual(d['2024-TSWGA-BASE-1']['roster'], 'Star Wars: A New Hope')
        self.assertEqual(d['2024-TSWGA-PTA-A-AS']['subset'], 'PREQUEL TRILOGY AUTOGRAPHS')
        self.assertIn('Supreme Leader Snoke (Andy Serkis)', d['2024-TSWGA-PTA-A-AS']['name'])
        self.assertIn('Jar Jar Binks (Ahmed Best)', d['2024-TSWGA-OTA-A-AB']['name'])
        self.assertIn('Kanan Jarrus (Freddie Prinze Jr.)', d['2024-TSWGA-STA-A-FP']['name'])
        for number in ['BC-O', 'BC-X']:
            book = d['2024-TSWGA-BC-' + number]
            self.assertEqual(len(book['name'].split(' / ')), 7)
            self.assertIn('Harrison Ford', book['name'])
        self.assertIn('David Prowse', d['2024-TSWGA-BC-BC-O']['name'])
        self.assertIn('Natalie Portman', d['2024-TSWGA-BC-BC-X']['name'])
        self.assertEqual(len(source['sketchArtists']), 47)
        self.assertEqual(len({x['name'] for x in source['sketchArtists']}), 47)
        self.assertNotIn('Alex Mines', ' '.join(x['name'] for x in d.values()))

    def test_odds_pairing_and_no_guessed_mapping(self):
        source = json.loads(s.SOURCE.read_text())
        tables = s.tables()
        odds, rules = source['odds'], tables['catalogue_parallel_rules']
        self.assertEqual((len(odds), len(rules), len(tables['catalogue_sources'])), (47, 31, 3))
        self.assertEqual((odds[0]['label'], odds[0]['hobby']), ('BASE CARDS CHARACTERS', '1:1'))
        self.assertEqual((odds[31]['label'], odds[31]['hobby']), ('AUTOGRAPH BOOK CARD GOLD', '1:1,009'))
        self.assertEqual((odds[-1]['labelPage'], odds[-1]['ratePage'], odds[-1]['hobby']), (2, 4, '1:1'))
        self.assertTrue(all(x['serial_cap'] is None for x in rules))
        self.assertEqual({x['parallel_group'] for x in rules}, {'BASE', 'METAL', 'FA', 'BC', 'WA', 'MA', 'TA'})
        self.assertFalse(any(x['parallel_group'] in ['PTA', 'OTA', 'STA'] for x in rules))
        self.assertEqual(sum(x['label'].startswith(('AUTOGRAPHS A DESIGN', 'AUTOGRAPHS B DESIGN', 'AUTOGRAPHS C DESIGN')) for x in odds), 15)

    def test_preservation_repeat_and_conflict(self):
        def old(path):
            return subprocess.check_output(['git', 'show', f'4543c5c:{path}'], cwd=ROOT)
        prior = json.loads(old('data/catalogue-index.json'))
        current = load_catalogue()
        self.assertGreaterEqual(len(current['sets']), 36)
        self.assertGreaterEqual(len(current['cards']), 17648)
        self.assertGreaterEqual(sum(x['cardCount'] for x in current['sets'] if x['categoryId'] == 'star-wars'), 6350)
        for row in prior['sets']:
            self.assertEqual((ROOT / 'data' / row['file']).read_bytes(), old('data/' + row['file']))
            self.assertEqual(next(x for x in current['sets'] if x['id'] == row['id']), {k: v for k, v in row.items() if k != 'file'})
        self.assertEqual((ROOT / 'data/catalogue.json').read_bytes(), old('data/catalogue.json'))
        r, c, _ = s.build()
        before = {p: p.read_bytes() for p in (ROOT / 'data').glob('**/*.json')}
        save_catalogue(s.apply(copy.deepcopy(current), r, c))
        self.assertTrue(all(p.read_bytes() == b for p, b in before.items()))
        bad = copy.deepcopy(current)
        next(x for x in bad['cards'] if x['setId'] == s.SET_ID)['name'] = 'Conflict'
        with self.assertRaises(ValueError):
            s.apply(bad, r, c)

    def test_bad_evidence_and_guarded_sql(self):
        for index in range(10):
            source = json.loads(s.SOURCE.read_text())
            source['subsets'][index]['rows'].pop()
            with self.assertRaises(ValueError):
                s.build(source)
        source = json.loads(s.SOURCE.read_text())
        source['subsets'][0]['rows'][1]['number'] = '1'
        with self.assertRaises(ValueError):
            s.build(source)
        sql = generate()
        self.assertEqual(sql, OUT.read_text())
        self.assertTrue(sql.rstrip().endswith('commit;'))
        self.assertNotRegex(sql.lower(), r'(insert into|update|delete from|truncate) public\.(collection_items|reference_images)')
        self.assertIn('Conflicting catalogue_cards identity', sql)

if __name__ == '__main__':
    unittest.main()
