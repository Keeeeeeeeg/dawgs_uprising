// Golden terrain from the web game: exactly what buildMap() returns for each map, copied at that moment
// (later setup steps flatten plots, add walls and outskirt props to the same arrays). Test-only hook: a copy of the SIM source gets one extra line that hands the
// fresh terrain to this script. Nothing is published.
//   node tools/web_terrain.js web/dawgs_uprising_v22.5.html godot/tests/golden/terrain0.json
// Per map: zonesFinal (after start slots), SHA-256 of the heights (Float32 bytes), passability and
// water grids, every prop and cove, and 400 sample heights as exact hex for pinpointing differences.
'use strict';
const fs = require('fs'), vm = require('vm'), crypto = require('crypto');
const [html, out] = process.argv.slice(2);
if (!out) { console.error('usage: node tools/web_terrain.js <web.html> <out.json>'); process.exit(2); }
const page = fs.readFileSync(html, 'utf8');
let simSrc = [...page.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]).find(s => s.includes('SIMULATION CORE'));
const HOOK_AT = 'const {hv,VW,pass,wpass}=map;';
if (!simSrc.includes(HOOK_AT)) throw new Error('hook point not found; the web SIM changed');
simSrc = simSrc.replace(HOOK_AT, HOOK_AT + 'globalThis.__terrain0={map:{hv:map.hv.slice(),pass:map.pass.slice(),wpass:map.wpass.slice(),props:structuredClone(map.props),coves:structuredClone(map.coves)},zonesFinal:structuredClone(zonesFinal),W:WORLD_W,H:WORLD_H,GW,GH,VW,slotOf:slotOf.slice()};');
const ctx = { module: { exports: {} }, console };
ctx.structuredClone = structuredClone;
vm.createContext(ctx);
vm.runInContext(simSrc, ctx, { filename: 'web-sim.js' });
const SIM = ctx.module.exports;
const version = (page.match(/GAME_VERSION=\{number:'([^']+)'/) || [])[1] || '?';

const dv = new DataView(new ArrayBuffer(8));
const hex = x => { dv.setFloat64(0, x); return dv.getBigUint64(0).toString(16).padStart(16, '0'); };
const sha = a => crypto.createHash('sha256').update(Buffer.from(a.buffer, a.byteOffset, a.byteLength)).digest('hex');
const exact = v => typeof v === 'number' ? (Object.is(v, -0) || !Number.isInteger(v) ? '#' + hex(v) : v)
  : Array.isArray(v) ? v.map(exact) : v && typeof v === 'object' ? Object.fromEntries(Object.entries(v).map(([k, x]) => [k, exact(x)])) : v;

const runs = [];
const maps = Object.keys(SIM.MAPS).filter(k => !SIM.MAPS[k].carrier && k !== 'chaos');
for (const m of maps) runs.push({ name: m, opts: { map: m, seed: 20261017 } });
runs.push({ name: 'twinreach_teams', opts: { map: 'twinreach', seed: 5, mode: 'teams', ai: [{ p: 0, team: 1 }, { p: 1, team: 2 }, { p: 2, team: 2 }, { p: 3, team: 3 }] } });
runs.push({ name: 'chaos_s8', opts: { map: 'chaos', seed: 8 } });
runs.push({ name: 'chaos_s77', opts: { map: 'chaos', seed: 77, ai: Array.from({ length: 9 }, (_, i) => ({ p: i % 15, team: i + 2 })) } });

const res = {};
for (const r of runs) {
  SIM.createGame(r.opts);
  const t = ctx.__terrain0, M = t.map, hv = M.hv;
  const samples = [];
  for (let k = 0; k < 400; k++) { const i = Math.floor(k * 7919 % hv.length); samples.push([i, hex(hv[i])]); }
  res[r.name] = { opts: r.opts, W: t.W, H: t.H, GW: t.GW, GH: t.GH, slotOf: t.slotOf, zonesFinal: exact(t.zonesFinal),
    hv: sha(hv), pass: sha(M.pass), wpass: sha(M.wpass), passCount: M.pass.reduce((a, b) => a + b, 0), wpassCount: M.wpass.reduce((a, b) => a + b, 0),
    props: exact(M.props), coves: exact(M.coves), samples };
  console.log(`${r.name}: ${t.GW}x${t.GH} cells, land cells ${res[r.name].passCount}, props ${M.props.length}, coves ${M.coves.length}`);
}
fs.writeFileSync(out, JSON.stringify({ web: version, runs: res }) + '\n');
