"""Official 2025 Chrome identity reconciliation, source quirks and preservation."""
import copy,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import add_2025_topps_chrome_star_wars as s
from catalogue_io import load_catalogue,save_catalogue
from prepare_star_wars_chrome_2025_import import generate,OUT
class Chrome2025(unittest.TestCase):
 def test_source_reconciliation(self):
  source=json.loads(s.SOURCE.read_text());r,c,v=s.build(source)
  self.assertEqual(sum(len(x['rows']) for x in source['subsets']),1272)
  self.assertEqual((len(c),len(r['subsets'])),(1235,20))
  self.assertEqual((r['releaseDate'],r['categoryId']),('2025-08-20','star-wars'))
  self.assertEqual(len({x['id'] for x in c}),1235)
  self.assertEqual(len({(x['subsetCode'],x['number']) for x in c}),1235)
  self.assertEqual([x['order'] for x in c],list(range(1,1236)))
  self.assertEqual([sum(x['category']==k for x in c) for k in ['Base','Insert','Autograph']],[200,840,195])
  for code,prefix in [('BASE',''),('BC','BC-'),('HF','HF-'),('AV','AV-')]:
   self.assertEqual({x['number'] for x in c if x['subsetCode']==code},{prefix+str(i) for i in range(1,201)})
  for code,prefix,ns in [('R','R-',range(11,16)),('VC','VC-',range(6,11)),('OF','OF-',range(6,11))]:
   self.assertEqual({x['number'] for x in c if x['subsetCode']==code},{prefix+str(i) for i in ns})
  for code,n,m in [('DUAL',15,2),('TRIPLE',11,3)]:
   cards=[x for x in c if x['subsetCode']==code];self.assertEqual(len(cards),n);self.assertTrue(all(x['name'].count(' / ')==m-1 for x in cards))
  byid={x['id']:x for x in c}
  self.assertEqual(byid['2025-TCSW-BASE-78']['name'],byid['2025-TCSW-BASE-79']['name'])
  self.assertEqual(byid['2025-TCSW-BASE-138']['name'],byid['2025-TCSW-BASE-139']['name'])
  self.assertIn('Lee Jung-jae',byid['2025-TCSW-DUAL-DA-MJj']['name'])
  self.assertIn('Manny Jacinto',byid['2025-TCSW-DUAL-DA-MJj']['name'])
  self.assertEqual(sum(row['debut'] for x in source['subsets'] for row in x['rows']),281)
  self.assertEqual(len(source['sketchArtists']),188)
  self.assertEqual(len(v),1235);self.assertTrue(all(x['serial_cap'] is None and x['card_id'] in byid for x in v))
 def test_odds_and_source_notes(self):
  d=s.tables();source=json.loads(s.SOURCE.read_text())
  self.assertEqual(len(source['odds']),95);self.assertEqual(len(d['catalogue_parallel_rules']),91)
  self.assertTrue(all(x['serial_cap'] is None for x in d['catalogue_parallel_rules']))
  self.assertTrue(any('1::590' in x['exclusive_note'] for x in d['catalogue_parallel_rules']))
  self.assertEqual(sum(x['notes'].startswith('Official source marks DEBUT.') for x in d['catalogue_cards']),281)
  self.assertTrue(all(x['rookie'] is False for x in d['catalogue_cards']))
  self.assertEqual(len(d['catalogue_sources']),3)
  self.assertEqual({x['applies_to'] for x in d['catalogue_parallel_rules']},set(s.SECTIONS))
 def test_preservation_repeat_and_collisions(self):
  base='fd8235e'
  def old(p):return subprocess.check_output(['git','show',f'{base}:{p}'],cwd=ROOT)
  prior=json.loads(old('data/catalogue-index.json'));current=load_catalogue()
  self.assertGreaterEqual(len(current['sets']),31);self.assertGreaterEqual(len(current['cards']),16206)
  for r in prior['sets']:
   self.assertEqual((ROOT/'data'/r['file']).read_bytes(),old('data/'+r['file']))
   self.assertEqual(next(x for x in current['sets'] if x['id']==r['id']),{k:v for k,v in r.items() if k!='file'})
  self.assertEqual((ROOT/'data/catalogue.json').read_bytes(),old('data/catalogue.json'))
  r,c,_=s.build();before={p:p.read_bytes() for p in (ROOT/'data').glob('**/*.json')}
  save_catalogue(s.apply(copy.deepcopy(current),r,c));self.assertTrue(all(p.read_bytes()==b for p,b in before.items()))
  bad=copy.deepcopy(current);next(x for x in bad['cards'] if x['setId']==s.SET_ID)['name']='Conflict'
  with self.assertRaises(ValueError):s.apply(bad,r,c)
 def test_reject_partial_evidence_and_guard_sql(self):
  for i in [0,17,18]:
   source=json.loads(s.SOURCE.read_text());source['subsets'][i]['rows'].pop()
   with self.assertRaises(ValueError):s.build(source)
  sql=generate();self.assertEqual(sql,OUT.read_text());self.assertTrue(sql.rstrip().endswith('commit;'))
  self.assertNotRegex(sql.lower(),r'(insert into|update|delete from|truncate) public\.(collection_items|reference_images)')
  self.assertIn('Conflicting catalogue_cards identity',sql)
if __name__=='__main__':unittest.main()
