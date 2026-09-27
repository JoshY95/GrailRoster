#!/usr/bin/env node
// Import only WWE identities explicitly listed in Topps' 2026 NSCC checklist.
const fs = require('node:fs');
const { execFileSync } = require('node:child_process');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');
const CATALOGUE = path.join(ROOT, 'data/catalogue.json');
const SET_ID = '2026-topps-nscc-collection-wwe';
const SOURCE = 'https://cdn.shopify.com/s/files/1/0662/9749/5709/files/2026_National_Sports_Collectors_Convention_26NSCC_-_Checklist_1.pdf?v=1785264843';
const PRODUCT = 'https://www.topps.com/pages/nscc-collection';
const pdf = process.argv[2];
if (!pdf) throw new Error('Usage: node scripts/add_nscc_wwe.js /path/to/official-checklist.pdf [--sql]');
const text = execFileSync('pdftotext', ['-layout', pdf, '-'], { encoding: 'utf8' });

function section(start, end) {
  const a = text.indexOf(start);
  const b = text.indexOf(end, a + start.length);
  if (a < 0 || b < 0) throw new Error(`Missing PDF section boundary: ${start} / ${end}`);
  return text.slice(a + start.length, b);
}
function entries(body, prefix, allowedNumbers = null) {
  return body.split(/\r?\n/).map(line => line.trim()).filter(line => line.startsWith(prefix + '-')).filter(line => !allowedNumbers || allowedNumbers.test(line)).map(line => {
    const m = line.match(/^([A-Z]+-\d+)\s{2,}(.+?)\s{2,}(Raw|Smackdown|NXT)\s*$/);
    if (!m) throw new Error(`Unparsed WWE checklist line: ${line}`);
    return { number: m[1], name: m[2].trim(), roster: m[3] };
  });
}

const base = entries(section('WWE 2026 THE NATIONAL REFRACTORS\n', 'STAR WARS 2026 THE NATIONAL REFRACTORS'), 'WWE');
const autos = entries(section('WWE 2026 THE NATIONAL REFRACTORS AUTOGRAPH PARALLEL\n', 'STAR WARS 2026 THE NATIONAL REFRACTORS AUTOGRAPH PARALLEL'), 'WWE');
const nationalAutos = entries(section('THE NATIONAL COLLECTION AUTOGRAPH PARALLEL\n', 'UEFA 2026 THE NATIONAL REFRACTORS AUTOGRAPH PARALLEL'), 'NC', /^NC-1[1-5]\s/);
const national = entries(section('THE NATIONAL COLLECTION\n', 'NC-16'), 'NC', /^NC-1[1-5]\s/);
if (base.length !== 50 || autos.length !== 46 || national.length !== 5 || nationalAutos.length !== 4) {
  throw new Error(`Unexpected counts: ${[base.length, autos.length, national.length, nationalAutos.length]}`);
}
for (const [i, row] of base.entries()) if (row.number !== `WWE-${String(i + 1).padStart(2, '0')}`) throw new Error(`Base numbering mismatch: ${row.number}`);
const baseMap = new Map(base.map(x => [x.number, x.name]));
for (const row of autos) if (baseMap.get(row.number) !== row.name) throw new Error(`Autograph identity mismatch: ${row.number}`);
if (nationalAutos.some(x => x.number === 'NC-15')) throw new Error('Unexpected Stephanie Vaquer autograph');

const groups = [
  { code: 'NR', name: 'WWE 2026 THE NATIONAL REFRACTORS', category: 'Base', rows: base },
  { code: 'NRA', name: 'WWE 2026 THE NATIONAL REFRACTORS AUTOGRAPH PARALLEL', category: 'Autograph', rows: autos },
  { code: 'NC', name: 'THE NATIONAL COLLECTION', category: 'Insert', rows: national },
  { code: 'NCA', name: 'THE NATIONAL COLLECTION AUTOGRAPH PARALLEL', category: 'Autograph', rows: nationalAutos },
];
let order = 0;
const cards = groups.flatMap(g => g.rows.map(row => ({
  id: `2026-NSCCWWE-${g.code}-${row.number}`,
  setId: SET_ID, order: ++order, number: row.number, name: row.name,
  subject2: null, category: g.category, subset: g.name, subsetCode: g.code,
  roster: row.roster, rookie: 'No', parallelGroup: g.code,
})));
const set = {
  id: SET_ID, name: '2026 Topps NSCC Collection - WWE', shortName: 'NSCC Collection WWE',
  accent: '#ef4444', year: 2026, manufacturer: 'Topps', releaseDate: null,
  cardCount: cards.length, subsetCount: groups.length,
  subsets: groups.map(g => ({ category: g.category, name: g.name, code: g.code, count: g.rows.length })),
};
const catalogue = JSON.parse(fs.readFileSync(CATALOGUE, 'utf8'));
if (new Set(cards.map(x => x.id)).size !== cards.length) throw new Error('Duplicate card IDs');
if (catalogue.sets.some(x => x.id === SET_ID) || catalogue.cards.some(x => x.setId === SET_ID)) {
  if (!process.argv.includes('--sql')) throw new Error('NSCC set already exists');
  const existing = catalogue.cards.filter(x => x.setId === SET_ID);
  if (existing.length !== cards.length || existing.some((x, i) => x.id !== cards[i].id || x.name !== cards[i].name)) throw new Error('Existing NSCC data differs from official PDF');
} else {
  catalogue.sets.push(set);
  catalogue.cards.push(...cards);
  catalogue.setCount = catalogue.sets.length;
  catalogue.cardCount = catalogue.cards.length;
  catalogue.generatedAt = new Date().toISOString();
  fs.writeFileSync(CATALOGUE, JSON.stringify(catalogue));
}

if (process.argv.includes('--sql')) {
  const q = x => x == null ? 'null' : typeof x === 'number' ? String(x) : `'${String(x).replaceAll("'", "''")}'`;
  const values = rows => rows.map(row => '(' + row.map(q).join(',') + ')').join(',\n');
  const sql = [
    'begin;',
    `insert into public.catalogue_sets (id,name,short_name,year,manufacturer,release_date,source_file,accent,card_count,subset_count,variant_count) values ${values([[set.id,set.name,set.shortName,2026,'Topps',null,SOURCE,set.accent,cards.length,4,0]])} on conflict (id) do nothing;`,
    `insert into public.catalogue_subsets (set_id,subset_code,category,name,card_count,parallel_group,source_url) values ${values(groups.map(g => [SET_ID,g.code,g.category,g.name,g.rows.length,g.code,SOURCE]))} on conflict (set_id,subset_code) do nothing;`,
    `insert into public.catalogue_cards (id,set_id,checklist_order,category,subset_code,card_number,display_name,subject_1,subject_2,roster,rookie,parallel_group,image_status,pricing_status,source_url,notes) values ${values(cards.map(c => [c.id,SET_ID,c.order,c.category,c.subsetCode,c.number,c.name,c.name,null,c.roster,false,c.parallelGroup,'Missing','Unpriced',SOURCE,'Official Topps 2026 NSCC checklist']))} on conflict (id) do nothing;`,
    `insert into public.catalogue_sources (id,set_id,source,purpose,url,notes) values ${values([['2026-nscc-wwe-checklist',SET_ID,'Topps','Checklist',SOURCE,'Official PDF: WWE National Refractors, autograph parallel and National Collection identities'],['2026-nscc-wwe-product',SET_ID,'Topps','Product',PRODUCT,'Official product overview; /26 Annual Refractor is a subset-level statement, not per-card confirmation']])} on conflict (id) do nothing;`,
    `insert into public.catalogue_parallel_rules (id,set_id,parallel_group,applies_to,parallel,serial_cap,serial_exact,exclusive_note,numbering_note,verification_status) values ${values([['2026-nscc-wwe-annual-26',SET_ID,'NR','WWE 2026 THE NATIONAL REFRACTORS','NSCC Annual Refractor',26,null,null,'Topps product page states Base NSCC Annual Refractor numbered to 26; individual WWE card applicability unconfirmed','Set-level confirmed; card-level unverified']])} on conflict (id) do nothing;`,
    'commit;',
  ].join('\n');
  process.stdout.write(sql);
} else console.log(`Added ${cards.length} official NSCC WWE identities across ${groups.length} subsets.`);
