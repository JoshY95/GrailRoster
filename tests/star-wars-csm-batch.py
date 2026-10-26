"""Verified source identities and preservation for Chrome/Sapphire/Masterwork batch."""
import copy,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import star_wars_csm_batch as s
from catalogue_io import load_catalogue,save_catalogue
from prepare_star_wars_csm_batch_import import generate,OUT

class CSMBatch(unittest.TestCase):
 def test_manifests_and_numbering(self):
  for key,n,subsets,printed in [('chrome',838,16,865),('sapphire',187,8,190),('masterwork',372,20,403)]:
   with self.subTest(key=key):
    src=s.read_source(key);r,c,v=s.build(key,src)
    self.assertEqual((len(c),len(v),len(r['subsets'])),(n,n,subsets));self.assertEqual(len({x['id'] for x in c}),n)
    self.assertEqual(sum(len(x['rows']) for x in src['subsets']),printed)
    self.assertEqual([x['order'] for x in c],list(range(1,n+1)))
    self.assertEqual((r['year'],r['releaseDate'],r['categoryId']),(s.CONFIGS[key]['year'],s.CONFIGS[key]['date'],'star-wars'))
    base=[x for x in c if x['subsetCode']=='BASE'];self.assertEqual({x['number'] for x in base},{str(i) for i in range(1,len(base)+1)})
    self.assertTrue(all(x['serial_cap'] is None for x in v))
 def test_chrome_parallel_designs_and_flags(self):
  src=s.read_source('chrome');r,c,v=s.build('chrome');d={x['id']:x for x in c}
  for code in ['BASE','AV','HV','BC']:self.assertEqual(sum(x['subsetCode']==code for x in c),150)
  self.assertEqual(len({d[k]['id'] for k in ['2024-TCSW-BASE-1','2024-TCSW-AV-AV-1','2024-TCSW-HV-HV-1','2024-TCSW-BC-BC-1']}),4)
  self.assertEqual(sum(x['category']=='Autograph' for x in c),115)
  self.assertEqual(sum(r['fields'].count('DEBUT') for x in src['subsets'] for r in x['rows']),46)
  self.assertEqual(sum('DEBUT marked' in x['notes'] for x in s.tables('chrome')['catalogue_cards']),46)
  self.assertEqual(sum(x['subsetCode']=='GE' for x in c),9);self.assertEqual(sum(x['subsetCode']=='RA' for x in c),9)
  self.assertEqual(len(d['2024-TCSW-TA-TA-MBB']['name'].split(' / ')),3)
 def test_sapphire_v3_and_redemption(self):
  src=s.read_source('sapphire');r,c,v=s.build('sapphire')
  self.assertEqual(sum(x['category']=='Autograph' for x in c),25)
  self.assertEqual({x['number'] for x in c if x['subsetCode']=='PD'},{'PD-MB','PD-PK','PD-PM'})
  self.assertNotIn('PD-PL',{x['number'] for x in c})
  self.assertEqual(src['unresolved'][0]['label'],'Mystery Redemption')
  self.assertFalse(any('Mystery' in x['number'] for x in c))
  self.assertIn('The <i>Radiant VII</i> is Obliterated!',{x['name'] for x in c})
 def test_masterwork_spaced_number_and_full_quotes(self):
  src=s.read_source('masterwork');r,c,v=s.build('masterwork');d={x['id']:x for x in c}
  self.assertIn('Katee Sackhoff',d['2022-TSWMW-AUTO-MWA-KS']['name'])
  self.assertEqual(d['2022-TSWMW-AUTO-MWA-KS-KIRAN-SHAH']['number'],'MWA- KS')
  self.assertIn('Kiran Shah',d['2022-TSWMW-AUTO-MWA-KS-KIRAN-SHAH']['name'])
  self.assertTrue(d['2022-TSWMW-OB1-OB1-10']['name'].endswith('nothing.”'))
  self.assertTrue(d['2022-TSWMW-OB1G-OB1G-10']['name'].endswith('nothing.”'))
  self.assertEqual([len(x) for x in src['rosters'].values()],[94,48,45,46])
  self.assertEqual(sum(x['category']=='Autograph Relic' for x in c),52)
  self.assertEqual(sum(x['subsetCode']=='QA' for x in c),5)
  self.assertTrue(all(len(x['name'].split(' / '))==4 for x in c if x['subsetCode']=='QA'))
 def test_odds_limits(self):
  for k,rows,rules in [('chrome',82,71),('sapphire',41,41),('masterwork',0,0)]:
   self.assertEqual(len(s.read_source(k)['odds']),rows);d=s.tables(k);self.assertEqual(len(d['catalogue_parallel_rules']),rules)
   self.assertTrue(all(x['serial_cap'] is None for x in d['catalogue_parallel_rules']))
  self.assertTrue(all(len(x['rates'])==5 for x in s.read_source('chrome')['odds']))
  self.assertTrue(s.read_source('masterwork')['oddsUnavailable'].endswith('StarWarsMasterWorkOdds.pdf'))
  self.assertFalse(any('PUZZLE' in x['parallel'] for x in s.tables('chrome')['catalogue_parallel_rules']))
 def test_preservation_repeat_conflicts(self):
  def old(p):return subprocess.check_output(['git','show',f'f30ec10:{p}'],cwd=ROOT)
  oldindex=json.loads(old('data/catalogue-index.json'));current=load_catalogue()
  self.assertEqual((len(current['sets']),len(current['cards'])),(42,20616))
  self.assertEqual(sum(x['cardCount'] for x in current['sets'] if x['categoryId']=='star-wars'),9318)
  for x in oldindex['sets']:
   self.assertEqual((ROOT/'data'/x['file']).read_bytes(),old('data/'+x['file']))
   self.assertEqual(next(y for y in current['sets'] if y['id']==x['id']),{k:v for k,v in x.items() if k!='file'})
  self.assertEqual((ROOT/'data/catalogue.json').read_bytes(),old('data/catalogue.json'))
  before={p:p.read_bytes() for p in (ROOT/'data').glob('**/*.json')}
  for k in s.CONFIGS:s.apply(current,k)
  save_catalogue(current);self.assertTrue(all(p.read_bytes()==b for p,b in before.items()))
  for k in s.CONFIGS:
   bad=copy.deepcopy(current);next(x for x in bad['cards'] if x['setId']==s.CONFIGS[k]['id'])['name']='Conflict'
   with self.assertRaises(ValueError):s.apply(bad,k)
 def test_bad_source_and_transaction(self):
  for k in s.CONFIGS:
   for i in range(len(s.CONFIGS[k]['sections'])):
    src=s.read_source(k);src['subsets'][i]['rows'].pop()
    with self.assertRaises(ValueError):s.build(k,src)
  sql=generate();self.assertEqual(sql,OUT.read_text());self.assertEqual(sql.count('\nbegin;'),1);self.assertEqual(sql.count('\ncommit;'),1)
  self.assertNotRegex(sql.lower(),r'(insert into|update|delete from|truncate) public\.(collection_items|reference_images)')
  from prepare_star_wars_2024_batch_import import generate as prior,OUT as priorout
  self.assertEqual(prior(),priorout.read_text())
if __name__=='__main__':unittest.main()
