#!/usr/bin/env python3
"""Import printed Galactic Antiquities designs without inferring trilogy/design mappings."""
import argparse
import hashlib
import json
import re
import subprocess
from collections import OrderedDict
from pathlib import Path

from catalogue_io import load_catalogue, save_catalogue

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'sources/star-wars-galactic-antiquities-2024/checklist.json'
SET_ID = '2024-topps-star-wars-galactic-antiquities'
CHECKLIST_URL = 'https://cdn.shopify.com/s/files/1/0662/9749/5709/files/STW2384-2024StarWarsGalacticAntiquitiesChecklist.pdf?v=1787936593'
ODDS_URL = 'https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2024StarWarsGalacticAntiquitiesOdds_d1b92e48-e844-45cf-8291-80b194aa931a.pdf?v=1787936593'
PRODUCT_URL = 'https://www.topps.com/products/2024-topps-star-wars-galactic-antiquities'
SECTIONS = OrderedDict([
    ('CHARACTERS', ('BASE', 'Base')),
    ('METAL CHARACTERS', ('METAL', 'Base')),
    ('PREQUEL TRILOGY AUTOGRAPHS', ('PTA', 'Autograph')),
    ('ORIGINAL TRILOGY AUTOGRAPHS', ('OTA', 'Autograph')),
    ('SEQUEL TRILOGY AUTOGRAPHS', ('STA', 'Autograph')),
    ('FRAMED AUTOGRAPHS', ('FA', 'Autograph')),
    ('AUTOGRAPH BOOK CARD', ('BC', 'Autograph')),
    ('WOOD AUTOGRAPHS', ('WA', 'Autograph')),
    ('BESKAR METAL AUTOGRAPHS', ('MA', 'Autograph')),
    ('1977 STAR WARS SERIES 1 TRIBUTE AUTOGRAPHS', ('TA', 'Autograph')),
])
EXPECTED_COUNTS = [60, 30, 8, 8, 10, 11, 2, 11, 8, 17]
ARTISTS = 'OVERSIZED ORIGINAL ART CARD'


def extract_checklist(path):
    from pypdf import PdfReader
    pdf = PdfReader(path)
    if len(pdf.pages) != 5:
        raise ValueError('Expected five checklist pages')
    sections, artists, section, pending = OrderedDict(), [], None, None

    def finish():
        nonlocal pending
        if pending is None:
            return
        fields = pending.pop('fields')
        if len(fields) != 2:
            raise ValueError(f'Unexpected cells in {section}: {fields}')
        base = SECTIONS[section][1] == 'Base'
        pending.update(subject=fields[0] if base else fields[1],
                       signer=None if base else fields[0],
                       title=fields[1] if base else None, sourceFields=fields)
        sections[section].append(pending)
        pending = None

    for page_number, page in enumerate(pdf.pages, 1):
        chunks = []

        def visit(text, cm, tm, font, size):
            if text.strip():
                chunks.append((text.strip(), float(tm[4])))

        page.extract_text(visitor_text=visit)
        for text, x in chunks:
            if x > 0 and text in [*SECTIONS, ARTISTS, 'BASE', 'AUTOGRAPH']:
                finish()
                section = text
                if text in SECTIONS:
                    if text in sections:
                        raise ValueError('Repeated section heading')
                    sections[text] = []
            elif section == ARTISTS:
                artists.append(dict(name=text, page=page_number))
            elif section in SECTIONS and x > 0 and re.fullmatch(r'\d+|[A-Z]+-[A-Za-z0-9]+', text):
                finish()
                pending = dict(number=text, page=page_number, fields=[])
            elif pending is not None:
                pending['fields'].append(text)
            else:
                raise ValueError('Unclassified checklist text: ' + text)
    finish()
    if list(sections) != list(SECTIONS) or len(artists) != 47:
        raise ValueError('Checklist manifest changed')
    return [dict(name=k, rows=v) for k, v in sections.items()], artists


def normalize(directory):
    from pypdf import PdfReader
    subsets, artists = extract_checklist(directory / 'checklist.pdf')
    pdf = PdfReader(directory / 'odds.pdf')
    if len(pdf.pages) != 4:
        raise ValueError('Expected four odds pages: labels then corresponding rates')
    pages = [[line.strip() for line in page.extract_text().splitlines() if line.strip()]
             for page in pdf.pages]
    if pages[0].pop(0) != 'CARD' or pages[2].pop(0) != 'HOBBY':
        raise ValueError('Unexpected odds headers')
    labels, rates = pages[0] + pages[1], pages[2] + pages[3]
    if len(labels) != 47 or len(rates) != 47 or any(not re.fullmatch(r'1:[\d,]+', x) for x in rates):
        raise ValueError('Odds columns do not reconcile')
    odds = [dict(label=label, hobby=rate, labelPage=1 if i < 46 else 2,
                 ratePage=3 if i < 46 else 4)
            for i, (label, rate) in enumerate(zip(labels, rates))]
    source = dict(checklistUrl=CHECKLIST_URL, oddsUrl=ODDS_URL, productUrl=PRODUCT_URL,
                  checklistSha256=hashlib.sha256((directory / 'checklist.pdf').read_bytes()).hexdigest(),
                  oddsSha256=hashlib.sha256((directory / 'odds.pdf').read_bytes()).hexdigest(),
                  subsets=subsets, sketchArtists=artists, odds=odds)
    verify_poppler(directory, source)
    return source


def verify_poppler(directory, source):
    """Independent extraction must match every source field in order; whitespace only."""
    def lines(name):
        raw = subprocess.check_output(['pdftotext', '-layout', str(directory / (name + '.pdf')), '-']).decode()
        return [' '.join(x.split()) for x in raw.splitlines() if x.strip()]
    expected = ['BASE']
    for section in source['subsets']:
        if section['name'] == 'PREQUEL TRILOGY AUTOGRAPHS':
            expected.append('AUTOGRAPH')
        expected.append(section['name'])
        expected.extend(' '.join([r['number'], *r['sourceFields']]) for r in section['rows'])
    expected += [ARTISTS] + [r['name'] for r in source['sketchArtists']]
    if ' '.join(lines('checklist')) != ' '.join(expected):
        raise ValueError('Poppler checklist reconciliation failed')
    expected = ['CARD'] + [r['label'] for r in source['odds']] + ['HOBBY'] + [r['hobby'] for r in source['odds']]
    if lines('odds') != expected:
        raise ValueError('Poppler odds reconciliation failed')


def build(source=None):
    source = source or json.loads(SOURCE.read_text())
    if [s['name'] for s in source['subsets']] != list(SECTIONS):
        raise ValueError('Unexpected section manifest')
    cards, variants, subsets = [], [], []
    for section, expected in zip(source['subsets'], EXPECTED_COUNTS):
        name = section['name']
        code, category = SECTIONS[name]
        groups = OrderedDict()
        for row in section['rows']:
            groups.setdefault(row['number'], []).append(row)
        if len(groups) != expected or any(len(rows) != (7 if code == 'BC' else 1) for rows in groups.values()):
            raise ValueError('Missing or repeated source number in ' + name)
        if category == 'Base' and set(groups) != {str(i) for i in range(1, expected + 1)}:
            raise ValueError('Incomplete base numbering')
        if code == 'BC' and set(groups) != {'BC-O', 'BC-X'}:
            raise ValueError('Book identities changed')
        for number, rows in groups.items():
            display = ' / '.join(f"{r['subject']} ({r['signer']})" if r['signer'] else r['subject'] for r in rows)
            card = dict(id=f'2024-TSWGA-{code}-{number}', setId=SET_ID, order=len(cards) + 1,
                        number=number, name=display, subject2=rows[1]['subject'] if len(rows) > 1 else None,
                        category=category, subset=name, subsetCode=code, roster=rows[0]['title'],
                        rookie='No', parallelGroup=code)
            cards.append(card)
            variants.append(dict(id=card['id'] + '-IDENTITY', set_id=SET_ID, card_id=card['id'],
                                 variant_order=len(variants) + 1, subset=name, card_number=number,
                                 display_name=display, parallel='Checklist identity', serial_cap=None,
                                 serial_exact=None, exclusive_note=None,
                                 numbering_note='Official numbered design; repeated book rows combine signers. No inferred serial caps or subject/parallel grids.',
                                 verification_status='Official Topps checklist verified'))
        subsets.append(dict(category=category, name=name, code=code, count=len(groups)))
    record = dict(id=SET_ID, categoryId='star-wars', name='2024 Topps Star Wars Galactic Antiquities',
                  shortName='Galactic Antiquities 2024', accent='#bd9760', year=2024, manufacturer='Topps',
                  releaseDate='2025-02-05', cardCount=len(cards), subsetCount=len(subsets), subsets=subsets)
    return record, cards, variants


def apply(catalogue, record, cards):
    old_sets = [s for s in catalogue['sets'] if s['id'] == SET_ID]
    old_cards = [c for c in catalogue['cards'] if c['setId'] == SET_ID]
    if old_sets or old_cards:
        if old_sets != [record] or old_cards != cards:
            raise ValueError('Existing Galactic Antiquities identities differ; refusing overwrite')
        return catalogue
    catalogue['sets'].append(record)
    catalogue['cards'].extend(cards)
    catalogue['generatedAt'] = '2026-10-26T00:00:00Z'
    return catalogue


def tables():
    source = json.loads(SOURCE.read_text())
    record, cards, variants = build(source)
    result = OrderedDict()
    result['catalogue_sets'] = [dict(id=SET_ID, name=record['name'], short_name=record['shortName'], year=2024,
        manufacturer='Topps', release_date=record['releaseDate'], source_file=CHECKLIST_URL, accent=record['accent'],
        card_count=len(cards), subset_count=len(record['subsets']), variant_count=len(variants))]
    result['catalogue_subsets'] = [dict(set_id=SET_ID, subset_code=s['code'], category=s['category'], name=s['name'],
        card_count=s['count'], parallel_group=s['code'], source_url=CHECKLIST_URL) for s in record['subsets']]
    result['catalogue_cards'] = [dict(id=c['id'], set_id=SET_ID, checklist_order=c['order'], category=c['category'],
        subset_code=c['subsetCode'], card_number=c['number'], display_name=c['name'], subject_1=c['name'].split(' / ')[0],
        subject_2=c['subject2'], roster=c['roster'], rookie=False, parallel_group=c['parallelGroup'], image_status='Missing',
        pricing_status='Unpriced', source_url=CHECKLIST_URL,
        notes='Official printed heading, subject, signer and number retained, including unexpected trilogy groupings. Base screen titles retained in roster. Books combine seven signers per printed design; artist roster does not create sketch identities.') for c in cards]
    result['catalogue_variants'] = variants
    aliases = {name: name for name in list(SECTIONS)[5:]}
    aliases.update({'BASE CARDS CHARACTERS': 'CHARACTERS', 'METAL BASE CARDS CHARACTERS': 'METAL CHARACTERS'})
    rules = []
    for i, row in enumerate(source['odds'], 1):
        label = row['label']
        if re.match(r'AUTOGRAPHS [ABC] DESIGN(?: |$)', label) or label == 'OVERSIZED ORIGINAL ART SKETCH CARD':
            continue  # Manufacturer never maps A/B/C labels to the trilogy checklist headings.
        alias = next((a for a in sorted(aliases, key=len, reverse=True) if label == a or label.startswith(a + ' ')), None)
        if alias is None:
            raise ValueError('Unmapped odds label: ' + label)
        name = aliases[alias]
        rules.append(dict(id=f'{SET_ID}-ODDS-{i:03d}', set_id=SET_ID, parallel_group=SECTIONS[name][0], applies_to=name,
            parallel=label[len(alias):].strip() or 'Base issue', serial_cap=None, serial_exact=None,
            exclusive_note=f"Hobby pack odds {row['hobby']}.",
            numbering_note=f"Official odds label page {row['labelPage']}, corresponding rate page {row['ratePage']}; matched by ordered rows. Subset rule only; no serial caps or subject/parallel grids inferred.",
            verification_status='Official Topps odds; subset rule only'))
    result['catalogue_parallel_rules'] = rules
    result['catalogue_sources'] = [dict(id=SET_ID + '-' + key, set_id=SET_ID, source='Topps', purpose=purpose, url=url, notes=notes)
        for key, purpose, url, notes in [
            ('checklist', 'Checklist', CHECKLIST_URL, 'Five pages; 177 subject/signer rows produce 165 identities. 60 Characters and 30 Metal Characters have independent numbering. Two seven-signer books. Unexpected trilogy headings preserved. 47 artists remain a roster.'),
            ('odds', 'Parallel applicability', ODDS_URL, '47 labels on pages 1-2 paired with 47 corresponding rates on pages 3-4. 31 rules; 15 A/B/C design rows retained source-only because mapping to trilogy headings is unverified, plus one sketch rate. No inferred serial caps.'),
            ('product', 'Release date and product identity', PRODUCT_URL, 'Official 2024 title; Available From February 5, 2025. Generic Product Year 2025 is not a separate product.')]]
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--extract', type=Path)
    parser.add_argument('--verify-pdf', type=Path)
    args = parser.parse_args()
    if args.extract:
        source = normalize(args.extract)
        SOURCE.parent.mkdir(parents=True, exist_ok=True)
        SOURCE.write_text(json.dumps(source, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps(dict(rows=sum(len(s['rows']) for s in source['subsets']), artists=len(source['sketchArtists']), odds=len(source['odds']))))
    else:
        if args.verify_pdf and normalize(args.verify_pdf) != json.loads(SOURCE.read_text()):
            raise ValueError('Normalized manufacturer evidence changed')
        record, cards, _ = build()
        save_catalogue(apply(load_catalogue(), record, cards))
        print(json.dumps(dict(cards=len(cards), subsets=len(record['subsets']), rules=len(tables()['catalogue_parallel_rules']))))
