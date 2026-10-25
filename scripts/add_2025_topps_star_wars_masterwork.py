#!/usr/bin/env python3
"""Masterwork's numbered designs; preserve relic metadata and multi-signer identity."""
import argparse
import hashlib
import json
import re
from collections import OrderedDict
from pathlib import Path
from catalogue_io import load_catalogue,save_catalogue

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'sources/masterwork-star-wars-2025/checklist.json'
SET_ID='2025-topps-star-wars-masterwork'
CHECKLIST_URL='https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2025_Star_Wars_Masterwork_Checklist.pdf?v=1777400855'
ODDS_URL='https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2025_Star_Wars_Masterwork_Odds.pdf?v=1777320886'
PRODUCT_URL='https://www.topps.com/products/2025-star-wars-masterwork-hobby-box'
OVERVIEW_URL='https://www.topps.com/pages/topps-masterwork-star-wars'
SECTIONS=OrderedDict([
 ('CHARACTERS',('BASE','Base')),
 ('UNDER DISGUISE',('UN','Insert')),
 ('FALL OF THE CHOSEN ONE',('FALL','Insert')),
 ('GALACTIC DIE CUT PODS',('GPOD','Insert')),
 ('SHORT CIRCUIT',('SHOC','Insert')),
 ('BB-8',('BB8','Insert')),
 ('LOTHAL JEDI TEMPLE MORTIS GODS PAINTING PUZZLE',('MORTIS','Insert')),
 ('2025 MASTERWORKS ON CARD AUTOGRAPHS',('AUTO','Autograph')),
 ('DUO AUTOGRAPHS',('DUO','Autograph')),
 ('TRIO AUTOGRAPHS',('TRIO','Autograph')),
 ('QUAD AUTOGRAPHS',('QUAD','Autograph')),
 ('ULTIMATE BOOK CARD AUTOGRAPHS',('UBC','Autograph')),
 ('SKELETON CREW RELIC',('SCR','Relic')),
 ('RELIC CARDS',('REL','Relic')),
 ('ROTJ FILM CEL',('ROC','Relic')),
 ('SKELETON CREW AUTOGRAPH RELIC',('SCAR','Autograph Relic')),
 ('AUTOGRAPH RELIC CARDS',('ARC','Autograph Relic')),
 ('ROTJ FILM CEL AUTOGRAPH RELIC',('RAR','Autograph Relic')),
 ('PEN AUTOGRAPH RELIC',('PEN','Autograph Relic')),
])
PROGRAMMES=['10 YEARS OF MASTERWORKS BUYBACKS','HARRISON FORD BUYBACK ON CARD AUTOS','SKETCH ARTISTS']
EXPECTED_COUNTS=[100,26,24,24,26,10,9,96,10,5,5,4,10,12,91,9,11,32,85]
MULTIPLICITY={('UBC',n):10 for n in ['UBC-456','UBC-MAN','UBC-REV','UBC-SKY']}


def extract_checklist(path):
 from pypdf import PdfReader
 pdf=PdfReader(path)
 if len(pdf.pages)!=18:raise ValueError('Expected 18 checklist pages')
 sections,artists,programmes,section,pending=OrderedDict(),[],[],None,None
 def finish():
  nonlocal pending
  if pending is None:return
  fields=pending.pop('fields');category=SECTIONS[section][1]
  autograph=category.startswith('Autograph')
  minimum=2 if autograph else 1
  if len(fields)<minimum:raise ValueError('Incomplete source row')
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
   # Header BB-8 must not be confused with a character's BB-8 body cell.
   if 'Bold' in font and text in [*SECTIONS,*PROGRAMMES,'BASE','INSERTS','AUTOGRAPHS']:
    finish()
    if text in SECTIONS:
     if text in sections:raise ValueError('Repeated section heading')
     section=text;sections[text]=[]
    elif text in PROGRAMMES:
     section=text;programmes.append(dict(name=text,page=page_number))
    continue
   if section=='SKETCH ARTISTS':artists.append(dict(name=text,page=page_number));continue
   if section not in SECTIONS:raise ValueError(f'Unexpected text in unenumerated section: {text}')
   if 0<x<150 and re.fullmatch(r'[0-9]+|[A-Z0-9]+-[A-Z0-9-]+',text):
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
    if page_number==6 and label=='Lothal Jedi Tem':
     # The manufacturer clips the label; the visible rate is 1:160.
     label='Lothal Jedi Temple Mortis Gods Painting Puzzle';rate='1:160'
    valid=bool(re.fullmatch(r'\d[\d,]*:\d[\d,]*',rate))
    if not valid and not re.fullmatch(r'\d[\d,]*',rate):raise ValueError(f'Unparsed odds row: {raw}')
    odds.append(dict(label=label,hobby=rate,page=page_number,rawCells=raw,validRate=valid))
 return dict(checklistUrl=CHECKLIST_URL,oddsUrl=ODDS_URL,productUrl=PRODUCT_URL,overviewUrl=OVERVIEW_URL,
  checklistSha256=hashlib.sha256((directory/'checklist.pdf').read_bytes()).hexdigest(),
  oddsSha256=hashlib.sha256((directory/'odds.pdf').read_bytes()).hexdigest(),
  subsets=subsets,sketchArtists=artists,unenumeratedProgrammes=programmes,odds=odds,
  filmCelNumbering=dict(subset='ROTJ FILM CEL',serialCap=1,sourceUrl=OVERVIEW_URL,
   scope='Official release overview explicitly describes the non-autograph ROTJ film cel relic cards as all 1/1. Do not extend this assertion to unenumerated frames or autograph relic editions.'))


def build(source=None):
 source=source or json.loads(SOURCE.read_text())
 if [s['name'] for s in source['subsets']]!=list(SECTIONS) or len(EXPECTED_COUNTS)!=len(SECTIONS):
  raise ValueError('Unexpected section manifest')
 cards,variants,subsets=[],[],[]
 for section,expected_count in zip(source['subsets'],EXPECTED_COUNTS):
  name=section['name'];code,category=SECTIONS[name];identities=OrderedDict()
  for row in section['rows']:identities.setdefault(row['number'],[]).append(row)
  if len(identities)!=expected_count:raise ValueError('Unexpected count: '+name)
  if code=='BASE' and set(identities)!=set(map(str,range(1,101))):raise ValueError('Incomplete base set')
  for number,rows in identities.items():
   expected=MULTIPLICITY.get((code,number),{'DUO':2,'TRIO':3,'QUAD':4}.get(code,1))
   if len(rows)!=expected or len({(r['subject'],r['signer']) for r in rows})!=expected:
    raise ValueError(f'Unexpected repeated identity: {name} {number}')
   names=[f"{r['subject']} ({r['signer']})" if r['signer'] and r['signer']!=r['subject'] else r['subject'] for r in rows]
   card=dict(id=f'2025-TSWMW-{code}-{number}',setId=SET_ID,order=len(cards)+1,number=number,
    name=' / '.join(names),subject2=' / '.join(names[1:]) or None,category=category,subset=name,subsetCode=code,
    roster=None,rookie='No',parallelGroup=code)
   cards.append(card)
   variants.append(dict(id=card['id']+'-IDENTITY',set_id=SET_ID,card_id=card['id'],variant_order=len(variants)+1,
    subset=name,card_number=number,display_name=card['name'],parallel='Checklist identity',serial_cap=None,
    serial_exact=None,exclusive_note=None,numbering_note='Official numbered design; no parallel grid or serial cap inferred.',
    verification_status='Official Topps checklist verified'))
  subsets.append(dict(category=category,name=name,code=code,count=len(identities)))
 if source.get('filmCelNumbering',{}).get('serialCap')!=1 or source['filmCelNumbering'].get('sourceUrl')!=OVERVIEW_URL:
  raise ValueError('Missing official film-cel numbering evidence')
 for c in cards:
  if c['subsetCode']=='ROC':
   variants.append(dict(id=c['id']+'-FILM-CEL-1-OF-1',set_id=SET_ID,card_id=c['id'],variant_order=len(variants)+1,
    subset=c['subset'],card_number=c['number'],display_name=c['name'],parallel='Film cel relic',serial_cap=1,
    serial_exact='1/1',exclusive_note=None,
    numbering_note='Official Topps release overview explicitly states all non-autograph ROTJ film cel relic cards are 1/1. This is the numbered design, not an invented frame checklist.',
    verification_status='Official Topps release overview verified'))
 record=dict(id=SET_ID,categoryId='star-wars',name='2025 Topps Star Wars Masterwork',shortName='Star Wars Masterwork',
  accent='#d3b56a',year=2025,manufacturer='Topps',releaseDate='2026-06-03',cardCount=len(cards),subsetCount=len(subsets),subsets=subsets)
 return record,cards,variants


def apply(catalogue,record,cards):
 old_sets=[s for s in catalogue['sets'] if s['id']==SET_ID];old_cards=[c for c in catalogue['cards'] if c['setId']==SET_ID]
 if old_sets or old_cards:
  if old_sets!=[record] or old_cards!=cards:raise ValueError('Existing Masterwork identities differ; refusing overwrite')
  return catalogue
 catalogue['sets'].append(record);catalogue['cards'].extend(cards);catalogue['generatedAt']='2026-10-25T16:00:00Z'
 return catalogue


def tables():
 source=json.loads(SOURCE.read_text());record,cards,variants=build(source)
 evidence={(SECTIONS[s['name']][0],r['number']):r for s in source['subsets'] for r in s['rows']}
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
  notes='Official manufacturer spelling and numbers retained. '+
  (f"Relic material/source: {evidence[(c['subsetCode'],c['number'])]['material']}. " if evidence[(c['subsetCode'],c['number'])]['material'] else '')+
  'Repeated signer rows combine by printed number; matching numbers across subsets remain distinct. Film-cel subjects are not expanded into unenumerated frame identities.') for c in cards]
 result['catalogue_variants']=variants
 aliases={name.title():name for name in SECTIONS}
 aliases.update({'Base Cards':'CHARACTERS','ROTJ Film Cell Relic':'ROTJ FILM CEL',
  'Ultimate Book Card Autos':'ULTIMATE BOOK CARD AUTOGRAPHS','Skeleton Crew Auto Relic':'SKELETON CREW AUTOGRAPH RELIC',
  'ROTJ Film Cell Auto Relic':'ROTJ FILM CEL AUTOGRAPH RELIC'})
 rules=[]
 for i,row in enumerate(source['odds'],1):
  label=row['label']
  if label in ['10 Years of Masterworks Buybacks','Harrison Ford Buyback On Card Autos'] or label.startswith('Sketch Cards'):continue
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
  for key,purpose,url,notes in [('checklist','Checklist',CHECKLIST_URL,'18-page manufacturer PDF. Numbered relic/design identities retained. No invented buyback or sketch checklist.'),
   ('odds','Parallel applicability',ODDS_URL,'14-page table. Clipped Mortis-puzzle row reconciled to the checklist; visible pack rate 1:160.'),
   ('product','Release and product year',PRODUCT_URL,'2025 product title; released June 3, 2026. Generic Product Year metadata says 2026; title year retained.'),
   ('overview','Film-cel numbering and product scope',OVERVIEW_URL,'Manufacturer explicitly describes non-autograph ROTJ film cels as all 1/1. 91 numbered design editions verified; no autograph-relic caps or unenumerated frames inferred.')]]
 return result


if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--extract',type=Path);parser.add_argument('--verify-pdf',type=Path);args=parser.parse_args()
 if args.extract:
  s=normalize(args.extract);SOURCE.parent.mkdir(parents=True,exist_ok=True);SOURCE.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
  print(json.dumps(dict(rows=sum(len(x['rows']) for x in s['subsets']),artists=len(s['sketchArtists']),odds=len(s['odds']),
   counts={x['name']:len({r['number'] for r in x['rows']}) for x in s['subsets']},
   books={r['number']:sum(z['number']==r['number'] for z in x['rows']) for x in s['subsets'] if x['name']=='ULTIMATE BOOK CARD AUTOGRAPHS' for r in x['rows']})))
 else:
  if args.verify_pdf and normalize(args.verify_pdf)!=json.loads(SOURCE.read_text()):raise ValueError('Manufacturer evidence changed')
  record,cards,_=build();save_catalogue(apply(load_catalogue(),record,cards));print(json.dumps(dict(cards=len(cards),subsets=len(record['subsets']),rules=len(tables()['catalogue_parallel_rules']))))
