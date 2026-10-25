#!/usr/bin/env python3
"""Source-backed first Star Wars import; no inferred subjects or parallel grids."""
import argparse
import hashlib
import json
import re
from collections import OrderedDict
from pathlib import Path

from catalogue_io import load_catalogue, save_catalogue

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / 'sources/chrome-star-wars-2026'
SOURCE = DIRECTORY / 'checklist.json'
SET_ID = '2026-topps-chrome-star-wars'
CHECKLIST_URL = 'https://cdn.shopify.com/s/files/1/0662/9749/5709/files/CheckList_26SWCM4.pdf?v=1790785945'
ODDS_URL = 'https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2026-09-29_2026-Topps-Chrome-Star-Wars_Odds-2.pdf?v=1790777195'
GUIDE_URL = 'https://ripped.topps.com/2026-topps-chrome-star-wars-box-guide/'
SECTIONS = OrderedDict([
    ('CHARACTERS', ('BASE', 'Base')),
    ('CHARACTERS HOTHFRACTOR', ('HOTH', 'Insert')),
    ('CHARACTERS AUREBESH', ('AURE', 'Insert')),
    ('ANDOR SEASON 2 CHARACTERS', ('A2', 'Insert')),
    ('ANDOR SEASON 2 MOMENTS', ('AM', 'Insert')),
    ('VISIONS SEASON 3 CHARACTERS', ('V3', 'Insert')),
    ('VISIONS SEASON 3 MOMENTS', ('V3M', 'Insert')),
    ('MANDO AND GROGU CHARACTERS', ('MAGR', 'Insert')),
    ('MANDO AND GROGU MOMENTS', ('MAGM', 'Insert')),
    ('OBLIVION', ('O', 'Insert')),
    ('STORMTROOPER COMMAND', ('SC', 'Insert')),
    ('GALAXYS CUTEST', ('GC', 'Insert')),
    ('GALATIC MAXIMALISTS', ('GMAX', 'Insert')),
    ('FACTIONS', ('FACTIONS', 'Insert')),
    ('COSMIC CRYSTALS', ('COS', 'Insert')),
    ('BONUS STAGE', ('BO', 'Insert')),
    ('KYBER LIGHT', ('KL', 'Insert')),
    ('HIDDEN GEMS', ('HG', 'Insert')),
    ('ERAS', ('E', 'Insert')),
    ('REFLECTIONS', ('REF', 'Insert')),
    ('COMICFRACTOR', ('VC', 'Insert')),
    ('BASE PRINTING PLATE BOOK CARDS I', ('PLATE', 'Insert')),
    ('CHARACTERS AUTOGRAPHS', ('AUTO', 'Autograph')),
    ('ANDOR SEASON 2 CHARACTERS AUTOGRAPHS', ('A2A', 'Autograph')),
    ('MANDO AND GROGU CHARACTERS AUTOGRAPHS', ('MAGA', 'Autograph')),
    ('VISIONS SEASON 3 CHARACTERS AUTOGRAPHS', ('V3A', 'Autograph')),
    ('DUO AUTOGRAPHS', ('DUO', 'Autograph')),
    ('TRIPLE AUTOGRAPHS', ('TRIP', 'Autograph')),
])
# Hidden Gems has only Sapphire pack odds in the combined manufacturer document.
DEFERRED = {'HIDDEN GEMS'}
EXPECTED_COUNTS = [200,200,200,17,12,14,9,26,17,16,20,15,10,10,50,12,10,5,9,5,5,200,182,14,5,5,22,19]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_checklist(path):
    import pdfplumber
    def column(chars, left, right=1000):
        # Bold DEBUT glyphs overlap long normal-weight subjects in the PDF.
        selected = [c for c in chars if left <= c['x0'] < right and 'Bold' not in c['fontname']]
        text, end = '', None
        for char in selected:
            if end is not None and char['x0'] - end > 2:
                text += ' '
            text += char['text']
            end = char['x1']
        return text.strip()
    groups, artists, section = OrderedDict(), [], None
    with pdfplumber.open(path) as pdf:
        if len(pdf.pages) != 31:
            raise ValueError('Expected 31 checklist pages')
        for page_number, page in enumerate(pdf.pages, 1):
            for line in page.extract_text_lines():
                text = line['text'].strip()
                if text in ('BASE', 'INSERT', 'AUTOGRAPHS'):
                    continue
                if text in SECTIONS or text == 'SKETCH ARTISTS':
                    section = text
                    if text in SECTIONS:
                        groups[text] = []
                    continue
                if section == 'SKETCH ARTISTS':
                    artists.append(dict(name=text, page=page_number))
                    continue
                if text == 'DEBUT':
                    if not groups[section]:
                        raise ValueError('Unattached DEBUT flag')
                    groups[section][-1]['debut'] = True
                    continue
                number = column(line['chars'], 0, 129)
                if not re.fullmatch(r'[0-9]+|[A-Z0-9]+-[A-Z0-9-]+', number) or section not in SECTIONS:
                    raise ValueError(f'Unclassified page {page_number}: {text}')
                row = dict(number=number, subject=column(line['chars'],129), signer=None,
                           debut=any('Bold' in c['fontname'] for c in line['chars']), page=page_number)
                if SECTIONS[section][1] == 'Autograph':
                    # Column positions separate even the overlapping Henderson/Gatori glyphs.
                    row['signer'] = column(line['chars'],129,273)
                    row['subject'] = column(line['chars'],273)
                    if not row['signer'] or not row['subject']:
                        raise ValueError('Missing autograph signer/subject')
                row['subject'] = re.sub(r'\s*DEBUT$', '', row['subject']).strip()
                groups[section].append(row)
    if list(groups) != list(SECTIONS):
        raise ValueError('Checklist section order changed')
    return [dict(name=name, rows=rows) for name, rows in groups.items()], artists


def extract_odds(path):
    import pdfplumber
    rows = []
    with pdfplumber.open(path) as pdf:
        for page_number, page in enumerate(pdf.pages, 1):
            for line in page.extract_text(layout=True).splitlines():
                parts = re.split(r'\s{2,}', line.strip())
                if len(parts) == 5:
                    first = re.fullmatch(r'(.+) (\d[\d,]*:\d[\d,]*)', parts[0])
                    if first:
                        parts = [first[1],first[2],*parts[1:]]
                if len(parts) == 6 and re.fullmatch(r'(?:\d[\d,]*:\d[\d,]*|-)', parts[1]):
                    rows.append(dict(label=parts[0], hobby=parts[1], delight=parts[2], sapphire=parts[3],
                                     value=parts[4], superbox=parts[5], page=page_number))
                elif parts[0] == 'TRIO AUTOS PADPARADSCHA SAPPHIRE':
                    # Final Sapphire row spills four dash cells onto otherwise empty page 5.
                    if parts[1:] != ['1:3,035']:
                        raise ValueError('Unexpected last odds row')
                    rows.append(dict(label=parts[0], hobby='-', delight='-', sapphire='1:3,035',
                                     value='-', superbox='-', page=page_number))
    if len(rows) != 186:
        raise ValueError(f'Expected 186 odds rows, got {len(rows)}')
    return rows


def normalize():
    subsets, artists = extract_checklist(DIRECTORY / 'checklist.pdf')
    return dict(checklistUrl=CHECKLIST_URL, oddsUrl=ODDS_URL, guideUrl=GUIDE_URL,
                checklistSha256=digest(DIRECTORY / 'checklist.pdf'), oddsSha256=digest(DIRECTORY / 'odds.pdf'),
                subsets=subsets, sketchArtists=artists, odds=extract_odds(DIRECTORY / 'odds.pdf'))


def build(source=None):
    source = source or json.loads(SOURCE.read_text())
    cards, variants, subsets = [], [], []
    if [s['name'] for s in source['subsets']] != list(SECTIONS):
        raise ValueError('Unexpected source sections')
    for section, expected_count in zip(source['subsets'], EXPECTED_COUNTS):
        name = section['name']
        if name in DEFERRED:
            continue
        code, category = SECTIONS[name]
        identities = OrderedDict()
        for row in section['rows']:
            identities.setdefault(row['number'], []).append(row)
        if len(identities) != expected_count:
            raise ValueError(f'Unexpected identity count for {name}')
        if code == 'BASE' and set(identities) != set(map(str,range(1,201))):
            raise ValueError('Incomplete base checklist')
        for number, rows in identities.items():
            expected = 2 if code == 'DUO' else 3 if code == 'TRIP' else 1
            if len(rows) != expected or len({(r['subject'], r['signer']) for r in rows}) != expected:
                raise ValueError(f'Unexpected identity duplication: {name} {number}')
            names = [f"{r['subject']} ({r['signer']})" if r['signer'] else r['subject'] for r in rows]
            card = dict(id=f'2026-TCSW-{code}-{number}', setId=SET_ID, order=len(cards)+1,
                        number=number, name=' / '.join(names), subject2=' / '.join(names[1:]) or None,
                        category=category, subset=name, subsetCode=code, roster=None, rookie='No', parallelGroup=code)
            cards.append(card)
            variants.append(dict(id=card['id']+'-IDENTITY', set_id=SET_ID, card_id=card['id'],
                variant_order=len(variants)+1, subset=name, card_number=number, display_name=card['name'],
                parallel='Checklist identity', serial_cap=None, serial_exact=None, exclusive_note=None,
                numbering_note='Official checklist identity; no serial cap or parallel availability inferred.',
                verification_status='Official Topps checklist verified'))
        subsets.append(dict(category=category, name=name, code=code, count=len(identities)))
    if len(cards) != 1304:
        raise ValueError('Unexpected Chrome identity total')
    record = dict(id=SET_ID, categoryId='star-wars', name='2026 Topps Chrome Star Wars', shortName='Chrome Star Wars',
                  accent='#e5bd59', year=2026, manufacturer='Topps', releaseDate='2026-09-30',
                  cardCount=len(cards), subsetCount=len(subsets), subsets=subsets)
    return record, cards, variants


def apply(catalogue, record, cards):
    old_sets = [s for s in catalogue['sets'] if s['id'] == SET_ID]
    old_cards = [c for c in catalogue['cards'] if c['setId'] == SET_ID]
    if old_sets or old_cards:
        if old_sets != [record] or old_cards != cards:
            raise ValueError('Existing Star Wars data differs; refusing overwrite')
        return catalogue
    # Retain the current global ordering; the UI sorts within each franchise.
    catalogue['sets'].append(record)
    catalogue['cards'].extend(cards)
    catalogue['generatedAt'] = '2026-10-25T14:00:00Z'
    return catalogue


def tables():
    source = json.loads(SOURCE.read_text())
    record, cards, variants = build(source)
    result = OrderedDict()
    result['catalogue_sets'] = [dict(id=SET_ID, name=record['name'], short_name=record['shortName'],
        year=2026, manufacturer='Topps', release_date=record['releaseDate'], source_file=CHECKLIST_URL,
        accent=record['accent'], card_count=len(cards), subset_count=len(record['subsets']), variant_count=len(variants))]
    result['catalogue_subsets'] = [dict(set_id=SET_ID, subset_code=s['code'], category=s['category'], name=s['name'],
        card_count=s['count'], parallel_group=s['code'], source_url=CHECKLIST_URL) for s in record['subsets']]
    result['catalogue_cards'] = [dict(id=c['id'], set_id=SET_ID, checklist_order=c['order'], category=c['category'],
        subset_code=c['subsetCode'], card_number=c['number'], display_name=c['name'], subject_1=c['name'].split(' / ')[0],
        subject_2=c['subject2'], roster=None, rookie=False, parallel_group=c['parallelGroup'], image_status='Missing',
        pricing_status='Unpriced', source_url=CHECKLIST_URL,
        notes='Manufacturer spelling/numbers retained, including apparent errors. DEBUT does not imply a sports rookie. Multiple signer rows share one card identity.') for c in cards]
    result['catalogue_variants'] = variants
    aliases = {name: name for name in SECTIONS if name not in DEFERRED}
    aliases.update({'CHARACTERS AUTOGRAPH':'CHARACTERS AUTOGRAPHS',
        'ANDOR SEASON 2 CHARACTERS AUTOGRAPH':'ANDOR SEASON 2 CHARACTERS AUTOGRAPHS',
        'MANDO & GROGU CHARACTERS AUTOGRAPH':'MANDO AND GROGU CHARACTERS AUTOGRAPHS',
        'MANDO & GROGU CHARACTERS':'MANDO AND GROGU CHARACTERS',
        'MANDO & GROGU MOMENTS':'MANDO AND GROGU MOMENTS',
        'VISIONS SEASON 3 CHARACTERS AUTOGRAPH':'VISIONS SEASON 3 CHARACTERS AUTOGRAPHS',
        'GALACTIC MAXIMALISTS':'GALATIC MAXIMALISTS', "THE GALAXY'S CUTEST":'GALAXYS CUTEST',
        'PRINTING PLATE BOOK CARD':'BASE PRINTING PLATE BOOK CARDS I',
        'DUO AUTOS':'DUO AUTOGRAPHS', 'TRIO AUTOS':'TRIPLE AUTOGRAPHS',
        'CHARACTERS HOTH FROZENFRACTOR':'CHARACTERS HOTHFRACTOR'})
    rules = []
    for i, row in enumerate(source['odds'], 1):
        # Combined odds include a separately sold Sapphire set and unenumerated designs/sketches.
        if all(row[key] == '-' for key in ('hobby','delight','value','superbox')):
            continue
        label = row['label']
        if label.startswith(('CHARACTERS DESIGN VARIATION', 'SKETCH CARDS')):
            continue
        alias = next((a for a in sorted(aliases, key=len, reverse=True) if label == a or label.startswith(a+' ')), None)
        if alias is None:
            raise ValueError('Unmapped odds label: '+label)
        name = aliases[alias]
        parallel = label[len(alias):].strip() or 'Base issue'
        # Only the guide explicitly specifies /77, at subset level. No card grid is generated.
        cap = 77 if label == 'CHARACTERS SW LOGOFRACTOR' else None
        rules.append(dict(id=f'{SET_ID}-ODDS-{i:03d}', set_id=SET_ID, parallel_group=SECTIONS[name][0],
            applies_to=name, parallel=parallel, serial_cap=cap, serial_exact='/77' if cap else None,
            exclusive_note=f"Pack odds: Hobby {row['hobby']}; Delight {row['delight']}; Value {row['value']}; Superbox {row['superbox']}.",
            numbering_note=f"Official odds PDF page {row['page']}; subset rule only. Subject inclusion is not guaranteed in every parallel." + (' Topps box guide explicitly states Logofractor /77.' if cap else ' Pack odds do not establish serial caps.'),
            verification_status='Official Topps odds/guide; subset rule only'))
    result['catalogue_parallel_rules'] = rules
    result['catalogue_sources'] = [dict(id=SET_ID+'-'+key, set_id=SET_ID, source='Topps', purpose=purpose, url=url, notes=notes)
        for key,purpose,url,notes in [
            ('checklist','Checklist',CHECKLIST_URL,'31 pages; preserve printed identifiers and combine repeated multi-signer rows. Hidden Gems is Sapphire-only in the combined odds and deferred.'),
            ('odds','Parallel applicability',ODDS_URL,'186 rows retained, including the final split-page Trio Sapphire row. Sapphire-only rows, unenumerated Superbox design subjects and sketch artist roster excluded from imported card identities.'),
            ('guide','Release and format verification',GUIDE_URL,'Street date September 30, 2026. Four box formats belong to Chrome; Sapphire remains a separate product. Logofractor /77 is a subset rule, not guaranteed per subject.')]]
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--extract', action='store_true')
    parser.add_argument('--verify-pdf', action='store_true')
    args = parser.parse_args()
    if args.extract:
        SOURCE.write_text(json.dumps(normalize(), ensure_ascii=False, indent=2)+'\n')
    if args.verify_pdf and normalize() != json.loads(SOURCE.read_text()):
        raise ValueError('Normalized source does not match manufacturer PDFs')
    record, cards, variants = build()
    save_catalogue(apply(load_catalogue(), record, cards))
    print(json.dumps(dict(cards=len(cards), subsets=len(record['subsets']), variants=len(variants),
                         rules=len(tables()['catalogue_parallel_rules']), sections=record['subsets'])))
