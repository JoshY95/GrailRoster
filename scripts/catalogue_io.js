const { execFileSync } = require('node:child_process');
const path = require('node:path');
const helper = path.join(__dirname, 'catalogue_io.py');
exports.loadCatalogue = () => JSON.parse(execFileSync('python', [helper, '--read'], {encoding: 'utf8', maxBuffer: 32 * 1024 * 1024}));
exports.saveCatalogue = catalogue => execFileSync('python', [helper, '--write'], {input: JSON.stringify(catalogue), encoding: 'utf8', maxBuffer: 32 * 1024 * 1024});
