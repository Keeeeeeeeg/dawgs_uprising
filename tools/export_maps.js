// Export the web game's finished map definitions to godot/data/maps.json, plus an exact
// fingerprint for the tests. Runs only the SIM script (no DOM), like tools/web_trace.js.
//   node tools/export_maps.js web/dawgs_uprising_v22.5.html godot/data/maps.json godot/tests/golden/maps.json
//
// Numbers that Godot's JSON reader parses exactly (up to 12 significant digits) are written as
// plain numbers. Longer ones are written as "#<16 hex digits>" (the exact 64-bit pattern); the
// Godot loader (sim/maps.gd) turns those back into the identical double.
// Chaos Isles is not exported: it is rolled every battle by sim/maps.gd. The golden file holds
// web-built Chaos maps for a few seeds so that port can be checked.
'use strict';
const fs = require('fs'), vm = require('vm');
const [html, outMaps, outGolden] = process.argv.slice(2);
if (!outGolden) { console.error('usage: node tools/export_maps.js <web.html> <maps.json> <golden.json>'); process.exit(2); }
const page = fs.readFileSync(html, 'utf8');
const simSrc = [...page.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]).find(s => s.includes('SIMULATION CORE'));
const ctx = { module: { exports: {} }, console };
vm.createContext(ctx);
vm.runInContext(simSrc, ctx, { filename: 'web-sim.js' });
const SIM = ctx.module.exports;
const version = (page.match(/GAME_VERSION=\{number:'([^']+)'/) || [])[1] || '?';

const dv = new DataView(new ArrayBuffer(8));
const hex = x => { dv.setFloat64(0, x); return dv.getBigUint64(0).toString(16).padStart(16, '0'); };
const enc = x => !Object.is(x, -0) && (Number.isInteger(x) || Number(x.toPrecision(12)) === x) ? x : '#' + hex(x); // JSON would turn -0 into 0

// the fields a map needs; everything else on the web object is derived at runtime
const KEYS = ['id', 'name', 'desc', 'W', 'H', 'ns', 'maxPlayers', 'blobs', 'necks', 'carves', 'ridges', 'zones', 'slots', 'mix',
  'palette', 'noWater', 'hidden', 'carrier', 'large', 'balanced', 'fixedTypes', 'generated'];
function pack(v) {
  if (typeof v === 'number') return enc(v);
  if (Array.isArray(v)) return v.map(pack);
  if (v && typeof v === 'object') { const o = {}; for (const k of Object.keys(v)) if (v[k] !== undefined) o[k] = pack(v[k]); return o; }
  return v;
}
function mapOut(m) { const o = {}; for (const k of KEYS) if (m[k] !== undefined && m[k] !== false) o[k] = pack(m[k]); return o; }
// every number of a map, in a fixed order, as exact hex: what the test compares
function fingerprint(v, out = []) {
  if (typeof v === 'number') out.push(hex(v));
  else if (Array.isArray(v)) v.forEach(x => fingerprint(x, out));
  else if (v && typeof v === 'object') for (const k of Object.keys(v).sort()) fingerprint(v[k], out);
  return out;
}

const ids = Object.keys(SIM.MAPS).filter(id => id !== 'chaos');
const maps = {};
for (const id of ids) maps[id] = mapOut(SIM.MAPS[id]);
const longNums = JSON.stringify(maps).match(/"#[0-9a-f]{16}"/g) || [];
fs.writeFileSync(outMaps, JSON.stringify({ _about: `Map definitions exported from web v${version} by tools/export_maps.js. "#hex" = exact 64-bit value.`, web: version, maps }, null, 1) + '\n');

const golden = { web: version, maps: {}, chaos: {} };
const rawOut = m => { const o = {}; for (const k of KEYS) if (m[k] !== undefined && m[k] !== false) o[k] = m[k]; return o; };
for (const id of ids) golden.maps[id] = fingerprint(rawOut(SIM.MAPS[id]));
// Chaos Isles is made inside createGame from the battle seed; makeChaosMap is private, so build games
for (const seed of [8, 1234, 99, 20261017]) {
  const G = SIM.createGame({ map: 'chaos', seed });
  const m = SIM.MAPS.chaos;
  golden.chaos[seed] = { map: pack(Object.fromEntries(KEYS.filter(k => m[k] !== undefined && k !== 'desc').map(k => [k, m[k]]))) };
}
fs.writeFileSync(outGolden, JSON.stringify(golden) + '\n');
console.log(`web v${version}: ${ids.length} maps (${ids.join(' ')}), ${longNums.length} long numbers stored as hex; chaos goldens: ${Object.keys(golden.chaos).join(' ')}`);
