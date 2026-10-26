"""Hyperspace source fidelity, separately numbered variations and additive preservation."""
import copy,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import add_2025_topps_star_wars_hyperspace as s
from catalogue_io import load_catalogue,save_catalogue
from prepare_star_wars_hyperspace_2025_import import generate,OUT

class Hyperspace2025(unittest.TestCase):
 def test_numbered_identity_coverage(self):
  source=json.loads(s.SOURCE.read_text());r,c,v=s.build(source)
  self.assertEqual((len(c),len(r['subsets'])),(347,12))
  self.assertEqual((r['releaseDate'],r['categoryId']),('2025-12-30','star-wars'))
  self.assertEqual(len({x['id'] for x in c}),347)
  self.assertEqual(len({(x['subsetCode'],x['number']) for x in c}),347)
  self.assertEqual([x['order'] for x in c],list(range(1,348)))
  self.assertEqual([sum(x['category']==k for x in c) for k in ['Base','Variation','Insert','Autograph']],[100,100,110,37])
  byid={x['id']:x for x in c}
  self.assertEqual(byid['2025-TSWH-BASE-1']['name'],byid['2025-TSWH-BPV-BPV-1']['name'])
  for code,expected in [('R',range(16,21)),('PV',range(6,11)),('WIDE',range(1,6))]:
   self.assertEqual({x['number'] for x in c if x['subsetCode']==code},{f'{code}-{i}' for i in expected})
  self.assertIn('Lee Jung-jae',byid['2025-TSWH-AUTO-AV-LJj']['name'])
  self.assertEqual(byid['2025-TSWH-GO-GO-3']['name'],'Ahsoka Tano')
  self.assertEqual(byid['2025-TSWH-GO-GO-3']['roster'],'Corellia')
  self.assertEqual(len(v),347);self.assertTrue(all(x['serial_cap'] is None and x['card_id'] in byid for x in v))
  self.assertEqual([len(source['rosters'][k]) for k in s.ROSTERS],[5,18,144])
  self.assertEqual(source['rosters']['SKETCH ARTIST'][-1]['name'],'ジェイソン (Jason)')
  self.assertEqual(sum(len(x['rows']) for x in source['subsets']),347)
 def test_planet_and_artist_metadata(self):
  source=json.loads(s.SOURCE.read_text());d=s.tables()
  for code in ['BASE','BPV']:
   cards=[c for c in d['catalogue_cards'] if c['subset_code']==code]
   self.assertEqual({p:sum(c['roster']==p for c in cards) for p in s.PLANETS},dict(zip(s.PLANETS,[15,9,18,18,40])))
  self.assertEqual(sum('Artist credit: Steve Hamilton.' in x['notes'] for x in d['catalogue_cards']),15)
  self.assertEqual(sum('Artist credit: Christian Waggoner.' in x['notes'] for x in d['catalogue_cards']),5)
  self.assertEqual(sum('Artist credit: Traci Easterday.' in x['notes'] for x in d['catalogue_cards']),10)
  self.assertTrue(all(not c['rookie'] for c in d['catalogue_cards']))
  self.assertEqual(len(d['catalogue_sources']),3)
 def test_odds_aliases_and_limits(self):
  source=json.loads(s.SOURCE.read_text());d=s.tables();rules=d['catalogue_parallel_rules']
  self.assertEqual(len(source['odds']),77);self.assertEqual(len(rules),71)
  self.assertTrue(all(x['serial_cap'] is None for x in rules))
  self.assertEqual(sum('Bigger a Bigger Fish' in x['numbering_note'] for x in rules),2)
  self.assertEqual(sum(x['parallel']=='Superfractor Refractor' for x in rules),1)
  self.assertEqual(sum(x['parallel_group']=='BPV' for x in rules),5)
  self.assertEqual(sum(x['parallel_group']=='WIDE' for x in rules),1)
  self.assertEqual(sum(x['parallel_group']=='AUTO' for x in rules),6)
  for section in s.SECTIONS:self.assertTrue(any(x['applies_to']==section for x in rules))
 def test_preservation_and_repeat(self):
  baseline='286e5b1'
  def old(p):return subprocess.check_output(['git','show',f'{baseline}:{p}'],cwd=ROOT)
  prior=json.loads(old('data/catalogue-index.json'));current=load_catalogue()
  self.assertGreaterEqual(len(current['sets']),32);self.assertGreaterEqual(len(current['cards']),16553)
  self.assertGreaterEqual(sum(x['cardCount'] for x in current['sets'] if x['categoryId']=='star-wars'),5255)
  for r in prior['sets']:
   self.assertEqual((ROOT/'data'/r['file']).read_bytes(),old('data/'+r['file']))
   self.assertEqual(next(x for x in current['sets'] if x['id']==r['id']),{k:v for k,v in r.items() if k!='file'})
  self.assertEqual((ROOT/'data/catalogue.json').read_bytes(),old('data/catalogue.json'))
  r,c,_=s.build();before={p:p.read_bytes() for p in (ROOT/'data').glob('**/*.json')}
  save_catalogue(s.apply(copy.deepcopy(current),r,c));self.assertTrue(all(p.read_bytes()==b for p,b in before.items()))
  bad=copy.deepcopy(current);next(c for c in bad['cards'] if c['setId']==s.SET_ID)['name']='Conflict'
  with self.assertRaises(ValueError):s.apply(bad,r,c)
 def test_bad_evidence_and_sql_guards(self):
  for mutate in ['missing','duplicate','number']:
   source=json.loads(s.SOURCE.read_text())
   if mutate=='missing':source['subsets'][0]['rows'].pop()
   elif mutate=='duplicate':source['subsets'][1]['rows'][0]=source['subsets'][1]['rows'][1]
   else:source['subsets'][6]['rows'][0]['number']='R-1'
   with self.assertRaises(ValueError):s.build(source)
  sql=generate();self.assertEqual(sql,OUT.read_text())
  self.assertTrue(sql.rstrip().endswith('commit;'))
  self.assertNotRegex(sql.lower(),r'(insert into|update|delete from|truncate) public\.(collection_items|reference_images)')
  self.assertIn('Conflicting catalogue_cards identity',sql)
  self.assertIn('Count, linkage or preservation check failed',sql)

if __name__=='__main__':unittest.main()
