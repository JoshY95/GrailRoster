"""Checklist evidence, actual edition applicability and collector preservation."""
import copy,hashlib,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import wwe_2024_batch as b
from catalogue_io import load_catalogue,save_catalogue
from prepare_wwe_2024_batch_import import generate,OUT
class WWE2024Batch(unittest.TestCase):
 def test_original_distributor_and_two_workbook_comparison(self):
  for k in b.CONFIGS:self.assertEqual(b.extract(k),b.read_source(k))
 def test_manifests_and_versions(self):
  for k,n,subs,versions,numbered in [('three-count',415,13,3333,3313),('select',789,21,11234,7240),('photogenic',395,12,2924,2544)]:
   with self.subTest(k=k):
    r,c,v=b.build(k);self.assertEqual((len(c),len(r['subsets']),len(v)),(n,subs,versions));self.assertEqual(len({x['id'] for x in c}),n);self.assertEqual(len({x['id'] for x in v}),versions)
    self.assertEqual(sum(x['serial_cap'] is not None for x in v),numbered)
    source=b.read_source(k)['rows'];byid={x['id']:x for x in c}
    for row,x in zip(source,v):
     family,p=b.classify(k,row[0]);card=byid[x['card_id']]
     self.assertEqual((card['subset'],card['number'],tuple(b.subjects(card['name']))),(family[0],row[1],tuple(b.subjects(row[2]))))
     self.assertEqual((x['parallel'],x['serial_cap']),(p,int(row[4]) if row[4] else None))
 def test_photo_numbering_and_multi_subjects(self):
  _,c,v=b.build('photogenic');conflict=[x for x in c if x['subsetCode']=='BV' and x['number']=='175']
  self.assertEqual({x['name'] for x in conflict},{'Triple H','Beth Phoenix'});self.assertEqual(len({x['id'] for x in conflict}),2)
  triple=next(x for x in conflict if x['name']=='Triple H');beth=next(x for x in conflict if x['name']=='Beth Phoenix')
  self.assertEqual([x['parallel'] for x in v if x['card_id']==triple['id']],['Base'])
  self.assertNotIn('Base',[x['parallel'] for x in v if x['card_id']==beth['id']])
  dual=[x for x in c if x['subsetCode']=='DA'];self.assertEqual(len(dual),10);self.assertTrue(all(len(x['name'].split(' / '))==2 for x in dual))
  prog=[x for x in c if x['subsetCode']=='PRO'];self.assertEqual(len(prog),15);self.assertIn('"The Fiend" Bray Wyatt',next(x for x in prog if x['number']=='6')['name'])
 def test_parallel_only_and_source_labels(self):
  for k in b.CONFIGS:
   _,c,v=b.build(k);missing=[x for x in c if not any(y['card_id']==x['id'] and y['parallel']=='Base' for y in v)]
   self.assertGreater(len(missing),0,'Parallel-only subjects must survive union')
  _,c,v=b.build('select');card=next(x for x in c if x['subsetCode']=='CON' and x['number']=='1')
  self.assertTrue({'Red and Blue','Red and Blue Prizms'}<={x['parallel'] for x in v if x['card_id']==card['id']})
 def test_all_existing_bytes_and_repeat_conflict(self):
  def old(p):return subprocess.check_output(['git','show',f'{b.BASELINE}:{p}'],cwd=ROOT)
  base=json.loads(old('data/catalogue-index.json'));cat=load_catalogue()
  self.assertGreaterEqual(len(cat['sets']),45);self.assertGreaterEqual(len(cat['cards']),22215);self.assertGreaterEqual(sum(x['cardCount'] for x in cat['sets'] if x['categoryId']=='wwe'),12897)
  for s in base['sets']:
   self.assertEqual((ROOT/'data'/s['file']).read_bytes(),old('data/'+s['file']))
   self.assertEqual(next(x for x in cat['sets'] if x['id']==s['id']),{k:v for k,v in s.items() if k!='file'})
  self.assertEqual((ROOT/'data/catalogue.json').read_bytes(),old('data/catalogue.json'))
  before={p:p.read_bytes() for p in (ROOT/'data').rglob('*.json')}
  for k in b.CONFIGS:b.apply(cat,k)
  save_catalogue(cat);self.assertTrue(all(p.read_bytes()==x for p,x in before.items()))
  for k in b.CONFIGS:
   bad=copy.deepcopy(cat);next(x for x in bad['cards'] if x['setId']==b.CONFIGS[k]['id'])['name']='Conflict'
   with self.assertRaises(ValueError):b.apply(bad,k)
 def test_missing_rows_and_atomic_guards(self):
  for k in b.CONFIGS:
   src=b.read_source(k);src['rows'].pop()
   with self.assertRaises(ValueError):b.build(k,src)
  sql=generate();self.assertEqual(sql,OUT.read_text());self.assertEqual(sql.count('\nbegin;'),1);self.assertEqual(sql.count('\ncommit;'),1)
  self.assertNotRegex(sql.lower(),r'(update|delete from|truncate) public\.')
  self.assertNotRegex(sql.lower(),r'insert into public\.(collection_items|reference_images)')
  for t in b.tables('three-count'):self.assertIn('Conflicting '+t+' identity',sql)
if __name__=='__main__':unittest.main()
