"""Source manifests and shared additive import for the authorised three-set batch."""
import argparse
import hashlib
import json
import re
import subprocess
from collections import OrderedDict
from pathlib import Path
from catalogue_io import load_catalogue, save_catalogue

ROOT = Path(__file__).resolve().parents[1]
CDN = 'https://cdn.shopify.com/s/files/1/0662/9749/5709/files/'
CONFIGS = OrderedDict([
 ('black', dict(id='2024-topps-chrome-black-star-wars', prefix='2024-TSWCB',
  name='2024 Topps Chrome Black Star Wars', shortName='Chrome Black Star Wars 2024', accent='#a98cc7', date='2025-03-19', pages=9,
  checklist=CDN+'STW2448-CheckList_24SWCB_VERSION1.pdf?v=1787938579', odds=CDN+'2024StarWarsChromeBlackOdds.pdf?v=1787938579',
  product='https://www.topps.com/products/2024-topps-chrome-r-black-star-wars-hobby-box',
  sections=[('BASE CARDS','BASE','Base'),('ANIMATED SHORT PRINTS','SP','Insert'),('25 YEARS OF DARTH MAUL','DM','Insert'),
   ('EMBRACE THE DARKSIDE','ED','Insert'),('DEPTHS OF THE DARKSIDE','DD','Insert'),('GALACTIC FACTIONS','GL','Insert'),
   ('AUTOGRAPH LIGHT SIDE','ALS','Autograph'),('AUTOGRAPH DARK SIDE','ADS','Autograph'),
   ('DUALITY OF THE GALAXY AUTOGRAPHS','BFA','Autograph'),('DUAL AUTOGRAPHS','DA','Autograph'),('TRIPLE AUTOGRAPHS','TA','Autograph')],
  rosters=[], counts=[100,20,20,15,20,20,77,63,72,11,6])),
 ('high-tek', dict(id='2024-topps-star-wars-high-tek', prefix='2024-TSWHT',
  name='2024 Topps Star Wars High-Tek', shortName='Star Wars High-Tek 2024', accent='#6dbfc4', date='2025-01-08', pages=18,
  checklist=CDN+'STW2487-2024StarWarsHigh-TekChecklist.pdf', odds=CDN+'2024NYCCStarWarsHi-TekOdds.pdf',
  product='https://www.topps.com/products/2024-topps-star-wars-high-tek-hobby-box',
  guide='https://ripped.topps.com/how-to-collect-2024-topps-star-wars-high-tek-tiered-and-parallel-structure-base-set-product/',
  sections=[('BASE CARDS THRONE ROOM PATTERN','TR','Base'),('BASE CARDS HYPERSPACE PATTERN','HP','Base'),
   ('BASE CARDS IMPERIAL PATTERN','IM','Base'),('BASE CARDS LASER PATTERN','LA','Base'),('BASE CARDS REBEL PATTERN','RE','Base'),
   ('BASE CARDS DEATH STAR INTERIOR PATTERN','DSI','Base'),('BASE CARDS DEATH STAR EXTERIOR PATTERN','DSE','Base'),
   ('BLACK AND WHITE VARIATION','BW','Variation'),('WOOKIEE TEK','WT','Insert'),('SPECTACULAR SPECIES','SS','Insert'),
   ('SHADOW TEK','ST','Insert'),('FANTASTEK','FT','Insert'),('AUTOGRAPH CARDS','AUTO','Autograph'),
   ('DUAL AUTOGRAPH CARDS','DA','Autograph'),('DOUBLE SIDED DUAL AUTOGRAPHS','DS','Autograph'),
   ('BLACK AND WHITE AUTOGRAPH VARIATION','ABW','Autograph')], rosters=[], counts=[100]*7+[25,10,20,20,25,55,10,3,14])),
 ('galaxy', dict(id='2024-topps-chrome-star-wars-galaxy', prefix='2024-TSWG',
  name='2024 Topps Chrome Star Wars Galaxy', shortName='Chrome Star Wars Galaxy 2024', accent='#8d9ad9', date='2024-11-01', pages=9,
  checklist=CDN+'STW2458-CheckList_24SWCG.pdf', odds=CDN+'2024StarWarsGalaxyChromeOdds.pdf',
  product='https://ripped.topps.com/2024-topps-star-wars-galaxy-chrome-checklist-spotlight-product/',
  guide='https://ripped.topps.com/2024-topps-star-wars-galaxy-chrome-checklist-spotlight-product/',
  sections=[('BASE CARDS','BASE','Base'),('ART OF THE SITH','SITH','Insert'),('ART OF NABOO','NABOO','Insert'),
   ('PHANTOM MENACE 25TH ANNIVERSARY THE ART OF DARTH MAUL','MAUL','Insert'),('POWER OF THE DARKSIDE','PD','Insert'),
   ('GALACTIC EMPIRE ART','GE','Insert'),('ARMOR SHADOWBOX','ARMOR','Insert'),('ONE WITH THE FORCE','OF','Insert'),
   ('FIGURINE COMIC COVER VARIATION','VC','Insert'),('GALAXY AUTOGRAPHS','AUTO','Autograph'),
   ('DUAL AUTOGRAPHS','DA','Autograph'),('TRIPLE AUTOGRAPHS','TA','Autograph'),('QUAD AUTOGRAPHS','QA','Autograph')],
  rosters=['SKETCH CARD ARTISTS','BLANK CANVAS ART CARD ARTISTS/LucasFilm Animators'], counts=[100,10,15,15,15,15,15,5,5,56,6,4,4])),
])

def source_path(key):
    return ROOT / f'sources/star-wars-{key}-2024/checklist.json'

def extract(key, directory):
    from pypdf import PdfReader
    cfg = CONFIGS[key]
    sections = OrderedDict((name, []) for name, _, _ in cfg['sections'])
    roster = OrderedDict((name, []) for name in cfg['rosters'])
    pdf = PdfReader(directory / f'{key}-checklist.pdf')
    if len(pdf.pages) != cfg['pages']:
        raise ValueError('Unexpected page count')
    section, pending, events, seen = None, None, [], []
    def finish():
        nonlocal pending
        if pending is not None:
            sections[section].append(pending)
            pending = None
    for page_number, page in enumerate(pdf.pages, 1):
        chunks = []
        def visit(text, cm, tm, font, size):
            if text.strip():
                chunks.append((text.strip(), float(tm[4])))
        page.extract_text(visitor_text=visit)
        for text, x in chunks:
            if x > 0 and text in [*sections, *roster, 'BASE', 'INSERT', 'AUTOGRAPH', 'PACKAGING', 'SELL SHEET']:
                finish()
                events.append(text)
                section = text
                if text in sections:
                    seen.append(text)
            elif section in roster:
                roster[section].append(dict(name=text, page=page_number))
                events.append(text)
            elif section in sections and x > 0 and re.fullmatch(r'\d+|[A-Z]+-[A-Za-z0-9]+', text):
                finish()
                pending = dict(number=text, page=page_number, fields=[])
                events.append(text)
            elif pending is not None:
                pending['fields'].append(text)
                events.append(text)
            else:
                raise ValueError(f'Unclassified {key} source: {text}')
    finish()
    if seen != list(sections):
        raise ValueError('Section manifest changed')
    def whitespace(s):
        return re.sub(r'\s+', '', s)
    raw = subprocess.check_output(['pdftotext', '-raw', str(directory / f'{key}-checklist.pdf'), '-']).decode()
    if whitespace(raw) != whitespace(' '.join(events)):
        raise ValueError(key + ' independent Poppler reconciliation failed')
    return dict(checklistUrl=cfg['checklist'], oddsUrl=cfg['odds'], productUrl=cfg['product'],
                checklistSha256=hashlib.sha256((directory / f'{key}-checklist.pdf').read_bytes()).hexdigest(),
                oddsSha256=hashlib.sha256((directory / f'{key}-odds.pdf').read_bytes()).hexdigest(),
                subsets=[dict(name=k, rows=v) for k, v in sections.items()], rosters=roster,
                odds=extract_odds(key, directory), guideUrl=cfg.get('guide'), guideCaps=guide_caps(key))

def extract_odds(key, directory):
    import pdfplumber
    rows = []
    with pdfplumber.open(directory / f'{key}-odds.pdf') as pdf:
        for pn, page in enumerate(pdf.pages, 1):
            for line in page.extract_text(layout=True).splitlines():
                line = ' '.join(line.split())
                if not line or line.startswith(('2024 ', 'Card ')):
                    continue
                match = re.fullmatch(r"(.+?)\s+(1:[\d,]+|#'d to \d+)", line)
                if not match:
                    raise ValueError(f'Unparsed {key} odds: {line}')
                rows.append(dict(label=match[1], hobby=match[2], page=pn, rawLine=line))
    raw = subprocess.check_output(['pdftotext', '-layout', str(directory / f'{key}-odds.pdf'), '-']).decode()
    expected = []
    for line in raw.splitlines():
        line = ' '.join(line.split())
        if line and not line.startswith(('2024 ', 'Card ')):
            expected.append(line)
    if expected != [r['rawLine'] for r in rows]:
        raise ValueError('Independent odds reconciliation failed')
    return rows

def guide_caps(key):
    """Only editions explicitly named by the manufacturer's guide; never a per-card grid."""
    out = []
    def add(code, editions):
        out.extend(dict(code=code, parallel=p, cap=n) for p,n in editions)
    if key == 'high-tek':
        editions = [('GOLD FOIL',50),('ORANGE DIFFRACTOR',25),('GREEN DIFFRACTOR',10),('RED DIFFRACTOR',5),('BLACK DIFFRACTOR',1)]
        for code in ['TR','HP','IM','LA']: add(code,editions)
        add('RE',editions[2:])
        for code in ['DSI','DSE']: add(code,editions[1:])
    elif key == 'galaxy':
        editions = [('Aqua Refractor',199),('Aqua Lava Refractor',175),('Blue Refractor',150),
                    ('Wave Refractor',99),('Prism Refractor',75),('Mojo Refractor',50),('Orange Refractor',25),
                    ('X-Fractor',10),('Red Refractor',5),('Superfractor',1)]
        add('BASE',[editions[0],('Aqua Sonar Refractor',199),*editions[1:]])
        add('NABOO',editions)
        add('OF',[('Superfractor',1)])
        add('AUTO',[editions[3],editions[5],editions[6],editions[8],editions[9]])
        add('DA',[('Red Parallel',5),('Superfractor Parallel',1)])
        add('TA',[('Refractror',5),('Superfractor Parallel',1)])
        add('QA',[('Refractor',5),('Superfractor Parallel',1)])
    return out

def read_source(key):
    return json.loads(source_path(key).read_text())

def build(key, source=None):
    source = source or read_source(key); cfg = CONFIGS[key]
    if [s['name'] for s in source['subsets']] != [x[0] for x in cfg['sections']]:
        raise ValueError('Unexpected source manifest')
    cards, variants, subsets = [], [], []
    for section, (name, code, category), expected in zip(source['subsets'],cfg['sections'],cfg['counts']):
        groups = OrderedDict()
        for row in section['rows']:
            suffix = ''
            if key == 'black' and code == 'ALS' and row['number'] == 'ALS-KK':
                if row['fields'] not in [['Keira Knightley','Sabé'],['Katy Kartwheel','Rio Durant']]:
                    raise ValueError('Unrecognized ALS-KK subject')
                suffix = '-' + re.sub(r'[^A-Z0-9]+','-',row['fields'][0].upper()).strip('-')
            groups.setdefault((row['number'],suffix),[]).append(row)
        if len(groups) != expected:
            raise ValueError(f'Missing/extra identities in {key} {name}')
        if category == 'Base' and {n for n,_ in groups} != {str(i) for i in range(1,101)}:
            raise ValueError('Incomplete base numbering')
        for (number, suffix), rows in groups.items():
            people, artist, title = [], None, None
            expected_signers = {'DA':2,'TA':3,'QA':4,'DS':2}.get(code,1) if category == 'Autograph' else 1
            if category == 'Autograph':
                for row in rows:
                    f = row['fields']
                    if len(f) not in [2,4] or (len(f)==4 and key!='high-tek'):
                        raise ValueError('Unrecognized autograph cells')
                    people.extend(dict(subject=f[i+1],signer=f[i]) for i in range(0,len(f),2))
                if len(people) != expected_signers or len({(p['subject'],p['signer']) for p in people}) != len(people):
                    raise ValueError('Incorrect signer multiplicity')
                display = ' / '.join(f"{p['subject']} ({p['signer']})" for p in people)
            else:
                if len(rows)!=1: raise ValueError('Unexpected repeated printed design')
                f = rows[0]['fields']
                if key=='galaxy' and code=='BASE' and number=='93':
                    if f!=['Falcon','Rising','Mark Chilcott']: raise ValueError('Falcon Rising cells changed')
                    f = ['Falcon Rising','Mark Chilcott']
                expected_fields = 1 if (key=='black' and code in ['DD','GL']) or (key=='galaxy' and code in ['ARMOR','OF']) else 2
                if len(f)!=expected_fields: raise ValueError(f'Incorrect cells {key} {name} {number}')
                display = f[0]
                if len(f)>1:
                    if key=='galaxy': artist=f[1]
                    else: title=f[1]
            card = dict(id=f"{cfg['prefix']}-{code}-{number}{suffix}",setId=cfg['id'],order=len(cards)+1,
                        number=number,name=display,subject2=people[1]['subject'] if len(people)>1 else None,
                        category=category,subset=name,subsetCode=code,roster=artist or title,rookie='No',parallelGroup=code)
            cards.append(card)
            note = 'Official checklist identity; no subject/parallel grid inferred.'
            if suffix: note += ' Source repeats ALS-KK for two different signers; both retain the printed number with distinct internal subject suffixes.'
            variants.append(dict(id=card['id']+'-IDENTITY',set_id=cfg['id'],card_id=card['id'],variant_order=len(variants)+1,
                subset=name,card_number=number,display_name=display,parallel='Checklist identity',serial_cap=None,
                serial_exact=None,exclusive_note=None,numbering_note=note,verification_status='Official Topps checklist verified'))
        subsets.append(dict(category=category,name=name,code=code,count=len(groups)))
    record = dict(id=cfg['id'],categoryId='star-wars',name=cfg['name'],shortName=cfg['shortName'],accent=cfg['accent'],
                  year=2024,manufacturer='Topps',releaseDate=cfg['date'],cardCount=len(cards),subsetCount=len(subsets),subsets=subsets)
    return record,cards,variants

def apply(catalogue,key):
    record,cards,_ = build(key); sid=CONFIGS[key]['id']
    old_sets=[s for s in catalogue['sets'] if s['id']==sid];old_cards=[c for c in catalogue['cards'] if c['setId']==sid]
    if old_sets or old_cards:
        if old_sets!=[record] or old_cards!=cards: raise ValueError('Existing identities differ; refusing overwrite')
        return catalogue
    catalogue['sets'].append(record);catalogue['cards'].extend(cards);catalogue['generatedAt']='2026-10-26T00:00:00Z'
    return catalogue

def rules(key,source):
    cfg=CONFIGS[key]; manifest={name:code for name,code,_ in cfg['sections']}
    aliases={name:name for name in manifest}
    if key=='high-tek':
        aliases.update({'BLACK & WHITE VARIATION':'BLACK AND WHITE VARIATION','AUTOGRAPHS':'AUTOGRAPH CARDS',
            'DUAL AUTOGRAPHS':'DUAL AUTOGRAPH CARDS','DOUBLE-SIDED DUAL AUTOGRAPHS':'DOUBLE SIDED DUAL AUTOGRAPHS',
            'BLACK & WHITE AUTOGRAPH VARIATIONS':'BLACK AND WHITE AUTOGRAPH VARIATION',
            'BASE CARDS DEATH STAR INTERIOR':'BASE CARDS DEATH STAR INTERIOR PATTERN',
            'BASE CARDS DEATH STAR EXTERIOR':'BASE CARDS DEATH STAR EXTERIOR PATTERN'})
    elif key=='galaxy':
        aliases.update({'Base':'BASE CARDS','Art of the Naboo':'ART OF NABOO','Galactic Empire':'GALACTIC EMPIRE ART',
            'Phantom Menace 25th Annversary the Art of Darth Maul':'PHANTOM MENACE 25TH ANNIVERSARY THE ART OF DARTH MAUL',
            'FigurineComicCoverVariant':'FIGURINE COMIC COVER VARIATION','Dual':'DUAL AUTOGRAPHS',
            'Triple':'TRIPLE AUTOGRAPHS','Quad Autograph':'QUAD AUTOGRAPHS'})
    out=[];caps={(r['code'],r['parallel']):r['cap'] for r in source['guideCaps']};used=set()
    for i,row in enumerate(source['odds'],1):
        label=row['label']
        if (key=='high-tek' and (label=='BASE CARDS PATTERN' or label.startswith('SKETCH ART CARDS'))) or (key=='galaxy' and ('Sketch Card' in label or label=='Blank Canvas Art Card')):
            continue
        alias=next((a for a in sorted(aliases,key=len,reverse=True) if label.lower()==a.lower() or label.lower().startswith((a.lower()+' ',a.lower()+'-'))),None)
        if alias is None:raise ValueError('Unmapped odds '+label)
        name=aliases[alias];code=manifest[name];parallel=label[len(alias):].lstrip(' -') or 'Base issue'
        cp=parallel
        if key=='high-tek' and cp=='GOLD FOIL FOIL':cp='GOLD FOIL'
        cap=caps.get((code,cp))
        if cap is not None:used.add((code,cp))
        if key=='black' and code=='GL' and row['hobby']=="#'d to 99":cap=99
        out.append(dict(id=f"{cfg['id']}-ODDS-{i:03d}",set_id=cfg['id'],parallel_group=code,applies_to=name,
            parallel=parallel,serial_cap=cap,serial_exact=None,
            exclusive_note=('Official numbering '+row['hobby']+'.') if row['hobby'].startswith('#') else f"Hobby pack odds {row['hobby']}.",
            numbering_note=f"Official odds page {row['page']}, label: {label}. Subset rule only; no per-card applicability inferred."+
                (' Serial cap explicitly confirmed in the manufacturer guide.' if cap is not None and key!='black' else ''),
            verification_status='Official Topps odds and explicit numbering' if cap is not None else 'Official Topps odds; subset rule only'))
    for (code,parallel),cap in caps.items():
        if (code,parallel) in used:continue
        name=next(n for n,c,_ in cfg['sections'] if c==code)
        out.append(dict(id=f"{cfg['id']}-GUIDE-{code}-{len(out)+1:03d}",set_id=cfg['id'],parallel_group=code,
            applies_to=name,parallel=parallel,serial_cap=cap,serial_exact=None,exclusive_note=None,
            numbering_note='Explicit manufacturer-guide subset cap. No pack rate or subject-specific applicability inferred; printed guide edition spelling retained.',
            verification_status='Official Topps guide verified'))
    return out

def tables(key):
    cfg=CONFIGS[key];source=read_source(key);r,c,v=build(key,source);sid=cfg['id'];out=OrderedDict()
    out['catalogue_sets']=[dict(id=sid,name=r['name'],short_name=r['shortName'],year=2024,manufacturer='Topps',release_date=r['releaseDate'],
        source_file=cfg['checklist'],accent=r['accent'],card_count=len(c),subset_count=len(r['subsets']),variant_count=len(v))]
    out['catalogue_subsets']=[dict(set_id=sid,subset_code=x['code'],category=x['category'],name=x['name'],card_count=x['count'],
        parallel_group=x['code'],source_url=cfg['checklist']) for x in r['subsets']]
    out['catalogue_cards']=[dict(id=x['id'],set_id=sid,checklist_order=x['order'],category=x['category'],subset_code=x['subsetCode'],
        card_number=x['number'],display_name=x['name'],subject_1=x['name'].split(' / ')[0],subject_2=x['subject2'],roster=x['roster'],
        rookie=False,parallel_group=x['parallelGroup'],image_status='Missing',pricing_status='Unpriced',source_url=cfg['checklist'],
        notes='Manufacturer number, spelling and source context retained; multi-signer rows combine only within printed designs. '+
            ('ALS-KK is reused for Keira Knightley and Katy Kartwheel; subject-specific internal suffixes prevent identity collisions. ' if key=='black' and x['number']=='ALS-KK' else '')+
            'No unnumbered sketch identities or subject/parallel grids inferred.') for x in c]
    out['catalogue_variants']=v;out['catalogue_parallel_rules']=rules(key,source)
    urls=[('checklist','Checklist',cfg['checklist'],'All printed rows reconciled to independent Poppler extraction; source anomalies documented in batch audit.'),
          ('odds','Parallel applicability',cfg['odds'],'All odds rows retained in source evidence. Sketch rates and unresolved generic labels remain source-only; no inferred subject grids.'),
          ('product','Product identity, release date and guide',cfg['product'],'Official title year retained with actual release date; explicit guide caps are subset-level only.')]
    if cfg.get('guide') and cfg['guide']!=cfg['product']:urls.append(('guide','Explicit subset serial caps',cfg['guide'],'Seven base-pattern ladders explicitly confirmed; no autograph caps or per-card grids inferred.'))
    out['catalogue_sources']=[dict(id=sid+'-'+k,set_id=sid,source='Topps',purpose=p,url=u,notes=n) for k,p,u,n in urls]
    return out

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--extract', type=Path)
    parser.add_argument('--verify-pdf', type=Path)
    args = parser.parse_args()
    if args.extract:
        for key in CONFIGS:
            s = extract(key, args.extract)
            p = source_path(key); p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(s, ensure_ascii=False, indent=2) + '\n')
            print(key, [(x['name'], len(x['rows']), len({r['number'] for r in x['rows']}), sorted({len(r['fields']) for r in x['rows']})) for x in s['subsets']], 'rosters', {k:len(v) for k,v in s['rosters'].items()}, 'odds',len(s['odds']))
    else:
        catalogue=load_catalogue()
        for key in CONFIGS:
            if args.verify_pdf and extract(key,args.verify_pdf)!=read_source(key):raise ValueError('Source evidence changed')
            apply(catalogue,key)
            print(key,len(build(key)[1]),'cards',len(tables(key)['catalogue_parallel_rules']),'rules')
        save_catalogue(catalogue)
