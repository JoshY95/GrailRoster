"""Classifications must be explicit and remain stable before any files change."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('category_io', ROOT / 'scripts/catalogue_io.py')
io = importlib.util.module_from_spec(spec)
spec.loader.exec_module(io)

with tempfile.TemporaryDirectory() as directory:
    io.DATA = Path(directory)
    io.INDEX = io.DATA / 'catalogue-index.json'
    payload = {'sets': [{'id': 'existing', 'categoryId': 'wwe', 'cardCount': 1}],
               'cards': [{'id': 'existing-1', 'setId': 'existing', 'number': '1'}]}
    io.save_catalogue(payload)
    baseline = {p: p.read_bytes() for p in io.DATA.rglob('*.json')}
    omitted = copy.deepcopy(payload)
    del omitted['sets'][0]['categoryId']
    io.save_catalogue(omitted)
    assert all(p.read_bytes() == data for p, data in baseline.items())
    for category in (None, 'unknown', 'marvel'):
        invalid = copy.deepcopy(payload)
        invalid['sets'][0]['categoryId'] = category
        try:
            io.save_catalogue(invalid)
            raise AssertionError('Invalid reclassification accepted')
        except ValueError:
            pass
        assert all(p.read_bytes() == data for p, data in baseline.items())
    unknown = copy.deepcopy(payload)
    unknown['sets'].append({'id': 'new', 'cardCount': 0})
    try:
        io.save_catalogue(unknown)
        raise AssertionError('Unclassified new set accepted')
    except ValueError:
        pass
    assert all(p.read_bytes() == data for p, data in baseline.items())
    unknown['sets'][-1]['categoryId'] = 'star-wars'
    io.save_catalogue(unknown)
    assert io.load_catalogue()['sets'][-1]['categoryId'] == 'star-wars'
    assert (io.DATA / 'sets/existing.json').read_bytes() == baseline[io.DATA / 'sets/existing.json']

print('PASS: category metadata retention, explicit new-set assignment, rejected reclassification before writes, and untouched existing card files.')
