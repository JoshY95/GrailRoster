"""Manufacturer counts, finite design identities and preservation of all earlier sets."""
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import add_2025_topps_star_wars_masterwork as mw
from catalogue_io import load_catalogue,save_catalogue
from prepare_star_wars_masterwork_import import generate,OUT


class MasterworkImport(unittest.TestCase):
 def test_manufacturer_identity_reconciliation(self):
  source=json.loads(mw.SOURCE.read_text());record,cards,variants=mw.build(source)
  self.assertEqual(sum(len(s['rows']) for s in source['subsets']),660)
  self.assertEqual((len(cards),len(record['subsets'])),(589,19))
  self.assertEqual((record['year'],record['releaseDate'],record['categoryId']),(2025,'2026-06-03','star-wars'))
  self.assertEqual(len(source['sketchArtists']),209)
  self.assertEqual(len(source['unenumeratedProgrammes']),3)
  self.assertEqual(len({c['id'] for c in cards}),589)
  self.assertEqual(len({(c['subsetCode'],c['number']) for c in cards}),589)
  self.assertEqual([c['order'] for c in cards],list(range(1,590)))
  self.assertEqual({c['number'] for c in cards if c['subsetCode']=='BASE'},set(map(str,range(1,101))))
  self.assertEqual([sum(c['category']==x for c in cards) for x in ['Base','Insert','Autograph','Relic','Autograph Relic']],[100,119,120,113,137])
  books=[c for c in cards if c['subsetCode']=='UBC']
  self.assertEqual(len(books),4)
  self.assertTrue(all(c['name'].count(' / ')==9 for c in books))
  indexed={c['id']:c for c in cards}
  self.assertEqual(indexed['2025-TSWMW-BASE-56']['name'],'BB-8')
  self.assertEqual(indexed['2025-TSWMW-RAR-RAR-C3']['name'],'Anthony Daniels')
  self.assertEqual(indexed['2025-TSWMW-AUTO-A-AA']['name'],indexed['2025-TSWMW-PEN-A-AA']['name'])
  self.assertNotEqual(indexed['2025-TSWMW-AUTO-A-AA']['id'],indexed['2025-TSWMW-PEN-A-AA']['id'])
  self.assertEqual(len(variants),680)
  numbered=[v for v in variants if v['serial_cap'] is not None]
  self.assertEqual(len(numbered),91)
  self.assertTrue(all(v['serial_cap']==1 and v['serial_exact']=='1/1' and indexed[v['card_id']]['subsetCode']=='ROC' for v in numbered))
  self.assertTrue(all(v['card_id'] in indexed for v in variants))
  self.assertEqual([v['variant_order'] for v in variants],list(range(1,681)))

 def test_odds_scope_and_unresolved_rate(self):
  source=json.loads(mw.SOURCE.read_text());data=mw.tables()
  self.assertEqual(len(source['odds']),90)
  malformed=[r for r in source['odds'] if not r['validRate']]
  self.assertEqual([(r['label'],r['hobby']) for r in malformed],[('Skeleton Crew Auto Relic Black','1,249')])
  rules=data['catalogue_parallel_rules'];self.assertEqual(len(rules),84)
  self.assertFalse(any('Buyback' in r['parallel'] or 'Sketch' in r['parallel'] for r in rules))
  self.assertTrue(all(r['serial_cap'] is None for r in rules))
  unresolved=[r for r in rules if 'unresolved' in r['verification_status']]
  self.assertEqual(len(unresolved),1);self.assertIn('not interpreted',unresolved[0]['exclusive_note'])
  self.assertTrue(any(r['applies_to']=='LOTHAL JEDI TEMPLE MORTIS GODS PAINTING PUZZLE' and '1:160' in r['exclusive_note'] for r in rules))
  relic=next(c for c in data['catalogue_cards'] if c['id']=='2025-TSWMW-ARC-ARC-LUNA')
  self.assertIn('Missle: Andor',relic['notes'])

 def test_preservation_repeat_and_conflict(self):
  base='f16adeee60e5cab1d5c1f2934bfa6d4dd2378e21'
  def old(path):return subprocess.check_output(['git','show',f'{base}:{path}'],cwd=ROOT)
  prior=json.loads(old('data/catalogue-index.json'));current=load_catalogue()
  self.assertEqual((current['setCount'],current['cardCount']),(27,13514))
  for record in prior['sets']:
   self.assertEqual((ROOT/'data'/record['file']).read_bytes(),old('data/'+record['file']))
   self.assertEqual(next(s for s in current['sets'] if s['id']==record['id']),{k:v for k,v in record.items() if k!='file'})
  self.assertEqual((ROOT/'data/catalogue.json').read_bytes(),old('data/catalogue.json'))
  record,cards,_=mw.build();before={p:p.read_bytes() for p in (ROOT/'data').glob('**/*.json')}
  save_catalogue(mw.apply(copy.deepcopy(current),record,cards))
  self.assertTrue(all(p.read_bytes()==b for p,b in before.items()))
  bad=copy.deepcopy(current);next(c for c in bad['cards'] if c['setId']==mw.SET_ID)['name']='Conflict'
  with self.assertRaises(ValueError):mw.apply(bad,record,cards)

 def test_invalid_evidence_and_guarded_transaction(self):
  source=json.loads(mw.SOURCE.read_text());source['subsets'][0]['rows'].pop()
  with self.assertRaises(ValueError):mw.build(source)
  source=json.loads(mw.SOURCE.read_text());source['filmCelNumbering']['serialCap']=99
  with self.assertRaises(ValueError):mw.build(source)
  sql=generate();self.assertEqual(sql,OUT.read_text())
  self.assertNotRegex(sql.lower(),r'(insert into|update|delete from|truncate) public\.(collection_items|reference_images)')
  self.assertIn('Conflicting catalogue_cards identity',sql)
  self.assertTrue(sql.rstrip().endswith('commit;'))


if __name__=='__main__':unittest.main()
