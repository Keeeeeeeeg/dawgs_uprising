// Army profiles -> data/factions.json, and the web SIM's derived tables (UTYPES, ZTYPES,
// FACILITIES) -> golden file, so the SIM's Tables can be checked against them.
//   node tools/web_tables.js web/dawgs_uprising_v22.5.html data/factions.json tests/golden/tables.json
'use strict';
const fs = require('fs'), vm = require('vm');
const [html, outFactions, outGolden] = process.argv.slice(2);
if (!outGolden) { console.error('usage: node tools/web_tables.js <web.html> <factions.json> <golden.json>'); process.exit(2); }
const page = fs.readFileSync(html, 'utf8');
const simSrc = [...page.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]).find(s => s.includes('SIMULATION CORE'));
const ctx = { module: { exports: {} }, console };
vm.createContext(ctx);
vm.runInContext(simSrc, ctx, { filename: 'web-sim.js' });
const SIM = ctx.module.exports;
const version = (page.match(/GAME_VERSION=\{number:'([^']+)'/) || [])[1] || '?';
const dv = new DataView(new ArrayBuffer(8));
const hex = x => { dv.setFloat64(0, x); return dv.getBigUint64(0).toString(16).padStart(16, '0'); };
const exact = v => typeof v === 'number' ? (Object.is(v, -0) || !Number.isInteger(v) ? '#' + hex(v) : v)
  : Array.isArray(v) ? v.map(exact) : v && typeof v === 'object' ? Object.fromEntries(Object.entries(v).map(([k, x]) => [k, exact(x)])) : v;

// colours as "#rrggbb" so the file is readable; css kept as the web had it
const fac = f => Object.assign({}, f, { color: '#' + f.color.toString(16).padStart(6, '0') });
fs.writeFileSync(outFactions, JSON.stringify({
  _about: `Armies from web v${version} (PLAYER_FACTION + AI_POOL), exported by tools/web_tables.js. comp = unit mix weights, prefer = base types it wants more.`,
  player: fac(SIM.PLAYER_FACTION), ai: SIM.AI_POOL.map(fac) }, null, 1) + '\n');
fs.writeFileSync(outGolden, JSON.stringify({ web: version, UTYPES: exact(SIM.UTYPES), ZTYPES: exact(SIM.ZTYPES), FACILITIES: exact(SIM.FACILITIES) }) + '\n');
console.log(`web v${version}: ${SIM.AI_POOL.length} AI armies; ${Object.keys(SIM.UTYPES).length} unit types, ${Object.keys(SIM.ZTYPES).length} zone types, ${Object.keys(SIM.FACILITIES).length} facilities`);
