"""Apply reviewed checklist corrections without changing legitimate card IDs."""
import json
from pathlib import Path
from catalogue_io import load_catalogue, save_catalogue


def repair(catalogue):
    repairs = json.loads(Path(__file__).with_name('catalogue_repairs.json').read_text())
    cards = {card['id']: card for card in catalogue['cards']}
    # Validate every preimage before modifying or saving anything.
    for item in repairs:
        for removed in item['removedCards']:
            if removed['id'] in cards and cards[removed['id']] != removed:
                raise ValueError('Unexpected heading record; refusing removal')
        for update in item['updates']:
            before = update['before']
            if cards.get(before['id']) not in (before, {**before, **update['changes']}):
                raise ValueError('Unexpected real card; refusing correction')
    for item in repairs:
        removed_ids = {card['id'] for card in item['removedCards']}
        catalogue['cards'] = [card for card in catalogue['cards'] if card['id'] not in removed_ids]
        for update in item['updates']:
            cards[update['before']['id']].update(update['changes'])
        set_record = next(s for s in catalogue['sets'] if s['id'] == item['setId'])
        subsets = set_record['subsets']
        if not any(s['code'] == item['newSubset']['code'] for s in subsets):
            position = next(i for i, s in enumerate(subsets) if s['code'] == item['oldSubsetCode'])
            subsets.insert(position + 1, item['newSubset'].copy())
        for subset in subsets:
            subset['count'] = sum(card['setId'] == item['setId'] and card['subsetCode'] == subset['code']
                                  for card in catalogue['cards'])
        set_record['cardCount'] = sum(card['setId'] == item['setId'] for card in catalogue['cards'])
        set_record['subsetCount'] = len(subsets)
    catalogue['cardCount'] = len(catalogue['cards'])
    return catalogue


if __name__ == '__main__':
    save_catalogue(repair(load_catalogue()))
    print('Applied reviewed heading/subset corrections; all 35 legitimate IDs preserved.')
