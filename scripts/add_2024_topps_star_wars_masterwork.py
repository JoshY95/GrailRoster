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
SOURCE=ROOT/'sources/masterwork-star-wars-2024/checklist.json'
SET_ID='2024-topps-star-wars-masterwork'
CHECKLIST_URL='https://cdn.shopify.com/s/files/1/0739/2015/1805/files/STW2456-2024StarWarsMasterworkChecklistv2.pdf?v=1787909664'
ODDS_URL='https://cdn.shopify.com/s/files/1/0739/2015/1805/files/2024StarWarsMasterworkOdds.pdf?v=1787909664'
PRODUCT_URL='https://uk.topps.com/products/2024-topps%C2%AE-masterwork-star-wars-master-box'
SECTIONS=OrderedDict([
 ('BASE CARDS',('BASE','Base')),('BEHIND THE NEW SCENES',('BTS','Insert')),
 ('JOURNEY OF AHSOKA TANO',('JA','Insert')),('THE GRAND ADMIRAL',('HG','Insert')),
 ('MARVEL COMIC COVERS',('MC','Insert')),('FORCE SPIRITS',('FS','Insert')),
 ('ARTOO-DETOO',('AR','Insert')),('SEE-THREEPIO',('CP','Insert')),
 ('ON CARD AUTOGRAPHS',('AUTO','Autograph')),('DUAL AUTOGRAPHS',('DUO','Autograph')),
 ('TRIPLE AUTOGRAPHS',('TRIO','Autograph')),('QUAD AUTOGRAPH BOOK CARD',('QUAD','Autograph')),
 ('PEN AUTOGRAPH RELICS',('PEN','Autograph Relic')),
 ('STORMTROOPER ARMOR AUTOGRAPH VARIATION',('SA','Autograph Relic')),
 ('STORMTROOPER ARMOR',('S','Relic')),('RISE OF THE RESISTANCE RELICS',('RR','Relic')),
])
EXPECTED_COUNTS=[100,23,20,20,33,6,10,10,50,9,4,3,31,2,8,8]
MULTIPLICITY={}


def extract_checklist(path):
 from pypdf import PdfReader
 pdf=PdfReader(path)
 if len(pdf.pages)!=17:raise ValueError('Expected 17 checklist pages')
 sections,artists,multi,labels=OrderedDict(),[],{},[]
 artifacts,blank_pages=[],[]
 section,pending=None,None
 def finish():
  nonlocal pending
  if pending is None:return
  fields=pending.pop('fields');category=SECTIONS[section][1];auto=category.startswith('Autograph')
  minimum=2 if auto else 1
  if len(fields)<minimum or len(fields)>2:raise ValueError(f'Unexpected source cells {section} {fields}')
  pending.update(subject=fields[1] if auto else fields[0],signer=fields[0] if auto else None,
   material=' '.join(fields[minimum:]) or None,sourceFields=fields)
  (multi[section] if section in multi else sections[section]).append(pending);pending=None
 for pn,page in enumerate(pdf.pages,1):
  chunks=[]
  def visit(t,cm,tm,font,size):
   if t.strip():chunks.append((t.strip(),float(tm[4]),float(tm[5]),str((font or {}).get('/BaseFont',''))))
  page.extract_text(visitor_text=visit)
  if pn>12:
   finish()
   if not chunks:blank_pages.append(pn)
   for text,x,y,font in chunks:
    if x>=0 or not text.startswith('Star Wars:'):raise ValueError('Unexpected trailing PDF artifact')
    artifacts.append(dict(text=text,page=pn,x=x,y=y,reason='Detached off-page story-context fragment; not an artist or card identity.'))
   continue
  for text,x,y,font in chunks:
   if re.fullmatch(r'(?:DA|TA|QAB)-[A-Z]+',text):labels.append(dict(number=text,page=pn,y=y));continue
   if 'Bold' in font and text in [*SECTIONS,'BASE','INSERT','AUTOGRAPH','AUTOGRAPH RELIC','RELIC','SKETCH CARDS','SKETCH ARTIST LIST']:
    finish()
    if text in SECTIONS:
     if text in sections:raise ValueError('Repeated heading')
     section=text;sections[text]=[]
     if SECTIONS[text][0] in ('DUO','TRIO','QUAD'):multi[text]=[]
    else:section='SKETCH ARTIST LIST' if text=='SKETCH ARTIST LIST' else None
   elif section=='SKETCH ARTIST LIST':artists.append(dict(name=text,page=pn))
   elif section in multi:
    if x>100:finish();pending=dict(page=pn,y=y,fields=[text])
    elif pending is not None:pending['fields'].append(text)
    else:raise ValueError('Missing signer')
   elif section in SECTIONS and 0<x<150 and re.fullmatch(r'[0-9]+|[A-Z]+-[A-Z0-9]+',text):
    finish();pending=dict(number=text,page=pn,fields=[])
   elif pending is not None:pending['fields'].append(text)
   else:raise ValueError('Unclassified text '+text)
 finish()
 grouped=OrderedDict()
 for label in sorted(labels,key=lambda r:(r['page'],-r['y'])):grouped.setdefault(label['number'],[]).append(label)
 for name,rows in multi.items():
  code=SECTIONS[name][0];n={'DUO':2,'TRIO':3,'QUAD':4}[code];prefix={'DUO':'DA-','TRIO':'TA-','QUAD':'QAB-'}[code]
  group_labels=[(num,ls) for num,ls in grouped.items() if num.startswith(prefix)]
  if len(rows)!=len(group_labels)*n:raise ValueError('Multi-signer count mismatch')
  for i,(number,anchors) in enumerate(group_labels):
   batch=rows[i*n:(i+1)*n]
   pos=lambda r:r['page']*1000-r['y']
   if not all(pos(batch[0])<=pos(a)<=pos(batch[-1]) for a in anchors):raise ValueError('Label lies outside signer group '+number)
   if len(anchors)>1 and not (number=='DA-HR' and [a['page'] for a in anchors]==[6,7]):raise ValueError('Unexpected repeated label')
   sections[name].extend(dict(number=number,**r) for r in batch)
 if list(sections)!=list(SECTIONS):raise ValueError('Checklist manifest mismatch')
 return [dict(name=k,rows=v) for k,v in sections.items()],artists,labels,artifacts,blank_pages


def normalize(directory):
 from pypdf import PdfReader
 subsets,artists,labels,artifacts,blank_pages=extract_checklist(directory/'checklist.pdf');odds=[]
 pdf=PdfReader(directory/'odds.pdf')
 if len(pdf.pages)!=1:raise ValueError('Expected one odds page')
 cells=[]
 pdf.pages[0].extract_text(visitor_text=lambda t,cm,tm,font,size:cells.append(t.strip()) if t.strip() else None)
 if cells[:2]!=['Card','5667 - STW-MASTERWORK 2024  HOBBY DISTRIBUTOR']:raise ValueError('Unexpected odds header')
 if len(cells[2:])!=152:raise ValueError('Unpaired odds cells')
 for i in range(2,len(cells),2):
  label,rate=cells[i:i+2]
  if not re.fullmatch(r'\d[\d,]*:\d[\d,]*',rate):raise ValueError('Invalid source rate')
  odds.append(dict(label=label,hobby=rate,page=1,rawCells=[label,rate]))
 if len(odds)!=76:raise ValueError('Unexpected odds count')
 return dict(checklistUrl=CHECKLIST_URL,oddsUrl=ODDS_URL,productUrl=PRODUCT_URL,
  checklistSha256=hashlib.sha256((directory/'checklist.pdf').read_bytes()).hexdigest(),
  oddsSha256=hashlib.sha256((directory/'odds.pdf').read_bytes()).hexdigest(),
  subsets=subsets,sketchArtists=artists,multiSignerLabels=labels,sourceArtifacts=artifacts,blankPages=blank_pages,odds=odds)


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
   card=dict(id=f'2024-TSWMW-{code}-{number}',setId=SET_ID,order=len(cards)+1,number=number,
    name=' / '.join(names),subject2=' / '.join(names[1:]) or None,category=category,subset=name,subsetCode=code,
    roster=None,rookie='No',parallelGroup=code)
   cards.append(card)
   variants.append(dict(id=card['id']+'-IDENTITY',set_id=SET_ID,card_id=card['id'],variant_order=len(variants)+1,
    subset=name,card_number=number,display_name=card['name'],parallel='Checklist identity',serial_cap=None,
    serial_exact=None,exclusive_note=None,numbering_note='Official numbered design; no parallel grid or serial cap inferred.',
    verification_status='Official Topps checklist verified'))
  subsets.append(dict(category=category,name=name,code=code,count=len(identities)))
 record=dict(id=SET_ID,categoryId='star-wars',name='2024 Topps Star Wars Masterwork',shortName='Star Wars Masterwork 2024',
  accent='#d3b56a',year=2024,manufacturer='Topps',releaseDate='2025-04-16',cardCount=len(cards),subsetCount=len(subsets),subsets=subsets)
 return record,cards,variants


def apply(catalogue,record,cards):
 old_sets=[s for s in catalogue['sets'] if s['id']==SET_ID];old_cards=[c for c in catalogue['cards'] if c['setId']==SET_ID]
 if old_sets or old_cards:
  if old_sets!=[record] or old_cards!=cards:raise ValueError('Existing Masterwork identities differ; refusing overwrite')
  return catalogue
 catalogue['sets'].append(record);catalogue['cards'].extend(cards);catalogue['generatedAt']='2026-10-26T00:00:00Z'
 return catalogue


def tables():
 source=json.loads(SOURCE.read_text());record,cards,variants=build(source)
 evidence={(SECTIONS[s['name']][0],r['number']):r for s in source['subsets'] for r in s['rows']}
 result=OrderedDict()
 result['catalogue_sets']=[dict(id=SET_ID,name=record['name'],short_name=record['shortName'],year=2024,
  manufacturer='Topps',release_date=record['releaseDate'],source_file=CHECKLIST_URL,accent=record['accent'],
  card_count=len(cards),subset_count=len(record['subsets']),variant_count=len(variants))]
 result['catalogue_subsets']=[dict(set_id=SET_ID,subset_code=s['code'],category=s['category'],name=s['name'],
  card_count=s['count'],parallel_group=s['code'],source_url=CHECKLIST_URL) for s in record['subsets']]
 result['catalogue_cards']=[dict(id=c['id'],set_id=SET_ID,checklist_order=c['order'],category=c['category'],
  subset_code=c['subsetCode'],card_number=c['number'],display_name=c['name'],subject_1=c['name'].split(' / ')[0],
  subject_2=c['subject2'],roster=None,rookie=False,parallel_group=c['parallelGroup'],image_status='Missing',
  pricing_status='Unpriced',source_url=CHECKLIST_URL,
  notes='Official manufacturer spelling and numbers retained. '+
  (f"Source context: {evidence[(c['subsetCode'],c['number'])]['material']}. " if evidence[(c['subsetCode'],c['number'])]['material'] else '')+
  'Repeated signer rows combine by printed number; matching numbers across subsets remain distinct. Sketch artists remain a roster; no unique sketch identities or parallel grids inferred.') for c in cards]
 result['catalogue_variants']=variants
 aliases={name:name for name in SECTIONS}
 aliases.update({'MARVEL COMICS COVERS':'MARVEL COMIC COVERS','DUO AUTOGRAPHS':'DUAL AUTOGRAPHS',
  'TRIO AUTOGRAPHS':'TRIPLE AUTOGRAPHS','PEN AUTOGRAPHS RELICS':'PEN AUTOGRAPH RELICS',
  'RISE OF THE RESISTANCE RELIC':'RISE OF THE RESISTANCE RELICS'})
 rules=[]
 for i,row in enumerate(source['odds'],1):
  label=row['label']
  if label in ['SKETCH CARDS','SKETCH CARD BOOKS','PANORAMIC SKETCH CARDS','TRIPTYCH SKETCH CARDS']:continue
  alias=next((a for a in sorted(aliases,key=len,reverse=True) if label.lower()==a.lower() or label.lower().startswith(a.lower()+' ')),None)
  if alias is None:raise ValueError('Unmapped odds label: '+label)
  name=aliases[alias]
  rules.append(dict(id=f'{SET_ID}-ODDS-{i:03d}',set_id=SET_ID,parallel_group=SECTIONS[name][0],applies_to=name,
   parallel=label[len(alias):].strip() or 'Base issue',serial_cap=None,serial_exact=None,
   exclusive_note=f"Hobby pack odds {row['hobby']}.",
   numbering_note=f"Official odds PDF page {row['page']}; subset rule only. Pack odds do not establish serial caps or guarantee every subject in every parallel.",
   verification_status='Official Topps odds; subset rule only'))
 result['catalogue_parallel_rules']=rules
 result['catalogue_sources']=[dict(id=SET_ID+'-'+key,set_id=SET_ID,source='Topps',purpose=purpose,url=url,notes=notes)
  for key,purpose,url,notes in [('checklist','Checklist',CHECKLIST_URL,'17-page official v2 checklist. Multi-signer labels reconciled geometrically; DA-HR repeats at page boundary for one design. 182 sketch-artist entries remain a roster; three blank pages and 16 detached off-page story-context fragments do not create artists or identities.'),
   ('odds','Parallel applicability',ODDS_URL,'76 rows retained; 72 subset rules, four sketch rates source-only. BLAC label retained as printed, without inferring its missing character or serial caps.'),
   ('product','Release and title year',PRODUCT_URL,'Official 2024 product title; Available From April 16, 2025. Generic Product Year metadata says 2025. Title year retained.')]]
 return result


if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--extract',type=Path);parser.add_argument('--verify-pdf',type=Path);args=parser.parse_args()
 if args.extract:
  s=normalize(args.extract);SOURCE.parent.mkdir(parents=True,exist_ok=True);SOURCE.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
  print(json.dumps(dict(rows=sum(len(x['rows']) for x in s['subsets']),artists=len(s['sketchArtists']),odds=len(s['odds']),counts={x['name']:len({r['number'] for r in x['rows']}) for x in s['subsets']})))
 else:
  if args.verify_pdf and normalize(args.verify_pdf)!=json.loads(SOURCE.read_text()):raise ValueError('Manufacturer evidence changed')
  record,cards,_=build();save_catalogue(apply(load_catalogue(),record,cards));print(json.dumps(dict(cards=len(cards),subsets=len(record['subsets']),rules=len(tables()['catalogue_parallel_rules']))))
