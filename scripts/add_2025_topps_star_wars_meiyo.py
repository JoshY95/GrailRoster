#!/usr/bin/env python3
"""Meiyo importer: preserve source designs and resolve centered dual labels geometrically."""
import argparse,hashlib,json,re
from collections import OrderedDict
from pathlib import Path
from catalogue_io import load_catalogue,save_catalogue
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'sources/star-wars-meiyo-2025/checklist.json'
SET_ID='2025-topps-star-wars-meiyo'
CHECKLIST_URL='https://cdn.shopify.com/s/files/1/0662/9749/5709/files/STW2566-2025StarWarsMeiyoChecklist_Hobby.pdf?v=1787940399'
ODDS_URL='https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2025StarWarsMeiyoOdds.pdf?v=1787940399'
PRODUCT_URL='https://www.topps.com/products/2025-topps-star-wars-meiyo-hobby-box'
GUIDE_URL='https://ripped.topps.com/how-to-collect-2025-star-wars-meiyo-product/'
SECTIONS=OrderedDict([
 ('REBEL ALLIANCE BASE',('RA','Base',25)),('GALACTIC EMPIRE BASE',('GE','Base',25)),
 ('THE RESISTANCE BASE',('RS','Base',25)),('FIRST ORDER BASE',('FO','Base',25)),
 ('REBEL HONOR',('RBH','Insert',10)),('IMPERIAL HONOR',('IH','Insert',10)),
 ('RESISTANCE HONOR',('RSH','Insert',10)),('FIRST ORDER HONOR',('FH','Insert',10)),
 ('REBEL HONOR DIECUT VARIATION',('RBD','Variation',10)),('IMPERIAL HONOR DIECUT VARIATION',('IHD','Variation',10)),
 ('RESISTANCE HONOR DIECUT VARIATION',('RSD','Variation',10)),('FIRST ORDER HONOR DIECUT VARIATION',('FHD','Variation',10)),
 ('CHROME STICKERS',('S','Insert',10)),('STAR WARS JAPANESE POSTER VARIANTS',('MP','Insert',10)),
 ('UKIYO E',('UK','Insert',4)),('MEDAL OF YAVIN DIECUT',('Y','Insert',3)),
 ('CHROME AUTOGRAPHS',('AUTO','Autograph',22)),('CHROME DUAL AUTOGRAPHS',('DUAL','Autograph',13)),
 ('REBEL HONOR DIECUT AUTOGRAPH VARIATION',('RBHA','Autograph',6)),('IMPERIAL HONOR DIECUT AUTOGRAPH VARIATION',('IHA','Autograph',5)),
 ('RESISTANCE HONOR DIECUT AUTOGRAPH VARIATION',('RSHA','Autograph',7)),('FIRST ORDER HONOR DIECUT AUTOGRAPH VARIATION',('FHA','Autograph',7)),
])
DUAL='CHROME DUAL AUTOGRAPHS'
BASE_CAPS={'PURPLE FOIL':99,'BLACK FOIL':75,'BLUE FOIL':50,'GREEN FOIL':25,'RED FOIL':10,'FOILFRACTOR':1}

def extract_checklist(path):
 from pypdf import PdfReader
 pdf=PdfReader(path)
 if len(pdf.pages)!=8:raise ValueError('Expected eight pages')
 sections,artists,duals,labels=OrderedDict(),[],[],[]
 section,pending=None,None
 def finish():
  nonlocal pending
  if pending is None:return
  fields=pending.pop('fields');auto=SECTIONS[section][1]=='Autograph'
  if len(fields)!=(2 if auto else 1):raise ValueError(f'Unexpected cells {section} {fields}')
  pending.update(subject=fields[-1],signer=fields[0] if auto else None,sourceFields=fields)
  (duals if section==DUAL else sections[section]).append(pending);pending=None
 for pn,page in enumerate(pdf.pages,1):
  chunks=[]
  def visit(t,cm,tm,f,size):
   if t.strip():chunks.append((t.strip(),float(tm[4]),float(tm[5])))
  page.extract_text(visitor_text=visit)
  for text,x,y in chunks:
   if text.startswith('DA-'):labels.append(dict(number=text,page=pn,y=y));continue
   if x>0 and text in [*SECTIONS,'BASE','INSERT','AUTOGRAPH','SKETCH CARDS','SKETCH ARTISTS']:
    finish()
    if text in SECTIONS:
     if text in sections:raise ValueError('Repeated heading')
     section=text;sections[text]=[]
    else:section='SKETCH ARTISTS' if text=='SKETCH ARTISTS' else None
   elif section=='SKETCH ARTISTS':artists.append(dict(name=text,page=pn))
   elif section==DUAL:
    if x>100:finish();pending=dict(page=pn,y=y,fields=[text])
    elif pending is not None:pending['fields'].append(text)
    else:raise ValueError('Unclassified dual subject')
   elif section in SECTIONS and x>0 and re.fullmatch(r'[A-Z]+-[A-Za-z0-9]+',text):
    finish();pending=dict(number=text,page=pn,fields=[])
   elif pending is not None:pending['fields'].append(text)
   else:raise ValueError('Unclassified text '+text)
 finish();assigned=[]
 for label in sorted(labels,key=lambda x:(x['page'],-x['y'])):
  rows=[r for r in duals if r['page']==label['page'] and abs(r['y']-label['y'])<8]
  if len(rows)!=2 or rows[0]['y']<=label['y'] or rows[1]['y']>=label['y']:raise ValueError('Ambiguous dual geometry')
  for row in rows:assigned.append((row['page'],row['y']));sections[DUAL].append(dict(number=label['number'],**row))
 if len(labels)!=13 or len(duals)!=26 or len(set(assigned))!=26:raise ValueError('Dual coverage mismatch')
 if list(sections)!=list(SECTIONS):raise ValueError('Manifest changed')
 return [dict(name=k,rows=v) for k,v in sections.items()],artists

def normalize(directory):
 import pdfplumber
 subsets,artists=extract_checklist(directory/'checklist.pdf');odds=[]
 with pdfplumber.open(directory/'odds.pdf') as pdf:
  if len(pdf.pages)!=3:raise ValueError('Expected three odds pages')
  for pn,page in enumerate(pdf.pages,1):
   for line in page.extract_text(layout=True).splitlines():
    text=' '.join(line.split())
    if not text or text.startswith('Card 6278'):continue
    m=re.fullmatch(r'(.+?)\s+(\d[\d,]*:\d[\d,]*|-)\s+(\d[\d,]*:\d[\d,]*|-)',text)
    if not m:raise ValueError('Unparsed odds '+text)
    odds.append(dict(label=m[1],hobby=m[2],celebration=m[3],page=pn,rawLine=text))
 if len(odds)!=99:raise ValueError(f'Unexpected odds count {len(odds)}')
 return dict(checklistUrl=CHECKLIST_URL,oddsUrl=ODDS_URL,productUrl=PRODUCT_URL,guideUrl=GUIDE_URL,
  checklistSha256=hashlib.sha256((directory/'checklist.pdf').read_bytes()).hexdigest(),oddsSha256=hashlib.sha256((directory/'odds.pdf').read_bytes()).hexdigest(),
  subsets=subsets,sketchArtists=artists,odds=odds,baseParallelCaps=BASE_CAPS,
  deferred=[dict(name='MANGA MADNESS',reason='Celebration-exclusive programme verified in official odds/guide; no manufacturer or distributor card-by-card checklist located. No card IDs, subjects or caps inferred.')])

def build(source=None):
 source=source or json.loads(SOURCE.read_text())
 if [x['name'] for x in source['subsets']]!=list(SECTIONS):raise ValueError('Manifest mismatch')
 cards,variants,subsets=[],[],[]
 for sec in source['subsets']:
  name=sec['name'];code,category,count=SECTIONS[name];identities=OrderedDict()
  for row in sec['rows']:identities.setdefault(row['number'],[]).append(row)
  if len(identities)!=count:raise ValueError('Count mismatch '+name)
  if category!='Autograph' and set(identities)!={f'{code}-{i}' for i in range(1,count+1)}:raise ValueError('Number mismatch')
  for number,rows in identities.items():
   if len(rows)!=(2 if code=='DUAL' else 1) or len({(r['signer'],r['subject']) for r in rows})!=len(rows):raise ValueError('Repeated or missing subject')
   names=[f"{r['subject']} ({r['signer']})" if r['signer'] else r['subject'] for r in rows]
   c=dict(id=f'2025-TSWM-{code}-{number}',setId=SET_ID,order=len(cards)+1,number=number,name=' / '.join(names),subject2=' / '.join(names[1:]) or None,
    category=category,subset=name,subsetCode=code,roster={'RA':'Rebel Alliance','GE':'Galactic Empire','RS':'The Resistance','FO':'First Order'}.get(code),rookie='No',parallelGroup=code)
   cards.append(c);variants.append(dict(id=c['id']+'-IDENTITY',set_id=SET_ID,card_id=c['id'],variant_order=len(variants)+1,subset=name,card_number=number,
    display_name=c['name'],parallel='Checklist identity',serial_cap=None,serial_exact=None,exclusive_note='Hobby/online exclusive insert.' if code=='UK' else None,
    numbering_note='Official checklist identity; no card-specific parallel grid or cap inferred.',verification_status='Official Topps checklist verified'))
  subsets.append(dict(category=category,name=name,code=code,count=count))
 record=dict(id=SET_ID,categoryId='star-wars',name='2025 Topps Star Wars Meiyo',shortName='Star Wars Meiyo 2025',accent='#d76162',year=2025,manufacturer='Topps',releaseDate='2025-05-04',cardCount=len(cards),subsetCount=len(subsets),subsets=subsets)
 return record,cards,variants

def apply(catalogue,record,cards):
 old_sets=[s for s in catalogue['sets'] if s['id']==SET_ID];old_cards=[c for c in catalogue['cards'] if c['setId']==SET_ID]
 if old_sets or old_cards:
  if old_sets!=[record] or old_cards!=cards:raise ValueError('Existing Meiyo identities differ; refusing overwrite')
  return catalogue
 catalogue['sets'].append(record);catalogue['cards'].extend(cards);catalogue['generatedAt']='2026-10-26T00:00:00Z';return catalogue

def tables():
 source=json.loads(SOURCE.read_text());r,c,v=build(source);d=OrderedDict()
 d['catalogue_sets']=[dict(id=SET_ID,name=r['name'],short_name=r['shortName'],year=2025,manufacturer='Topps',release_date=r['releaseDate'],source_file=CHECKLIST_URL,accent=r['accent'],card_count=len(c),subset_count=len(r['subsets']),variant_count=len(v))]
 d['catalogue_subsets']=[dict(set_id=SET_ID,subset_code=s['code'],category=s['category'],name=s['name'],card_count=s['count'],parallel_group=s['code'],source_url=CHECKLIST_URL) for s in r['subsets']]
 d['catalogue_cards']=[dict(id=x['id'],set_id=SET_ID,checklist_order=x['order'],category=x['category'],subset_code=x['subsetCode'],card_number=x['number'],display_name=x['name'],subject_1=x['name'].split(' / ')[0],subject_2=x['subject2'],roster=x['roster'],rookie=False,parallel_group=x['parallelGroup'],image_status='Missing',pricing_status='Unpriced',source_url=CHECKLIST_URL,
  notes='Official spelling, numbers and signers retained. Centered dual labels mapped by PDF geometry; two signers form one card. No card-specific parallel grid inferred.'+(' Ukiyo E Hobby/online exclusive; Celebration odds show a dash.' if x['subsetCode']=='UK' else '')) for x in c]
 d['catalogue_variants']=v
 aliases={n.replace('DIECUT','DIE CUT'):n for n in SECTIONS};aliases.update({n+' CARDS':n for n in list(SECTIONS)[:4]})
 aliases.update({'JAPANESE POSTER CARD VARIANT':'STAR WARS JAPANESE POSTER VARIANTS','UKIYO-E':'UKIYO E','MEDAL OF YAVIN DIE CUT':'MEDAL OF YAVIN DIECUT'})
 rules=[]
 for i,row in enumerate(source['odds'],1):
  if row['label'].startswith(('MANGA MADNESS','SKETCH CARDS')):continue
  alias=next((a for a in sorted(aliases,key=len,reverse=True) if row['label']==a or row['label'].startswith(a+' ')),None)
  if alias is None:raise ValueError('Unmapped odds '+row['label'])
  section=aliases[alias];code=SECTIONS[section][0];parallel=row['label'][len(alias):].strip() or 'Base issue';cap=BASE_CAPS.get(parallel) if code in ('RA','GE','RS','FO') else None
  rules.append(dict(id=f'{SET_ID}-ODDS-{i:03d}',set_id=SET_ID,parallel_group=code,applies_to=section,parallel=parallel,serial_cap=cap,serial_exact=None,
   exclusive_note=f"Hobby distributor: {row['hobby']}; Celebration: {row['celebration']}. Dash means absent in that source format.",
   numbering_note=f"Official odds page {row['page']}; label {row['label']}. "+('Base cap explicitly confirmed by Topps collector guide. ' if cap else '')+'No card-specific applicability grid inferred.',verification_status='Official Topps odds/guide; subset rule only'))
 d['catalogue_parallel_rules']=rules
 d['catalogue_sources']=[dict(id=SET_ID+'-'+key,set_id=SET_ID,source='Topps',purpose=purpose,url=url,notes=notes) for key,purpose,url,notes in [
  ('checklist','Checklist',CHECKLIST_URL,'Eight-page Hobby checklist: 280 signer/subject rows form 267 designs /22 subsets; 13 centered dual labels. 25 sketch artists remain a roster. Manga Madness identities deferred.'),
  ('odds','Parallel applicability',ODDS_URL,'99 two-format odds rows; 91 subset rules. Four Manga Madness and four sketch rates source-only; format dashes and BLACK RREFRACTOR spelling retained.'),
  ('product','Release date and identity',PRODUCT_URL,'Available From May 4, 2025, used for general-public/Hobby release sorting. Earlier Celebration availability is noted without guessing an exact day.'),
  ('guide','Base serial caps and exclusives',GUIDE_URL,'Base Purple /99, Black /75, Blue /50, Green /25, Red /10, Foilfractor 1/1 explicitly confirmed. Manga Madness Celebration-only; Ukiyo E Hobby/online-only. Caps are subset rules only, no autograph caps or per-card grid assumed.')]]
 return d

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--extract',type=Path);p.add_argument('--verify-pdf',type=Path);a=p.parse_args()
 if a.extract:
  s=normalize(a.extract);SOURCE.parent.mkdir(parents=True,exist_ok=True);SOURCE.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(rows=sum(len(x['rows']) for x in s['subsets']),artists=len(s['sketchArtists']),odds=len(s['odds']))))
 else:
  if a.verify_pdf and normalize(a.verify_pdf)!=json.loads(SOURCE.read_text()):raise ValueError('PDF mismatch')
  r,c,v=build();save_catalogue(apply(load_catalogue(),r,c));print(json.dumps(dict(cards=len(c),subsets=len(r['subsets']),rules=len(tables()['catalogue_parallel_rules']))))
