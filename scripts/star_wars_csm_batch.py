"""Official Chrome 2024, Sapphire 2024 and Masterwork 2022 checklist batch."""
import argparse,hashlib,json,re,subprocess
from collections import OrderedDict
from pathlib import Path
from catalogue_io import load_catalogue,save_catalogue
ROOT=Path(__file__).resolve().parents[1]
CDN='https://cdn.shopify.com/s/files/1/0662/9749/5709/files/'
CONFIGS=OrderedDict([
 ('chrome',dict(id='2024-topps-chrome-star-wars',prefix='2024-TCSW',year=2024,date='2024-08-14',pages=18,
  name='2024 Topps Chrome Star Wars',shortName='Chrome Star Wars 2024',accent='#80bbc9',
  checklist=CDN+'CheckList_24SWCM_VERSION5.pdf',odds=CDN+'2024StarWarsChromeOdds.pdf',
  product='https://www.topps.com/products/2024-topps-star-wars-chrome-hobby-box',
  sections=[('CHARACTERS','BASE','Base'),('AUREBESH SHORT PRINTS','AV','Variation'),('I LOVE YOU I KNOW','ILY','Insert'),
   ('THE HEIRESS','TH','Insert'),('GALACTIC GEAR','GG','Insert'),('THE RISE OF PALPATINE','RP','Insert'),
   ('HOTH ICE BLUE FROZENFRACTOR SUPER SHORT PRINTS','HV','Variation'),
   ('GALACTIC EMPIRE','GE','Insert'),('REBEL ALLIANCE','RA','Insert'),('STARSHIP BLUEPRINTS','SB','Insert'),
   ('REFLECTIONS','R','Insert'),('BONUS STAGE','BS','Insert'),('PRINTING PLATES BOOK CARDS','BC','Insert'),
   ('AUTOGRAPH CARDS','AUTO','Autograph'),('DUAL AUTOGRAPH CARDS','DA','Autograph'),('TRIPLE AUTOGRAPH CARDS','TA','Autograph')],
  rosters=['Sketch Card Artists'],counts=[150,150,20,10,25,20,150,9,9,15,5,10,150,95,13,7])),
 ('sapphire',dict(id='2024-topps-star-wars-chrome-sapphire',prefix='2024-TSWCS',year=2024,date='2024-05-04',pages=5,
  name='2024 Topps Star Wars Chrome Sapphire Edition',shortName='Star Wars Sapphire 2024',accent='#6f9ee1',
  checklist=CDN+'STW2476-2024StarWarsChromeSapphireChecklistV3.pdf',odds=CDN+'2024StarWarsChromeSapphireOdds.pdf',
  product='https://www.topps.com/products/2024-topps-star-wars-chrome-sapphire-edition-sealed-case',
  sections=[('BASE CARDS','BASE','Base'),('DUEL OF THE FATES','DF','Insert'),('JEDI HIGH COUNCIL','JHC','Insert'),
   ('PODRACING','PR','Insert'),('SAPPHIRE SELECTIONS','SS','Insert'),('PHANTOM MENACE CAST','PA','Autograph'),
   ('DUAL AUTOGRAPHS','PD','Autograph'),('SAPPHIRE SELECTIONS AUTOGRAPHS','SSA','Autograph')],rosters=[],counts=[100,20,12,10,20,13,3,9])),
 ('masterwork',dict(id='2022-topps-star-wars-masterwork',prefix='2022-TSWMW',year=2022,date='2023-12-08',pages=13,
  name='2022 Topps Star Wars Masterwork',shortName='Star Wars Masterwork 2022',accent='#bfac77',
  checklist=CDN+'STW2256-CheckList_2022StarWarsMasterwork.pdf',odds=None,
  unavailableOdds='https://www.topps.com/media/pdf/odds/StarWarsMasterWorkOdds.pdf',
  product='https://www.topps.com/products/2022-star-wars-masterwork-master-box',
  sections=[('BASE CARDS','BASE','Base'),('BOUNTY HUNTING A COMPLICATED PROFESSION','BH','Insert'),
   ('BOUNTY HUNTING A COMPLICATED PROFESSION GOLD METAL VARIATION','BHG','Variation'),('ORIGINAL TRILOGY POSTER CARDS','OT','Insert'),
   ('ORIGINAL TRILOGY POSTER CARDS GOLD METAL VARIATION','OTG','Variation'),('HELLO THERE','OB1','Insert'),
   ('HELLO THERE GOLD METAL VARIATION','OB1G','Variation'),('ON CARD AUTOGRAPHS','AUTO','Autograph'),
   ('DUAL AUTOGRAPH CARDS','DA','Autograph'),('TRIPLE AUTOGRAPH CARDS','TA','Autograph'),('QUAD AUTOGRAPH BOOK CARDS','QA','Autograph'),
   ('MANUFACTURED TOOLS AND TECHNOLOGY MEDALLION CARDS','TT','Relic'),('ON SCREEN PROP RELICS','OSPR','Relic'),
   ('STAMP CARDS','SC','Relic'),('COSTUME RELIC CARDS','CRC','Relic'),
   ('MANUFACTURED TOOLS AND TECHNOLOGY MEDALLION CARDS AUTOGRAPH PARALLEL','TTA','Autograph Relic'),
   ('ON SCREEN PROP RELICS AUTOGRAPH PARALLEL','OSPRA','Autograph Relic'),('PEN RELIC AUTOGRAPHS','PRA','Autograph Relic'),
   ('COSTUME RELIC CARDS AUTOGRAPH PARALLEL','CRCA','Autograph Relic'),('STAMP CARDS AUTOGRAPH PARALLEL','SCA','Autograph Relic')],
  rosters=['SKETCH CARD','SKETCH BOOK CARD','PANORAMIC SKETCH CARD','TRIPTYCH SKETCH CARD'],counts=[100,15,15,25,25,10,10,63,10,3,5,9,10,9,11,7,8,25,7,5])),
])

def source_path(key):return ROOT/f'sources/star-wars-{key}-{CONFIGS[key]["year"]}/checklist.json'
def read_source(key):return json.loads(source_path(key).read_text())

def extract(key,directory):
 from pypdf import PdfReader
 cfg=CONFIGS[key];sections=OrderedDict((n,[]) for n,_,_ in cfg['sections']);rosters=OrderedDict((n,[]) for n in cfg['rosters'])
 pdf=PdfReader(directory/f'{key}-checklist.pdf')
 if len(pdf.pages)!=cfg['pages']:raise ValueError('Page count changed')
 events=[];seen=[];section=None;pending=None;unresolved=[]
 def finish():
  nonlocal pending
  if pending is not None:sections[section].append(pending);pending=None
 for pn,page in enumerate(pdf.pages,1):
  chunks=[]
  def visit(t,cm,tm,font,size):
   if t.strip():chunks.append((t.strip(),float(tm[4])))
  page.extract_text(visitor_text=visit)
  for text,x in chunks:
   events.append(text)
   if text in ['SUBJECT TO CHANGE','BASE','INSERT','AUTOGRAPH','RELIC','AUTOGRAPH RELIC','PACKAGING','SELL SHEET','Mystery Redemption','THE GALACTIC CIVIL WAR',*sections,*rosters] and x>0:
    finish();section=text
    if text in sections:seen.append(text)
    if text=='Mystery Redemption':unresolved.append(dict(label=text,page=pn,reason='No printed number or subject supplied; no identity invented.'))
   elif section in rosters:rosters[section].append(dict(name=text,page=pn))
   elif section in sections and x>0 and re.fullmatch(r'\d+|[A-Z0-9]+-\s*[A-Za-z0-9]+',text):
    finish();pending=dict(number=text,page=pn,fields=[])
   elif pending is not None:pending['fields'].append(text)
   else:raise ValueError(f'Unclassified {key}: {text}')
 finish()
 if seen!=list(sections):raise ValueError('Section manifest changed')
 raw=subprocess.check_output(['pdftotext','-raw',str(directory/f'{key}-checklist.pdf'),'-']).decode()
 actual=re.sub(r'\s+','',raw);expected=re.sub(r'\s+','',' '.join(events))
 if key=='masterwork' and actual!=expected:
  import pdfplumber
  with pdfplumber.open(directory/f'{key}-checklist.pdf') as independent:
   full=re.sub(r'\s+','',''.join(c['text'] for c in independent.pages[3].chars))
  quote=sections['HELLO THERE'][-1]['fields'][0];compact=re.sub(r'\s+','',quote)
  if compact not in full or not quote.endswith('nothing.”'):raise ValueError('Full quote not independently verified')
  clipped=compact[:-3]
  if actual.count(clipped)!=2:raise ValueError('Unexpected quote clipping')
  actual=actual.replace(clipped,compact)
 if actual!=expected:raise ValueError(key+' Poppler mismatch')
 return dict(checklistUrl=cfg['checklist'],checklistSha256=hashlib.sha256((directory/f'{key}-checklist.pdf').read_bytes()).hexdigest(),
  productUrl=cfg['product'],subsets=[dict(name=n,rows=r) for n,r in sections.items()],rosters=rosters,unresolved=unresolved,
  oddsUrl=cfg['odds'],oddsSha256=hashlib.sha256((directory/f'{key}-odds.pdf').read_bytes()).hexdigest() if cfg['odds'] else None,
  oddsUnavailable=cfg.get('unavailableOdds'),odds=extract_odds(key,directory) if cfg['odds'] else [])

def extract_odds(key,directory):
 import pdfplumber
 rows=[]
 with pdfplumber.open(directory/f'{key}-odds.pdf') as pdf:
  for pn,page in enumerate(pdf.pages,1):
   for line in page.extract_text(layout=True).splitlines():
    text=' '.join(line.split())
    if not text or not re.search(r'\s(?:1:[\d,]+|-)$',text):continue
    m=re.fullmatch(r'(.+?)\s+((?:(?:1:[\d,]+|-)\s+)*(?:1:[\d,]+|-))',text)
    if not m:raise ValueError('Unparsed odds '+text)
    rates=m[2].split()
    if len(rates)!=(5 if key=='chrome' else 1):raise ValueError('Odds column count changed '+text)
    rows.append(dict(label=m[1],rates=rates,page=pn,rawLine=text))
 raw=subprocess.check_output(['pdftotext','-layout',str(directory/f'{key}-odds.pdf'),'-']).decode()
 expected=[' '.join(l.split()) for l in raw.splitlines() if re.search(r'\s(?:1:[\d,]+|-)\s*$',l)]
 if expected!=[r['rawLine'] for r in rows]:raise ValueError('Poppler odds mismatch')
 return rows

def build(key,source=None):
 src=source or read_source(key);cfg=CONFIGS[key];cards=[];variants=[];subsets=[]
 if [s['name'] for s in src['subsets']]!=[x[0] for x in cfg['sections']]:raise ValueError('Unexpected section manifest')
 for section,(name,code,category),count in zip(src['subsets'],cfg['sections'],cfg['counts']):
  groups=OrderedDict()
  for row in section['rows']:groups.setdefault(row['number'],[]).append(row)
  if len(groups)!=count:raise ValueError('Missing/repeated design in '+name)
  if code=='BASE' and set(groups)!={str(i) for i in range(1,count+1)}:raise ValueError('Base numbering incomplete')
  for number,rows in groups.items():
   people=[];roster=None;debut=any('DEBUT' in r['fields'] for r in rows)
   if category.startswith('Autograph'):
    wanted={'DA':2,'PD':2,'TA':3,'QA':4}.get(code,1)
    if len(rows)!=wanted:raise ValueError('Incorrect signer count')
    for r in rows:
     fields=[f for f in r['fields'] if f!='DEBUT']
     if len(fields)!=2:raise ValueError('Incorrect autograph cells')
     people.append((fields[0],fields[1]))
    if len(set(people))!=len(people):raise ValueError('Repeated signer row')
    display=' / '.join(f'{subject} ({signer})' for signer,subject in people)
   else:
    if len(rows)!=1:raise ValueError('Unexpected repeated number')
    fields=[f for f in rows[0]['fields'] if f!='DEBUT']
    wanted=2 if key=='masterwork' and code in ['BH','BHG','OT','OTG','OB1','OB1G'] else 1
    if len(fields)!=wanted:raise ValueError('Incorrect checklist cells')
    display=fields[0];roster=fields[1] if wanted==2 else None
   suffix=''
   if key=='masterwork' and number=='MWA- KS':
    if people!=[('Kiran Shah','Nambi Ghima')]:raise ValueError('Spaced MWA- KS subject changed')
    suffix='-KIRAN-SHAH'
   card=dict(id=f"{cfg['prefix']}-{code}-{re.sub(r'\s+','',number)}{suffix}",setId=cfg['id'],order=len(cards)+1,number=number,name=display,
    subject2=people[1][1] if len(people)>1 else None,category=category,subset=name,subsetCode=code,roster=roster,rookie='No',parallelGroup=code)
   cards.append(card)
   variants.append(dict(id=card['id']+'-IDENTITY',set_id=cfg['id'],card_id=card['id'],variant_order=len(variants)+1,
    subset=name,card_number=number,display_name=display,parallel='Checklist identity',serial_cap=None,serial_exact=None,exclusive_note=None,
    numbering_note='Official printed design; source DEBUT flag retained in normalized evidence and card notes. No inferred serial caps or subject/parallel grid.',verification_status='Official Topps checklist verified'))
  subsets.append(dict(category=category,name=name,code=code,count=count))
 record=dict(id=cfg['id'],categoryId='star-wars',name=cfg['name'],shortName=cfg['shortName'],accent=cfg['accent'],year=cfg['year'],
  manufacturer='Topps',releaseDate=cfg['date'],cardCount=len(cards),subsetCount=len(subsets),subsets=subsets)
 return record,cards,variants

def apply(catalogue,key):
 r,c,_=build(key);sid=r['id'];oldsets=[x for x in catalogue['sets'] if x['id']==sid];oldcards=[x for x in catalogue['cards'] if x['setId']==sid]
 if oldsets or oldcards:
  if oldsets!=[r] or oldcards!=c:raise ValueError('Existing identities differ; refusing overwrite')
  return catalogue
 catalogue['sets'].append(r);catalogue['cards'].extend(c);catalogue['generatedAt']='2026-10-26T00:00:00Z';return catalogue

def rules(key,src):
 cfg=CONFIGS[key];aliases={n:n for n,_,_ in cfg['sections']};out=[]
 if key=='chrome':aliases.update({'BASE CHARACTER CARDS':'CHARACTERS','CHARACTER AUREBESH VARIATION SHORT PRINTS':'AUREBESH SHORT PRINTS',
  'CHARACTERS HOTH VARIATION SUPER SHORT PRINTS':'HOTH ICE BLUE FROZENFRACTOR SUPER SHORT PRINTS','I LOVE YOU / I KNOW':'I LOVE YOU I KNOW',
  'STARSHIPS':'STARSHIP BLUEPRINTS','AUTOGRAPHS':'AUTOGRAPH CARDS','DUAL AUTOGRAPHS':'DUAL AUTOGRAPH CARDS',
  'TRIPLE AUTOGRAPHS':'TRIPLE AUTOGRAPH CARDS','PRINTING PLATES BOOK CARD':'PRINTING PLATES BOOK CARDS'})
 if key=='sapphire':aliases.update({'BASE SET CARDS':'BASE CARDS','JEDI HIGH HIGH COUNCIL':'JEDI HIGH COUNCIL','PHANTOM MENACE CAST AUTOGRAPHS':'PHANTOM MENACE CAST'})
 for i,row in enumerate(src['odds'],1):
  label=row['label']
  if key=='chrome' and label.startswith(('SKETCH CARDS','CHARACTER PUZZLE CARDS')):continue
  alias=next((a for a in sorted(aliases,key=len,reverse=True) if label==a or label.startswith(a+' ')),None)
  if alias is None:raise ValueError('Unmapped odds '+label)
  name=aliases[alias];code=next(c for n,c,_ in cfg['sections'] if n==name)
  formats=['Hobby 5632',"Breaker Delight 5633",'Value SE 5634','Value EA 5635','Value CEE 5636'] if key=='chrome' else ['Online Exclusive 5666']
  out.append(dict(id=f"{cfg['id']}-ODDS-{i:03d}",set_id=cfg['id'],parallel_group=code,applies_to=name,
   parallel=label[len(alias):].strip() or 'Base issue',serial_cap=None,serial_exact=None,
   exclusive_note='; '.join(f'{f}: {rate}' for f,rate in zip(formats,row['rates']))+'. Dashes retain source non-listed rates.',
   numbering_note=f"Official odds page {row['page']}, label: {label}. Subset rule only; pack rates do not prove serial caps or every subject/parallel combination. Repeated unnamed Aurebesh label remains unresolved, without assigning an edition.",
   verification_status='Official Topps odds; subset rule only'))
 return out

def tables(key):
 cfg=CONFIGS[key];src=read_source(key);r,c,v=build(key,src);sid=r['id'];out=OrderedDict()
 evidence={(code,row['number']):row for section,(_,code,_) in zip(src['subsets'],cfg['sections']) for row in section['rows']}
 out['catalogue_sets']=[dict(id=sid,name=r['name'],short_name=r['shortName'],year=r['year'],manufacturer='Topps',release_date=r['releaseDate'],source_file=cfg['checklist'],accent=r['accent'],card_count=len(c),subset_count=len(r['subsets']),variant_count=len(v))]
 out['catalogue_subsets']=[dict(set_id=sid,subset_code=x['code'],category=x['category'],name=x['name'],card_count=x['count'],parallel_group=x['code'],source_url=cfg['checklist']) for x in r['subsets']]
 out['catalogue_cards']=[dict(id=x['id'],set_id=sid,checklist_order=x['order'],category=x['category'],subset_code=x['subsetCode'],card_number=x['number'],display_name=x['name'],subject_1=x['name'].split(' / ')[0],subject_2=x['subject2'],roster=x['roster'],rookie=False,parallel_group=x['parallelGroup'],image_status='Missing',pricing_status='Unpriced',source_url=cfg['checklist'],
  notes='Official printed number/spelling retained. '+('DEBUT marked in source. ' if 'DEBUT' in evidence[(x['subsetCode'],x['number'])]['fields'] else '')+
   ('Printed MWA- KS retains its space; internal KIRAN-SHAH suffix separates it from Katee Sackhoff MWA-KS. ' if x['number']=='MWA- KS' else '')+
   'Multi-signer rows combine by printed design. Unnumbered artists/redemptions remain source evidence; no serial caps or per-card grids inferred.') for x in c]
 out['catalogue_variants']=v;out['catalogue_parallel_rules']=rules(key,src)
 urls=[('checklist','Checklist',cfg['checklist'],'Complete printed checklist independently reconciled; source differences and unnumbered entries documented in batch audit.'),
  ('product','Product identity and release date',cfg['product'],'Official title year retained with actual US availability; generic product metadata is not a separate set.'),
  ('odds','Parallel applicability' if cfg['odds'] else 'Unrecovered odds source',cfg['odds'] or cfg['unavailableOdds'],
   'Official odds rows retained; no inferred caps or grids.' if cfg['odds'] else 'Manufacturer-linked document returns 404; no pack rates or parallel cap rules imported for Masterwork. Checklist identities are verified separately.')]
 out['catalogue_sources']=[dict(id=sid+'-'+k,set_id=sid,source='Topps',purpose=p,url=u,notes=n) for k,p,u,n in urls]
 return out

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--extract',type=Path);p.add_argument('--verify-pdf',type=Path);a=p.parse_args()
 if a.extract:
  for key in CONFIGS:
   src=extract(key,a.extract);path=source_path(key);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(src,ensure_ascii=False,indent=2)+'\n')
   print(key,[(x['name'],len(x['rows']),len({r['number'] for r in x['rows']}),sorted({len(r['fields']) for r in x['rows']})) for x in src['subsets']], 'rosters',{k:len(v) for k,v in src['rosters'].items()},'odds',len(src['odds']))
 else:
  catalogue=load_catalogue()
  for key in CONFIGS:
   if a.verify_pdf and extract(key,a.verify_pdf)!=read_source(key):raise ValueError('Source evidence changed')
   apply(catalogue,key);print(key,len(build(key)[1]),'cards',len(tables(key)['catalogue_parallel_rules']),'rules')
  save_catalogue(catalogue)
