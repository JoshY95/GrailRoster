"""Three-set manufacturer reconciliation and collector/catalogue preservation."""
import copy,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import star_wars_2024_batch as s
from catalogue_io import load_catalogue,save_catalogue
from prepare_star_wars_2024_batch_import import generate,OUT

class Batch2024(unittest.TestCase):
 def test_complete_manifest_and_numbering(self):
  for key,count,subset,rows,odds in [('black',424,11,447,60),('high-tek',882,16,882,68),('galaxy',265,13,291,95)]:
   with self.subTest(key=key):
    src=s.read_source(key);r,c,v=s.build(key,src)
    self.assertEqual((len(c),len(r['subsets']),len(v)),(count,subset,count))
    self.assertEqual([x['count'] for x in r['subsets']],s.CONFIGS[key]['counts'])
    self.assertEqual((r['year'],r['releaseDate'],r['categoryId']),(2024,s.CONFIGS[key]['date'],'star-wars'))
    self.assertEqual(sum(len(x['rows']) for x in src['subsets']),rows);self.assertEqual(len(src['odds']),odds)
    self.assertEqual(len({x['id'] for x in c}),count);self.assertEqual([x['order'] for x in c],list(range(1,count+1)))
    self.assertTrue(all(x['serial_cap'] is None for x in v))
    for x in r['subsets']:
     if x['category']=='Base':self.assertEqual({a['number'] for a in c if a['subsetCode']==x['code']},{str(i) for i in range(1,101)})
 def test_black_duplicate_number_and_multi_signers(self):
  r,c,v=s.build('black');dup=[x for x in c if x['number']=='ALS-KK']
  self.assertEqual(len(dup),2);self.assertNotEqual(dup[0]['id'],dup[1]['id'])
  self.assertIn('Keira Knightley',dup[0]['name']);self.assertIn('Katy Kartwheel',dup[1]['name'])
  self.assertTrue(dup[0]['id'].endswith('-KEIRA-KNIGHTLEY'));self.assertTrue(dup[1]['id'].endswith('-KATY-KARTWHEEL'))
  self.assertEqual(sum(x['category']=='Autograph' for x in c),229)
  self.assertEqual(sum(x['subsetCode']=='DA' for x in c),11);self.assertEqual(sum(x['subsetCode']=='TA' for x in c),6)
  self.assertTrue(all(len(x['name'].split(' / '))==3 for x in c if x['subsetCode']=='TA'))
  self.assertIn('F (Karen Fukuhara)',next(x['name'] for x in c if x['number']=='ALS-KF'))
 def test_high_tek_patterns_and_source_prefixes(self):
  r,c,v=s.build('high-tek');d={x['id']:x for x in c}
  patterns=[x for x in c if x['number']=='1'];self.assertEqual(len(patterns),7);self.assertEqual(len({x['id'] for x in patterns}),7)
  self.assertTrue(all(x['name']=='Aayla Secura' for x in patterns))
  self.assertEqual(d['2024-TSWHT-FT-S-M']['name'],'The Mandalorian');self.assertEqual(d['2024-TSWHT-FT-S-ZB']['name'],'Zorii Bliss')
  self.assertEqual(len([x for x in c if x['category']=='Base']),700)
  self.assertEqual(len([x for x in c if x['category']=='Autograph']),82)
  self.assertIn('Hayden Christensen',d['2024-TSWHT-DA-DA-EM']['name']);self.assertIn('Ewan McGregor',d['2024-TSWHT-DA-DA-EM']['name'])
  self.assertTrue(all(len(x['name'].split(' / '))==2 for x in c if x['subsetCode'] in ['DA','DS']))
 def test_galaxy_art_rosters_and_quads(self):
  src=s.read_source('galaxy');r,c,v=s.build('galaxy');d={x['id']:x for x in c}
  self.assertEqual(d['2024-TSWG-BASE-93']['name'],'Falcon Rising');self.assertEqual(d['2024-TSWG-BASE-93']['roster'],'Mark Chilcott')
  self.assertNotEqual(d['2024-TSWG-SITH-AS-1']['id'],d['2024-TSWG-ARMOR-AS-1']['id'])
  self.assertEqual([len(v) for v in src['rosters'].values()],[123,6])
  self.assertEqual(len([x for x in c if x['subsetCode']=='QA']),4)
  self.assertTrue(all(len(x['name'].split(' / '))==4 for x in c if x['subsetCode']=='QA'))
  self.assertIn('Diego Luna',d['2024-TSWG-QA-QA-DADK']['name'])
 def test_verified_caps_and_source_only_odds(self):
  for key,n,caps in [('black',60,1),('high-tek',63,31),('galaxy',92,33)]:
   rules=s.tables(key)['catalogue_parallel_rules'];self.assertEqual(len(rules),n);self.assertEqual(sum(x['serial_cap'] is not None for x in rules),caps)
  ht=s.tables('high-tek')['catalogue_parallel_rules'];self.assertFalse(any(x['parallel_group']=='RE' and x['serial_cap'] in [25,50] for x in ht))
  self.assertFalse(any(x['parallel_group'] in ['DSI','DSE'] and x['serial_cap']==50 for x in ht))
  self.assertTrue(all(x['serial_cap'] is None for x in ht if x['parallel_group'] in ['AUTO','DA','DS','ABW']))
  self.assertEqual(next(x['serial_cap'] for x in s.tables('black')['catalogue_parallel_rules'] if x['parallel_group']=='GL' and x['parallel']=='Base issue'),99)
  self.assertFalse(any(x['applies_to']=='BASE CARDS PATTERN' for x in ht))
  self.assertEqual(sum(x['id'].find('-GUIDE-')>=0 for x in s.tables('galaxy')['catalogue_parallel_rules']),2)
 def test_prior_bytes_metadata_idempotency_conflicts(self):
  def old(p):return subprocess.check_output(['git','show',f'52ed0f6:{p}'],cwd=ROOT)
  prior=json.loads(old('data/catalogue-index.json'));current=load_catalogue()
  self.assertGreaterEqual(len(current['sets']),39);self.assertGreaterEqual(len(current['cards']),19219)
  self.assertGreaterEqual(sum(x['cardCount'] for x in current['sets'] if x['categoryId']=='star-wars'),7921)
  for x in prior['sets']:
   self.assertEqual((ROOT/'data'/x['file']).read_bytes(),old('data/'+x['file']))
   self.assertEqual(next(y for y in current['sets'] if y['id']==x['id']),{k:v for k,v in x.items() if k!='file'})
  self.assertEqual((ROOT/'data/catalogue.json').read_bytes(),old('data/catalogue.json'))
  before={p:p.read_bytes() for p in (ROOT/'data').glob('**/*.json')}
  for key in s.CONFIGS:s.apply(current,key)
  save_catalogue(current);self.assertTrue(all(p.read_bytes()==b for p,b in before.items()))
  for key in s.CONFIGS:
   bad=copy.deepcopy(current);next(x for x in bad['cards'] if x['setId']==s.CONFIGS[key]['id'])['name']='Conflict'
   with self.assertRaises(ValueError):s.apply(bad,key)
 def test_bad_source_and_atomic_sql(self):
  for key in s.CONFIGS:
   for i in range(len(s.CONFIGS[key]['sections'])):
    src=s.read_source(key);src['subsets'][i]['rows'].pop()
    with self.assertRaises(ValueError):s.build(key,src)
  sql=generate();self.assertEqual(sql,OUT.read_text());self.assertEqual(sql.count('\nbegin;'),1);self.assertEqual(sql.count('\ncommit;'),1)
  self.assertNotRegex(sql.lower(),r'(insert into|update|delete from|truncate) public\.(collection_items|reference_images)')
  self.assertIn('Conflicting catalogue_cards identity',sql);self.assertIn('Count, linkage or preservation check failed',sql)

if __name__=='__main__':unittest.main()
