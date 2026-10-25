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
SOURCE = ROOT / 'sources/chrome-star-wars-galaxy-2026/checklist.json'
SET_ID = '2026-topps-chrome-star-wars-galaxy'
CHECKLIST_URL = 'https://cdn.shopify.com/s/files/1/0662/9749/5709/files/26SWCGCHECKLISTUPDATE.pdf?v=1786632392'
ODDS_URL = 'https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2026_Stars_Wars_Chrome_Galaxy.pdf?v=1786638023'
PRODUCT_URL = 'https://www.topps.com/products/2026-star-wars-chrome%C2%AE-galaxy-hobby-box'
SECTIONS = OrderedDict([
    ('BASE CARDS', ('BASE','Base')),
    ('DUEL ON CLOUD CITY', ('CLOUD','Insert')),
    ('ART OF ROGUE ONE', ('ARO','Insert')),
    ('ART OF THE DARK SIDE', ('ADS','Insert')),
    ('GALACTIC ANTHOLOGY', ('GA','Insert')),
    ('ART OF KNIGHTS OF THE REPUBLIC', ('KOTOR','Insert')),
    ('TOPPS CHROME LAYERS ORIGINAL ART', ('LAY','Insert')),
    ('COMICFRACTOR', ('VC','Insert')),
    ('ORIGINAL ART PUZZLE CARDS', ('PUZZLE','Insert')),
    ('FORCE ENERGY', ('FE','Insert')),
    ('GALAXY AUTOGRAPHS', ('AUTO','Autograph')),
    ('DUAL AUTOGRAPHS', ('DUAL','Autograph')),
    ('TRIPLE AUTOGRAPHS', ('TRIPLE','Autograph')),
    ('QUAD AUTOGRAPHS', ('QUAD','Autograph')),
])
EXPECTED_COUNTS = [100,15,15,15,15,15,11,5,36,10,62,10,9,5]


def extract_checklist(path):
    from pypdf import PdfReader
    pdf = PdfReader(path)
    if len(pdf.pages) != 17:
        raise ValueError('Expected 17 official checklist pages')
    sections, artists, section, pending = OrderedDict(), [], None, None
    for page_number, page in enumerate(pdf.pages,1):
        chunks = []
        def visit(text,*_):
            text=text.strip()
            # Nested Form XObject emits the overlaid GA-BDH cells twice in pypdf.
            if text and (not chunks or text!=chunks[-1]):chunks.append(text)
        page.extract_text(visitor_text=visit)
        for text in chunks:
            if text.startswith(('Checklists provided by Topps','actual contents and odds may vary.')):
                continue
            if pending is not None:
                pending['fields'].append(text)
                if len(pending['fields']) == 2:
                    first,second = pending.pop('fields')
                    autograph = SECTIONS[section][1] == 'Autograph'
                    pending.update(subject=second if autograph else first,
                                   signer=first if autograph else None,artist=None if autograph else second)
                    sections[section].append(pending)
                    pending = None
                continue
            if text in SECTIONS or text == 'SKETCH CARD ARTISTS':
                section = text
                if text in SECTIONS:
                    if text in sections:
                        raise ValueError('Repeated section heading')
                    sections[text] = []
                continue
            if text == 'INSERT':
                continue
            if section == 'SKETCH CARD ARTISTS':
                artists.append(dict(name=text,page=page_number))
            elif section in SECTIONS and re.fullmatch(r'[0-9]+|[A-Z0-9]+-[A-Z0-9-]+',text):
                pending = dict(number=text,page=page_number,fields=[])
            else:
                raise ValueError(f'Unclassified PDF text on page {page_number}: {text}')
    if pending or list(sections) != list(SECTIONS):
        raise ValueError('Incomplete checklist cells or sections')
    return [dict(name=k,rows=v) for k,v in sections.items()],artists


def normalize(directory):
    import pdfplumber
    subsets,artists = extract_checklist(directory/'checklist.pdf')
    odds=[]
    with pdfplumber.open(directory/'odds.pdf') as pdf:
        for page_number,page in enumerate(pdf.pages,1):
            for line in page.extract_text(layout=True).splitlines():
                match=re.fullmatch(r'\s*(.+?)\s+(\d[\d,]*:\d[\d,]*)\s*',line)
                if match:
                    odds.append(dict(label=match[1],hobby=match[2],page=page_number))
    if len(odds) != 110:
        raise ValueError(f'Unexpected odds count: {len(odds)}')
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
        if code=='BASE' and set(identities)!=set(map(str,range(1,101))):
            raise ValueError('Incomplete 100-card base set')
        for number,rows in identities.items():
            expected={'DUAL':2,'TRIPLE':3,'QUAD':4}.get(code,1)
            if len(rows)!=expected or len({(r['subject'],r['signer']) for r in rows})!=expected:
                raise ValueError(f'Unexpected repeated number {name} {number}')
            names=[f"{r['subject']} ({r['signer']})" if r['signer'] else r['subject'] for r in rows]
            card=dict(id=f'2026-TCSWG-{code}-{number}',setId=SET_ID,order=len(cards)+1,
                      number=number,name=' / '.join(names),subject2=' / '.join(names[1:]) or None,
                      category=category,subset=name,subsetCode=code,roster=None,rookie='No',parallelGroup=code)
            cards.append(card)
            variants.append(dict(id=card['id']+'-IDENTITY',set_id=SET_ID,card_id=card['id'],variant_order=len(variants)+1,
                subset=name,card_number=number,display_name=card['name'],parallel='Checklist identity',serial_cap=None,
                serial_exact=None,exclusive_note=None,numbering_note='Official checklist identity; no parallel grid or serial cap inferred.',
                verification_status='Official Topps checklist verified'))
        subsets.append(dict(category=category,name=name,code=code,count=len(identities)))
    record=dict(id=SET_ID,categoryId='star-wars',name='2026 Topps Chrome Star Wars Galaxy',shortName='Chrome Star Wars Galaxy',
                accent='#9778e6',year=2026,manufacturer='Topps',releaseDate='2026-08-12',cardCount=len(cards),
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
    catalogue['generatedAt']='2026-10-25T15:00:00Z'
    return catalogue


def tables():
    source=json.loads(SOURCE.read_text());record,cards,variants=build(source)
    evidence={(SECTIONS[s['name']][0],r['number']):r for s in source['subsets'] for r in s['rows']}
    result=OrderedDict()
    result['catalogue_sets']=[dict(id=SET_ID,name=record['name'],short_name=record['shortName'],year=2026,
        manufacturer='Topps',release_date=record['releaseDate'],source_file=CHECKLIST_URL,accent=record['accent'],
        card_count=len(cards),subset_count=len(record['subsets']),variant_count=len(variants))]
    result['catalogue_subsets']=[dict(set_id=SET_ID,subset_code=s['code'],category=s['category'],name=s['name'],
        card_count=s['count'],parallel_group=s['code'],source_url=CHECKLIST_URL) for s in record['subsets']]
    result['catalogue_cards']=[dict(id=c['id'],set_id=SET_ID,checklist_order=c['order'],category=c['category'],
        subset_code=c['subsetCode'],card_number=c['number'],display_name=c['name'],subject_1=c['name'].split(' / ')[0],
        subject_2=c['subject2'],roster=None,rookie=False,parallel_group=c['parallelGroup'],image_status='Missing',
        pricing_status='Unpriced',source_url=CHECKLIST_URL,notes='Official title, number and credits retained. '+
        (f"Artist credit: {evidence[(c['subsetCode'],c['number'])]['artist']}. " if c['category']!='Autograph' else 'Repeated signer rows combined into one identity. ')+
        'No checklist identifiers are invented for sketches.') for c in cards]
    result['catalogue_variants']=variants
    aliases={name.title():name for name in SECTIONS}
    aliases.update({'Art of Knights of the Old Republic':'ART OF KNIGHTS OF THE REPUBLIC',
                    'Chrome Layers Original Art':'TOPPS CHROME LAYERS ORIGINAL ART','Comic Fractor':'COMICFRACTOR'})
    rules=[]
    for i,row in enumerate(source['odds'],1):
        if row['label'].startswith('Sketch Cards '):continue
        alias=next((a for a in sorted(aliases,key=len,reverse=True) if row['label'].lower()==a.lower() or row['label'].lower().startswith(a.lower()+' ')),None)
        if alias is None:raise ValueError('Unmapped odds label: '+row['label'])
        section=aliases[alias]
        rules.append(dict(id=f'{SET_ID}-ODDS-{i:03d}',set_id=SET_ID,parallel_group=SECTIONS[section][0],
            applies_to=section,parallel=row['label'][len(alias):].strip() or 'Base issue',serial_cap=None,serial_exact=None,
            exclusive_note=f"Hobby pack odds {row['hobby']}.",numbering_note=f"Official odds PDF page {row['page']}; subset-level rule. Odds do not establish serial caps or subject inclusion in every parallel.",
            verification_status='Official Topps odds; subset rule only'))
    result['catalogue_parallel_rules']=rules
    result['catalogue_sources']=[dict(id=SET_ID+'-'+key,set_id=SET_ID,source='Topps',purpose=purpose,url=url,notes=notes)
        for key,purpose,url,notes in [('checklist','Checklist',CHECKLIST_URL,'Updated 17-page manufacturer PDF; numbered artwork and single/multi-signer autograph identities. Artist roster is not a card checklist.'),
            ('odds','Parallel applicability',ODDS_URL,'110 rows retained; 107 numbered-subset rules and three unenumerated sketch foil rules. No serial caps inferred.'),
            ('product','Release date and product identity',PRODUCT_URL,'Official product metadata: available August 12, 2026. Distinct from 2026 Chrome Star Wars.')]]
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
