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
SOURCE = ROOT / 'sources/chrome-star-wars-galaxy-2025/checklist.json'
SET_ID = '2025-topps-chrome-star-wars-galaxy'
CHECKLIST_URL = 'https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2025_Star_Wars_Chrome_Galaxy_Checklist.pdf?v=1787955654'
ODDS_URL = 'https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2025_Star_Wars_Chrome_Galaxy_Odds.pdf?v=1787955654'
PRODUCT_URL = 'https://www.topps.com/products/2025-star-wars-chrome%C2%AE-galaxy-hobby-box'
SECTIONS = OrderedDict([('BASE CARDS', ('BASE', 'Base')), ('GALACTIC INSPIRATIONS', ('SWIN', 'Insert')), ('DUEL ON MUSTAFAR', ('DOM', 'Insert')), ('POWER OF THE FORCE', ('POW', 'Insert')), ('FEAR THE DARKSIDE', ('FTD', 'Insert')), ('TOPPS CHROME LAYERS RALPH MCQUARRIE ORIGINAL CONCEPT ART', ('LAY', 'Insert')), ('COMICFRACTOR', ('VC', 'Insert')), ('ONE WITH THE FORCE', ('OF', 'Insert')), ('ORIGINAL ART PUZZLE CARDS', ('PUZZLE', 'Insert')), ('STAR WARS GALAXY RALPH MCQUARRIE BUYBACKS', ('MCQ', 'Buyback')), ('GALAXY AUTOGRAPHS', ('AUTO', 'Autograph')), ('DUAL AUTOGRAPHS', ('DUAL', 'Autograph')), ('TRIPLE AUTOGRAPHS', ('TRIPLE', 'Autograph')), ('QUAD AUTOGRAPHS', ('QUAD', 'Autograph')), ('AUTOGRAPH BUYBACKS', ('AB', 'Autograph'))])
EXPECTED_COUNTS = [100,15,15,15,15,15,5,5,18,20,49,10,5,4,2]
ARTIST_SECTIONS=['BLANK CANVAS SKETCH CARD ARTISTS','SKETCH CARD ARTISTS']


def extract_checklist(path):
    from pypdf import PdfReader
    pdf=PdfReader(path)
    if len(pdf.pages)!=11:raise ValueError('Expected 11 official checklist pages')
    sections,artists,section,pending=OrderedDict(),{k:[] for k in ARTIST_SECTIONS},None,None
    def finish():
        nonlocal pending
        if pending is None:return
        fields=pending.pop('fields');code,category=SECTIONS[section]
        autograph=category=='Autograph' and code!='AB'
        expected=2 if autograph or code in ['BASE','SWIN','DOM','POW','FTD','PUZZLE','MCQ','AB'] else 1
        if len(fields)!=expected:raise ValueError(f'Unexpected field count {section} {pending}: {fields}')
        buyback=code in ['MCQ','AB']
        pending.update(subject=' '.join(fields) if buyback else fields[1] if autograph else fields[0],
                       signer=fields[0] if autograph else None,artist=fields[1] if not autograph and not buyback and len(fields)==2 else None,
                       sourceFields=fields)
        sections[section].append(pending);pending=None
    for page_number,page in enumerate(pdf.pages,1):
        chunks=[]
        def visit(text,cm,tm,font,size):
            if text.strip():chunks.append((text.strip(),float(tm[4])))
        page.extract_text(visitor_text=visit)
        for text,x in chunks:
            if text.startswith(('Checklists provided by Topps','actual contents and odds may vary.')):continue
            if x>0 and text in [*SECTIONS,*ARTIST_SECTIONS,'INSERTS','AUTOGRAPHS','SKETCH CARDS']:
                finish()
                if text in SECTIONS:
                    if text in sections:raise ValueError('Repeated heading')
                    sections[text]=[];section=text
                elif text in ARTIST_SECTIONS:section=text
                continue
            if section in ARTIST_SECTIONS:
                artists[section].append(dict(name=text,page=page_number));continue
            if section not in SECTIONS:raise ValueError('Unclassified source heading '+text)
            if x>0 and re.fullmatch(r'[0-9]+|[A-Z0-9]+-[A-Z0-9-]+',text):
                finish();pending=dict(number=text,page=page_number,fields=[])
            elif pending is not None:pending['fields'].append(text)
            else:raise ValueError(f'Unclassified source text page {page_number}: {text}')
    finish()
    if list(sections)!=list(SECTIONS):raise ValueError('Unexpected section order')
    return [dict(name=k,rows=v) for k,v in sections.items()],artists


def normalize(directory):
    import pdfplumber
    subsets,artists=extract_checklist(directory/'checklist.pdf');odds=[]
    with pdfplumber.open(directory/'odds.pdf') as pdf:
        if len(pdf.pages)!=1:raise ValueError('Expected single-page odds')
        for line in pdf.pages[0].extract_text(layout=True).splitlines():
            text=' '.join(line.split())
            if not text or text.startswith('Card STW-'):continue
            m=re.fullmatch(r'(.+?)\s+(\d[\d,]*[:;]\d[\d,]*)',text)
            if not m:raise ValueError('Unparsed odds row '+text)
            odds.append(dict(label=m[1],hobby=m[2],validRate=':' in m[2],page=1,rawLine=text))
    if len(odds)!=93:raise ValueError(f'Unexpected odds count {len(odds)}')
    return dict(checklistUrl=CHECKLIST_URL,oddsUrl=ODDS_URL,productUrl=PRODUCT_URL,
                checklistSha256=hashlib.sha256((directory/'checklist.pdf').read_bytes()).hexdigest(),
                oddsSha256=hashlib.sha256((directory/'odds.pdf').read_bytes()).hexdigest(),
                subsets=subsets,sketchArtists=artists['SKETCH CARD ARTISTS'],blankCanvasArtists=artists['BLANK CANVAS SKETCH CARD ARTISTS'],odds=odds)


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
        if code=='BASE' and set(identities)!=set(map(str,range(1,101))):
            raise ValueError('Incomplete 100-card base set')
        for number,rows in identities.items():
            expected={'DUAL':2,'TRIPLE':3,'QUAD':4}.get(code,1)
            if len(rows)!=expected or len({(r['subject'],r['signer']) for r in rows})!=expected:
                raise ValueError(f'Unexpected repeated number {name} {number}')
            names=[f"{r['subject']} ({r['signer']})" if r['signer'] else r['subject'] for r in rows]
            card=dict(id=f'2025-TCSWG-{code}-{number}',setId=SET_ID,order=len(cards)+1,
                      number=number,name=' / '.join(names),subject2=' / '.join(names[1:]) or None,
                      category=category,subset=name,subsetCode=code,roster=None,rookie='No',parallelGroup=code)
            cards.append(card)
            variants.append(dict(id=card['id']+'-IDENTITY',set_id=SET_ID,card_id=card['id'],variant_order=len(variants)+1,
                subset=name,card_number=number,display_name=card['name'],parallel='Checklist identity',serial_cap=None,
                serial_exact=None,exclusive_note=None,numbering_note='Official checklist identity; no parallel grid or serial cap inferred.',
                verification_status='Official Topps checklist verified'))
        subsets.append(dict(category=category,name=name,code=code,count=len(identities)))
    record=dict(id=SET_ID,categoryId='star-wars',name='2025 Topps Chrome Star Wars Galaxy',shortName='Chrome Star Wars Galaxy 2025',
                accent='#9778e6',year=2025,manufacturer='Topps',releaseDate='2025-12-10',cardCount=len(cards),
                subsetCount=len(subsets),subsets=subsets)
    return record,cards,variants


def apply(catalogue,record,cards):
    old_sets=[s for s in catalogue['sets'] if s['id']==SET_ID]
    old_cards=[c for c in catalogue['cards'] if c['setId']==SET_ID]
    if old_sets or old_cards:
        if old_sets!=[record] or old_cards!=cards:
            raise ValueError('Existing Galaxy identities differ; refusing overwrite')
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
        pricing_status='Unpriced',source_url=CHECKLIST_URL,notes='Official title, number and credits retained. '+
        (f"Artist credit: {evidence[(c['subsetCode'],c['number'])]['artist']}. " if evidence[(c['subsetCode'],c['number'])]['artist'] else 'Repeated signer rows combine only within autograph designs; buyback references retain the original year, series and number. ')+
        'No checklist identifiers are invented for sketches.') for c in cards]
    result['catalogue_variants']=variants
    aliases={name:name for name in SECTIONS}
    aliases.update({'BASE.':'BASE CARDS','TOPPS CHROME LAYERS ORIGINAL ART':'TOPPS CHROME LAYERS RALPH MCQUARRIE ORIGINAL CONCEPT ART','QUAD AUTOGRAPHS BOOK CARD':'QUAD AUTOGRAPHS'})
    rules=[]
    for i,row in enumerate(source['odds'],1):
        if row['label'].startswith('SKETCH CARDS') or row['label']=='BLANK CANVAS ART CARD':continue
        alias=next((a for a in sorted(aliases,key=len,reverse=True) if row['label'].lower()==a.lower() or row['label'].lower().startswith((a.lower()+' ',a.lower()+'-'))),None)
        if alias is None:raise ValueError('Unmapped odds label: '+row['label'])
        section=aliases[alias]
        ambiguous=row['label']=='TOPPS CHROME LAYERS ORIGINAL ART' and row['hobby']=='1:49,018'
        rules.append(dict(id=f'{SET_ID}-ODDS-{i:03d}',set_id=SET_ID,parallel_group=SECTIONS[section][0],
            applies_to=section,parallel='Unspecified edition (manufacturer label repeated)' if ambiguous else row['label'][len(alias):].lstrip(' -') or 'Base issue (label as printed)',serial_cap=None,serial_exact=None,
            exclusive_note=f"Manufacturer repeats the unsuffixed Layers label at {row['hobby']}; edition unresolved, not assumed to be Superfractor or base." if ambiguous else f"Hobby pack odds {row['hobby']}." if row['validRate'] else f"Manufacturer printed rate {row['hobby']} has a semicolon; unresolved and not interpreted.",numbering_note=f"Official odds PDF page {row['page']}; subset-level rule. Odds do not establish serial caps or subject inclusion in every parallel.",
            verification_status='Official subset label; edition unresolved' if ambiguous else 'Official Topps odds; subset rule only'))
    result['catalogue_parallel_rules']=rules
    result['catalogue_sources']=[dict(id=SET_ID+'-'+key,set_id=SET_ID,source='Topps',purpose=purpose,url=url,notes=notes)
        for key,purpose,url,notes in [('checklist','Checklist',CHECKLIST_URL,'11-page manufacturer PDF. Numbered McQuarrie and autograph buyback references are distinct designs. Two artist rosters do not create card identities.'),
            ('odds','Parallel applicability',ODDS_URL,'93 rows retained; 88 numbered-subset rules and five unenumerated sketch/Blank Canvas rows. Semicolon rate and repeated unsuffixed Layers label retained without guessing corrections. No serial caps inferred.'),
            ('product','Release date and product identity',PRODUCT_URL,'Manufacturer Available From December 10, 2025. Distinct set and IDs from 2026 Galaxy.')]]

    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--extract',type=Path);parser.add_argument('--verify-pdf',type=Path)
    args=parser.parse_args()
    if args.extract:
        source=normalize(args.extract);SOURCE.parent.mkdir(parents=True,exist_ok=True)
        SOURCE.write_text(json.dumps(source,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({'rows':sum(len(s['rows']) for s in source['subsets']),'artists':len(source['sketchArtists']),
              'counts':{s['name']:len({r['number'] for r in s['rows']}) for s in source['subsets']}}))
    else:
        if args.verify_pdf and normalize(args.verify_pdf)!=json.loads(SOURCE.read_text()):
            raise ValueError('Normalized evidence differs from manufacturer PDFs')
        record,cards,_=build();save_catalogue(apply(load_catalogue(),record,cards))
        print(json.dumps(dict(cards=len(cards),subsets=len(record['subsets']),rules=len(tables()['catalogue_parallel_rules']))))
