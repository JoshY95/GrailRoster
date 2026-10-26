"""Import one Prizm parent, retaining source-listed Premium and Under Card editions."""
import argparse,hashlib,json,re
from collections import Counter,OrderedDict
from pathlib import Path
from catalogue_io import load_catalogue,save_catalogue
from wwe_2024_batch import clean,slug,subjects
ROOT=Path(__file__).resolve().parents[1];DIR=ROOT/'sources/2024-panini-prizm-wwe'
BASELINE='0cab343bf369f3fa4454b500cc77044d318df35c'
SID='2024-panini-prizm-wwe';PREFIX='2024-PPWWE'
SOURCE='https://gogts.net/wp-content/uploads/2024/07/2024-Panini-Prizm-WWE-Trading-Cards-Checklist.xls'
COMPARISON='https://xcdn.checklistinsider.com/public/2024/07/2024-Panini-Prizm-WWE-Wrestling-Checklist-Downloads-Excel-spreadsheet-updates.xlsx'
GTS='https://gogts.net/2024-panini-prizm-wwe-trading-cards-checklist/'
PREMIUM='https://www.checklistinsider.com/2024-panini-prizm-premium-wwe-factory-set'
FAMILIES=[('Base Horizontal','BH','Base',100),('Base Horizontal Prizms Under Card Variation','BHV','Variation',10),('Base Vertical','BV','Base',100),('Base Vertical Prizms Under Card Variation','BVV','Variation',10),('Black Color Blast','BCB','Insert',5),('Champion Signatures','CS','Autograph',10),('Color Blast','CB','Insert',10),('Emergent','EM','Insert',20),('Iconic Rivals Dual Autographs','IRDA','Autograph',10),('Legendary Signatures','LS','Autograph',19),('Prizmatic Entrances','PE','Insert',20),('Rumble Performances','RP','Insert',20),('Sensational Signatures','SS','Autograph',100),('Superstar Autographs','SA','Autograph',35),('Throwback Signatures','TS','Autograph',10),('WrestleMania Moments','WM','Insert',37)]
BAD='Seth â€œFreakinâ€\x9d Rollins';FIXED='Seth “Freakin” Rollins'
NOTE='Only source-listed subject/edition pairs. Blank SEQUENCE is unknown. The 200 base White Sparkle SEQUENCE=1 claims are held unresolved; no base 1/1 cap is asserted.'
STATUS='Original GTS/Panini workbook and independent copy reconciled; documented base White Sparkle cap exception'
def classify(label):
 choices=[f for f in FAMILIES if label==f[0] or label.startswith(f[0]+' ')]
 if not choices:raise ValueError('Unknown family '+label)
 f=max(choices,key=lambda x:len(x[0]));p=label[len(f[0]):].strip() or ('Under Card Variation' if f[1] in ('BHV','BVV') else 'Base')
 if f[1] in ('BHV','BVV') and p=='Gold':p='Under Card Variation Gold'
 return f,p

def extract():
 import xlrd,openpyxl
 s=xlrd.open_workbook(DIR/'checklist.xls').sheet_by_index(0)
 if s.ncols!=5 or s.row_values(2)!=['CARD #','CARD SET','ATHLETE','TEAM','SEQUENCE']:raise ValueError('Distributor columns changed')
 original=[[clean(s.cell_value(i,j)) for j in (1,0,2,3,4)] for i in range(3,s.nrows)]
 rows=[[v.replace(BAD,FIXED) for v in r] for r in original]
 w=openpyxl.load_workbook(DIR/'comparison.xlsx',data_only=True).active
 if list(next(w.values))!=['CARD SET','CARD #','ATHLETE','TEAM','SEQ']:raise ValueError('Comparison columns changed')
 comparison=[[clean(v) for v in r] for r in list(w.values)[1:]]
 def key(r):return r[0],r[1],tuple(subjects(r[2])),tuple(subjects(r[3])),r[4]
 if len(rows)!=9270 or len(comparison)!=9270 or Counter(map(key,rows))!=Counter(map(key,comparison)):raise ValueError('Complete workbook reconciliation failed')
 for r in rows:
  if not all(r[:4]) or (r[4] and (not r[4].isdigit() or int(r[4])<1)):raise ValueError('Invalid required cell/SEQUENCE')
 if sum(a!=b for a,b in zip(original,rows))!=59:raise ValueError('Encoding repair count changed')
 return dict(sourceUrl=SOURCE,sourceSha256=hashlib.sha256((DIR/'checklist.xls').read_bytes()).hexdigest(),comparisonUrl=COMPARISON,comparisonSha256=hashlib.sha256((DIR/'comparison.xlsx').read_bytes()).hexdigest(),sourceRows=9270,encodingRepairs=59,encodingOriginal=BAD,encodingDisplay=FIXED,capException=dict(label='Base Horizontal/Vertical Prizms White Sparkle',sourceSequence='1',storedCap=None,rows=200,reason='Base 1/1 assertion conflicts with unnumbered base treatment in Beckett/Checklist Center product guides; retained unresolved pending manufacturer clarification.'),rows=rows)
def read_source():return json.loads((DIR/'checklist.json').read_text())
def build(src=None):
 src=src or read_source();rows=src['rows']
 if len(rows)!=9270:raise ValueError('Source row count changed')
 groups=OrderedDict()
 for row in rows:
  f,p=classify(row[0]);groups.setdefault((f[0],row[1]),[]).append((row,p))
 cards=[];cardmap={};counts=Counter()
 for (family,n),rr in groups.items():
  f=next(x for x in FAMILIES if x[0]==family);_,code,category,_=f
  if len({tuple(subjects(r[2])) for r,p in rr})!=1:raise ValueError('Conflicting subjects for '+family+' '+n)
  canonical=next((r for r,p in rr if p in ['Base','Under Card Variation']),rr[0][0]);people=[x.strip() for x in canonical[2].split('/')]
  card=dict(id=f'{PREFIX}-{code}-{n}',setId=SID,order=len(cards)+1,number=n,name=' / '.join(people),subject2=' / '.join(people[1:]) or None,category=category,subset=family,subsetCode=code,roster=canonical[3],rookie='No',parallelGroup=code)
  cards.append(card);cardmap[(family,n)]=card;counts[family]+=1
 if counts!=Counter({n:count for n,_,_,count in FAMILIES}):raise ValueError('Identity manifest changed '+str(counts))
 variants=[];seen=set()
 for i,row in enumerate(rows,1):
  f,p=classify(row[0]);c=cardmap[(f[0],row[1])];cap=int(row[4]) if row[4] else None
  if f[1] in ('BH','BV') and p=='Prizms White Sparkle':cap=None
  vid=c['id']+'-'+slug(p)
  if vid in seen:raise ValueError('Duplicate exact edition '+vid)
  seen.add(vid)
  variants.append(dict(id=vid,set_id=SID,card_id=c['id'],variant_order=i,subset=c['subset'],card_number=c['number'],display_name=c['name'],parallel=p,serial_cap=cap,serial_exact=('1/1' if cap==1 else f'/{cap}') if cap else None,exclusive_note='First Off the Line' if 'FOTL' in p else 'Premium Factory Set exclusive' if 'Premium Box Set' in p else None,numbering_note=NOTE,verification_status=STATUS))
 subsets=[dict(category=category,name=n,code=code,count=count) for n,code,category,count in FAMILIES]
 record=dict(id=SID,categoryId='wwe',name='2024 Panini Prizm WWE',shortName='Prizm WWE 2024',accent='#aebbd1',year=2024,manufacturer='Panini',releaseDate='2024-08-09',cardCount=len(cards),subsetCount=len(subsets),subsets=subsets)
 return record,cards,variants

def apply(cat):
 r,c,_=build();old=[s for s in cat['sets'] if s['id']==SID];oc=[x for x in cat['cards'] if x['setId']==SID]
 if old or oc:
  if old!=[r] or oc!=c:raise ValueError('Existing Prizm identities differ; refusing overwrite')
 else:cat['sets'].append(r);cat['cards'].extend(c);cat['generatedAt']='2026-10-26T00:00:00Z'
 return cat

def tables():
 r,c,v=build();out=OrderedDict()
 out['catalogue_sets']=[dict(id=SID,name=r['name'],short_name=r['shortName'],year=2024,manufacturer='Panini',release_date=r['releaseDate'],source_file=SOURCE,accent=r['accent'],card_count=len(c),subset_count=len(r['subsets']),variant_count=len(v))]
 out['catalogue_subsets']=[dict(set_id=SID,subset_code=s['code'],category=s['category'],name=s['name'],card_count=s['count'],parallel_group=s['code'],source_url=SOURCE) for s in r['subsets']]
 out['catalogue_cards']=[dict(id=x['id'],set_id=SID,checklist_order=x['order'],category=x['category'],subset_code=x['subsetCode'],card_number=x['number'],display_name=x['name'],subject_1=x['name'].split(' / ')[0],subject_2=x['subject2'],roster=x['roster'],rookie=False,parallel_group=x['parallelGroup'],image_status='Missing',pricing_status='Unpriced',source_url=SOURCE,notes='Official distributor workbook. Premium Factory Set is a parallel edition of this parent; Under Card image/persona variations have separate identities. '+NOTE) for x in c]
 out['catalogue_variants']=v;byid={x['id']:x for x in c};rules=OrderedDict()
 for x in v:
  code=byid[x['card_id']]['subsetCode'];p=x['parallel'];cap=x['serial_cap'];key=(code,p,cap)
  if key not in rules:rules[key]=dict(id=SID+'-'+code.lower()+'-'+slug(p).lower()+'-'+str(cap or 'unknown'),set_id=SID,parallel_group=code,applies_to=x['subset'],parallel=p,serial_cap=cap,serial_exact=x['serial_exact'],exclusive_note=x['exclusive_note'],numbering_note='Exact listed card/edition rows only; never extrapolate a full grid. '+NOTE,verification_status=STATUS)
 out['catalogue_parallel_rules']=list(rules.values())
 out['catalogue_sources']=[dict(id=SID+'-'+suffix,set_id=SID,source=name,purpose=purpose,url=url,notes=note) for suffix,name,purpose,url,note in [
 ('checklist','GTS Distribution / Panini','Checklist and exact edition sequences',SOURCE,'All 9,270 rows reconciled to independent workbook; 59 Seth nickname encoding repairs documented. Base White Sparkle cap claims withheld.'),
 ('comparison','Checklist Insider','Independent workbook comparison',COMPARISON,'All numbers, subjects, editions and sequences reconcile after one known encoding repair and signer-order normalization.'),
 ('release','GTS Distribution','Release dates',GTS,'Hobby scheduled 9 August 2024; Under Card 23 August 2024. One parent set.'),
 ('premium','Checklist Insider','Premium Factory Set edition relationship',PREMIUM,'Premium uses the same 200 base designs; original workbook individually lists 200 Premium Box Set /199 and 200 Premium Box Set Gold /5 variants. No duplicate parent/identities created.'),
 ('white-sparkle','Beckett','Conflicting base White Sparkle serial claim','https://www.beckett.com/news/2024-panini-prizm-wwe-wrestling-cards/','Base White Sparkle is unnumbered in this guide, whereas original workbook and mirror print SEQUENCE=1. Store unknown cap for those 200 base versions; retain literal source evidence. Autograph source sequences remain 1/1.')]]
 return out
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--extract',action='store_true');a=p.parse_args()
 if a.extract:
  src=extract();(DIR/'checklist.json').write_text(json.dumps(src,ensure_ascii=False,separators=(',',':'))+'\n');print('Reconciled',len(src['rows']),'rows; 59 encoding repairs')
 else:
  cat=load_catalogue();apply(cat);save_catalogue(cat);r,c,v=build();print(len(c),'identities',len(r['subsets']),'subsets',len(v),'versions',sum(x['serial_cap'] is not None for x in v),'verified cap rows')
