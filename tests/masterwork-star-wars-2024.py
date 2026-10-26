"""2024 Masterwork: cross-page autograph geometry, PDF artifacts and additive preservation."""
import copy,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import add_2024_topps_star_wars_masterwork as s
from catalogue_io import load_catalogue,save_catalogue
from prepare_star_wars_masterwork_2024_import import generate,OUT
class Masterwork2024(unittest.TestCase):
 def test_source_coverage_and_artifacts(self):
  source=json.loads(s.SOURCE.read_text());r,c,v=s.build(source)
  self.assertEqual((len(c),len(r['subsets'])),(337,16));self.assertEqual(r['releaseDate'],'2025-04-16')
  self.assertEqual(r['year'],2024);self.assertEqual(r['categoryId'],'star-wars')
  self.assertEqual(sum(len(x['rows']) for x in source['subsets']),363)
  self.assertEqual(len({x['id'] for x in c}),337);self.assertEqual([x['order'] for x in c],list(range(1,338)))
  self.assertEqual([sum(x['category']==k for x in c) for k in ['Base','Insert','Autograph','Autograph Relic','Relic']],[100,122,66,33,16])
  self.assertEqual({x['number'] for x in c if x['subsetCode']=='BASE'},set(map(str,range(1,101))))
  self.assertEqual(len(source['sketchArtists']),182);self.assertEqual(len({r['name'] for r in source['sketchArtists']}),182)
  self.assertEqual(source['blankPages'],[13,14,15]);self.assertEqual(len(source['sourceArtifacts']),16)
  self.assertTrue(all(x['x']<0 and x['page'] in [16,17] for x in source['sourceArtifacts']))
  self.assertEqual(len(v),337);self.assertTrue(all(x['serial_cap'] is None for x in v))
 def test_multi_designs_and_context(self):
  source=json.loads(s.SOURCE.read_text());r,c,v=s.build(source);d={x['id']:x for x in c}
  self.assertEqual(len(source['multiSignerLabels']),17)
  self.assertEqual([x['page'] for x in source['multiSignerLabels'] if x['number']=='DA-HR'],[6,7])
  for code,n,m in [('DUO',9,2),('TRIO',4,3),('QUAD',3,4)]:
   cards=[x for x in c if x['subsetCode']==code];self.assertEqual(len(cards),n);self.assertTrue(all(x['name'].count(' / ')==m-1 for x in cards))
  for name in ['Rosario Dawson','Hayden Christensen']:self.assertIn(name,d['2024-TSWMW-DUO-DA-HR']['name'])
  for name in ['Mark Hamill','Rosario Dawson','Temuera Morrison','Pedro Pascal']:self.assertIn(name,d['2024-TSWMW-QUAD-QAB-MPPH']['name'])
  self.assertEqual(d['2024-TSWMW-S-S-1']['name'],d['2024-TSWMW-S-S-2']['name'])
  self.assertNotEqual(d['2024-TSWMW-S-S-1']['id'],d['2024-TSWMW-S-S-2']['id'])
  self.assertTrue(any(x['number']=='HG-13' and 'Oppurtinity' in x['name'] for x in c))
  tables=s.tables();self.assertTrue(any('Source context: Stormtrooper.' in x['notes'] for x in tables['catalogue_cards'] if x['subset_code']=='S'))
 def test_odds_limits(self):
  source=json.loads(s.SOURCE.read_text());d=s.tables();rules=d['catalogue_parallel_rules']
  self.assertEqual((len(source['odds']),len(rules)),(76,72));self.assertEqual(len(d['catalogue_sources']),3)
  self.assertTrue(all(x['serial_cap'] is None for x in rules))
  self.assertEqual(sum(x['parallel']=='BLAC' for x in rules),1)
  self.assertEqual({x['applies_to'] for x in rules},set(s.SECTIONS))
  self.assertFalse(any(x['parallel_group']=='HG' and x['parallel'] in ['METAL','GOLD METAL'] for x in rules))
 def test_preservation_and_repeat(self):
  def old(p):return subprocess.check_output(['git','show',f'12c336b:{p}'],cwd=ROOT)
  prior=json.loads(old('data/catalogue-index.json'));current=load_catalogue()
  self.assertEqual((len(current['sets']),len(current['cards'])),(34,17157))
  self.assertEqual(sum(x['cardCount'] for x in current['sets'] if x['categoryId']=='star-wars'),5859)
  for r in prior['sets']:
   self.assertEqual((ROOT/'data'/r['file']).read_bytes(),old('data/'+r['file']))
   self.assertEqual(next(x for x in current['sets'] if x['id']==r['id']),{k:v for k,v in r.items() if k!='file'})
  self.assertEqual((ROOT/'data/catalogue.json').read_bytes(),old('data/catalogue.json'))
  r,c,_=s.build();before={p:p.read_bytes() for p in (ROOT/'data').glob('**/*.json')}
  save_catalogue(s.apply(copy.deepcopy(current),r,c));self.assertTrue(all(p.read_bytes()==b for p,b in before.items()))
  bad=copy.deepcopy(current);next(x for x in bad['cards'] if x['setId']==s.SET_ID)['name']='Conflict'
  with self.assertRaises(ValueError):s.apply(bad,r,c)
 def test_reject_partial_and_guard_sql(self):
  for name in ['BASE CARDS','DUAL AUTOGRAPHS','QUAD AUTOGRAPH BOOK CARD']:
   source=json.loads(s.SOURCE.read_text());next(x for x in source['subsets'] if x['name']==name)['rows'].pop()
   with self.assertRaises(ValueError):s.build(source)
  sql=generate();self.assertEqual(sql,OUT.read_text());self.assertTrue(sql.rstrip().endswith('commit;'))
  self.assertNotRegex(sql.lower(),r'(insert into|update|delete from|truncate) public\.(collection_items|reference_images)')
  self.assertIn('Conflicting catalogue_cards identity',sql)
if __name__=='__main__':unittest.main()
