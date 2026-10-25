"""Official source reconciliation, duplicate-number handling and additive preservation."""
import copy,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import add_2025_topps_star_wars_smugglers_outpost as so
from catalogue_io import load_catalogue,save_catalogue
from prepare_star_wars_smugglers_import import generate,OUT
class SmugglersImport(unittest.TestCase):
 def test_official_designs_and_numbering_error(self):
  source=json.loads(so.SOURCE.read_text());record,cards,variants=so.build(source)
  self.assertEqual(sum(len(s['rows']) for s in source['subsets']),881)
  self.assertEqual((len(cards),len(record['subsets'])),(806,23))
  self.assertEqual((record['year'],record['releaseDate'],record['categoryId']),(2025,'2026-03-18','star-wars'))
  self.assertEqual(len(source['sketchArtists']),216)
  self.assertEqual(source['sketchArtists'][-1]['name'],'ジェイソン (Jason)')
  self.assertEqual(len({c['id'] for c in cards}),806)
  self.assertEqual([c['order'] for c in cards],list(range(1,807)))
  self.assertEqual([sum(c['category']==x for c in cards) for x in ['Base','Insert','Autograph','Sketch']],[200,260,221,125])
  for code,count in [('F',75),('CB',75),('GA',50)]:
   self.assertEqual({c['number'] for c in cards if c['subsetCode']==code},{f'{code}-{i}' for i in range(1,count+1)})
  conflict=[c for c in cards if c['subsetCode']=='ROTS' and c['number']=='ARS-25']
  self.assertEqual({c['name'] for c in conflict},{'Jar Jar Binks','Darth Vader'})
  self.assertEqual(len({c['id'] for c in conflict}),2)
  self.assertFalse(any(c['number']=='ARS-23' for c in cards))
  self.assertTrue(all('pending physical-card verification' in c['notes'] for c in so.tables()['catalogue_cards'] if c['id'] in {x['id'] for x in conflict}))
  for code in ['LSU','DSU']:
   book=[c for c in cards if c['subsetCode']==code];self.assertEqual(len(book),1);self.assertEqual(book[0]['name'].count(' / '),19)
  self.assertEqual(sum(c['subsetCode']=='TA' for c in cards),8)
  self.assertEqual(sum(c['subsetCode']=='QA' for c in cards),7)
  self.assertTrue(any(c['number']=='SCA-LJj' for c in cards),'Retain printed mixed-case number')
  self.assertEqual(len(variants),806);self.assertTrue(all(v['serial_cap'] is None for v in variants))
  self.assertTrue(all(v['card_id'] in {c['id'] for c in cards} for v in variants))
 def test_odds_are_subset_rules(self):
  s=json.loads(so.SOURCE.read_text());d=so.tables()
  self.assertEqual(len(s['odds']),127);self.assertTrue(all(r['validRate'] for r in s['odds']))
  self.assertEqual(len(d['catalogue_parallel_rules']),124)
  self.assertTrue(all(r['serial_cap'] is None for r in d['catalogue_parallel_rules']))
  self.assertEqual(len(d['catalogue_sources']),3)
  self.assertTrue(any(r['parallel_group']=='TSC' for r in d['catalogue_parallel_rules']))
  self.assertTrue(any(r['parallel_group']=='SA' for r in d['catalogue_parallel_rules']))
 def test_preservation_idempotency_and_conflicts(self):
  base='edcb8f60034b2dec0b5425535b989849e9e3efe7'
  def old(p):return subprocess.check_output(['git','show',f'{base}:{p}'],cwd=ROOT)
  prior=json.loads(old('data/catalogue-index.json'));current=load_catalogue()
  for record in prior['sets']:
   self.assertEqual((ROOT/'data'/record['file']).read_bytes(),old('data/'+record['file']))
   self.assertEqual(next(s for s in current['sets'] if s['id']==record['id']),{k:v for k,v in record.items() if k!='file'})
  self.assertEqual((ROOT/'data/catalogue.json').read_bytes(),old('data/catalogue.json'))
  record,cards,_=so.build();before={p:p.read_bytes() for p in (ROOT/'data').glob('**/*.json')}
  save_catalogue(so.apply(copy.deepcopy(current),record,cards))
  self.assertTrue(all(p.read_bytes()==b for p,b in before.items()))
  bad=copy.deepcopy(current);next(c for c in bad['cards'] if c['setId']==so.SET_ID)['name']='Conflict'
  with self.assertRaises(ValueError):so.apply(bad,record,cards)
 def test_bad_evidence_and_guarded_sql(self):
  s=json.loads(so.SOURCE.read_text());s['subsets'][3]['rows'][-1]['number']='ARS-23'
  with self.assertRaises(ValueError):so.build(s)
  s=json.loads(so.SOURCE.read_text());s['subsets'][18]['rows'].pop()
  with self.assertRaises(ValueError):so.build(s)
  sql=generate();self.assertEqual(sql,OUT.read_text());self.assertTrue(sql.rstrip().endswith('commit;'))
  self.assertNotRegex(sql.lower(),r'(insert into|update|delete from|truncate) public\.(collection_items|reference_images)')
  self.assertIn('Conflicting catalogue_cards identity',sql)
if __name__=='__main__':unittest.main()
