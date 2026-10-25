"""Complete regular Chrome programmes, five-format odds and additive preservation."""
import copy,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import add_2025_topps_chrome_star_wars as m
from catalogue_io import load_catalogue,save_catalogue
from prepare_star_wars_chrome_2025_import import generate,OUT
class Chrome2025(unittest.TestCase):
 def test_manufacturer_design_reconciliation(self):
  source=json.loads(m.SOURCE.read_text());r,c,v=m.build(source)
  self.assertEqual(sum(len(x['rows']) for x in source['subsets']),1272)
  self.assertEqual((len(c),len(r['subsets'])),(1235,20))
  self.assertEqual((r['year'],r['releaseDate'],r['categoryId']),(2025,'2025-08-20','star-wars'))
  self.assertEqual(len({x['id'] for x in c}),1235)
  self.assertEqual(len({(x['subsetCode'],x['number']) for x in c}),1235)
  self.assertEqual([x['order'] for x in c],list(range(1,1236)))
  self.assertEqual([sum(x['category']==k for x in c) for k in ['Base','Insert','Autograph']],[200,840,195])
  for code,prefix in [('BASE',''),('PLATE','BC-'),('HOTH','HF-'),('AURE','AV-')]:
   self.assertEqual({x['number'] for x in c if x['subsetCode']==code},{prefix+str(i) for i in range(1,201)})
  for code,n,mult in [('DUAL',15,2),('TRIPLE',11,3)]:
   cards=[x for x in c if x['subsetCode']==code];self.assertEqual(len(cards),n);self.assertTrue(all(x['name'].count(' / ')==mult-1 for x in cards))
  self.assertEqual(sum(x['subsetCode']=='TVA' for x in c),47)
  self.assertEqual(sum(row['debut'] for x in source['subsets'] for row in x['rows']),281)
  self.assertEqual(sum(row['debut'] for x in source['subsets'] if x['name']=='AUTOGRAPH CARDS' for row in x['rows']),21)
  self.assertEqual(len(source['sketchArtists']),188)
  d={x['id']:x for x in c};self.assertEqual(d['2025-TCSW-TVA-TV-CF']['name'],'Leia Organa (Carrie Fisher)')
  self.assertEqual(d['2025-TCSW-AUTO-A-CAM']['name'],'Indara (Carrie-Anne Moss)')
  self.assertIn('Lee Jung-jae',d['2025-TCSW-DUAL-DA-MJj']['name'])
  self.assertEqual(d['2025-TCSW-BASE-78']['name'],d['2025-TCSW-BASE-79']['name'])
  self.assertEqual(len(v),1235);self.assertTrue(all(x['serial_cap'] is None and x['card_id'] in d for x in v))
 def test_all_formats_and_malformed_odds(self):
  source=json.loads(m.SOURCE.read_text());d=m.tables();odds=source['odds']
  self.assertEqual(len(odds),95);self.assertTrue(all(list(x['rates'])==m.FORMATS for x in odds))
  invalid=[(x['label'],k,x['rates'][k]) for x in odds for k in x['invalidFormats']]
  self.assertEqual(invalid,[('Characters Kamino Purple Refractor Parallel','valueSE','1::590'),('Kyber Light Superfractor Refractor Parallel','valueSE','1:1,942400'),('Single Autographs Superfractor Refractor Parallel','valueEA','1:38,4384'),('Trio Autographs','valueEA','1:38,4384'),("Tribute to '75 Autograph Variation Superfractor Refractor Parallel",'valueEA','1:38,4384')])
  rules=d['catalogue_parallel_rules'];self.assertEqual(len(rules),91)
  self.assertEqual(sum('unresolved' in x['verification_status'] for x in rules),5)
  self.assertTrue(all(x['serial_cap'] is None for x in rules))
  self.assertEqual(sum(x['parallel_group']=='UO' for x in rules),7)
  self.assertTrue(any('valueSE: 1::590' in x['exclusive_note'] and 'Not interpreted' in x['exclusive_note'] for x in rules))
  self.assertEqual(sum(x['notes'].startswith('Official source marks DEBUT.') for x in d['catalogue_cards']),281)
  self.assertTrue(all(x['rookie'] is False for x in d['catalogue_cards']))
 def test_preservation_repeat_and_conflicts(self):
  base='fd8235e6fc2cc5238a9619247147918b58c7c695'
  def old(p):return subprocess.check_output(['git','show',f'{base}:{p}'],cwd=ROOT)
  prior=json.loads(old('data/catalogue-index.json'));current=load_catalogue()
  for r in prior['sets']:
   self.assertEqual((ROOT/'data'/r['file']).read_bytes(),old('data/'+r['file']))
   self.assertEqual(next(x for x in current['sets'] if x['id']==r['id']),{k:v for k,v in r.items() if k!='file'})
  self.assertEqual((ROOT/'data/catalogue.json').read_bytes(),old('data/catalogue.json'))
  r,c,_=m.build();before={p:p.read_bytes() for p in (ROOT/'data').glob('**/*.json')}
  save_catalogue(m.apply(copy.deepcopy(current),r,c));self.assertTrue(all(p.read_bytes()==b for p,b in before.items()))
  bad=copy.deepcopy(current);next(c for c in bad['cards'] if c['setId']==m.SET_ID)['name']='Conflict'
  with self.assertRaises(ValueError):m.apply(bad,r,c)
 def test_bad_source_and_guarded_sql(self):
  source=json.loads(m.SOURCE.read_text());source['subsets'][2]['rows'].pop()
  with self.assertRaises(ValueError):m.build(source)
  source=json.loads(m.SOURCE.read_text());source['subsets'][17]['rows'].pop()
  with self.assertRaises(ValueError):m.build(source)
  self.assertFalse(m.valid_rate('1::590'));self.assertFalse(m.valid_rate('1:38,4384'));self.assertTrue(m.valid_rate('1:1942400'))
  sql=generate();self.assertEqual(sql,OUT.read_text());self.assertTrue(sql.rstrip().endswith('commit;'))
  self.assertNotRegex(sql.lower(),r'(insert into|update|delete from|truncate) public\.(collection_items|reference_images)')
  self.assertIn('Conflicting catalogue_cards identity',sql)
if __name__=='__main__':unittest.main()
