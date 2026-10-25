#!/usr/bin/env python3
"""Import regular Chrome's numbered designs and multi-signer identities."""
import argparse
import hashlib
import json
import re
from collections import OrderedDict
from pathlib import Path

from catalogue_io import load_catalogue, save_catalogue

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'sources/chrome-star-wars-2025/checklist.json'
SET_ID = '2025-topps-chrome-star-wars'
CHECKLIST_URL = 'https://cdn.shopify.com/s/files/1/0662/9749/5709/files/Checklist_-_2025_Topps_Chrome_Star_Wars_cbb6bdaf-a6f0-4435-9bcc-59f4b3497263.pdf?v=1787946290'
ODDS_URL = 'https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2025_Topps_Chrome_Star_Wars_Odds.pdf?v=1787948202'
PRODUCT_URL = 'https://www.topps.com/products/2025-topps-chrome-star-wars-hobby-box'
SECTIONS=OrderedDict([('CHARACTERS', ('BASE', 'Base')), ('PRINTING PLATE BOOK CARD', ('PLATE', 'Insert')), ('HOTHFRACTOR SHORT PRINT', ('HOTH', 'Insert')), ('AUREBESH SHORT PRINT', ('AURE', 'Insert')), ('1975 TRIBUTE', ('TRIBUTE', 'Insert')), ('SKELETON CREW', ('SC', 'Insert')), ('ACOLYTE', ('AC', 'Insert')), ('UNDERWORLD ODDITIES', ('UO', 'Insert')), ('STAR WARS BY THE NUMBER', ('CP', 'Insert')), ('GALACTIC GRAFITTI', ('GG', 'Insert')), ('BONUS STAGE', ('BS', 'Insert')), ('KYBER LIGHT', ('KL', 'Insert')), ('REFLECTIONS', ('REF', 'Insert')), ('COMICFRACTOR', ('VC', 'Insert')), ('ONE WITH THE FORCE', ('OF', 'Insert')), ('DOUBLE VISION', ('DV', 'Insert')), ('AUTOGRAPH CARDS', ('AUTO', 'Autograph')), ('DUO AUTOGRAPHS', ('DUAL', 'Autograph')), ('TRIO AUTOGRAPHS', ('TRIPLE', 'Autograph')), ('1975 TRIBUTE AUTOGRAPH VARIATION', ('TVA', 'Autograph'))])
EXPECTED_COUNTS=[200,200,200,200,50,25,25,25,24,21,10,20,5,5,5,25,122,15,11,47]
FORMATS=['hobby','breaker','valueSE','valueEA','valueCEE']


def extract_checklist(path):
    from pypdf import PdfReader
    pdf=PdfReader(path)
    if len(pdf.pages)!=16:raise ValueError('Expected 16 checklist pages')
    sections,artists,section,pending=OrderedDict(),[],None,None
    def finish():
        nonlocal pending
        if pending is None:return
        fields=pending.pop('fields');code,category=SECTIONS[section]
        expected=2 if category=='Autograph' else 1
        if len(fields)!=expected:raise ValueError(f'Unexpected source cells: {section} {pending} {fields}')
        auto=category=='Autograph'
        pending.update(subject=fields[1] if auto else fields[0],signer=fields[0] if auto else None,sourceFields=fields)
        sections[section].append(pending);pending=None
    for page_number,page in enumerate(pdf.pages,1):
        chunks=[]
        def visit(text,cm,tm,font,size):
            if text.strip():chunks.append((text.strip(),float(tm[4])))
        page.extract_text(visitor_text=visit)
        for text,x in chunks:
            if text in [*SECTIONS,'Sketch Artists','BASE','INSERT','AUTOGRAPHS'] and x>0:
                finish()
                if text in SECTIONS:
                    if text in sections:raise ValueError('Repeated heading')
                    section=text;sections[text]=[]
                elif text=='Sketch Artists':section=text
                continue
            if section=='Sketch Artists':artists.append(dict(name=text,page=page_number));continue
            if text=='DEBUT':
                if pending is None or pending['debut']:raise ValueError(f'Unattached/repeated DEBUT page {page_number}: {section} {pending}')
                pending['debut']=True;continue
            if section not in SECTIONS:raise ValueError('Unclassified text '+text)
            if x>0 and re.fullmatch(r'[0-9]+|[A-Z0-9]+-[A-Za-z0-9-]+',text):
                finish();pending=dict(number=text,page=page_number,fields=[],debut=False)
            elif pending is not None:pending['fields'].append(text)
            else:raise ValueError('Unclassified cell '+text)
    finish()
    if list(sections)!=list(SECTIONS):raise ValueError('Checklist manifest changed')
    return [dict(name=k,rows=v) for k,v in sections.items()],artists


def valid_rate(rate):
    return rate=='-' or bool(re.fullmatch(r'\d+:(?:\d+|\d{1,3}(?:,\d{3})+)',rate))


def normalize(directory):
    import pdfplumber
    subsets,artists=extract_checklist(directory/'checklist.pdf');odds=[]
    with pdfplumber.open(directory/'odds.pdf') as pdf:
        if len(pdf.pages)!=1:raise ValueError('Expected single-page odds')
        for line in pdf.pages[0].extract_text(layout=True).splitlines():
            text=' '.join(line.split())
            if not text or text.startswith('Cards Hobby'):continue
            parts=text.rsplit(' ',5)
            if len(parts)!=6 or not all(re.fullmatch(r'[0-9,:;]+|-',r) for r in parts[1:]):raise ValueError('Unparsed odds row '+text)
            rates=dict(zip(FORMATS,parts[1:]));invalid=[k for k,v in rates.items() if not valid_rate(v)]
            odds.append(dict(label=parts[0],rates=rates,invalidFormats=invalid,page=1,rawLine=text))
    if len(odds)!=95:raise ValueError('Unexpected odds count')
    return dict(checklistUrl=CHECKLIST_URL,oddsUrl=ODDS_URL,productUrl=PRODUCT_URL,
                checklistSha256=hashlib.sha256((directory/'checklist.pdf').read_bytes()).hexdigest(),
                oddsSha256=hashlib.sha256((directory/'odds.pdf').read_bytes()).hexdigest(),
                subsets=subsets,sketchArtists=artists,odds=odds)


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
        if code in ['PLATE','HOTH','AURE'] and set(identities)!={f'{prefix}-{i}' for i in range(1,201) for prefix in [{'PLATE':'BC','HOTH':'HF','AURE':'AV'}[code]]}:raise ValueError('Incomplete character design programme')
        for number,rows in identities.items():
            expected={'DUAL':2,'TRIPLE':3,'QUAD':4}.get(code,1)
            if len(rows)!=expected or len({(r['subject'],r['signer']) for r in rows})!=expected:
                raise ValueError(f'Unexpected repeated number {name} {number}')
            names=[f"{r['subject']} ({r['signer']})" if r['signer'] else r['subject'] for r in rows]
            card=dict(id=f'2025-TCSW-{code}-{number}',setId=SET_ID,order=len(cards)+1,
                      number=number,name=' / '.join(names),subject2=' / '.join(names[1:]) or None,
                      category=category,subset=name,subsetCode=code,roster=None,rookie='No',parallelGroup=code)
            cards.append(card)
            variants.append(dict(id=card['id']+'-IDENTITY',set_id=SET_ID,card_id=card['id'],variant_order=len(variants)+1,
                subset=name,card_number=number,display_name=card['name'],parallel='Checklist identity',serial_cap=None,
                serial_exact=None,exclusive_note=None,numbering_note='Official checklist identity; no parallel grid or serial cap inferred.',
                verification_status='Official Topps checklist verified'))
        subsets.append(dict(category=category,name=name,code=code,count=len(identities)))
    record=dict(id=SET_ID,categoryId='star-wars',name='2025 Topps Chrome Star Wars',shortName='Chrome Star Wars 2025',
                accent='#9778e6',year=2025,manufacturer='Topps',releaseDate='2025-08-20',cardCount=len(cards),
                subsetCount=len(subsets),subsets=subsets)
    return record,cards,variants


def apply(catalogue,record,cards):
    old_sets=[s for s in catalogue['sets'] if s['id']==SET_ID]
    old_cards=[c for c in catalogue['cards'] if c['setId']==SET_ID]
    if old_sets or old_cards:
        if old_sets!=[record] or old_cards!=cards:
            raise ValueError('Existing Chrome identities differ; refusing overwrite')
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
    aliases={name.title():name for name in SECTIONS}
    aliases.update({'Characters Hoth Ice Blue Frozenfractor Variation':'HOTHFRACTOR SHORT PRINT',
                   'Characters Aurebesh Variation':'AUREBESH SHORT PRINT',
                   'Outerworld Oddities':'UNDERWORLD ODDITIES','Star Wars By The Numbers':'STAR WARS BY THE NUMBER',
                   "Tribute to '75 Autograph Variation":'1975 TRIBUTE AUTOGRAPH VARIATION',"Tribute to '75":'1975 TRIBUTE',
                   'Single Autographs':'AUTOGRAPH CARDS'})
    rules=[]
    for i,row in enumerate(source['odds'],1):
        if row['label'].startswith('Sketch Card'):continue
        alias=next((a for a in sorted(aliases,key=len,reverse=True) if row['label'].lower()==a.lower() or row['label'].lower().startswith(a.lower()+' ')),None)
        if alias is None:raise ValueError('Unmapped odds label '+row['label'])
        section=aliases[alias]
        rates='; '.join(f"{k}: {v}" for k,v in row['rates'].items())
        if row['invalidFormats']:rates+='; unresolved malformed manufacturer rates: '+', '.join(row['invalidFormats'])+'. Not interpreted or corrected.'
        rules.append(dict(id=f'{SET_ID}-ODDS-{i:03d}',set_id=SET_ID,parallel_group=SECTIONS[section][0],applies_to=section,
            parallel=row['label'][len(alias):].strip() or 'Base issue',serial_cap=None,serial_exact=None,
            exclusive_note=rates,
            numbering_note='Official single-page odds PDF, all five formats retained. A dash is retained as printed. Odds do not establish serial caps or universal subject/parallel applicability.',
            verification_status='Official subset label; malformed pack rate unresolved' if row['invalidFormats'] else 'Official Topps odds; subset rule only'))
    result['catalogue_parallel_rules']=rules
    result['catalogue_sources']=[dict(id=SET_ID+'-'+key,set_id=SET_ID,source='Topps',purpose=purpose,url=url,notes=notes)
        for key,purpose,url,notes in [('checklist','Checklist',CHECKLIST_URL,'16-page manufacturer checklist. Numbered design identities retained; artist roster does not create sketch identities.'),
            ('odds','Parallel applicability',ODDS_URL,'Five box formats retained verbatim. Malformed double-colon/grouped-digit rates are flagged unresolved. Outerworld Oddities odds label reconciles to Underworld Oddities checklist heading. No serial caps inferred.'),
            ('product','Release date and product identity',PRODUCT_URL,'Official release August 20, 2025. Separate IDs from Sapphire, Galaxy and 2026 Chrome.')]]
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--extract',type=Path);parser.add_argument('--verify-pdf',type=Path)
    args=parser.parse_args()
    if args.extract:
        source=normalize(args.extract);SOURCE.parent.mkdir(parents=True,exist_ok=True)
        SOURCE.write_text(json.dumps(source,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(dict(rows=sum(len(s['rows']) for s in source['subsets']),counts={s['name']:len({r['number'] for r in s['rows']}) for s in source['subsets']},debut=sum(r['debut'] for s in source['subsets'] for r in s['rows']),artists=len(source['sketchArtists']),odds=len(source['odds']),invalid=[dict(label=r['label'],formats=r['invalidFormats']) for r in source['odds'] if r['invalidFormats']])))
    else:
        if args.verify_pdf and normalize(args.verify_pdf)!=json.loads(SOURCE.read_text()):
            raise ValueError('Normalized evidence differs from manufacturer PDFs')
        record,cards,_=build();save_catalogue(apply(load_catalogue(),record,cards))
        print(json.dumps(dict(cards=len(cards),subsets=len(record['subsets']),rules=len(tables()['catalogue_parallel_rules']))))
