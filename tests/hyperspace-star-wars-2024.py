"""Hyperspace 2024: numbered variants, source differences and additive preservation."""
import copy,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import add_2024_topps_star_wars_hyperspace as s
from catalogue_io import load_catalogue,save_catalogue
from prepare_star_wars_hyperspace_2024_import import generate,OUT
class Hyperspace2024(unittest.TestCase):
 def test_coverage_and_numbering(self):
  source=json.loads(s.SOURCE.read_text());r,c,v=s.build(source)
  self.assertEqual((len(c),len(r['subsets'])),(326,10));self.assertEqual((r['year'],r['releaseDate'],r['categoryId']),(2024,'2025-02-19','star-wars'))
  self.assertEqual(sum(len(x['rows']) for x in source['subsets']),326)
  self.assertEqual(len({x['id'] for x in c}),326);self.assertEqual([x['order'] for x in c],list(range(1,327)))
  self.assertEqual([sum(x['category']==k for x in c) for k in ['Base','Variation','Insert','Autograph']],[100,100,80,46])
  for code,n in [('BASE',100),('BPV',100),('R',5),('PV',5)]:
   start=6 if code=='R' else 1
   self.assertEqual({x['number'] for x in c if x['subsetCode']==code},{str(i) if code=='BASE' else f'{code}-{i}' for i in range(start,start+n)})
  self.assertEqual(len(v),326);self.assertTrue(all(x['serial_cap'] is None for x in v))
 def test_preserve_printed_differences_and_rosters(self):
  source=json.loads(s.SOURCE.read_text());r,c,v=s.build(source);d={x['id']:x for x in c}
  self.assertEqual(d['2024-TSWH-BASE-54']['roster'],'Kashyyyk');self.assertEqual(d['2024-TSWH-BPV-BPV-54']['roster'],'Naboo')
  self.assertEqual(d['2024-TSWH-BASE-56']['roster'],'Hoth');self.assertEqual(d['2024-TSWH-BPV-BPV-56']['roster'],'Bespin')
  self.assertEqual(d['2024-TSWH-BASE-8']['name'],'Mylaya');self.assertEqual(d['2024-TSWH-BPV-BPV-8']['name'],'Mylayas')
  self.assertEqual(d['2024-TSWH-BASE-86']['name'],'Maximillian Veers');self.assertEqual(d['2024-TSWH-BPV-BPV-86']['name'],'Maximilian Veers')
  self.assertEqual(d['2024-TSWH-GE-GE-4']['name'],'Obi-Wan Kenobi vs Anakin Skywalker')
  self.assertIn('Kashyyyk',{x['roster'] for x in c});self.assertIn('Ewan McGregor',' '.join(x['name'] for x in c if x['category']=='Autograph'))
  self.assertEqual([r['name'] for r in source['rosters']['Planets']],s.PLANETS)
  self.assertEqual(len(source['rosters']['Artists']),106);self.assertEqual(len({x['name'] for x in source['rosters']['Artists']}),105)
 def test_odds_and_no_inferred_grid(self):
  source=json.loads(s.SOURCE.read_text());d=s.tables();rules=d['catalogue_parallel_rules']
  self.assertEqual((len(source['odds']),len(rules)),(61,56));self.assertEqual(len(d['catalogue_sources']),3)
  self.assertTrue(all(x['serial_cap'] is None for x in rules))
  self.assertEqual(sum(x['parallel_group']=='BPV' for x in rules),5)
  self.assertEqual(sum(x['parallel']=='Superfractor Refractor' for x in rules),1)
  self.assertEqual({x['applies_to'] for x in rules},set(s.SECTIONS))
  self.assertFalse(any(x['subsetCode'] in ['HYP','WIDE','AOT'] for x in s.build()[1]))
 def test_preservation_and_repeat(self):
  def old(p):return subprocess.check_output(['git','show',f'6bf9fcd:{p}'],cwd=ROOT)
  prior=json.loads(old('data/catalogue-index.json'));current=load_catalogue()
  self.assertGreaterEqual(len(current['sets']),35);self.assertGreaterEqual(len(current['cards']),17483)
  self.assertGreaterEqual(sum(x['cardCount'] for x in current['sets'] if x['categoryId']=='star-wars'),6185)
  for r in prior['sets']:
   self.assertEqual((ROOT/'data'/r['file']).read_bytes(),old('data/'+r['file']))
   self.assertEqual(next(x for x in current['sets'] if x['id']==r['id']),{k:v for k,v in r.items() if k!='file'})
  self.assertEqual((ROOT/'data/catalogue.json').read_bytes(),old('data/catalogue.json'))
  r,c,_=s.build();before={p:p.read_bytes() for p in (ROOT/'data').glob('**/*.json')}
  save_catalogue(s.apply(copy.deepcopy(current),r,c));self.assertTrue(all(p.read_bytes()==b for p,b in before.items()))
  bad=copy.deepcopy(current);next(x for x in bad['cards'] if x['setId']==s.SET_ID)['name']='Conflict'
  with self.assertRaises(ValueError):s.apply(bad,r,c)
 def test_bad_evidence_and_guard_sql(self):
  for idx in [0,1,6,9]:
   source=json.loads(s.SOURCE.read_text());source['subsets'][idx]['rows'].pop()
   with self.assertRaises(ValueError):s.build(source)
  sql=generate();self.assertEqual(sql,OUT.read_text());self.assertTrue(sql.rstrip().endswith('commit;'))
  self.assertNotRegex(sql.lower(),r'(insert into|update|delete from|truncate) public\.(collection_items|reference_images)')
  self.assertIn('Conflicting catalogue_cards identity',sql)
if __name__=='__main__':unittest.main()
