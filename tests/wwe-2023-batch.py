"""Source reconciliation, actual edition applicability and collector preservation."""
import copy,hashlib,json,subprocess,sys,unittest
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import wwe_2023_batch as b
from catalogue_io import load_catalogue,save_catalogue
from prepare_wwe_2023_batch_import import generate,OUT
class WWE2023Batch(unittest.TestCase):
 def test_all_retained_source_evidence(self):
  for k in b.configs():self.assertEqual(b.extract(k),b.read_source(k))
  imm=b.read_source('immaculate');self.assertEqual(imm['originRows'],2516);self.assertEqual(len(b.extra_immaculate()),846);self.assertEqual(len(imm['comparisonDisagreements']),1)
  self.assertEqual(b.read_source('impeccable')['encodingRepairs'],19)
 def test_identity_and_exact_edition_applicability(self):
  for k,n,subs,versions in [('immaculate',1047,35,3362),('chronicles',843,34,5862),('impeccable',664,24,2335)]:
   with self.subTest(k=k):
    r,c,v=b.build(k);self.assertEqual((len(c),len(r['subsets']),len(v)),(n,subs,versions));self.assertEqual(len({x['id'] for x in c}),n);self.assertEqual(len({x['id'] for x in v}),versions)
    byid={x['id']:x for x in c}
    for row,x in zip(b.read_source(k)['rows'],v):
     f,p=b.classify(k,row[0]);card=byid[x['card_id']]
     self.assertEqual((card['subset'],card['number'],b.subjects(card['name'])),(f[0],row[1],b.subjects(row[2])))
     self.assertEqual((x['parallel'],x['serial_cap']),(p,int(row[4]) if row[4] else None))
 def test_missing_numbers_parallel_only_and_multi_signers(self):
  _,c,v=b.build('impeccable');self.assertNotIn('36',[x['number'] for x in c if x['subsetCode']=='BASE'])
  ink=[x for x in c if x['subsetCode']=='IN'];self.assertEqual(len(ink),39)
  absent=[x for x in ink if not any(y['parallel']=='Base' and y['card_id']==x['id'] for y in v)];self.assertEqual(len(absent),1);self.assertIn('Nova',absent[0]['name'])
  triples=[x for x in c if x['subsetCode']=='IFTS'];self.assertEqual(len(triples),2);self.assertTrue(all(len(x['name'].split(' / '))==3 for x in triples))
  _,c,v=b.build('chronicles');base=[x for x in c if x['subsetCode']=='BCHR'];self.assertEqual(len(base),99);self.assertNotIn('14',[x['number'] for x in base])
  self.assertEqual(len([x for x in c if x['subsetCode'].startswith('B')]),394)
  _,c,v=b.build('immaculate');quad=next(x for x in c if x['subsetCode']=='QA' and x['number']=='3');self.assertEqual(len(quad['name'].split(' / ')),4);self.assertIn('The Sandman',quad['name'])
  book=next(x for x in c if x['subsetCode']=='TAE');self.assertEqual(len(book['name'].split(' / ')),8)
  relics=[x for x in c if x['subsetCode'] in ('RM','STM','SSW','TIS')];self.assertEqual(len(relics),249);self.assertEqual(sum(x['card_id'] in {c['id'] for c in relics} for x in v),846)
 def test_every_prior_set_and_frozen_snapshot_unchanged(self):
  def old(path):return subprocess.check_output(['git','show',b.BASELINE+':'+path],cwd=ROOT)
  base=json.loads(old('data/catalogue-index.json'));cat=load_catalogue();self.assertGreaterEqual(len(cat['sets']),49);self.assertGreaterEqual(len(cat['cards']),25285)
  for s in base['sets']:
   self.assertEqual((ROOT/'data'/s['file']).read_bytes(),old('data/'+s['file']))
   self.assertEqual(next(x for x in cat['sets'] if x['id']==s['id']),{k:v for k,v in s.items() if k!='file'})
  self.assertEqual((ROOT/'data/catalogue.json').read_bytes(),old('data/catalogue.json'))
  before={p:p.read_bytes() for p in (ROOT/'data').rglob('*.json')}
  for k in b.configs():b.apply(cat,k)
  save_catalogue(cat);self.assertTrue(all(p.read_bytes()==s for p,s in before.items()))
  for k in b.configs():
   bad=copy.deepcopy(cat);next(c for c in bad['cards'] if c['setId']==b.configs()[k]['id'])['name']='Conflict'
   with self.assertRaises(ValueError):b.apply(bad,k)
 def test_tamper_detection_and_guarded_atomic_transaction(self):
  for k in b.configs():
   src=b.read_source(k);src['rows'].pop()
   with self.assertRaises(ValueError):b.build(k,src)
  sql=generate();self.assertEqual(sql,OUT.read_text());self.assertEqual(sql.count('\nbegin;'),1);self.assertEqual(sql.count('\ncommit;'),1)
  self.assertNotRegex(sql.lower(),r'(update|delete from|truncate) public\.')
  self.assertNotRegex(sql.lower(),r'insert into public\.(collection_items|reference_images)')
  for t in b.tables('immaculate'):self.assertIn('Conflicting '+t+' identity',sql);self.assertIn('before_'+t,sql)
if __name__=='__main__':unittest.main()
