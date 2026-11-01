"""HH01 source scope, stable-ID preservation and split-catalogue checks."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from catalogue_io import load_catalogue
from prepare_hh01_import import generate

BASE = '32be1877e9d5825d38a83a074c79a4dc53498725'
def old(path):
    return subprocess.check_output(['git','show',f'{BASE}:{path}'], cwd=ROOT)

cat = load_catalogue()
prior = json.loads(old('data/catalogue-index.json'))
sid = '2026-topps-now-wwe'
for s in prior['sets']:
    path = 'data/'+s['file']
    if s['id'] != sid:
        assert (ROOT/path).read_bytes() == old(path), s['id']
    else:
        before = json.loads(old(path))['cards']
        after = [c for c in cat['cards'] if c['setId']==sid]
        assert after[:-1] == before
        assert len(after)==133 and after[-1]['number']=='HH01'
        assert after[-1]['id']=='2026-TNWWE-POSTER-HH01'
        assert after[-1]['name']=='Halloween Havoc'
        assert after[-1]['subsetCode']=='POSTER' and after[-1]['order']==133
        current = next(x for x in cat['sets'] if x['id']==sid)
        assert current['cardCount']==133
        assert next(x for x in current['subsets'] if x['code']=='POSTER')['count']==15
assert (ROOT/'data/catalogue.json').read_bytes()==old('data/catalogue.json')
assert cat['cardCount']==25286
source=json.loads((ROOT/'sources/topps-now-2025-2026/2026-11-02-hh01.json').read_text())
assert source['printRun'] is None and source['releaseDate']=='2026-10-30'
assert [(x['parallel'],x['serialCap']) for x in source['publishedEditions']]==[
    ('Base',None),('Rainbow Foil Short Print',None),('Gold Super Short Print',26)]
sql=generate()
assert sql==(ROOT/'supabase/corrections/2026-11-02-now-hh01.sql').read_text()
assert 'update public.collection_items' not in sql and 'insert into public.collection_items' not in sql
print('PASS: HH01 identity/source/editions, all prior cards and unrelated files preserved, exact guarded SQL.')
