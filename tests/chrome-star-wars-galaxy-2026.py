"""Galaxy source reconciliation and preservation of every earlier set."""
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import add_2026_topps_chrome_star_wars_galaxy as galaxy
from catalogue_io import load_catalogue,save_catalogue
from prepare_star_wars_galaxy_import import generate,OUT


class GalaxyImport(unittest.TestCase):
    def test_manufacturer_reconciliation(self):
        source=json.loads(galaxy.SOURCE.read_text());record,cards,variants=galaxy.build(source)
        self.assertEqual(sum(len(s['rows']) for s in source['subsets']),366)
        self.assertEqual((len(cards),len(record['subsets'])),(323,14))
        self.assertEqual(len(source['sketchArtists']),218)
        self.assertEqual(len({c['id'] for c in cards}),323)
        self.assertEqual(len({(c['subsetCode'],c['number']) for c in cards}),323)
        self.assertEqual([c['order'] for c in cards],list(range(1,324)))
        self.assertEqual({c['number'] for c in cards if c['subsetCode']=='BASE'},set(map(str,range(1,101))))
        self.assertEqual([sum(c['category']==kind for c in cards) for kind in ['Base','Insert','Autograph']],[100,137,86])
        self.assertEqual([sum(c['subsetCode']==code for c in cards) for code in ['DUAL','TRIPLE','QUAD']],[10,9,5])
        indexed={c['id']:c for c in cards}
        self.assertEqual(indexed['2026-TCSWG-BASE-56']['name'],"You're Not Actually Going Into an Asteroid Field?")
        self.assertEqual(indexed['2026-TCSWG-AUTO-GA-BDH']['name'],'Director (Bryce Dallas Howard)')
        self.assertEqual(indexed['2026-TCSWG-AUTO-GA-CHEW']['name'],'Chewbacca (Joonas Suotamo)')
        quad=next(c for c in cards if c['number']=='Q-P15')
        self.assertEqual(quad['name'].count(' / '),3)
        self.assertTrue(all(v['serial_cap'] is None for v in variants))
        self.assertTrue(all(v['card_id'] in indexed for v in variants))
        self.assertEqual(len(variants),323)

    def test_odds_and_artist_credits(self):
        source=json.loads(galaxy.SOURCE.read_text())
        self.assertEqual(len(source['odds']),110)
        data=galaxy.tables()
        self.assertEqual(len(data['catalogue_parallel_rules']),107)
        self.assertFalse(any('Sketch' in r['parallel'] for r in data['catalogue_parallel_rules']))
        self.assertTrue(all(r['serial_cap'] is None for r in data['catalogue_parallel_rules']))
        card=next(c for c in data['catalogue_cards'] if c['id']=='2026-TCSWG-BASE-1')
        self.assertIn('Artist credit: Claudio Aboy.',card['notes'])

    def test_preservation_repeat_and_number_collisions(self):
        base='109ff57850cdb470a1e05ae4bc25bc6a685b42b9'
        def previous(path):return subprocess.check_output(['git','show',f'{base}:{path}'],cwd=ROOT)
        old_index=json.loads(previous('data/catalogue-index.json'))
        catalogue=load_catalogue()
        self.assertEqual(len([c for c in catalogue['cards'] if c['setId']==galaxy.SET_ID]),323)
        for record in old_index['sets']:
            self.assertEqual((ROOT/'data'/record['file']).read_bytes(),previous('data/'+record['file']))
            self.assertEqual(next(s for s in catalogue['sets'] if s['id']==record['id']),{k:v for k,v in record.items() if k!='file'})
        self.assertEqual((ROOT/'data/catalogue.json').read_bytes(),previous('data/catalogue.json'))
        copies=[c for c in catalogue['cards'] if c['number']=='VC-16' and c['setId'].startswith('2026-topps-chrome-star-wars')]
        self.assertEqual(len(copies),2)
        self.assertEqual(len({c['id'] for c in copies}),2)
        record,cards,_=galaxy.build();before={p:p.read_bytes() for p in (ROOT/'data').glob('**/*.json')}
        save_catalogue(galaxy.apply(copy.deepcopy(catalogue),record,cards))
        self.assertTrue(all(p.read_bytes()==v for p,v in before.items()))
        broken=copy.deepcopy(catalogue);next(c for c in broken['cards'] if c['setId']==galaxy.SET_ID)['name']='Conflict'
        with self.assertRaises(ValueError):galaxy.apply(broken,record,cards)

    def test_invalid_source_and_guarded_sql(self):
        source=json.loads(galaxy.SOURCE.read_text());source['subsets'][0]['rows'].pop()
        with self.assertRaises(ValueError):galaxy.build(source)
        sql=generate();self.assertEqual(sql,OUT.read_text())
        self.assertNotRegex(sql.lower(),r'(insert into|update|delete from|truncate) public\.(collection_items|reference_images)')
        self.assertIn('Conflicting catalogue_cards identity',sql)
        self.assertTrue(sql.rstrip().endswith('commit;'))


if __name__=='__main__':unittest.main()
