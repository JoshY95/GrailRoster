"""Sapphire identities, attached DEBUT flags, trailing PDF artifacts and preservation."""
import copy,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import add_2025_topps_chrome_sapphire_star_wars as s
from catalogue_io import load_catalogue,save_catalogue
from prepare_star_wars_sapphire_2025_import import generate,OUT
class Sapphire2025(unittest.TestCase):
 def test_designs_and_source_flags(self):
  source=json.loads(s.SOURCE.read_text());r,c,v=s.build(source)
  self.assertEqual(sum(len(x['rows']) for x in source['subsets']),395)
  self.assertEqual((len(c),len(r['subsets'])),(358,5))
  self.assertEqual((r['year'],r['releaseDate'],r['categoryId']),(2025,'2025-09-17','star-wars'))
  self.assertEqual(len({x['id'] for x in c}),358)
  self.assertEqual(len({(x['subsetCode'],x['number']) for x in c}),358)
  self.assertEqual([x['order'] for x in c],list(range(1,359)))
  self.assertEqual([sum(x['category']==k for x in c) for k in ['Base','Insert','Autograph']],[200,10,148])
  self.assertEqual({x['number'] for x in c if x['subsetCode']=='BASE'},set(map(str,range(1,201))))
  for code,n,m in [('DUAL',15,2),('TRIPLE',11,3)]:
   cards=[x for x in c if x['subsetCode']==code];self.assertEqual(len(cards),n);self.assertTrue(all(x['name'].count(' / ')==m-1 for x in cards))
  byid={x['id']:x for x in c}
  self.assertEqual(byid['2025-TCSSW-BASE-78']['name'],byid['2025-TCSSW-BASE-79']['name'])
  self.assertEqual(byid['2025-TCSSW-BASE-138']['name'],byid['2025-TCSSW-BASE-139']['name'])
  self.assertIn('Lee Jung-jae',byid['2025-TCSSW-DUAL-DA-MJj']['name'])
  self.assertIn('Manny Jacinto',byid['2025-TCSSW-DUAL-DA-MJj']['name'])
  self.assertEqual(sum(row['debut'] for x in source['subsets'] for row in x['rows']),65)
  self.assertEqual(len(source['sourceArtifacts']),21);self.assertEqual(source['blankPages'],[9,10,11,12])
  self.assertTrue(all(x['text']=='DEBUT' and x['page']>8 for x in source['sourceArtifacts']))
  self.assertTrue(all(not row['debut'] for x in source['subsets'][1:] for row in x['rows']))
  self.assertEqual(len(v),358);self.assertTrue(all(x['serial_cap'] is None and x['card_id'] in byid for x in v))
 def test_odds_and_debut_notes(self):
  d=s.tables();source=json.loads(s.SOURCE.read_text())
  self.assertEqual(len(source['odds']),17);self.assertEqual(len(d['catalogue_parallel_rules']),17)
  self.assertTrue(all(x['serial_cap'] is None for x in d['catalogue_parallel_rules']))
  self.assertEqual(sum('Padpradascha' in x['parallel'] for x in d['catalogue_parallel_rules']),5)
  self.assertEqual(sum(x['notes'].startswith('Official source marks DEBUT.') for x in d['catalogue_cards']),65)
  self.assertTrue(all(x['rookie'] is False for x in d['catalogue_cards']))
  self.assertEqual(len(d['catalogue_sources']),3)
 def test_preservation_repeat_and_collisions(self):
  base='c52c3742a36480e8f3d1d8c89559579cea922db9'
  def old(p):return subprocess.check_output(['git','show',f'{base}:{p}'],cwd=ROOT)
  prior=json.loads(old('data/catalogue-index.json'));current=load_catalogue()
  for r in prior['sets']:
   self.assertEqual((ROOT/'data'/r['file']).read_bytes(),old('data/'+r['file']))
   self.assertEqual(next(x for x in current['sets'] if x['id']==r['id']),{k:v for k,v in r.items() if k!='file'})
  self.assertEqual((ROOT/'data/catalogue.json').read_bytes(),old('data/catalogue.json'))
  r,c,_=s.build();before={p:p.read_bytes() for p in (ROOT/'data').glob('**/*.json')}
  save_catalogue(s.apply(copy.deepcopy(current),r,c));self.assertTrue(all(p.read_bytes()==b for p,b in before.items()))
  bad=copy.deepcopy(current);next(c for c in bad['cards'] if c['setId']==s.SET_ID)['name']='Conflict'
  with self.assertRaises(ValueError):s.apply(bad,r,c)
 def test_bad_evidence_and_guard_sql(self):
  source=json.loads(s.SOURCE.read_text());source['subsets'][0]['rows'].pop()
  with self.assertRaises(ValueError):s.build(source)
  source=json.loads(s.SOURCE.read_text());source['subsets'][3]['rows'].pop()
  with self.assertRaises(ValueError):s.build(source)
  sql=generate();self.assertEqual(sql,OUT.read_text());self.assertTrue(sql.rstrip().endswith('commit;'))
  self.assertNotRegex(sql.lower(),r'(insert into|update|delete from|truncate) public\.(collection_items|reference_images)')
  self.assertIn('Conflicting catalogue_cards identity',sql)
if __name__=='__main__':unittest.main()
