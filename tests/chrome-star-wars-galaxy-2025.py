"""Source reconciliation, buyback boundaries, odds ambiguity and additive preservation."""
import copy,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import add_2025_topps_chrome_star_wars_galaxy as g
from catalogue_io import load_catalogue,save_catalogue
from prepare_star_wars_galaxy_2025_import import generate,OUT
class Galaxy2025(unittest.TestCase):
 def test_numbered_design_reconciliation(self):
  s=json.loads(g.SOURCE.read_text());r,c,v=g.build(s)
  self.assertEqual(sum(len(x['rows']) for x in s['subsets']),325)
  self.assertEqual((len(c),len(r['subsets'])),(293,15))
  self.assertEqual((r['year'],r['releaseDate'],r['categoryId']),(2025,'2025-12-10','star-wars'))
  self.assertEqual((len(s['sketchArtists']),len(s['blankCanvasArtists'])),(154,7))
  self.assertEqual(len({x['id'] for x in c}),293)
  self.assertEqual(len({(x['subsetCode'],x['number']) for x in c}),293)
  self.assertEqual([x['order'] for x in c],list(range(1,294)))
  self.assertEqual([sum(x['category']==k for x in c) for k in ['Base','Insert','Buyback','Autograph']],[100,103,20,70])
  self.assertEqual({x['number'] for x in c if x['subsetCode']=='BASE'},set(map(str,range(1,101))))
  for code,n,m in [('DUAL',10,2),('TRIPLE',5,3),('QUAD',4,4)]:
   cards=[x for x in c if x['subsetCode']==code];self.assertEqual(len(cards),n);self.assertTrue(all(x['name'].count(' / ')==m-1 for x in cards))
  byid={x['id']:x for x in c}
  self.assertEqual(byid['2025-TCSWG-BASE-1']['name'],'What Remains')
  self.assertEqual(byid['2025-TCSWG-MCQ-MCQ-1']['name'],'1993 Star Wars Galaxy Series 1 #15')
  self.assertEqual(byid['2025-TCSWG-AB-AB-15']['name'],'1993 Star Wars Galaxy Series 1 #15')
  self.assertEqual(byid['2025-TCSWG-MCQ-MCQ-14']['name'],'1994 Star Wars Galaxy Series 2 #142')
  self.assertEqual(byid['2025-TCSWG-AUTO-GA-JOO']['name'],'Chewbacca (Joonas Suotamo)')
  self.assertEqual(len(v),293);self.assertTrue(all(x['serial_cap'] is None and x['card_id'] in byid for x in v))
 def test_odds_ambiguities_and_source_credits(self):
  s=json.loads(g.SOURCE.read_text());d=g.tables()
  self.assertEqual(len(s['odds']),93)
  self.assertEqual([(x['label'],x['hobby']) for x in s['odds'] if not x['validRate']],[('SKETCH CARDS BLACK FOIL','1;11,140')])
  rules=d['catalogue_parallel_rules'];self.assertEqual(len(rules),88)
  self.assertTrue(all(x['serial_cap'] is None for x in rules))
  unresolved=[x for x in rules if 'unresolved' in x['verification_status']]
  self.assertEqual(len(unresolved),1);self.assertIn('Unspecified edition',unresolved[0]['parallel'])
  self.assertIn('not assumed',unresolved[0]['exclusive_note'])
  notes={x['id']:x['notes'] for x in d['catalogue_cards']}
  self.assertIn('Artist credit: Candice Dailey.',notes['2025-TCSWG-BASE-1'])
  self.assertIn('Artist credit: Chrstian Benavides.',notes['2025-TCSWG-DOM-DOM-1'])
  self.assertNotIn('Artist credit:',notes['2025-TCSWG-MCQ-MCQ-1'])
  self.assertNotIn('Artist credit:',notes['2025-TCSWG-AB-AB-15'])
 def test_preservation_repeat_and_number_collisions(self):
  base='d267bd9e7d490f75246c9fd03ee5742e36186d9c'
  def old(p):return subprocess.check_output(['git','show',f'{base}:{p}'],cwd=ROOT)
  prior=json.loads(old('data/catalogue-index.json'));current=load_catalogue()
  for r in prior['sets']:
   self.assertEqual((ROOT/'data'/r['file']).read_bytes(),old('data/'+r['file']))
   self.assertEqual(next(s for s in current['sets'] if s['id']==r['id']),{k:v for k,v in r.items() if k!='file'})
  self.assertEqual((ROOT/'data/catalogue.json').read_bytes(),old('data/catalogue.json'))
  copies=[c for c in current['cards'] if c['number']=='1' and c['setId'] in [g.SET_ID,'2026-topps-chrome-star-wars-galaxy']]
  self.assertEqual(len(copies),2);self.assertEqual(len({c['id'] for c in copies}),2)
  r,c,_=g.build();before={p:p.read_bytes() for p in (ROOT/'data').glob('**/*.json')}
  save_catalogue(g.apply(copy.deepcopy(current),r,c));self.assertTrue(all(p.read_bytes()==b for p,b in before.items()))
  bad=copy.deepcopy(current);next(c for c in bad['cards'] if c['setId']==g.SET_ID)['name']='Conflict'
  with self.assertRaises(ValueError):g.apply(bad,r,c)
 def test_reject_bad_source_and_guard_sql(self):
  s=json.loads(g.SOURCE.read_text());s['subsets'][0]['rows'].pop()
  with self.assertRaises(ValueError):g.build(s)
  s=json.loads(g.SOURCE.read_text());s['subsets'][11]['rows'].pop()
  with self.assertRaises(ValueError):g.build(s)
  sql=generate();self.assertEqual(sql,OUT.read_text());self.assertTrue(sql.rstrip().endswith('commit;'))
  self.assertNotRegex(sql.lower(),r'(insert into|update|delete from|truncate) public\.(collection_items|reference_images)')
  self.assertIn('Conflicting catalogue_cards identity',sql)
if __name__=='__main__':unittest.main()
