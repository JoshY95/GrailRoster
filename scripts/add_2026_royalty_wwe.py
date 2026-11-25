"""Import only identities explicitly listed in Topps' 2026 Royalty PDF."""
import re,json,hashlib
from pathlib import Path
from collections import OrderedDict
from catalogue_io import load_catalogue,save_catalogue
ROOT=Path(__file__).resolve().parents[1]
SID='2026-topps-royalty-wwe'
DIR=ROOT/'sources/royalty-wwe-2026'
URL='https://cdn.shopify.com/s/files/1/0662/9749/5709/files/26RWWE_-_2026_Topps_Royalty_Collection_WWE_Checklist.xls_-_Read-Only_-_Compatibility_Mode.pdf?v=1795531628'
NOTE='Official checklist identity only. Parallel applicability and serial caps unverified; Liquid Silver/Gold identities absent from PDF. Release announced for 4 December 2026; shipping unconfirmed.'
def build():
 sections=OrderedDict(); cat='Base'; section=None; pending=None
 for raw in (DIR/'checklist.txt').read_text().splitlines():
  line=raw.strip()
  if not line or line.startswith(('2026 Topps','Checklists provided','at the time')):continue
  if line in ('BASE','AUTOGRAPH RELIC','AUTOGRAPH','RELIC'):
   cat={'BASE':'Base','AUTOGRAPH RELIC':'Autograph Relic','AUTOGRAPH':'Autograph','RELIC':'Relic'}[line];continue
  m=re.match(r'^(\d+|[A-Z][A-Z0-9]*-[A-Z0-9]+|LIT\d+|TRS\d+)\s+(.+)$',line)
  if m:
   number,tail=m.groups(); rm=re.search(r'(Smackdown|Raw|Legend|NXT|WWE)(?:\s+(Rookie))?$',tail)
   # Roster may wrap onto the next PDF line.
   pending=dict(number=number,name=tail[:rm.start()].strip() if rm else tail,roster=rm[1] if rm else None,rookie='Yes' if rm and rm[2] else 'No')
   sections[section]['rows'].append(pending)
  elif re.fullmatch(r'[A-Z][A-Z 0-9]+',line) and line!='NXT':
   section=line;sections[section]=dict(category=cat,rows=[]);pending=None
  elif pending:
   if line in ('NXT','Legend','Smackdown','Raw','WWE'):pending['roster']=line
   elif pending['name']=='"The American Nightmare"':
    roster=re.search(r'Smackdown|Raw|Legend|WWE|NXT',line)
    if roster:pending['roster']=roster[0];line=line.replace(roster[0],'').strip()
    if line:pending['name']+=' '+line
   else:raise ValueError('Unparsed continuation '+line)
  else:raise ValueError('Unparsed '+line)
 cards=[]; subsets=[]
 for name,sec in sections.items():
  groups=OrderedDict()
  for row in sec['rows']:groups.setdefault(row['number'],[]).append(row)
  first=next(iter(groups));code='BC' if first.isdigit() else first.split('-')[0] if '-' in first else re.sub(r'\d','',first)
  if name=='TRISH STRATUS 25TH ANNIVERSARY AUTOGRAPHS':code='TRISH25'
  for number,rows in groups.items():
   names=[r['name'] for r in rows];assert all(names)
   assert len(rows)==({'DSR':2,'DA':2,'TTA':3,'FFW':4,'WC':2,'PP':2}.get(code,1))
   cards.append(dict(id=f'2026-TRWWE-{code}-{number}',setId=SID,order=len(cards)+1,number=number,name=' / '.join(names),subject2=' / '.join(names[1:]) or None,category=sec['category'],subset=name,subsetCode=code,roster=rows[0]['roster'] if len(rows)==1 else None,rookie='Yes' if any(r['rookie']=='Yes' for r in rows) else 'No',parallelGroup=code))
  subsets.append(dict(category=sec['category'],name=name,code=code,count=len(groups)))
 assert len(cards)==878 and len(subsets)==38,(len(cards),len(subsets))
 assert len({c['id'] for c in cards})==878
 record=dict(id=SID,name='2026 Topps Royalty WWE',shortName='Royalty WWE 2026',accent='#7c3aed',year=2026,manufacturer='Topps',releaseDate='2026-12-04',cardCount=len(cards),subsetCount=len(subsets),subsets=subsets,categoryId='wwe')
 return record,cards

def tables():
 r,c=build();d=OrderedDict()
 d['catalogue_sets']=[dict(id=SID,name=r['name'],short_name=r['shortName'],year=2026,manufacturer='Topps',release_date=r['releaseDate'],source_file=URL,accent=r['accent'],card_count=len(c),subset_count=len(r['subsets']),variant_count=len(c))]
 d['catalogue_subsets']=[dict(set_id=SID,subset_code=s['code'],category=s['category'],name=s['name'],card_count=s['count'],parallel_group=s['code'],source_url=URL) for s in r['subsets']]
 d['catalogue_cards']=[dict(id=x['id'],set_id=SID,checklist_order=x['order'],category=x['category'],subset_code=x['subsetCode'],card_number=x['number'],display_name=x['name'],subject_1=x['name'].split(' / ')[0],subject_2=x['subject2'],roster=x['roster'],rookie=x['rookie']=='Yes',parallel_group=x['parallelGroup'],image_status='Missing',pricing_status='Unpriced',source_url=URL,notes=NOTE) for x in c]
 d['catalogue_variants']=[dict(id=x['id']+'-IDENTITY',set_id=SID,card_id=x['id'],variant_order=x['order'],subset=x['subset'],card_number=x['number'],display_name=x['name'],parallel='Checklist identity',serial_cap=None,serial_exact=None,exclusive_note=None,numbering_note=NOTE,verification_status='Official Topps checklist verified') for x in c]
 d['catalogue_sources']=[dict(id=SID+'-checklist',set_id=SID,source='Topps official checklist',purpose='Card identities and printed checklist codes',url=URL,notes=NOTE),dict(id=SID+'-release',set_id=SID,source='Topps UK',purpose='UK availability via EQL',url='https://uk.topps.com/pages/topps-royalty-wwe',notes=NOTE)]
 return d
if __name__=='__main__':
 r,c=build();old=load_catalogue();existing=[s for s in old['sets'] if s['id']==SID]
 if existing:assert existing==[r] and [x for x in old['cards'] if x['setId']==SID]==c
 else:old['sets'].append(r);old['cards'].extend(c);old['generatedAt']='2026-11-26T00:00:00Z'
 save_catalogue(old)
 from prepare_star_wars_chrome_import import generate
 (ROOT/'supabase/corrections/2026-11-26-royalty-wwe.sql').write_text(generate(tables(),set_id=SID,baseline_sets=49,baseline_cards=25297))
 (DIR/'verification.json').write_text(json.dumps(dict(checklistUrl=URL,sha256=hashlib.sha256((DIR/'checklist.pdf').read_bytes()).hexdigest(),cardCount=len(c),subsets=r['subsets'],gaps=NOTE),indent=2)+'\n')
 print('Imported',len(c),'identities',len(r['subsets']),'subsets')
