#!/usr/bin/env node
// Import stable card identities from Topps' official 2025 Chrome WWE checklist.
// Frozenfractors reuse the 200 base-card identities and are emitted as variants.
const fs = require('node:fs');
const { execFileSync } = require('node:child_process');
const path = require('node:path');
const {loadCatalogue, saveCatalogue} = require('./catalogue_io');

const ROOT = path.resolve(__dirname, '..');
const CATALOGUE = path.join(ROOT, 'data/catalogue.json');
const SET_ID = '2025-topps-chrome-wwe';
const SOURCE = 'https://cdn.shopify.com/s/files/1/0662/9749/5709/files/WWE2502-CheckList_25CWWE.pdf';
const PRODUCT = 'https://www.topps.com/pages/checklists';
const pdf = process.argv[2];
if (!pdf) throw new Error('Usage: node scripts/add_2025_topps_chrome_wwe.js /path/to/official-checklist.pdf [--sql-dir DIR]');

const raw = execFileSync('pdftotext', ['-layout', pdf, '-'], { encoding: 'utf8' });
const lines = raw.split(/\r?\n/).map(line => line.replace(/^\f/, '').trimEnd());
const rosterPattern = '(Raw|Smackdown|NXT|Legend|WWE)';

const definitions = [
  ['BASE CARDS I', 'BASE-I', 'Base', /^\d+$/],
  ['BASE CARDS II', 'BASE-II', 'Base', /^\d+$/],
  ['BASE CARDS IMAGE VARIATIONS', 'BIV', 'Insert', /^\d+$/],
  ['PARADIGM', 'PAR', 'Insert', /^PAR-/],
  ['1985 TOPPS LEGENDS', '85TL', 'Insert', /^85TL-/],
  ['WOMENS DIVISION', 'WD', 'Insert', /^WD-/],
  ['THE TIME IS NOW', 'TIN', 'Insert', /^TIN-/],
  ['SLAMMY', 'SMY', 'Insert', /^SMY-/],
  ['SHIFTING GEARS', 'SG', 'Insert', /^SG-/],
  ['FAMILY TREE', 'FT', 'Insert', /^FT-/],
  ['EMBEDDED', 'EMB', 'Insert', /^EMB-/],
  ['WRESTLEMANIA RECALL', 'WM', 'Insert', /^WM-/],
  ['ALLEN AND GINTER', 'AG', 'Insert', /^AG-/],
  ['1985 TOPPS CURRENT', '85TC', 'Insert', /^85TC-/],
  ['TITLE TOWN', 'TT', 'Insert', /^TT-/],
  ['TAG TEAM', 'TAG', 'Insert', /^TAG-/],
  ['PERSONA', 'P', 'Insert', /^P-/],
  ['MANIA', 'MNA', 'Insert', /^MNA-/],
  ['HELIX', 'HLX', 'Insert', /^HLX-/],
  ['HEADSHOTS', 'HS', 'Insert', /^HS-/],
  ['HIDDEN GEMS', 'HG', 'Insert', /^HG-/],
  ['LETS GO', 'LG', 'Insert', /^LG-/],
  ['FEEL THE POP', 'FTP', 'Insert', /^FTP-/],
  ['BLUE BRAND CHROME AUTOGRAPHS', 'BBA', 'Autograph', /^BBA-/],
  ['RED BRAND CHROME AUTOGRAPHS', 'RBA', 'Autograph', /^RBA-/],
  ['LEGENDARY CHROME AUTOGRAPHS', 'LCA', 'Autograph', /^LCA-/],
  ['NXT CHROME AUTOGRAPHS', 'NXT', 'Autograph', /^NXT-/],
  ['MAIN EVENT AUTOGRAPHS', 'MEA', 'Autograph', /^MEA-/],
  ['MARKS OF CHAMPIONS', 'MOC', 'Autograph', /^MOC-/],
  ['HALL OF FAME AUTOGRAPHS', 'HOF', 'Autograph', /^HOF-/],
  ['FUTURE STARS AUTOGRAPHS', 'FSA', 'Autograph', /^FSA-/],
  ['BASE CARDS I AUTOGRAPH PARALLEL', 'CLA-I', 'Autograph', /^CLA-/],
  ['BASE CARDS II AUTOGRAPH PARALLEL', 'CLA-II', 'Autograph', /^CLA-/],
];

const allHeadings = new Set([
  'BASE', 'INSERT', 'AUTOGRAPH', 'PACKAGING', 'SELL SHEET',
  'BASE CARDS I FROZENFRACTOR VARIATION', 'BASE CARDS II FROZENFRACTOR VARIATION',
  ...definitions.map(([heading]) => heading),
]);

function bodyFor(heading) {
  const start = lines.findIndex(line => line.trim() === heading);
  if (start < 0) throw new Error(`Missing checklist heading: ${heading}`);
  let end = start + 1;
  while (end < lines.length && !allHeadings.has(lines[end].trim())) end++;
  return lines.slice(start + 1, end);
}

function parseRows(heading, numberPattern) {
  const parsed = [];
  let current = null;
  for (const original of bodyFor(heading)) {
    const line = original.replace(/^\s+/, '');
    if (!line) continue;
    const match = line.match(new RegExp(`^(.*?)\\s+${rosterPattern}\\s*$`, 'i'));
    if (!match) throw new Error(`Unparsed row in ${heading}: ${original}`);
    const left = match[1].trim();
    const roster = ({ raw: 'Raw', smackdown: 'Smackdown', nxt: 'NXT', legend: 'Legend', wwe: 'WWE' })[match[2].toLowerCase()];
    const firstSpace = left.search(/\s/);
    const possibleNumber = firstSpace < 0 ? left : left.slice(0, firstSpace);
    if (numberPattern.test(possibleNumber)) {
      const subject = left.slice(possibleNumber.length).trim();
      if (!subject) throw new Error(`Missing subject in ${heading}: ${original}`);
      if (current && current.number === possibleNumber) {
        current.subjects.push(subject);
        current.rosters.push(roster);
        continue;
      }
      current = { number: possibleNumber, subjects: [subject], rosters: [roster] };
      parsed.push(current);
    } else {
      if (!current) throw new Error(`Orphan continuation in ${heading}: ${original}`);
      current.subjects.push(left);
      current.rosters.push(roster);
    }
  }
  return parsed;
}

const expectedCounts = {
  'BASE CARDS I': 100, 'BASE CARDS II': 100, 'BASE CARDS IMAGE VARIATIONS': 100,
  'PARADIGM': 25, '1985 TOPPS LEGENDS': 25, 'WOMENS DIVISION': 40,
  'THE TIME IS NOW': 25, 'SLAMMY': 25, 'SHIFTING GEARS': 20, 'FAMILY TREE': 14,
  'EMBEDDED': 15, 'WRESTLEMANIA RECALL': 10, 'ALLEN AND GINTER': 40,
  '1985 TOPPS CURRENT': 25, 'TITLE TOWN': 10, 'TAG TEAM': 15, 'PERSONA': 25,
  'MANIA': 20, 'HELIX': 25, 'HEADSHOTS': 10, 'HIDDEN GEMS': 5, 'LETS GO': 15,
  'FEEL THE POP': 5, 'BLUE BRAND CHROME AUTOGRAPHS': 35,
  'RED BRAND CHROME AUTOGRAPHS': 37, 'LEGENDARY CHROME AUTOGRAPHS': 14,
  'NXT CHROME AUTOGRAPHS': 39, 'MAIN EVENT AUTOGRAPHS': 18,
  'MARKS OF CHAMPIONS': 14, 'HALL OF FAME AUTOGRAPHS': 12,
  'FUTURE STARS AUTOGRAPHS': 10, 'BASE CARDS I AUTOGRAPH PARALLEL': 91,
  'BASE CARDS II AUTOGRAPH PARALLEL': 75,
};

const groups = definitions.map(([heading, code, category, numberPattern]) => {
  const rows = parseRows(heading, numberPattern);
  return { heading, code, category, rows };
});
if (process.argv.includes('--counts')) {
  console.log(groups.map(group => `${group.heading}\t${group.rows.length}`).join('\n'));
  process.exit(0);
}
for (const { heading, rows } of groups) {
  if (rows.length !== expectedCounts[heading]) {
    throw new Error(`Unexpected ${heading} count: ${rows.length}; expected ${expectedCounts[heading]}`);
  }
}

const baseRows = [...groups[0].rows, ...groups[1].rows];
for (const [index, row] of baseRows.entries()) {
  if (row.number !== String(index + 1)) throw new Error(`Base numbering mismatch at ${index + 1}: ${row.number}`);
}

const frozenOne = parseRows('BASE CARDS I FROZENFRACTOR VARIATION', /^\d+$/);
const frozenTwo = parseRows('BASE CARDS II FROZENFRACTOR VARIATION', /^\d+$/);
if (frozenOne.length !== 100 || frozenTwo.length !== 100) throw new Error('Frozenfractor checklist must contain 200 rows');
for (const [index, row] of [...frozenOne, ...frozenTwo].entries()) {
  if (row.number !== String(index + 1)) throw new Error(`Frozenfractor numbering mismatch at ${index + 1}: ${row.number}`);
}

function cleanId(value) {
  return String(value).replace(/[^A-Za-z0-9-]/g, '');
}

let order = 0;
const cards = groups.flatMap(group => group.rows.map(row => ({
  id: `2025-TCWWE-${group.code}-${cleanId(row.number)}`,
  setId: SET_ID,
  order: ++order,
  number: row.number,
  name: row.subjects.join(' / '),
  subject2: row.subjects.length > 1 ? row.subjects.slice(1).join(' / ') : null,
  category: group.category,
  subset: group.heading,
  subsetCode: group.code,
  roster: [...new Set(row.rosters)].join(' / '),
  rookie: 'No',
  parallelGroup: group.code,
})));

const ids = new Set(cards.map(card => card.id));
if (ids.size !== cards.length) throw new Error(`Duplicate card IDs: ${cards.length - ids.size}`);
const identityKeys = new Set(cards.map(card => `${card.subsetCode}\u001f${card.number}`));
if (identityKeys.size !== cards.length) throw new Error('Duplicate subset/card-number identities');
if (cards.some(card => !card.name || !card.number || !card.subsetCode)) throw new Error('Blank required card field');

const baseCardByNumber = new Map(cards.filter(card => card.subsetCode === 'BASE-I' || card.subsetCode === 'BASE-II').map(card => [card.number, card]));
const variants = [...frozenOne, ...frozenTwo].map((row, index) => {
  const card = baseCardByNumber.get(row.number);
  if (!card) throw new Error(`Frozenfractor orphan: ${row.number}`);
  return {
    id: `${card.id}-FROZENFRACTOR`, cardId: card.id, order: index + 1,
    subset: card.subset, number: card.number, name: card.name,
  };
});

const set = {
  id: SET_ID, name: '2025 Topps Chrome WWE', shortName: 'Chrome WWE 2025',
  accent: '#f97316', year: 2025, manufacturer: 'Topps', releaseDate: '2025-01-31',
  cardCount: cards.length, subsetCount: groups.length,
  subsets: groups.map(group => ({
    category: group.category, name: group.heading, code: group.code, count: group.rows.length,
  })),
};

const catalogue = loadCatalogue();
const existingCards = catalogue.cards.filter(card => card.setId === SET_ID);
if (catalogue.sets.some(item => item.id === SET_ID) || existingCards.length) {
  if (existingCards.length !== cards.length || existingCards.some((card, index) => card.id !== cards[index].id || card.name !== cards[index].name)) {
    throw new Error('Existing 2025 Topps Chrome WWE data differs from official PDF');
  }
} else {
  catalogue.sets.push(set);
  catalogue.cards.push(...cards);
  catalogue.sets.sort((a, b) => String(b.releaseDate || '').localeCompare(String(a.releaseDate || '')) || a.name.localeCompare(b.name));
  catalogue.cards.sort((a, b) => {
    const setOrder = catalogue.sets.findIndex(item => item.id === a.setId) - catalogue.sets.findIndex(item => item.id === b.setId);
    return setOrder || a.order - b.order;
  });
  catalogue.setCount = catalogue.sets.length;
  catalogue.cardCount = catalogue.cards.length;
  catalogue.generatedAt = new Date().toISOString();
  saveCatalogue(catalogue);
}

const sqlDirIndex = process.argv.indexOf('--sql-dir');
if (sqlDirIndex >= 0) {
  const sqlDir = path.resolve(process.argv[sqlDirIndex + 1]);
  fs.mkdirSync(sqlDir, { recursive: true });
  for (const file of fs.readdirSync(sqlDir)) if (file.endsWith('.sql')) fs.unlinkSync(path.join(sqlDir, file));
  const q = value => value == null ? 'null' : typeof value === 'number' ? String(value) : typeof value === 'boolean' ? String(value) : `'${String(value).replaceAll("'", "''")}'`;
  const values = rows => rows.map(row => '(' + row.map(q).join(',') + ')').join(',\n');
  const statements = [];
  statements.push(`insert into public.catalogue_sets (id,name,short_name,year,manufacturer,release_date,source_file,accent,card_count,subset_count,variant_count) values ${values([[set.id,set.name,set.shortName,set.year,set.manufacturer,set.releaseDate,SOURCE,set.accent,cards.length,groups.length,variants.length]])} on conflict (id) do update set name=excluded.name,short_name=excluded.short_name,release_date=excluded.release_date,source_file=excluded.source_file,accent=excluded.accent,card_count=excluded.card_count,subset_count=excluded.subset_count,variant_count=excluded.variant_count;`);
  statements.push(`insert into public.catalogue_subsets (set_id,subset_code,category,name,card_count,parallel_group,source_url) values ${values(groups.map(group => [SET_ID,group.code,group.category,group.heading,group.rows.length,group.code,SOURCE]))} on conflict (set_id,subset_code) do update set category=excluded.category,name=excluded.name,card_count=excluded.card_count,parallel_group=excluded.parallel_group,source_url=excluded.source_url;`);
  for (let start = 0; start < cards.length; start += 200) {
    const batch = cards.slice(start, start + 200);
    statements.push(`insert into public.catalogue_cards (id,set_id,checklist_order,category,subset_code,card_number,display_name,subject_1,subject_2,roster,rookie,parallel_group,image_status,pricing_status,source_url,notes) values ${values(batch.map(card => [card.id,SET_ID,card.order,card.category,card.subsetCode,card.number,card.name,card.name.split(' / ')[0],card.subject2,card.roster,false,card.parallelGroup,'Missing','Unpriced',SOURCE,'Official Topps 2025 Chrome WWE checklist']))} on conflict (id) do update set checklist_order=excluded.checklist_order,category=excluded.category,subset_code=excluded.subset_code,card_number=excluded.card_number,display_name=excluded.display_name,subject_1=excluded.subject_1,subject_2=excluded.subject_2,roster=excluded.roster,parallel_group=excluded.parallel_group,source_url=excluded.source_url,notes=excluded.notes;`);
  }
  for (let start = 0; start < variants.length; start += 200) {
    const batch = variants.slice(start, start + 200);
    statements.push(`insert into public.catalogue_variants (id,set_id,card_id,variant_order,subset,card_number,display_name,parallel,serial_cap,serial_exact,exclusive_note,numbering_note,verification_status) values ${values(batch.map(variant => [variant.id,SET_ID,variant.cardId,variant.order,variant.subset,variant.number,variant.name,'Frozenfractor Variation',null,null,null,'Official checklist identifies a Frozenfractor variation for this base number','Official checklist verified']))} on conflict (id) do update set card_id=excluded.card_id,variant_order=excluded.variant_order,display_name=excluded.display_name,parallel=excluded.parallel,numbering_note=excluded.numbering_note,verification_status=excluded.verification_status;`);
  }
  statements.push(`insert into public.catalogue_sources (id,set_id,source,purpose,url,notes) values ${values([['2025-topps-chrome-wwe-checklist',SET_ID,'Topps','Checklist',SOURCE,'Official 27-page checklist; stable identities normalized from all base, insert and autograph sections'],['2025-topps-chrome-wwe-product',SET_ID,'Topps','Product index',PRODUCT,'Official Topps checklist index']])} on conflict (id) do update set url=excluded.url,notes=excluded.notes;`);
  statements.push(`insert into public.catalogue_parallel_rules (id,set_id,parallel_group,applies_to,parallel,serial_cap,serial_exact,exclusive_note,numbering_note,verification_status) values ${values([['2025-topps-chrome-wwe-frozenfractor',SET_ID,'BASE-I / BASE-II','BASE CARDS I and II','Frozenfractor Variation',null,null,null,'All 200 subjects are explicitly listed in the official checklist; no serial cap inferred','Official checklist verified']])} on conflict (id) do update set numbering_note=excluded.numbering_note,verification_status=excluded.verification_status;`);
  statements.forEach((statement, index) => fs.writeFileSync(path.join(sqlDir, `${String(index + 1).padStart(2, '0')}.sql`), `begin;\n${statement}\ncommit;\n`, 'utf8'));
}

console.log(`Validated ${cards.length} stable identities across ${groups.length} subsets and ${variants.length} Frozenfractor variants.`);
