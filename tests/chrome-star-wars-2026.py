"""Manufacturer reconciliation, first-franchise import and immutable WWE regression."""
import copy
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import add_2026_topps_chrome_star_wars as sw
from catalogue_io import load_catalogue,save_catalogue
from prepare_star_wars_chrome_import import generate,OUT


class ChromeStarWars(unittest.TestCase):
    def test_official_identities(self):
        source=json.loads(sw.SOURCE.read_text())
        record,cards,variants=sw.build(source)
        self.assertEqual((len(cards),len(record['subsets'])),(1304,27))
        self.assertEqual(sum(len(s['rows']) for s in source['subsets']),1369)
        self.assertEqual(len(source['sketchArtists']),134)
        self.assertEqual(record['categoryId'],'star-wars')
        self.assertEqual(len({c['id'] for c in cards}),1304)
        self.assertEqual(len({(c['subsetCode'],c['number']) for c in cards}),1304)
        self.assertEqual([c['order'] for c in cards],list(range(1,1305)))
        by_id={c['id']:c for c in cards}
        self.assertEqual(by_id['2026-TCSW-BASE-127']['name'],'Imperial Remnant Snowtrooper')
        self.assertEqual(by_id['2026-TCSW-AUTO-156']['name'],'Gatori (Stephen McKinley Henderson)')
        self.assertEqual(by_id['2026-TCSW-GMAX-GMAX-CHEWIE']['name'],'Chewbacca')
        self.assertTrue('2026-TCSW-PLATE-PALTE-194' in by_id,'Preserve the printed PALTE typo')
        self.assertEqual(by_id['2026-TCSW-GMAX-GMAX-VADER']['name'],'Darth Vader')
        self.assertEqual(sum(c['subsetCode']=='DUO' for c in cards),22)
        self.assertEqual(sum(c['subsetCode']=='TRIP' for c in cards),19)
        self.assertIn('Obi-Wan Kenobi (Ewan McGregor)',by_id['2026-TCSW-DUO-DUO-HE']['name'])
        self.assertFalse(any(c['subsetCode']=='HG' for c in cards))
        self.assertFalse(any(c['rookie']!='No' for c in cards))
        self.assertEqual(len(variants),1304)
        self.assertTrue(all(v['serial_cap'] is None and v['card_id'] in by_id for v in variants))

    def test_odds_boundaries(self):
        source=json.loads(sw.SOURCE.read_text())
        self.assertEqual(len(source['odds']),186)
        rules=sw.tables()['catalogue_parallel_rules']
        self.assertEqual(len(rules),151)
        self.assertFalse(any('SAPPHIRE' in r['parallel'] or 'DESIGN VARIATION' in r['parallel'] for r in rules))
        self.assertEqual([(r['parallel'],r['serial_cap']) for r in rules if r['serial_cap']],[('SW LOGOFRACTOR',77)])

    def test_preservation_and_repeat_import(self):
        base='b579bc05bf19229b87ab9437a2394ee19d5bf10f'
        def old(path):return subprocess.check_output(['git','show',f'{base}:{path}'],cwd=ROOT)
        old_index=json.loads(old('data/catalogue-index.json'))
        current=load_catalogue()
        self.assertEqual(len([c for c in current['cards'] if c['setId']==sw.SET_ID]),1304)
        for record in old_index['sets']:
            self.assertEqual((ROOT/'data'/record['file']).read_bytes(),old('data/'+record['file']))
            self.assertEqual(next(s for s in current['sets'] if s['id']==record['id']),{k:v for k,v in record.items() if k!='file'})
        self.assertEqual((ROOT/'data/catalogue.json').read_bytes(),old('data/catalogue.json'))
        before={p:p.read_bytes() for p in (ROOT/'data').glob('**/*.json')}
        record,cards,_=sw.build()
        save_catalogue(sw.apply(copy.deepcopy(current),record,cards))
        self.assertTrue(all(p.read_bytes()==data for p,data in before.items()))
        broken=copy.deepcopy(current)
        next(c for c in broken['cards'] if c['setId']==sw.SET_ID)['name']='Conflicting card'
        with self.assertRaises(ValueError):sw.apply(broken,record,cards)

    def test_bad_source_and_sql_guards(self):
        source=json.loads(sw.SOURCE.read_text());source['subsets'][0]['rows'].pop()
        with self.assertRaises(ValueError):sw.build(source)
        sql=generate()
        self.assertEqual(sql,OUT.read_text())
        self.assertNotRegex(sql.lower(),r'(insert into|update|delete from|truncate) public\.(collection_items|reference_images)')
        self.assertIn('Conflicting catalogue_cards identity',sql)
        self.assertTrue(sql.rstrip().endswith('commit;'))


if __name__=='__main__':unittest.main()
