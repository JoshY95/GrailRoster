"""Meiyo source coverage, centered dual identities, format limits and preservation."""
import copy,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import add_2025_topps_star_wars_meiyo as s
from catalogue_io import load_catalogue,save_catalogue
from prepare_star_wars_meiyo_2025_import import generate,OUT
class Meiyo2025(unittest.TestCase):
 def test_coverage_and_duals(self):
  source=json.loads(s.SOURCE.read_text());r,c,v=s.build(source)
  self.assertEqual((len(c),len(r['subsets'])),(267,22));self.assertEqual(r['releaseDate'],'2025-05-04')
  self.assertEqual([sum(x['category']==k for x in c) for k in ['Base','Variation','Insert','Autograph']],[100,40,67,60])
  self.assertEqual(len({x['id'] for x in c}),267);self.assertEqual([x['order'] for x in c],list(range(1,268)))
  self.assertEqual(sum(len(x['rows']) for x in source['subsets']),280);self.assertEqual(len(source['sketchArtists']),25)
  duals=[x for x in c if x['subsetCode']=='DUAL'];self.assertEqual(len(duals),13)
  self.assertTrue(all(x['name'].count(' / ')==1 for x in duals))
  d={x['number']:x for x in duals}
  for number,names in {'DA-DF':['Felicity Jones','Diego Luna'],'DA-DM':['Daisy Ridley','Dave Chapman'],'DA-H':['Billy Dee Williams','Harrison Ford'],'DA-W':['Warwick Davis','Mike Edmonds'],'DA-NE':['Natasha Liu Bordizzo','Eman Esfandi']}.items():
   for name in names:self.assertIn(name,d[number]['name'])
  self.assertIn('C-3P0',d['DA-M']['name'])
  posters=[x for x in c if x['subsetCode']=='MP'];self.assertEqual(sum(x['name']=='Star Wars: A New Hope' for x in posters),2)
  self.assertEqual(len(v),267);self.assertTrue(all(x['serial_cap'] is None for x in v))
 def test_odds_caps_and_format_limits(self):
  source=json.loads(s.SOURCE.read_text());d=s.tables();rules=d['catalogue_parallel_rules']
  self.assertEqual((len(source['odds']),len(rules)),(99,91))
  self.assertEqual(sum(x['serial_cap'] is not None for x in rules),24)
  for code in ['RA','GE','RS','FO']:
   self.assertEqual({x['parallel']:x['serial_cap'] for x in rules if x['parallel_group']==code},s.BASE_CAPS)
  self.assertTrue(all(x['serial_cap'] is None for x in rules if x['parallel_group'] not in ['RA','GE','RS','FO']))
  self.assertEqual(sum(x['parallel']=='BLACK RREFRACTOR' for x in rules),1)
  self.assertTrue(all('Celebration: -' in x['exclusive_note'] for x in rules if x['parallel_group']=='UK'))
  self.assertTrue(all(not x['id'].startswith('2025-TSWM-MM-') for x in d['catalogue_cards']))
  self.assertEqual(source['deferred'][0]['name'],'MANGA MADNESS');self.assertEqual(len(d['catalogue_sources']),4)
 def test_preservation_repeat(self):
  def old(p):return subprocess.check_output(['git','show',f'502153f:{p}'],cwd=ROOT)
  prior=json.loads(old('data/catalogue-index.json'));current=load_catalogue()
  self.assertGreaterEqual(len(current['sets']),33);self.assertGreaterEqual(len(current['cards']),16820)
  self.assertGreaterEqual(sum(x['cardCount'] for x in current['sets'] if x['categoryId']=='star-wars'),5522)
  for r in prior['sets']:
   self.assertEqual((ROOT/'data'/r['file']).read_bytes(),old('data/'+r['file']))
   self.assertEqual(next(x for x in current['sets'] if x['id']==r['id']),{k:v for k,v in r.items() if k!='file'})
  self.assertEqual((ROOT/'data/catalogue.json').read_bytes(),old('data/catalogue.json'))
  r,c,_=s.build();before={p:p.read_bytes() for p in (ROOT/'data').glob('**/*.json')}
  save_catalogue(s.apply(copy.deepcopy(current),r,c));self.assertTrue(all(p.read_bytes()==b for p,b in before.items()))
  bad=copy.deepcopy(current);next(x for x in bad['cards'] if x['setId']==s.SET_ID)['name']='Conflict'
  with self.assertRaises(ValueError):s.apply(bad,r,c)
 def test_rejection_and_guard_sql(self):
  for name in ['REBEL ALLIANCE BASE',s.DUAL]:
   source=json.loads(s.SOURCE.read_text());next(x for x in source['subsets'] if x['name']==name)['rows'].pop()
   with self.assertRaises(ValueError):s.build(source)
  sql=generate();self.assertEqual(sql,OUT.read_text());self.assertTrue(sql.rstrip().endswith('commit;'))
  self.assertNotRegex(sql.lower(),r'(insert into|update|delete from|truncate) public\.(collection_items|reference_images)')
  self.assertIn('Conflicting catalogue_cards identity',sql);self.assertIn('Count, linkage or preservation check failed',sql)
if __name__=='__main__':unittest.main()
