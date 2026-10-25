#!/usr/bin/env python3
"""Smugglers Outpost's numbered designs; preserve brand boundaries and multi-signer identity."""
import argparse
import hashlib
import json
import re
from collections import OrderedDict
from pathlib import Path
from catalogue_io import load_catalogue,save_catalogue

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'sources/smugglers-outpost-star-wars-2025/checklist.json'
SET_ID='2025-topps-star-wars-smugglers-outpost'
CHECKLIST_URL='https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2025_Star_Wars_Smugglers_Outpost_Checklist.pdf?v=1787961928'
ODDS_URL='https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2025_Star_Wars_Smugglers_Outpost_Odds.pdf?v=1787961928'
PRODUCT_URL='https://www.topps.com/products/2025-topps-star-wars-smugglers-outpost-hobby-box'
SECTIONS=OrderedDict([('Finest Base Set', ('F', 'Base')), ('Chrome Black Base Set', ('CB', 'Base')), ('Galactic Antiquities Base Set', ('GA', 'Base')), ('20th Anniversary of Revenge of the Sith', ('ROTS', 'Insert')), ('Power of the Force', ('POF', 'Insert')), ('Finest Jedi Knights', ('FJK', 'Insert')), ('Stellar Signatures Art Reproduction', ('SAS', 'Insert')), ('Galactic Funk', ('GF', 'Insert')), ('Cortosis Metal', ('CM', 'Insert')), ('Droid Shadowbox', ('DS', 'Insert')), ('Lightsaber Shadowbox', ('LS', 'Insert')), ('Civilized Age Art', ('CAA', 'Insert')), ('Chrome Black Autograph', ('CBA', 'Autograph')), ('Finest Autograph', ('FA', 'Autograph')), ('Stellar Signatures Autograph', ('SSA', 'Autograph')), ('Cortosis Metal Autograph', ('CMA', 'Autograph')), ('Trio Autograph', ('TA', 'Autograph')), ('Quad Autograph', ('QA', 'Autograph')), ('Light Side Ultimate Autograph Book Card', ('LSU', 'Autograph')), ('Dark Side Ultimate Autograph Book Card', ('DSU', 'Autograph')), ('Sketchagraphs', ('SCA', 'Autograph')), ('Stellar Signatures Art Cards', ('SA', 'Sketch')), ('Triptych Sketch Cards', ('TSC', 'Sketch'))])
PROGRAMMES=['Sketch Artist List']
EXPECTED_COUNTS=[75,75,50,25,25,25,100,15,20,20,20,10,51,49,54,11,8,7,1,1,39,100,25]


def extract_checklist(path):
 from pypdf import PdfReader
 pdf=PdfReader(path)
 if len(pdf.pages)!=29:raise ValueError('Expected 29 checklist pages')
 sections,artists,programmes,section,pending=OrderedDict(),[],[],None,None
 def finish():
  nonlocal pending
  if pending is None:return
  fields=pending.pop('fields');category=SECTIONS[section][1]
  autograph=category.startswith('Autograph')
  minimum=2 if autograph else 1
  if len(fields)!=minimum:raise ValueError('Unexpected source field count')
  pending.update(subject=fields[1] if autograph else fields[0],signer=fields[0] if autograph else None,
                 material=' '.join(fields[minimum:]) or None,sourceFields=fields)
  sections[section].append(pending);pending=None
 for page_number,page in enumerate(pdf.pages,1):
  chunks=[]
  def visit(text,cm,tm,font,size):
   if text.strip():chunks.append((text.strip(),float(tm[4]),str((font or {}).get('/BaseFont',''))))
  page.extract_text(visitor_text=visit)
  for text,x,font in chunks:
   if text.startswith(('Checklists provided by Topps','actual contents and odds may vary.')):continue
   # Only styled headings change sections; body cells can contain heading-like text.
   if 'Bold' in font and text in [*SECTIONS,*PROGRAMMES,'BASE','INSERT','AUTOGRAPH','SKETCH CARDS']:
    finish()
    if text in SECTIONS:
     if text in sections:raise ValueError('Repeated section heading')
     section=text;sections[text]=[]
    elif text in PROGRAMMES:
     section=text;programmes.append(dict(name=text,page=page_number))
    continue
   if section=='Sketch Artist List':
    if x>100 and artists:artists[-1]['name']+=' '+text
    else:artists.append(dict(name=text,page=page_number))
    continue
   if section not in SECTIONS:raise ValueError(f'Unexpected text in unenumerated section: {text}')
   if 0<x<150 and re.fullmatch(r'[0-9]+|[A-Z0-9]+-[A-Za-z0-9-]+',text):
    finish();pending=dict(number=text,page=page_number,fields=[])
   elif pending is not None:pending['fields'].append(text)
   else:raise ValueError(f'Unclassified page {page_number}: {text}')
 finish()
 if list(sections)!=list(SECTIONS):raise ValueError('Unexpected checklist sections')
 return [dict(name=k,rows=v) for k,v in sections.items()],artists,programmes


def normalize(directory):
 import pdfplumber
 subsets,artists,programmes=extract_checklist(directory/'checklist.pdf');odds=[]
 with pdfplumber.open(directory/'odds.pdf') as pdf:
  for page_number,page in enumerate(pdf.pages,1):
   tables=page.extract_tables()
   if len(tables)!=1:raise ValueError('Expected one odds table per page')
   for raw in tables[0][1:]:
    label,rate=[' '.join((cell or '').split()) for cell in raw]
    valid=bool(re.fullmatch(r'\d[\d,]*:\d[\d,]*',rate))
    if not valid and not re.fullmatch(r'\d[\d,]*',rate):raise ValueError(f'Unparsed odds row: {raw}')
    odds.append(dict(label=label,hobby=rate,page=page_number,rawCells=raw,validRate=valid))
 return dict(checklistUrl=CHECKLIST_URL,oddsUrl=ODDS_URL,productUrl=PRODUCT_URL,
  checklistSha256=hashlib.sha256((directory/'checklist.pdf').read_bytes()).hexdigest(),
  oddsSha256=hashlib.sha256((directory/'odds.pdf').read_bytes()).hexdigest(),
  subsets=subsets,sketchArtists=artists,unenumeratedProgrammes=programmes,odds=odds)


def build(source=None):
 source=source or json.loads(SOURCE.read_text())
 if [s['name'] for s in source['subsets']]!=list(SECTIONS) or len(EXPECTED_COUNTS)!=len(SECTIONS):
  raise ValueError('Unexpected section manifest')
 cards,variants,subsets=[],[],[]
 for section,expected_count in zip(source['subsets'],EXPECTED_COUNTS):
  name=section['name'];code,category=SECTIONS[name];identities=OrderedDict()
  for row in section['rows']:
   key=row['number']
   if code=='ROTS' and key=='ARS-25':
    if row['subject'] not in ['Jar Jar Binks','Darth Vader']:raise ValueError('Unreviewed duplicate printed number')
    key+='-'+row['subject'].upper().replace(' ','-')
   identities.setdefault(key,[]).append(row)
  if code=='ROTS' and [r['number'] for r in section['rows']]!=[f'ARS-{i}' for i in [*range(1,23),24,25,25]]:raise ValueError('Manufacturer numbering discrepancy changed')
  if len(identities)!=expected_count:raise ValueError('Unexpected count: '+name)
  if code in ['F','CB','GA'] and set(identities)!={f'{code}-{i}' for i in range(1,expected_count+1)}:raise ValueError('Incomplete base programme')
  for identity_key,rows in identities.items():
   number=rows[0]['number']
   expected={'TA':3,'QA':4,'LSU':20,'DSU':20}.get(code,1)
   if len(rows)!=expected or len({(r['subject'],r['signer']) for r in rows})!=expected:
    raise ValueError(f'Unexpected repeated identity: {name} {number}')
   names=[f"{r['subject']} ({r['signer']})" if r['signer'] and r['signer']!=r['subject'] else r['subject'] for r in rows]
   card=dict(id=f'2025-TSWSO-{code}-{identity_key}',setId=SET_ID,order=len(cards)+1,number=number,
    name=' / '.join(names),subject2=' / '.join(names[1:]) or None,category=category,subset=name,subsetCode=code,
    roster=None,rookie='No',parallelGroup=code)
   cards.append(card)
   variants.append(dict(id=card['id']+'-IDENTITY',set_id=SET_ID,card_id=card['id'],variant_order=len(variants)+1,
    subset=name,card_number=number,display_name=card['name'],parallel='Checklist identity',serial_cap=None,
    serial_exact=None,exclusive_note=None,numbering_note='Official numbered design; no parallel grid or serial cap inferred.',
    verification_status='Official Topps checklist verified'))
  subsets.append(dict(category=category,name=name,code=code,count=len(identities)))
 record=dict(id=SET_ID,categoryId='star-wars',name='2025 Topps Star Wars Smugglers Outpost',shortName='Smugglers Outpost',
  accent='#d3b56a',year=2025,manufacturer='Topps',releaseDate='2026-03-18',cardCount=len(cards),subsetCount=len(subsets),subsets=subsets)
 return record,cards,variants


def apply(catalogue,record,cards):
 old_sets=[s for s in catalogue['sets'] if s['id']==SET_ID];old_cards=[c for c in catalogue['cards'] if c['setId']==SET_ID]
 if old_sets or old_cards:
  if old_sets!=[record] or old_cards!=cards:raise ValueError('Existing Smugglers Outpost identities differ; refusing overwrite')
  return catalogue
 catalogue['sets'].append(record);catalogue['cards'].extend(cards);catalogue['generatedAt']='2026-10-25T23:00:00Z'
 return catalogue


def tables():
 source=json.loads(SOURCE.read_text());record,cards,variants=build(source)
 result=OrderedDict()
 result['catalogue_sets']=[dict(id=SET_ID,name=record['name'],short_name=record['shortName'],year=2025,
  manufacturer='Topps',release_date=record['releaseDate'],source_file=CHECKLIST_URL,accent=record['accent'],
  card_count=len(cards),subset_count=len(record['subsets']),variant_count=len(variants))]
 result['catalogue_subsets']=[dict(set_id=SET_ID,subset_code=s['code'],category=s['category'],name=s['name'],
  card_count=s['count'],parallel_group=s['code'],source_url=CHECKLIST_URL) for s in record['subsets']]
 result['catalogue_cards']=[dict(id=c['id'],set_id=SET_ID,checklist_order=c['order'],category=c['category'],
  subset_code=c['subsetCode'],card_number=c['number'],display_name=c['name'],subject_1=c['name'].split(' / ')[0],
  subject_2=c['subject2'],roster=None,rookie=False,parallel_group=c['parallelGroup'],image_status='Missing',
  pricing_status='Unpriced',source_url=CHECKLIST_URL,
  notes=('Topps PDF prints ARS-25 for both Jar Jar Binks and Darth Vader, with no ARS-23. Source number retained; subject suffix distinguishes IDs pending physical-card verification. ' if c['subsetCode']=='ROTS' and c['number']=='ARS-25' else '')+'Official manufacturer spelling and printed numbers retained. Multi-signer rows combine by subset and number. Numbered sketch subjects are design identities, not invented unique artist/frame IDs.') for c in cards]
 result['catalogue_variants']=variants
 aliases={name:name for name in SECTIONS}
 aliases.update({'Stellar Art Reproduction':'Stellar Signatures Art Reproduction','Sketchagraph':'Sketchagraphs','Stellar Signatures Sketch Card':'Stellar Signatures Art Cards','Triptych Sketch Card':'Triptych Sketch Cards'})
 rules=[]
 for i,row in enumerate(source['odds'],1):
  label=row['label']
  if label in ['Sketch Card','Sketch Card Gold Foil','Sketch Card Black Foil']:continue
  alias=next((a for a in sorted(aliases,key=len,reverse=True) if label.lower()==a.lower() or label.lower().startswith(a.lower()+' ')),None)
  if alias is None:raise ValueError('Unmapped odds label: '+label)
  name=aliases[alias]
  rules.append(dict(id=f'{SET_ID}-ODDS-{i:03d}',set_id=SET_ID,parallel_group=SECTIONS[name][0],applies_to=name,
   parallel=label[len(alias):].strip() or 'Base issue',serial_cap=None,serial_exact=None,
   exclusive_note=f"Hobby pack odds {row['hobby']}." if row['validRate'] else f"Manufacturer printed rate {row['hobby']} without a colon; unresolved and not interpreted.",
   numbering_note=f"Official odds PDF page {row['page']}; subset rule only. Pack odds do not establish serial caps or guarantee every subject in every parallel.",
   verification_status='Official Topps odds; subset rule only' if row['validRate'] else 'Official Topps subset label; pack rate unresolved'))
 result['catalogue_parallel_rules']=rules
 result['catalogue_sources']=[dict(id=SET_ID+'-'+key,set_id=SET_ID,source='Topps',purpose=purpose,url=url,notes=notes)
  for key,purpose,url,notes in [('checklist','Checklist',CHECKLIST_URL,'29-page manufacturer PDF. Numbered sketch designs retained; artist roster does not create additional identities.'),
   ('odds','Parallel applicability',ODDS_URL,'7-page manufacturer odds. Subset rules only; no inferred serial caps or card-specific applicability.'),
   ('product','Release and product scope',PRODUCT_URL,'2025 title; manufacturer Available From March 18, 2026. Generic product-year metadata 2026; title year retained.')]]

 return result


if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--extract',type=Path);parser.add_argument('--verify-pdf',type=Path);args=parser.parse_args()
 if args.extract:
  s=normalize(args.extract);SOURCE.parent.mkdir(parents=True,exist_ok=True);SOURCE.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
  print(json.dumps(dict(rows=sum(len(x['rows']) for x in s['subsets']),artists=len(s['sketchArtists']),odds=len(s['odds']),
   counts={x['name']:len({r['number'] for r in x['rows']}) for x in s['subsets']},
   programmes=s['unenumeratedProgrammes'])))
 else:
  if args.verify_pdf and normalize(args.verify_pdf)!=json.loads(SOURCE.read_text()):raise ValueError('Manufacturer evidence changed')
  record,cards,_=build();save_catalogue(apply(load_catalogue(),record,cards));print(json.dumps(dict(cards=len(cards),subsets=len(record['subsets']),rules=len(tables()['catalogue_parallel_rules']))))
