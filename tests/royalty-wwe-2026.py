"""Reconcile source identities, multi-signer cards and prior-set preservation."""
import sys,subprocess,json,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from add_2026_royalty_wwe import build,SID,tables
r,c=build();assert len(c)==878 and len(r['subsets'])==38
assert collections.Counter(x['category'] for x in c)==dict(Base=100,Autograph=328,Relic=130,**{'Autograph Relic':320})
assert {x['number'] for x in c if x['category']=='Base'}==set(map(str,range(1,101)))
assert next(x for x in c if x['number']=='TTA-ATD')['name']=='Undertaker / "Stone Cold" Steve Austin / The Rock'
assert next(x for x in c if x['number']=='AFA-JC')['name']=='John Cena'
assert all(v['serial_cap'] is None for v in tables()['catalogue_variants'])
assert len({(x['subsetCode'],x['number']) for x in c})==878
for f in (ROOT/'data/sets').glob('*.json'):
 if f.stem!=SID:assert f.read_bytes()==subprocess.check_output(['git','show','origin/main:data/sets/'+f.name],cwd=ROOT)
before={p:p.read_bytes() for p in (ROOT/'data').rglob('*.json')}
subprocess.run([sys.executable,'scripts/add_2026_royalty_wwe.py'],cwd=ROOT,check=True)
assert all(p.read_bytes()==b for p,b in before.items())
print('PASS: 878 identities, 38 subsets, multi-signers grouped, no inferred editions, prior sets preserved, idempotent import')
