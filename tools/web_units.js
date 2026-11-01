// Unit scenarios from the web game's SIM: units, orders, movement and combat on their own.
//   node tools/web_units.js web/dawgs_uprising_v22.5.html tests/golden/units.json
// Test-only hooks in a copy of the SIM source (nothing is published):
//  - "bare" battles start with no garrisons, squads or starting buildings,
//  - walls are left out (BALANCE.walls.types emptied; walls are ported later),
//  - each tick runs only the unit systems: spatial hash, updateUnit, separate, projectiles and dead-unit cleanup
//    (no AI, production, economy, capture, healing or fog),
//  - the battle's random generator is reseeded when the scenario starts.
// Each scenario is a script (spawns and orders at given ticks). Every tick gets a fingerprint of all units, and every
// second the full state of every unit, projectile and army is recorded exactly, so a port that drifts shows when and where.
'use strict';
const fs = require('fs'), vm = require('vm');
const [html, out] = process.argv.slice(2);
if (!out) { console.error('usage: node tools/web_units.js <web.html> <out.json>'); process.exit(2); }
const page = fs.readFileSync(html, 'utf8');
let src = [...page.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]).find(s => s.includes('SIMULATION CORE'));
const swap = (from, to) => { if (!src.includes(from)) throw new Error('hook point not found: ' + from.slice(0, 60)); src = src.replace(from, to); };
swap('const rnd=mulberry32((opts.rngSeed||seed)^0x9e3779b9);',
  'let __r=mulberry32((opts.rngSeed||seed)^0x9e3779b9);const rnd=()=>__r();globalThis.__reseed=s=>{__r=mulberry32(s);};');
swap('  for(const z of G.zones){\n    if(z.owner===null)continue;\n    const n=garrisonCap(z);',
  '  if(!globalThis.__bare)for(const z of G.zones){\n    if(z.owner===null)continue;\n    const n=garrisonCap(z);');
swap('  if(!CVM)for(let f=0;f<NF;f++){\n    const hq=', '  if(!CVM&&!globalThis.__bare)for(let f=0;f<NF;f++){\n    const hq=');
swap('  if(ST.airbaseHangar)for', '  if(ST.airbaseHangar&&!globalThis.__bare)for');
swap('  function tick(dt){\n    G.time+=dt;\n',
  '  function tick(dt){\n    if(globalThis.__unitsOnly){G.time+=dt;pathBudget=10;rebuildHash();for(const u of G.units)if(u.alive)updateUnit(u,dt);separate(dt);updateProjectiles(dt);\n' +
  '      cleanT+=dt;if(cleanT>=1){G.units=G.units.filter(u=>u.alive);cleanT=0;}return;}\n    G.time+=dt;\n');
const ctx = { module: { exports: {} }, console };
vm.createContext(ctx);
vm.runInContext(src, ctx, { filename: 'web-sim.js' });
const SIM = ctx.module.exports;
const version = (page.match(/GAME_VERSION=\{number:'([^']+)'/) || [])[1] || '?';
SIM.BALANCE.walls.types = [];

const dv = new DataView(new ArrayBuffer(8));
const hex = x => { dv.setFloat64(0, x); return dv.getBigUint64(0).toString(16).padStart(16, '0'); };
// fingerprint of every unit (FNV-1a over the 32-bit halves of each number), the same in the port's test
function fp(G) {
  let h = 2166136261;
  const mix = x => { dv.setFloat64(0, x); h = Math.imul(h ^ dv.getUint32(0), 16777619) >>> 0; h = Math.imul(h ^ dv.getUint32(4), 16777619) >>> 0; };
  for (const u of G.units) { mix(u.id); mix(u.alive ? 1 : 0); mix(u.x); mix(u.z); mix(u.ang); mix(u.hp); mix(u.cd); }
  mix(G.projectiles.length);
  return h.toString(16).padStart(8, '0');
}
const idOf = u => u ? u.id : -1;
const unitRow = u => [u.id, u.type, u.f, u.alive, u.mode, hex(u.x), hex(u.z), hex(u.ang), hex(u.hp), hex(u.maxHp), hex(u.cd), hex(u.acqT),
  idOf(u.target), idOf(u.forced), u.path ? u.path.length : -1, u.pi, u.deployed, hex(u.deployT), idOf(u.lastHitBy), u.stance || null, u.guard ? idOf(u.guard.t) : -1];
const projRow = p => [idOf(p.src), idOf(p.tgt), p.wpn, hex(p.ex), hex(p.ez), hex(p.t), hex(p.T)];

// scenarios: spawns [type, f, x, z] and orders [f, kind, ids, a, b] at a tick. Unit ids are the ones spawnUnit
// hands out, in spawn order; an order's target unit is written {uid}.
function sq(types, f, x, z, gap) { return types.map((t, i) => [t, f, x + (i % 4) * gap, z + Math.floor(i / 4) * gap]); }
const SCENARIOS = [
  { name: 'march', map: 'dawgs', seed: 1, rseed: 101, seconds: 30, script: (S) => [
    { at: 0, spawn: sq(['rifle', 'rifle', 'rifle', 'rifle', 'mg', 'at', 'ltank', 'ltank', 'tech'], 0, 70, -64, 2.2) },
    { at: 0, order: [0, 'move', S.ids(0, 9), -100, 53] },
    { at: 0, spawn: sq(['rifle', 'rifle', 'mg', 'mtank'], 0, 150, -88, 2.5) },
    { at: 0, order: [0, 'amove', S.ids(9, 4), 25, -10] },
    { at: 300, order: [0, 'move', S.ids(9, 4), 75, 53] }] },
  { name: 'firefight', map: 'dawgs', seed: 1, rseed: 202, seconds: 40, script: (S) => [
    { at: 0, spawn: sq(['rifle', 'rifle', 'rifle', 'rifle', 'mg', 'mg', 'at'], 0, 22, -14, 2) },
    { at: 0, spawn: sq(['rifle', 'rifle', 'rifle', 'mg', 'mg', 'at', 'how'], 1, -54, 0, 2) },
    { at: 0, order: [0, 'amove', S.ids(0, 7), -50, 3] }] },
  { name: 'armor', map: 'dawgs', seed: 1, rseed: 303, seconds: 40, script: (S) => [
    { at: 0, spawn: sq(['mtank', 'mtank', 'htank', 'spg', 'flak'], 0, 72, -64, 3) },
    { at: 0, spawn: sq(['at', 'at', 'at', 'ltank', 'tech', 'lheli', 'heli', 'sam'], 2, 146, -88, 2.5) },
    { at: 0, order: [0, 'amove', S.ids(0, 5), 150, -85] },
    { at: 60, order: [2, 'amove', [S.id(10), S.id(11)], 90, -66] }] },
  { name: 'orders', map: 'dawgs', seed: 1, rseed: 404, seconds: 30, script: (S) => [
    { at: 0, spawn: sq(['ltank', 'rifle', 'rifle', 'rifle', 'mg', 'at'], 0, 22, -14, 2.2) },
    { at: 0, spawn: sq(['rifle', 'rifle', 'mg'], 1, -10, 30, 2) },
    { at: 0, order: [0, 'guard', [S.id(1), S.id(2), S.id(3)], { uid: S.id(0) }] },
    { at: 0, order: [0, 'move', [S.id(0)], -20, 20] },
    { at: 0, order: [0, 'stance', [S.id(4)], 'hold'] },
    { at: 0, order: [0, 'slots', [S.id(4), S.id(5)], [{ x: 0, z: -20 }, { x: 4, z: -18 }]] },
    { at: 90, order: [1, 'attack', [S.id(6), S.id(7)], { uid: S.id(5) }] },
    { at: 240, order: [1, 'stop', [S.id(6), S.id(7), S.id(8)]] },
    { at: 300, order: [0, 'stance', [S.id(5)], 'ret'] },
    { at: 450, order: [0, 'amove', [S.id(0), S.id(4), S.id(5)], -10, 30] }] },
  { name: 'naval', map: 'dawgs', seed: 1, rseed: 505, seconds: 30, script: (S) => [
    { at: 0, spawn: [['boat', 0, -150, -205], ['boat', 0, -146, -207], ['monitor', 0, -152, -210]] },
    { at: 0, spawn: [['boat', 3, -40, -205], ['boat', 3, -36, -208]] },
    { at: 0, order: [0, 'amove', [S.id(0), S.id(1), S.id(2)], -60, -205] },
    { at: 0, order: [3, 'amove', [S.id(3), S.id(4)], -140, -205] }] },
];

function run(sc) {
  ctx.__bare = true;
  ctx.__unitsOnly = true;
  const G = SIM.createGame({ map: sc.map, seed: sc.seed });
  ctx.__reseed(sc.rseed);
  const id0 = G.nextId;
  const S = { id: k => id0 + k, ids: (k, n) => Array.from({ length: n }, (_, i) => id0 + k + i) };
  const actions = sc.script(S);
  const events = {};
  for (const ev of ['shot', 'death', 'spawn', 'impact', 'raid']) G.on(ev, () => { events[ev] = (events[ev] || 0) + 1; });
  const ticks = Math.round(sc.seconds / G.STEP), every = Math.round(1 / G.STEP);
  const tickFp = [], snaps = [];
  const snap = (k) => snaps.push({ tick: k, time: hex(G.time), units: G.units.map(unitRow), projectiles: G.projectiles.map(projRow),
    factions: G.factions.map(f => [f.kills, f.losses, f.aggro.map(hex)]), events: Object.assign({}, events) });
  for (let k = 0; k <= ticks; k++) {
    for (const a of actions) if (a.at === k) {
      if (a.spawn) for (const [t, f, x, z] of a.spawn) G.spawnUnit(t, f, x, z);
      if (a.order) { const [f, kind, ids, x, z] = a.order; const A = x && x.uid != null ? G.units.find(u => u.id === x.uid) : x; G.orderAs(f, kind, ids, A, z); }
    }
    if (k % every === 0) snap(k);
    if (k === ticks) break;
    G.stepTicks(1);
    tickFp.push(fp(G));
  }
  const last = snaps[snaps.length - 1];
  console.log(`${sc.name}: ${ticks} ticks, ${last.units.filter(u => u[3]).length} units alive, events ${JSON.stringify(events)}`);
  ctx.__bare = ctx.__unitsOnly = false;
  return { map: sc.map, seed: sc.seed, rseed: sc.rseed, ticks, id0, actions, tickFp, snaps };
}

const res = {};
for (const sc of SCENARIOS) res[sc.name] = run(sc);
fs.writeFileSync(out, JSON.stringify({ web: version, runs: res }) + '\n');
console.log('web v' + version + ' -> ' + out);
