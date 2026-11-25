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
latest_release = json.loads((ROOT/'sources/topps-now-2025-2026/2026-11-22-now-122.json').read_text())
assert [c['number'] for c in latest_release] == ['122']
new_releases = json.loads((ROOT/'sources/topps-now-2025-2026/2026-11-10-now-119-121.json').read_text())
assert [c['number'] for c in new_releases] == ['119','120','121']
for s in prior['sets']:
    path = 'data/'+s['file']
    expected_metadata = {k:v for k,v in s.items() if k!='file'}
    if s['id']==sid:
        expected_metadata['cardCount'] += 5 + len(additions) + len(new_releases) + len(latest_release)
        next(x for x in expected_metadata['subsets'] if x['code']=='BASE')['count'] += len(additions) + 3 + len(new_releases) + len(latest_release)
        next(x for x in expected_metadata['subsets'] if x['code']=='POSTER')['count'] += 2
    assert next(x for x in cat['sets'] if x['id']==s['id']) == expected_metadata
    if s['id'] != sid:
        assert (ROOT/path).read_bytes() == old(path), s['id']
    else:
        before = json.loads(old(path))['cards']
        after = [c for c in cat['cards'] if c['setId']==sid]
        latest = after.pop()
        assert latest == dict(id='2026-TNWWE-BASE-122', setId=sid, order=144, number='122',
                              name='IYO SKY', subject2=None, category='Base', subset='Regular',
                              subsetCode='BASE', roster=None, rookie='No', parallelGroup='BASE')
        newest = after[-len(new_releases):]
        after = after[:-len(new_releases)]
        for card, release, order in zip(newest, new_releases, range(141,144)):
            assert card == dict(id='2026-TNWWE-BASE-'+release['number'], setId=sid, order=order,
                                number=release['number'], name=release['subject'], subject2=release['subject2'],
                                category='Base', subset='Regular', subsetCode='BASE', roster=None,
                                rookie='No', parallelGroup='BASE')
        assert after[:len(before)] == before
        hh01 = after[len(before)]
        appended = after[len(before)+1:-4]
        assert after[-4] == dict(id='2026-TNWWE-POSTER-CJ26',setId=sid,order=137,number='CJ26',name='Crown Jewel',subject2=None,category='Base',subset='Event poster',subsetCode='POSTER',roster=None,rookie='No',parallelGroup='POSTER')
        assert [(c['number'],c['order']) for c in after[-3:]] == [('114',138),('115',139),('116',140)]
        assert [(c['number'],c['name'],c['order']) for c in appended] == [
            (c['number'],c['subject'],i) for i,c in enumerate(additions,134)]
        assert all(c['id']=='2026-TNWWE-BASE-'+c['number'] and c['subsetCode']=='BASE' for c in appended)
        assert len(after)==140 and hh01['number']=='HH01'
        assert hh01['id']=='2026-TNWWE-POSTER-HH01'
        assert hh01['name']=='Halloween Havoc'
        assert hh01['subsetCode']=='POSTER' and hh01['order']==133
        current = next(x for x in cat['sets'] if x['id']==sid)
        assert current['cardCount']==144
        assert next(x for x in current['subsets'] if x['code']=='POSTER')['count']==16
assert (ROOT/'data/catalogue.json').read_bytes()==old('data/catalogue.json')
assert cat['cardCount']==25297 + 878
assert next(s for s in cat['sets'] if s['id']=='2026-topps-royalty-wwe')['cardCount']==878
source=json.loads((ROOT/'sources/topps-now-2025-2026/2026-11-02-hh01.json').read_text())
assert source['printRun'] == 934 and source['releaseDate']=='2026-10-30'
assert [(x['parallel'],x['serialCap']) for x in source['publishedEditions']]==[
    ('Base',None),('Rainbow Foil Short Print',None),('Gold Super Short Print',26)]
sql=generate()
assert sql==(ROOT/'supabase/corrections/2026-11-02-now-hh01.sql').read_text()
assert 'update public.collection_items' not in sql and 'insert into public.collection_items' not in sql
print('PASS: HH01 identity/source/editions, all prior cards and unrelated files preserved, exact guarded SQL.')

# Current append: exact verified editions and reproducible guarded SQL.
from prepare_now_122 import records as latest_records, generate_sql
cards, editions, sources = latest_records()
assert [(c['card_number'],c['display_name'],c['checklist_order']) for c in cards] == [('122','IYO SKY',144)]
assert [(v['parallel'],v['serial_cap']) for v in editions] == [('Checklist identity',None),('Gold Foil',50),('Orange Foil',25),('Black Foil',10),('Red Foil',5),('FoilFractor',1)]
assert len(sources)==1
assert '-- Official Topps NOW #122; guarded catalogue-only append.\n'+generate_sql() == (ROOT/'supabase/corrections/2026-11-22-now-122.sql').read_text()
print('PASS: NOW 122 official identity, six editions and reproducible preservation SQL.')
