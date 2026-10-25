#!/usr/bin/env python3
"""Import only identities and card-specific editions supported by Topps sources.

The normalized source retains every physical PDF row and page. Repeated signers
are combined by (subset, printed number), never by subject. The odds document
does not state serial caps or guarantee each subject in every parallel.
"""
import argparse
import hashlib
import json
import re
from collections import OrderedDict
from pathlib import Path

from catalogue_io import load_catalogue, save_catalogue

ROOT = Path(__file__).resolve().parents[1]
SET_ID = '2026-topps-stadium-club-wwe'
SOURCE = ROOT / 'sources/stadium-club-wwe-2026/checklist.json'
SUBSETS = OrderedDict([
    ('BASE CARDS', ('BASE', 'Base', 200)),
    ('CHROME BASE CARDS', ('CHROME', 'Base', 200)),
    ('BEAM TEAM', ('BT', 'Insert', 20)),
    ('INKED', ('INK', 'Insert', 25)),
    ('CONCENTRATION', ('C', 'Insert', 25)),
    ('THE AFTERMATH', ('AM', 'Insert', 25)),
    ('MAIN STAGE', ('MS', 'Insert', 25)),
    ('TRIUMVIRATES', ('TV', 'Insert', 60)),
    ('TRIUMVIRATES NICKNAME', ('TVN', 'Insert', 39)),
    ('BASE CARDS AUTOGRAPH VARIATION', ('SCA', 'Autograph', 91)),
    ('BASE CARDS CHROME AUTOGRAPH VARIATION', ('SCCA', 'Autograph', 89)),
    ('INKED AUTOGRAPHS', ('INKA', 'Autograph', 17)),
    ('THE AFTERMATH AUTOGRAPHS', ('AMA', 'Autograph', 18)),
    ('DUAL AUTOGRAPHS', ('DA', 'Autograph', 8)),
    ('MAIN STAGE AUTOGRAPHS', ('MSA', 'Autograph', 17)),
    ('ABSTRACT AUTOGRAPHS', ('AA', 'Autograph', 15)),
    ('CONCENTRATION AUTOGRAPHS', ('CA', 'Autograph', 14)),
    ('BASE CARDS AUTOGRAPH VARIATION II', ('SCA-II', 'Autograph', 24)),
    ('STONE COLD STEVE AUSTIN 30TH ANNIVERSARY AUTOGRAPHS', ('SCSA30', 'Autograph', 2)),
    ('DUDLEY BOYZ 30TH ANNIVERSARY AUTOGRAPHS', ('DB30', 'Autograph', 2)),
    ('CM PUNK 20TH ANNIVERSARY AUTOGRAPHS', ('CMP20', 'Autograph', 3)),
    ('THE ROCK 30TH ANNIVERSARY AUTOGRAPHS', ('TR30', 'Autograph', 2)),
    ('NWO 30TH ANNIVERSARY AUTOGRAPHS', ('NWO30', 'Autograph', 3)),
    ('LITA 25TH ANNIVERSARY AUTOGRAPHS', ('LITA25', 'Autograph', 3)),
    ('TRISH STRATUS 25TH ANNIVERSARY AUTOGRAPHS', ('TRISH25', 'Autograph', 3)),
])


def extract_pdf(path):
    """Text flow keeps overlapping subject/roster glyphs in authoring order."""
    import pdfplumber
    groups = OrderedDict()
    section = None
    with pdfplumber.open(path) as pdf:
        if len(pdf.pages) != 21:
            raise ValueError('Expected 21 manufacturer PDF pages')
        for page, sheet in enumerate(pdf.pages, 1):
            for line in sheet.extract_text(use_text_flow=True).splitlines():
                if line in ('BASE', 'INSERT', 'AUTOGRAPH') or line.startswith(('2026 Topps', 'Checklists provided')):
                    continue
                if not line.strip():
                    continue
                if line in SUBSETS:
                    section = line
                    groups[section] = []
                    continue
                match = re.fullmatch(r'([A-Z0-9-]+) (.+?)(Raw|Smackdown|NXT|Legend|WWE)(?: (Rookie))?', line)
                if not match or section is None:
                    raise ValueError(f'Unclassified PDF line on page {page}: {line}')
                groups[section].append(dict(number=match[1], subject=match[2].strip(),
                                           roster=match[3], rookie=bool(match[4]), page=page))
    return [dict(name=name, rows=rows) for name, rows in groups.items()]


def slug(value):
    return re.sub(r'[^A-Z0-9]+', '-', value.upper()).strip('-')


def build(source=None):
    source = source or json.loads(SOURCE.read_text())
    if [s['name'] for s in source['subsets']] != list(SUBSETS):
        raise ValueError('Manufacturer section list changed')
    cards, variants = [], []
    for section in source['subsets']:
        name = section['name']
        code, category, expected = SUBSETS[name]
        identities = OrderedDict()
        for row in section['rows']:
            identities.setdefault(row['number'], []).append(row)
        if len(identities) != expected:
            raise ValueError(f'Unexpected identity count for {name}')
        if code in ('BASE', 'CHROME') and set(identities) != set(map(str, range(1, 201))):
            raise ValueError('Base programme is incomplete')
        for number, rows in identities.items():
            if len(rows) != (2 if code == 'DA' else 1) or len({r['subject'] for r in rows}) != len(rows):
                raise ValueError(f'Unexpected duplicate row: {name} {number}')
            subjects = [r['subject'] for r in rows]
            card = dict(id=f'2026-TSCWWE-{code}-{number}', setId=SET_ID, order=len(cards) + 1,
                        number=number, name=' / '.join(subjects), subject2=' / '.join(subjects[1:]) or None,
                        category=category, subset=name, subsetCode=code,
                        roster=' / '.join(dict.fromkeys(r['roster'] for r in rows)),
                        rookie='Yes' if any(r['rookie'] for r in rows) else 'No', parallelGroup=code)
            cards.append(card)
            variants.append(dict(id=card['id'] + '-IDENTITY', set_id=SET_ID, card_id=card['id'],
                                 variant_order=len(variants) + 1, subset=name, card_number=number,
                                 display_name=card['name'], parallel='Checklist identity', serial_cap=None,
                                 serial_exact=None, exclusive_note=None,
                                 numbering_note='Checklist identity; no serial cap inferred.',
                                 verification_status='Official Topps checklist verified'))
    if len(cards) != 930 or sum(len(s['rows']) for s in source['subsets']) != 938:
        raise ValueError('Manufacturer row reconciliation failed')
    card_map = {(c['subset'], c['number']): c for c in cards}
    for edition in source['confirmedCardEditions']:
        c = card_map[(edition['subset'], edition['number'])]
        variants.append(dict(id=c['id'] + '-' + slug(edition['parallel']), set_id=SET_ID,
                             card_id=c['id'], variant_order=len(variants) + 1, subset=c['subset'],
                             card_number=c['number'], display_name=c['name'], parallel=edition['parallel'],
                             serial_cap=edition['serialCap'], serial_exact='1/1' if edition['serialCap'] == 1 else '/25',
                             exclusive_note=None, numbering_note='This card and edition explicitly illustrated/described in the Topps collector guide.',
                             verification_status='Official Topps collector guide verified'))
    record = dict(id=SET_ID, categoryId='wwe', name='2026 Topps Stadium Club WWE', shortName='Stadium Club WWE',
                  accent='#f97316', year=2026, manufacturer='Topps', releaseDate='2026-10-23',
                  cardCount=len(cards), subsetCount=len(SUBSETS),
                  subsets=[dict(category=v[1], name=k, code=v[0], count=v[2]) for k, v in SUBSETS.items()])
    return record, cards, variants


def apply(catalogue, record, cards):
    old_sets = [s for s in catalogue['sets'] if s['id'] == SET_ID]
    old_cards = [c for c in catalogue['cards'] if c['setId'] == SET_ID]
    if old_sets or old_cards:
        if old_sets != [record] or old_cards != cards:
            raise ValueError('Existing Stadium Club data differs; refusing overwrite')
        return catalogue
    catalogue['sets'].insert(0, record)
    catalogue['cards'] = cards + catalogue['cards']
    catalogue['generatedAt'] = '2026-10-24T10:00:00Z'
    return catalogue


def tables():
    """Database rows; odds are subset rules, never an assumed card/parallel cross product."""
    source = json.loads(SOURCE.read_text())
    record, cards, variants = build(source)
    result = OrderedDict()
    result['catalogue_sets'] = [dict(id=SET_ID, name=record['name'], short_name=record['shortName'],
        year=2026, manufacturer='Topps', release_date=record['releaseDate'], source_file=source['checklistUrl'],
        accent=record['accent'], card_count=930, subset_count=25, variant_count=len(variants))]
    result['catalogue_subsets'] = [dict(set_id=SET_ID, subset_code=code, category=category, name=name,
        card_count=count, parallel_group=code, source_url=source['checklistUrl'])
        for name, (code, category, count) in SUBSETS.items()]
    result['catalogue_cards'] = [dict(id=c['id'], set_id=SET_ID, checklist_order=c['order'], category=c['category'],
        subset_code=c['subsetCode'], card_number=c['number'], display_name=c['name'],
        subject_1=c['name'].split(' / ')[0], subject_2=c['subject2'], roster=c['roster'], rookie=c['rookie'] == 'Yes',
        parallel_group=c['parallelGroup'], image_status='Missing', pricing_status='Unpriced',
        source_url=source['checklistUrl'], notes='Official manufacturer checklist; repeated dual signers combined by printed card number.') for c in cards]
    result['catalogue_variants'] = variants
    # Map the odds sheet's marketing labels to exact checklist sections.
    aliases = {name.title(): name for name in SUBSETS}
    aliases.update({'Base': 'BASE CARDS', 'Chrome Base': 'CHROME BASE CARDS',
        'Base Card Autographs': 'BASE CARDS AUTOGRAPH VARIATION',
        'Base Chrome Autographs': 'BASE CARDS CHROME AUTOGRAPH VARIATION',
        'Base Card Autographs II': 'BASE CARDS AUTOGRAPH VARIATION II'})
    rules = []
    for index, row in enumerate(source['odds'], 1):
        if 111 <= index <= 115:
            continue  # Chrome II has odds but no checklist; its final two labels also omit "II".
        label = row['label']
        alias = next((a for a in sorted(aliases, key=len, reverse=True)
                      if label.lower() == a.lower() or label.lower().startswith(a.lower() + ' ')), None)
        if alias is None:
            raise ValueError(f'Unmapped odds label: {label}')
        name = aliases[alias]
        rules.append(dict(id=f'{SET_ID}-ODDS-{index:03d}', set_id=SET_ID,
            parallel_group=SUBSETS[name][0], applies_to=name, parallel=label[len(alias):].strip() or 'Base issue',
            serial_cap=None, serial_exact=None,
            exclusive_note=f"Pack odds: Hobby {row['hobby']}; Value {row['value']}; Mega {row['mega']}.",
            numbering_note=f"Official odds PDF page {row['page']}. Serial cap unspecified here; pack odds are not serial numbers. Subject inclusion is not guaranteed in every parallel.",
            verification_status='Official Topps odds; subset rule only'))
    result['catalogue_parallel_rules'] = rules
    result['catalogue_sources'] = [dict(id=SET_ID + '-' + key, set_id=SET_ID, source='Topps', purpose=purpose,
        url=source[url], notes=notes) for key, purpose, url, notes in [
        ('checklist', 'Checklist', 'checklistUrl', '938 source rows; 930 physical card identities; 25 subsets. Chrome autograph II missing from checklist.'),
        ('odds', 'Parallel applicability', 'oddsUrl', '122 odds rows retained in source; 117 mapped rules. Five Chrome II rows deferred. Pack odds do not establish serial caps.'),
        ('guide', 'Release and explicit numbered editions', 'guideUrl', 'Four card-specific numbered editions confirmed. Guide Chrome autograph Pearl White/Gold Minted language conflicts with odds; not generated.'),
    ]]
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-pdf', type=Path)
    args = parser.parse_args()
    if args.verify_pdf:
        source = json.loads(SOURCE.read_text())
        if hashlib.sha256(args.verify_pdf.read_bytes()).hexdigest() != source['checklistSha256']:
            raise ValueError('Manufacturer PDF changed; review source before import')
        if extract_pdf(args.verify_pdf) != source['subsets']:
            raise ValueError('Normalized rows differ from actual manufacturer PDF')
    record, cards, variants = build()
    save_catalogue(apply(load_catalogue(), record, cards))
    print(f'Validated {len(cards)} identities, 25 subsets, {len(variants)} identity/confirmed edition rows.')
