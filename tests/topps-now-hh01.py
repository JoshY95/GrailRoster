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
additions = json.loads((ROOT/'sources/topps-now-2025-2026/2026-11-05-now.json').read_text())
assert [c['number'] for c in additions] == ['113','117','118']
for s in prior['sets']:
    path = 'data/'+s['file']
    expected_metadata = {k:v for k,v in s.items() if k!='file'}
    if s['id']==sid:
        expected_metadata['cardCount'] += 2 + len(additions)
        next(x for x in expected_metadata['subsets'] if x['code']=='BASE')['count'] += len(additions)
        next(x for x in expected_metadata['subsets'] if x['code']=='POSTER')['count'] += 2
    assert next(x for x in cat['sets'] if x['id']==s['id']) == expected_metadata
    if s['id'] != sid:
        assert (ROOT/path).read_bytes() == old(path), s['id']
    else:
        before = json.loads(old(path))['cards']
        after = [c for c in cat['cards'] if c['setId']==sid]
        assert after[:len(before)] == before
        hh01 = after[len(before)]
        appended = after[len(before)+1:-1]
        assert after[-1] == dict(id='2026-TNWWE-POSTER-CJ26',setId=sid,order=137,number='CJ26',name='Crown Jewel',subject2=None,category='Base',subset='Event poster',subsetCode='POSTER',roster=None,rookie='No',parallelGroup='POSTER')
        assert [(c['number'],c['name'],c['order']) for c in appended] == [
            (c['number'],c['subject'],i) for i,c in enumerate(additions,134)]
        assert all(c['id']=='2026-TNWWE-BASE-'+c['number'] and c['subsetCode']=='BASE' for c in appended)
        assert len(after)==137 and hh01['number']=='HH01'
        assert hh01['id']=='2026-TNWWE-POSTER-HH01'
        assert hh01['name']=='Halloween Havoc'
        assert hh01['subsetCode']=='POSTER' and hh01['order']==133
        current = next(x for x in cat['sets'] if x['id']==sid)
        assert current['cardCount']==137
        assert next(x for x in current['subsets'] if x['code']=='POSTER')['count']==16
assert (ROOT/'data/catalogue.json').read_bytes()==old('data/catalogue.json')
assert cat['cardCount']==25290
source=json.loads((ROOT/'sources/topps-now-2025-2026/2026-11-02-hh01.json').read_text())
assert source['printRun'] is None and source['releaseDate']=='2026-10-30'
assert [(x['parallel'],x['serialCap']) for x in source['publishedEditions']]==[
    ('Base',None),('Rainbow Foil Short Print',None),('Gold Super Short Print',26)]
sql=generate()
assert sql==(ROOT/'supabase/corrections/2026-11-02-now-hh01.sql').read_text()
assert 'update public.collection_items' not in sql and 'insert into public.collection_items' not in sql
print('PASS: HH01 identity/source/editions, all prior cards and unrelated files preserved, exact guarded SQL.')
