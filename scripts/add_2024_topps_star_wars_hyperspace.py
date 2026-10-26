#!/usr/bin/env python3
"""Import manufacturer-numbered Hyperspace designs; retain unnumbered sketch rosters."""
import argparse
import hashlib
import json
import re
from collections import OrderedDict
from pathlib import Path

from catalogue_io import load_catalogue, save_catalogue

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'sources/star-wars-hyperspace-2024/checklist.json'
SET_ID = '2024-topps-star-wars-hyperspace'
CHECKLIST_URL = 'https://cdn.shopify.com/s/files/1/0662/9749/5709/files/STW2488-CheckList_24SWRS.pdf?v=1787937372'
ODDS_URL = 'https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2024_Star_Wars_Hyperspace_Odds.pdf?v=1787937372'
PRODUCT_URL = 'https://www.topps.com/products/2024-star-wars-hyperspace-hobby-box'
SECTIONS = OrderedDict([
 ('BASE CARDS',('BASE','Base')),('BASE CARDS PLANETARY VARIATIONS I',('BPV','Variation')),
 ('JUMP TO HYPERSPACE',('JH','Insert')),('THERES ALWAYS A BIGGER FISH',('BF','Insert')),
 ('FIRST ARRIVAL',('FA','Insert')),('GALACTIC ERAS',('GE','Insert')),
 ('STAR WARS REFLECTIONS',('R','Insert')),('PLANETARY VIEWS',('PV','Insert')),
 ('GALACTIC ORIGINS',('GO','Insert')),('STAR WARS AUTOGRAPH VARIATION',('AUTO','Autograph')),
])
EXPECTED_COUNTS = [100,100,5,15,15,25,5,5,10,46]
ROSTERS = ['Planets','Artists']
PLANETS = ['Naboo','Kashyyyk','Hoth','Bespin','Mustafar']


def extract_checklist(path):
    from pypdf import PdfReader
    pdf = PdfReader(path)
    if len(pdf.pages) != 10: raise ValueError('Expected 10 checklist pages')
    sections, rosters, section, pending = OrderedDict(), {k:[] for k in ROSTERS}, None, None
    def finish():
        nonlocal pending
        if pending is None: return
        fields = pending.pop('fields'); code, category = SECTIONS[section]
        field_count = 1 if code in ('R','PV') else 2
        if len(fields) != field_count: raise ValueError(f'Unexpected cells: {section} {pending} {fields}')
        subject, signer, artist, planet = fields[0], None, None, None
        if category == 'Autograph': signer, subject = fields
        elif field_count == 2: planet = fields[1]
        if planet is not None and planet not in PLANETS: raise ValueError('Unrecognized planet')
        pending.update(subject=subject, signer=signer, artist=artist, planet=planet, sourceFields=fields)
        sections[section].append(pending); pending = None
    for page_number, page in enumerate(pdf.pages, 1):
        chunks=[]
        def visit(text,cm,tm,font,size):
            if text.strip(): chunks.append((text.strip(),float(tm[4]),float(tm[5])))
        page.extract_text(visitor_text=visit)
        last_roster_line=None
        for text,x,y in chunks:
            if x > 0 and text in [*SECTIONS,*ROSTERS,'BASE','INSERT','AUTOGRAPH','SKETCH CARDS']:
                finish()
                if text in SECTIONS:
                    if text in sections: raise ValueError('Repeated heading')
                    section=text; sections[text]=[]
                elif text in ROSTERS: section=text
                else: section=None
            elif section in rosters:
                if last_roster_line==(section,y):
                    rosters[section][-1]['name']+=' '+text
                else: rosters[section].append(dict(name=text,page=page_number))
                last_roster_line=(section,y)
            elif section in SECTIONS and x > 0 and re.fullmatch(r'[0-9]+|[A-Z]+-[A-Za-z0-9]+',text):
                finish(); pending=dict(number=text,page=page_number,fields=[])
            elif pending is not None: pending['fields'].append(text)
            else: raise ValueError('Unclassified source text '+text)
    finish()
    if list(sections) != list(SECTIONS): raise ValueError('Checklist section manifest changed')
    if [r['name'] for r in rosters[ROSTERS[0]]] != PLANETS:
        raise ValueError('Sketch planet list changed')
    return [dict(name=k,rows=v) for k,v in sections.items()], rosters


def normalize(directory):
    import pdfplumber
    subsets,rosters=extract_checklist(directory/'checklist.pdf'); odds=[]
    with pdfplumber.open(directory/'odds.pdf') as pdf:
        if len(pdf.pages)!=2: raise ValueError('Expected two odds pages')
        for page_number,page in enumerate(pdf.pages,1):
            for line in page.extract_text(layout=True).splitlines():
                text=' '.join(line.split())
                if not text or text in ['2024 Star Wars Hyperspace','Card Odds']: continue
                match=re.fullmatch(r'(.+?)\s+(\d[\d,]*:\d[\d,]*)',text)
                if not match: raise ValueError('Unparsed odds row '+text)
                odds.append(dict(label=match[1],hobby=match[2],page=page_number,rawLine=text))
    if len(odds)!=61: raise ValueError(f'Unexpected odds count {len(odds)}')
    return dict(checklistUrl=CHECKLIST_URL,oddsUrl=ODDS_URL,productUrl=PRODUCT_URL,
        checklistSha256=hashlib.sha256((directory/'checklist.pdf').read_bytes()).hexdigest(),
        oddsSha256=hashlib.sha256((directory/'odds.pdf').read_bytes()).hexdigest(),
        subsets=subsets,rosters=rosters,odds=odds)


def build(source=None):
    source=source or json.loads(SOURCE.read_text())
    if [s['name'] for s in source['subsets']]!=list(SECTIONS): raise ValueError('Unexpected section manifest')
    cards,variants,subsets=[],[],[]
    for section,expected in zip(source['subsets'],EXPECTED_COUNTS):
        name=section['name'];code,category=SECTIONS[name];rows=section['rows']
        numbers={r['number'] for r in rows}
        if len(rows)!=expected or len(numbers)!=expected: raise ValueError('Missing or repeated number in '+name)
        if code!='AUTO':
            start={'R':6}.get(code,1)
            wanted={str(i) if code=='BASE' else f'{code}-{i}' for i in range(start,start+expected)}
            if numbers!=wanted: raise ValueError('Unexpected numbering in '+name)
        for row in rows:
            number=row['number'];subject=row['subject']
            display=f"{subject} ({row['signer']})" if row['signer'] else subject
            card=dict(id=f'2024-TSWH-{code}-{number}',setId=SET_ID,order=len(cards)+1,
                number=number,name=display,subject2=None,category=category,subset=name,subsetCode=code,
                roster=row['planet'],rookie='No',parallelGroup=code)
            cards.append(card)
            variants.append(dict(id=card['id']+'-IDENTITY',set_id=SET_ID,card_id=card['id'],variant_order=len(variants)+1,
                subset=name,card_number=number,display_name=display,parallel='Checklist identity',serial_cap=None,
                serial_exact=None,exclusive_note=None,numbering_note='Official numbered checklist identity; no serial cap or subject/parallel grid inferred.',
                verification_status='Official Topps checklist verified'))
        subsets.append(dict(category=category,name=name,code=code,count=len(rows)))
    record=dict(id=SET_ID,categoryId='star-wars',name='2024 Topps Star Wars Hyperspace',shortName='Star Wars Hyperspace 2024',
        accent='#dd9b50',year=2024,manufacturer='Topps',releaseDate='2025-02-19',cardCount=len(cards),subsetCount=len(subsets),subsets=subsets)
    return record,cards,variants


def apply(catalogue,record,cards):
    old_sets=[s for s in catalogue['sets'] if s['id']==SET_ID]
    old_cards=[c for c in catalogue['cards'] if c['setId']==SET_ID]
    if old_sets or old_cards:
        if old_sets!=[record] or old_cards!=cards: raise ValueError('Existing Hyperspace identities differ; refusing overwrite')
        return catalogue
    catalogue['sets'].append(record);catalogue['cards'].extend(cards)
    catalogue['generatedAt']='2026-10-26T00:00:00Z'
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
        subset_code=c['subsetCode'],card_number=c['number'],display_name=c['name'],subject_1=c['name'],
        subject_2=None,roster=c['roster'],rookie=False,parallel_group=c['parallelGroup'],image_status='Missing',
        pricing_status='Unpriced',source_url=CHECKLIST_URL,
        notes='Official spelling, printed number and subject retained. '+
        (f"Artist credit: {evidence[(c['subsetCode'],c['number'])]['artist']}. " if evidence[(c['subsetCode'],c['number'])]['artist'] else '')+
        'Planet metadata is retained in roster where supplied. No unnumbered sketch identities or serial caps inferred.') for c in cards]
    result['catalogue_variants']=variants
    aliases={'Base Planetary Variations':'BASE CARDS PLANETARY VARIATIONS I','Base':'BASE CARDS',
        'Jump to Hyperspace':'JUMP TO HYPERSPACE',"There's Always a Bigger Fish":'THERES ALWAYS A BIGGER FISH',
        "There's Always a Bigger a Bigger Fish":'THERES ALWAYS A BIGGER FISH','Galactic Eras':'GALACTIC ERAS',
        'First Arrival':'FIRST ARRIVAL','Reflections':'STAR WARS REFLECTIONS','Star Wars Reflections':'STAR WARS REFLECTIONS',
        'Planetary Views':'PLANETARY VIEWS','Galactic Origins':'GALACTIC ORIGINS',
        'Autographs':'STAR WARS AUTOGRAPH VARIATION','Autograph':'STAR WARS AUTOGRAPH VARIATION'}
    rules=[]
    for i,row in enumerate(source['odds'],1):
        if row['label'].startswith('Sketch Cards '): continue
        alias=next((a for a in sorted(aliases,key=len,reverse=True) if row['label']==a or row['label'].startswith((a+'-',a+' '))),None)
        if alias is None: raise ValueError('Unmapped odds label '+row['label'])
        section=aliases[alias]
        rules.append(dict(id=f'{SET_ID}-ODDS-{i:03d}',set_id=SET_ID,parallel_group=SECTIONS[section][0],applies_to=section,
            parallel=row['label'][len(alias):].lstrip(' -') or 'Base issue',serial_cap=None,serial_exact=None,
            exclusive_note=f"Hobby pack odds {row['hobby']}.",
            numbering_note=f"Official odds page {row['page']}, label: {row['label']}. Subset rule only; planetary labels describe the source planet group, not an all-card parallel. No serial caps or subject/parallel grid inferred.",
            verification_status='Official Topps odds; subset rule only'))
    result['catalogue_parallel_rules']=rules
    result['catalogue_sources']=[dict(id=SET_ID+'-'+key,set_id=SET_ID,source='Topps',purpose=purpose,url=url,notes=notes)
        for key,purpose,url,notes in [
            ('checklist','Checklist',CHECKLIST_URL,'10-page official checklist. Base/BPV printed spelling and planet differences retained. Reflections starts R-6. Sketch planet themes and artists remain rosters.'),
            ('odds','Parallel applicability',ODDS_URL,'Two-page official odds; sketch rates retained source-only. Alwaysa/Biggera wording and Superfractor Refractor labels retained. No inferred caps or grids.'),
            ('product','Release date and product identity',PRODUCT_URL,'Official 2024 title; Available From February 19, 2025 and generic Product Year 2025. Keep the title year and actual release date.')]]
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--extract',type=Path);parser.add_argument('--verify-pdf',type=Path)
    args=parser.parse_args()
    if args.extract:
        source=normalize(args.extract);SOURCE.parent.mkdir(parents=True,exist_ok=True)
        SOURCE.write_text(json.dumps(source,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(dict(rows=sum(len(s['rows']) for s in source['subsets']),rosters={k:len(v) for k,v in source['rosters'].items()},odds=len(source['odds']))))
    else:
        if args.verify_pdf and normalize(args.verify_pdf)!=json.loads(SOURCE.read_text()): raise ValueError('Normalized evidence differs from PDFs')
        record,cards,_=build();save_catalogue(apply(load_catalogue(),record,cards))
        print(json.dumps(dict(cards=len(cards),subsets=len(record['subsets']),rules=len(tables()['catalogue_parallel_rules']))))
