"""Complete distributor reconciliation, parent/edition identity and preservation."""
import copy,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import prizm_wwe_2024 as p
from catalogue_io import load_catalogue,save_catalogue
from prepare_prizm_wwe_2024_import import generate,OUT
class PrizmWWE2024(unittest.TestCase):
 def test_full_distributor_reconciliation(self):
  self.assertEqual(p.extract(),p.read_source());self.assertEqual(p.read_source()['encodingRepairs'],59)
 def test_complete_exact_editions(self):
  r,c,v=p.build();self.assertEqual((len(c),len(r['subsets']),len(v)),(516,16,9270));self.assertEqual(len({x['id'] for x in c}),516);self.assertEqual(len({x['id'] for x in v}),9270)
  byid={x['id']:x for x in c}
  for row,x in zip(p.read_source()['rows'],v):
   f,parallel=p.classify(row[0]);card=byid[x['card_id']];self.assertEqual((card['subset'],card['number'],tuple(p.subjects(card['name']))),(f[0],row[1],tuple(p.subjects(row[2]))));self.assertEqual(x['parallel'],parallel)
   expected=None if f[1] in ('BH','BV') and parallel=='Prizms White Sparkle' else int(row[4]) if row[4] else None
   self.assertEqual(x['serial_cap'],expected)
  self.assertEqual(sum(x['serial_cap'] is not None for x in v),6770)
 def test_premium_parent_and_all_base_numbers(self):
  r,c,v=p.build();base=[x for x in c if x['category']=='Base'];self.assertEqual({x['number'] for x in base},{str(i) for i in range(1,201)})
  premium=[x for x in v if 'Premium Box Set' in x['parallel']];self.assertEqual(len(premium),400);self.assertEqual({x['card_id'] for x in premium},{x['id'] for x in base})
  self.assertEqual(Counter((x['parallel'],x['serial_cap']) for x in premium),Counter({('Prizms Premium Box Set',199):200,('Prizms Premium Box Set Gold',5):200}));self.assertTrue(all(x['exclusive_note']=='Premium Factory Set exclusive' for x in premium))
  self.assertFalse(any('premium' in x['setId'] for x in c));self.assertEqual(r['releaseDate'],'2024-08-09')
 def test_variations_duals_and_printed_gaps(self):
  _,c,v=p.build();d={x['id']:x for x in c};variations=[x for x in c if x['category']=='Variation'];self.assertEqual(len(variations),20)
  self.assertEqual(d['2024-PPWWE-BHV-14']['name'],'The Ringmaster');self.assertEqual(d['2024-PPWWE-BH-14']['name'],'"Stone Cold" Steve Austin')
  self.assertEqual(d['2024-PPWWE-BVV-119']['name'],'Mick Foley');self.assertEqual(d['2024-PPWWE-BV-119']['name'],'Dude Love')
  for card in variations:self.assertEqual([(x['parallel'],x['serial_cap']) for x in v if x['card_id']==card['id']],[('Under Card Variation',None),('Under Card Variation Gold',10)])
  self.assertEqual(len([x for x in c if x['subsetCode']=='IRDA']),10);self.assertEqual(len([x for x in v if x['card_id'].startswith('2024-PPWWE-IRDA-')]),40)
  self.assertTrue(all(len(x['name'].split(' / '))==2 for x in c if x['subsetCode']=='IRDA'))
  self.assertEqual({str(i) for i in range(1,41)}-{x['number'] for x in c if x['subsetCode']=='WM'},{'3','20','30'})
 def test_cap_exception_does_not_remove_editions(self):
  _,c,v=p.build();byid={x['id']:x for x in c};white=[x for x in v if x['parallel']=='Prizms White Sparkle'];base=[x for x in white if byid[x['card_id']]['category']=='Base'];autos=[x for x in white if byid[x['card_id']]['category']=='Autograph']
  self.assertEqual(len(base),200);self.assertTrue(all(x['serial_cap'] is None and x['serial_exact'] is None for x in base));self.assertEqual(len(autos),174);self.assertTrue(all(x['serial_cap']==1 for x in autos));self.assertEqual(len(p.tables()['catalogue_parallel_rules']),169)
 def test_prior_bytes_metadata_repeat_and_conflict(self):
  def old(path):return subprocess.check_output(['git','show',p.BASELINE+':'+path],cwd=ROOT)
  index=json.loads(old('data/catalogue-index.json'));cat=load_catalogue();self.assertGreaterEqual(len(cat['sets']),46);self.assertGreaterEqual(len(cat['cards']),22731);self.assertGreaterEqual(sum(x['cardCount'] for x in cat['sets'] if x['categoryId']=='wwe'),13413)
  for s in index['sets']:
   self.assertEqual((ROOT/'data'/s['file']).read_bytes(),old('data/'+s['file']));self.assertEqual(next(x for x in cat['sets'] if x['id']==s['id']),{k:v for k,v in s.items() if k!='file'})
  self.assertEqual((ROOT/'data/catalogue.json').read_bytes(),old('data/catalogue.json'))
  before={x:x.read_bytes() for x in (ROOT/'data').rglob('*.json')};p.apply(cat);save_catalogue(cat);self.assertTrue(all(x.read_bytes()==data for x,data in before.items()))
  bad=copy.deepcopy(cat);next(x for x in bad['cards'] if x['setId']==p.SID)['name']='Conflict'
  with self.assertRaises(ValueError):p.apply(bad)
 def test_bad_source_and_sql_guards(self):
  source=p.read_source();source['rows'].pop()
  with self.assertRaises(ValueError):p.build(source)
  source=p.read_source();source['rows'][1]=source['rows'][0]
  with self.assertRaises(ValueError):p.build(source)
  sql=generate();self.assertEqual(sql,OUT.read_text());self.assertNotRegex(sql.lower(),r'(update|delete from|truncate) public\.');self.assertNotRegex(sql.lower(),r'insert into public\.(collection_items|reference_images)')
  for t in p.tables():self.assertIn('Conflicting '+t+' identity',sql)
  from prepare_wwe_2024_batch_import import generate as previous,OUT as prior
  self.assertEqual(previous(),prior.read_text())
from collections import Counter
if __name__=='__main__':unittest.main()
