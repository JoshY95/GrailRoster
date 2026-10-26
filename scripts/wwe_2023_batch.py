"""Source-listed 2023 Immaculate, Chronicles and Impeccable WWE identities/editions.

No absent checklist numbers, caps or subject/parallel combinations are inferred.
Original workbooks and the explicit reconciliation evidence are retained.
"""
import argparse,hashlib,json,re
from collections import OrderedDict,Counter
from functools import lru_cache
from pathlib import Path
from catalogue_io import load_catalogue,save_catalogue

ROOT=Path(__file__).resolve().parents[1]
SOURCE_DIR=ROOT/'sources/wwe-2023-batch'
BASELINE='b3c7cbb6a66807c795eb94e60cdf84a5eda03601'
MANIFEST=SOURCE_DIR/'manifest.json'
MULTI={'Championship Lineage Triple Autographs','Dual Autographed Memorabilia','Dual Autographs','Triple Autographs','Quad Autographs','Main Event Dual Mat Autographs','The Attitude Era'}

@lru_cache(maxsize=1)
def configs():return json.loads(MANIFEST.read_text(),object_pairs_hook=OrderedDict)
def clean(x):
 if isinstance(x,(int,float)) and not isinstance(x,bool) and int(x)==x:return str(int(x))
 return re.sub(r'\s+',' ',str(x or '')).strip()
def slug(x):return re.sub('[^A-Z0-9]+','-',x.upper()).strip('-')
def subjects(x):return tuple(sorted(set(clean(s) for s in x.split('/'))))
def comparison_subjects(x):
 # Nickname quotation marks and exact repeated image/persona labels are display
 # formatting only. Original strings are retained in both source workbooks.
 return tuple(sorted(set(s.replace('“','').replace('”','').replace('"','') for s in subjects(x))))
def rowkey(r):return r[0],r[1],comparison_subjects(r[2]),subjects(r[3]),r[4]
def read_workbook(key,kind):
 import openpyxl
 p=SOURCE_DIR/(key+'-'+kind+'.xlsx');s=openpyxl.load_workbook(p,data_only=True).active
 head=list(next(s.values));expected=['CARD SET','CARD #','ATHLETE','TEAM']
 if kind=='insider' and (head[:4]!=expected or head[-1]!='SEQ'):raise ValueError('Unexpected published workbook columns')
 if kind=='center' and head[:3]!=['Set','Number','Name']:raise ValueError('Unexpected comparison columns')
 rows=[]
 for r in list(s.values)[1:]:
  if not r[0] and r[1] is None:continue
  indices=(0,1,2,3,5) if kind=='insider' and len(head)==6 else (0,1,2,3,4)
  rows.append([clean(r[i]) for i in indices])
 return rows
def read_origin(key):
 import xlrd
 p=SOURCE_DIR/(key+'-gts.xls');s=xlrd.open_workbook(p).sheet_by_index(0)
 if s.row_values(2)!=['CARD #','CARD SET','ATHLETE','TEAM','SEQUENCE']:raise ValueError('Unexpected GTS columns')
 return [[clean(s.cell_value(i,j)) for j in (1,0,2,3,4)] for i in range(3,s.nrows)]
def combine_signers(rows):
 out=OrderedDict()
 for r in rows:
  if any(r[0]==f or r[0].startswith(f+' ') for f in MULTI):
   g=out.setdefault((r[0],r[1],r[4]),[r[0],r[1],[],[],r[4]]);g[2].append(r[2]);g[3].append(r[3])
  else:out[('single',len(out))]=r
 return [[r[0],r[1],'/'.join(r[2]),'/'.join(r[3]),r[4]] if isinstance(r[2],list) else r for r in out.values()]
def extra_immaculate():
 evidence=json.loads((SOURCE_DIR/'immaculate-extra-evidence.json').read_text());rows=[]
 for section in evidence['sections']:
  family=section['heading'].split(' (#')[0]
  caps={'Base':99} if family=='The Immaculate Standard' else {'Base':35,'Red':25,'Gold':10,'Platinum':1}
  if len(caps)>1 and 'Parallels: Red #/25; Gold #/10; Platinum 1/1' not in section['text']:raise ValueError('Changed independent parallel statement')
  for line in section['text'].splitlines():
   m=re.fullmatch(r'___ (\d+) (.*?) [–—] (.*?) /(\d+)',line.strip())
   if not m:continue
   number,name,team,cap=m.groups()
   if int(cap)!=caps['Base']:raise ValueError('Changed independent subject cap')
   rows.extend([[family+(' '+p if p!='Base' else ''),number,name,team,str(c)] for p,c in caps.items()])
 if len(rows)!=846:raise ValueError('Incomplete independent supplement')
 return rows
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def extract(key):
 cfg=configs()[key];rows=read_workbook(key,'insider')
 if len(rows)!=cfg['rows'] or any(not all(r[:3]) or (r[4] and (not r[4].isdigit() or int(r[4])<1)) for r in rows):raise ValueError('Invalid source count/fields/printed sequence')
 primary=Counter(map(rowkey,rows));evidence={}
 if key!='impeccable':
  comparison=read_workbook(key,'center');raw_count=len(comparison)
  if key=='immaculate':comparison=combine_signers(comparison)+extra_immaculate()
  compared=Counter(map(rowkey,comparison))
  if key=='immaculate':
   # The older mirror repeats Rob Van Dam in Quad #3 where both original
   # GTS and the updated source list The Sandman. Record, do not hide, it.
   expected_primary=Counter(rowkey(r) for r in rows if r[0] in ('Quad Autographs','Quad Autographs Platinum') and r[1]=='3')
   expected_compare=Counter(rowkey(r) for r in comparison if r[0] in ('Quad Autographs','Quad Autographs Platinum') and r[1]=='3')
   wanted=('Bubba Ray Dudley','D-Von Dudley','Rob Van Dam','The Sandman')
   if any(r[2]!=wanted for r in expected_primary) or any(r[2]!=wanted[:-1] for r in expected_compare):raise ValueError('Changed Quad #3 source disagreement')
   if len(expected_primary)!=2 or len(expected_compare)!=2 or primary-compared!=expected_primary or compared-primary!=expected_compare:raise ValueError('Unexpected comparison disagreement')
   evidence['comparisonDisagreements']=['Quad Autographs #3 and Platinum #3: older mirror repeats Rob Van Dam and omits The Sandman; original GTS and updated workbook agree on all four signers.']
  elif compared!=primary:raise ValueError('Independent comparison differs for '+key)
  evidence.update(comparisonRawRows=raw_count,comparisonSha256=sha(SOURCE_DIR/(key+'-center.xlsx')))
 if key!='chronicles':
  original=read_origin(key);bad='Seth â€œFreakinâ€\x9d Rollins';fixed='Seth “Freakin” Rollins'
  repaired=[[s.replace(bad,fixed) for s in r] for r in original]
  expected=primary if key=='impeccable' else primary-Counter(map(rowkey,extra_immaculate()))
  if Counter(map(rowkey,repaired))!=expected:raise ValueError('Original distributor rows differ for '+key)
  evidence.update(originSha256=sha(SOURCE_DIR/(key+'-gts.xls')),originRows=len(original),encodingRepairs=sum(a!=b for a,b in zip(original,repaired)),originRowsOriginal=original)
 return dict(sourceUrl=cfg['source'],sourceSha256=sha(SOURCE_DIR/(key+'-insider.xlsx')),**evidence,rows=rows)
def read_source(key):return json.loads((SOURCE_DIR/(key+'.json')).read_text())
def classify(key,label):
 fs=configs()[key]['families'];choices=[f for f in fs if label==f[0] or label.startswith(f[0]+' ')]
 if not choices:raise ValueError('Unknown source family '+label)
 f=max(choices,key=lambda x:len(x[0]));return f,label[len(f[0]):].strip() or 'Base'
def build(key,src=None):
 cfg=configs()[key];src=src or read_source(key);rows=src['rows'];groups=OrderedDict();numbers={}
 if len(rows)!=cfg['rows']:raise ValueError('Source row count changed')
 for row in rows:
  f,p=classify(key,row[0]);g=(f[0],row[1],subjects(row[2]));groups.setdefault(g,[]).append((row,p));numbers.setdefault((f[0],row[1]),set()).add(g[2])
 if any(len(v)>1 for v in numbers.values()):raise ValueError('Unreviewed conflicting source identity')
 cards=[];variants=[];counts=Counter();card_for={}
 for (family,number,people),rr in groups.items():
  f=next(f for f in cfg['families'] if f[0]==family);_,code,category,_=f;counts[family]+=1
  canonical=next((r for r,p in rr if p=='Base'),rr[0][0]);names=list(dict.fromkeys(clean(s) for s in canonical[2].split('/')))
  card=dict(id=f"{cfg['prefix']}-{code}-{number}",setId=cfg['id'],order=len(cards)+1,number=number,name=' / '.join(names),subject2=' / '.join(names[1:]) or None,category=category,subset=family,subsetCode=code,roster=canonical[3] or None,rookie='No',parallelGroup=code)
  cards.append(card)
  for r,p in rr:card_for[tuple(r)]=card
 if dict(counts)!={n:c for n,_,_,c in cfg['families']}:raise ValueError('Identity manifest changed '+str(counts))
 seen=set()
 for i,row in enumerate(rows,1):
  card=card_for[tuple(row)];_,parallel=classify(key,row[0]);cap=int(row[4]) if row[4] else None;vid=card['id']+'-'+slug(parallel)
  if vid in seen:raise ValueError('Duplicate source edition '+vid)
  seen.add(vid);variants.append(dict(id=vid,set_id=cfg['id'],card_id=card['id'],variant_order=i,subset=card['subset'],card_number=card['number'],display_name=card['name'],parallel=parallel,serial_cap=cap,serial_exact=('1/1' if cap==1 else f'/{cap}') if cap else None,exclusive_note='First Off the Line' if 'FOTL' in parallel else None,numbering_note='Exact source-listed subject/edition only. Blank sequence remains unknown; no grid or missing base issue inferred.',verification_status='Published checklist rows reconciled to retained independent evidence; see WWE 2023 batch audit'))
 subsets=[dict(category=cat,name=n,code=code,count=count) for n,code,cat,count in cfg['families']]
 record=dict(id=cfg['id'],categoryId='wwe',name=cfg['name'],shortName=cfg['short'],accent=cfg['accent'],year=2023,manufacturer='Panini',releaseDate=cfg['date'],cardCount=len(cards),subsetCount=len(subsets),subsets=subsets)
 return record,cards,variants
def apply(cat,key):
 record,cards,_=build(key);old=[s for s in cat['sets'] if s['id']==record['id']];oc=[c for c in cat['cards'] if c['setId']==record['id']]
 if old or oc:
  if old!=[record] or oc!=cards:raise ValueError('Existing checklist differs; refusing overwrite')
 else:cat['sets'].append(record);cat['cards'].extend(cards);cat['generatedAt']='2026-10-27T00:00:00Z'
 return cat
def tables(key):
 cfg=configs()[key];record,cards,variants=build(key);sid=cfg['id'];source=cfg['source'];out=OrderedDict()
 out['catalogue_sets']=[dict(id=sid,name=record['name'],short_name=record['shortName'],year=2023,manufacturer='Panini',release_date=record['releaseDate'],source_file=source,accent=record['accent'],card_count=len(cards),subset_count=len(record['subsets']),variant_count=len(variants))]
 out['catalogue_subsets']=[dict(set_id=sid,subset_code=s['code'],category=s['category'],name=s['name'],card_count=s['count'],parallel_group=s['code'],source_url=source) for s in record['subsets']]
 out['catalogue_cards']=[dict(id=c['id'],set_id=sid,checklist_order=c['order'],category=c['category'],subset_code=c['subsetCode'],card_number=c['number'],display_name=c['name'],subject_1=c['name'].split(' / ')[0],subject_2=c['subject2'],roster=c['roster'],rookie=False,parallel_group=c['parallelGroup'],image_status='Missing',pricing_status='Unpriced',source_url=source,notes='Source workbook checklist numbering retained; physical card codes may differ. All listed editions reconciled; no absent base versions inferred. '+cfg['note']) for c in cards]
 out['catalogue_variants']=variants;rules=OrderedDict();by_id={c['id']:c for c in cards}
 for v in variants:
  code=by_id[v['card_id']]['subsetCode'];k=(code,v['parallel'],v['serial_cap'])
  if k not in rules:rules[k]=dict(id=sid+'-'+code.lower()+'-'+slug(v['parallel']).lower()+'-'+str(v['serial_cap'] or 'unannounced'),set_id=sid,parallel_group=code,applies_to=v['subset'],parallel=v['parallel'],serial_cap=v['serial_cap'],serial_exact=v['serial_exact'],exclusive_note=v['exclusive_note'],numbering_note='Applies ONLY to exact subject/version rows in catalogue_variants; no subset-wide applicability implied.',verification_status=v['verification_status'])
 out['catalogue_parallel_rules']=list(rules.values());out['catalogue_sources']=[dict(id=sid+'-'+s['id'],set_id=sid,source=s['source'],purpose=s['purpose'],url=s['url'],notes=s['notes']) for s in cfg['sources']]
 return out
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--extract',action='store_true');args=p.parse_args()
 if args.extract:
  for key in configs():
   src=extract(key);(SOURCE_DIR/(key+'.json')).write_text(json.dumps(src,ensure_ascii=False,separators=(',',':'))+'\n');print(key,len(src['rows']),'reconciled source editions')
 else:
  cat=load_catalogue()
  for key in configs():
   apply(cat,key);r,c,v=build(key);print(key,len(c),'identities',len(r['subsets']),'subsets',len(v),'editions')
  save_catalogue(cat)
