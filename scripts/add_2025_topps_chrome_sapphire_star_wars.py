#!/usr/bin/env python3
"""Import Galaxy's numbered artwork and autograph identities, preserving source quirks."""
import argparse
import hashlib
import json
import re
from collections import OrderedDict
from pathlib import Path

from catalogue_io import load_catalogue, save_catalogue

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'sources/chrome-sapphire-star-wars-2025/checklist.json'
SET_ID = '2025-topps-chrome-sapphire-star-wars'
CHECKLIST_URL = 'https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2025_Topps_Chrome_Sapphire_Star_Wars_Checklist.pdf?v=1787949354'
ODDS_URL = 'https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2025_Topps_Chrome_Sapphire_Star_Wars_Odds.pdf?v=1787949354'
PRODUCT_URL = 'https://www.topps.com/products/2025-topps-chrome%C2%AE-sapphire-star-wars-hobby-box'
SECTIONS=OrderedDict([
 ('CHARACTERS',('BASE','Base')),
 ('SAPPHIRE SELECTIONS',('SS','Insert')),
 ('AUTOGRAPH CARDS',('AUTO','Autograph')),
 ('DUO AUTOGRAPHS',('DUAL','Autograph')),
 ('TRIO AUTOGRAPHS',('TRIPLE','Autograph')),
])
EXPECTED_COUNTS=[200,10,122,15,11]


def extract_checklist(path):
    from pypdf import PdfReader
    pdf=PdfReader(path)
    if len(pdf.pages)!=15:raise ValueError('Expected 15 checklist pages')
    sections,artifacts,blank_pages,section,pending=OrderedDict(),[],[],None,None
    def finish():
        nonlocal pending
        if pending is None:return
        fields=pending.pop('fields');code,category=SECTIONS[section]
        expected=2 if category=='Autograph' else 1
        if len(fields)!=expected:raise ValueError(f'Unexpected source cells: {section} {pending} {fields}')
        auto=category=='Autograph'
        pending.update(subject=fields[1] if auto else fields[0],signer=fields[0] if auto else None,
                       artist=None,sourceFields=fields)
        sections[section].append(pending);pending=None
    for page_number,page in enumerate(pdf.pages,1):
        chunks=[]
        def visit(text,cm,tm,font,size):
            if text.strip():chunks.append((text.strip(),float(tm[4])))
        page.extract_text(visitor_text=visit)
        if not chunks:blank_pages.append(page_number)
        if page_number>8:
            finish()
            for text,x in chunks:
                if text!='DEBUT':raise ValueError('Unexpected trailing PDF content')
                artifacts.append(dict(text=text,page=page_number,x=x,reason='Unattached trailing DEBUT glyph; no numbered source row on page.'))
            continue
        for text,x in chunks:
            if text in [*SECTIONS,'BASE','INSERT','AUTOGRAPHS'] and x>0:
                finish()
                if text in SECTIONS:
                    if text in sections:raise ValueError('Repeated heading')
                    section=text;sections[text]=[]
                continue
            if text=='DEBUT':
                if pending is None or section!='CHARACTERS' or pending['debut']:raise ValueError('Unattached or repeated DEBUT flag')
                pending['debut']=True;continue
            if section not in SECTIONS:raise ValueError('Unclassified source text '+text)
            if x>0 and re.fullmatch(r'[0-9]+|[A-Z0-9]+-[A-Za-z0-9-]+',text):
                finish();pending=dict(number=text,page=page_number,fields=[],debut=False)
            elif pending is not None:pending['fields'].append(text)
            else:raise ValueError('Unclassified body cell '+text)
    finish()
    if list(sections)!=list(SECTIONS):raise ValueError('Checklist section manifest changed')
    return [dict(name=k,rows=v) for k,v in sections.items()],artifacts,blank_pages


def normalize(directory):
    import pdfplumber
    subsets,artifacts,blank_pages=extract_checklist(directory/'checklist.pdf');odds=[]
    with pdfplumber.open(directory/'odds.pdf') as pdf:
        if len(pdf.pages)!=1:raise ValueError('Expected single-page odds')
        for line in pdf.pages[0].extract_text(layout=True).splitlines():
            text=' '.join(line.split())
            if not text or text=='Cards Sapphire':continue
            m=re.fullmatch(r'(.+?)\s+(\d[\d,]*:\d[\d,]*)',text)
            if not m:raise ValueError('Unparsed odds row '+text)
            odds.append(dict(label=m[1],sapphire=m[2],page=1,rawLine=text))
    if len(odds)!=17:raise ValueError('Unexpected odds count')
    return dict(checklistUrl=CHECKLIST_URL,oddsUrl=ODDS_URL,productUrl=PRODUCT_URL,
                checklistSha256=hashlib.sha256((directory/'checklist.pdf').read_bytes()).hexdigest(),
                oddsSha256=hashlib.sha256((directory/'odds.pdf').read_bytes()).hexdigest(),
                subsets=subsets,sourceArtifacts=artifacts,blankPages=blank_pages,odds=odds)


def build(source=None):
    source=source or json.loads(SOURCE.read_text())
    if [s['name'] for s in source['subsets']] != list(SECTIONS) or len(EXPECTED_COUNTS)!=len(SECTIONS):
        raise ValueError('Unexpected checklist section manifest')
    cards,variants,subsets=[],[],[]
    for section,expected_count in zip(source['subsets'],EXPECTED_COUNTS):
        name=section['name'];code,category=SECTIONS[name]
        identities=OrderedDict()
        for row in section['rows']:
            identities.setdefault(row['number'],[]).append(row)
        if len(identities)!=expected_count:
            raise ValueError(f'Unexpected count for {name}')
        if code=='BASE' and set(identities)!=set(map(str,range(1,201))):
            raise ValueError('Incomplete 200-card base set')
        for number,rows in identities.items():
            expected={'DUAL':2,'TRIPLE':3,'QUAD':4}.get(code,1)
            if len(rows)!=expected or len({(r['subject'],r['signer']) for r in rows})!=expected:
                raise ValueError(f'Unexpected repeated number {name} {number}')
            names=[f"{r['subject']} ({r['signer']})" if r['signer'] else r['subject'] for r in rows]
            card=dict(id=f'2025-TCSSW-{code}-{number}',setId=SET_ID,order=len(cards)+1,
                      number=number,name=' / '.join(names),subject2=' / '.join(names[1:]) or None,
                      category=category,subset=name,subsetCode=code,roster=None,rookie='No',parallelGroup=code)
            cards.append(card)
            variants.append(dict(id=card['id']+'-IDENTITY',set_id=SET_ID,card_id=card['id'],variant_order=len(variants)+1,
                subset=name,card_number=number,display_name=card['name'],parallel='Checklist identity',serial_cap=None,
                serial_exact=None,exclusive_note=None,numbering_note='Official checklist identity; no parallel grid or serial cap inferred.',
                verification_status='Official Topps checklist verified'))
        subsets.append(dict(category=category,name=name,code=code,count=len(identities)))
    record=dict(id=SET_ID,categoryId='star-wars',name='2025 Topps Chrome Sapphire Star Wars',shortName='Chrome Sapphire Star Wars 2025',
                accent='#9778e6',year=2025,manufacturer='Topps',releaseDate='2025-09-17',cardCount=len(cards),
                subsetCount=len(subsets),subsets=subsets)
    return record,cards,variants


def apply(catalogue,record,cards):
    old_sets=[s for s in catalogue['sets'] if s['id']==SET_ID]
    old_cards=[c for c in catalogue['cards'] if c['setId']==SET_ID]
    if old_sets or old_cards:
        if old_sets!=[record] or old_cards!=cards:
            raise ValueError('Existing Sapphire identities differ; refusing overwrite')
        return catalogue
    catalogue['sets'].append(record);catalogue['cards'].extend(cards)
    catalogue['generatedAt']='2026-10-26T00:00:00Z'
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
        notes=('Official source marks DEBUT. ' if evidence[(c['subsetCode'],c['number'])]['debut'] else '')+
        'Official source spelling, numbers and signers retained. Multi-signer rows combine into one design. DEBUT is retained as source metadata and is not inferred to be an athlete rookie card. No card-specific parallel grid or serial cap inferred.') for c in cards]
    result['catalogue_variants']=variants
    aliases={'Characters':'CHARACTERS','Sapphire Selections':'SAPPHIRE SELECTIONS','Single Autographs':'AUTOGRAPH CARDS','Dual Autographs':'DUO AUTOGRAPHS','Triple Autographs':'TRIO AUTOGRAPHS'}
    rules=[]
    for i,row in enumerate(source['odds'],1):
        alias=next((a for a in sorted(aliases,key=len,reverse=True) if row['label']==a or row['label'].startswith((a+'-',a+' -'))),None)
        if alias is None:raise ValueError('Unmapped odds label '+row['label'])
        section=aliases[alias]
        rules.append(dict(id=f'{SET_ID}-ODDS-{i:03d}',set_id=SET_ID,parallel_group=SECTIONS[section][0],applies_to=section,
            parallel=row['label'][len(alias):].lstrip(' -') or 'Base issue',serial_cap=None,serial_exact=None,
            exclusive_note=f"Sapphire pack odds {row['sapphire']}.",
            numbering_note='Official single-page odds PDF. Manufacturer spelling retained, including Padpradascha. Pack odds do not establish serial caps or every subject/parallel combination.',
            verification_status='Official Topps odds; subset rule only'))
    result['catalogue_parallel_rules']=rules
    result['catalogue_sources']=[dict(id=SET_ID+'-'+key,set_id=SET_ID,source='Topps',purpose=purpose,url=url,notes=notes)
        for key,purpose,url,notes in [('checklist','Checklist',CHECKLIST_URL,'15-page official PDF: numbered rows on pages 1–8, blank pages 9–12 and unattached DEBUT glyphs on pages 13–15. Artifacts do not create identities or flags.'),
            ('odds','Parallel applicability',ODDS_URL,'17 Sapphire subset rules; pack odds do not imply serial caps or subject/parallel grids.'),
            ('product','Release date and product identity',PRODUCT_URL,'Manufacturer release September 17, 2025. Separate set from regular Chrome.')]]
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--extract',type=Path);parser.add_argument('--verify-pdf',type=Path)
    args=parser.parse_args()
    if args.extract:
        source=normalize(args.extract);SOURCE.parent.mkdir(parents=True,exist_ok=True)
        SOURCE.write_text(json.dumps(source,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(dict(rows=sum(len(s['rows']) for s in source['subsets']),counts={s['name']:len({r['number'] for r in s['rows']}) for s in source['subsets']},debut=sum(r['debut'] for s in source['subsets'] for r in s['rows']),artifacts=len(source['sourceArtifacts']),blankPages=source['blankPages'])))
    else:
        if args.verify_pdf and normalize(args.verify_pdf)!=json.loads(SOURCE.read_text()):
            raise ValueError('Normalized evidence differs from manufacturer PDFs')
        record,cards,_=build();save_catalogue(apply(load_catalogue(),record,cards))
        print(json.dumps(dict(cards=len(cards),subsets=len(record['subsets']),rules=len(tables()['catalogue_parallel_rules']))))
