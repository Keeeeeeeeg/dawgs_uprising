// Golden traces from the web game's SIM, for checking the Godot port against it.
//   node tools/web_trace.js web/dawgs_uprising_v22.5.html godot/tests/golden
// Runs only the SIM script (no DOM, renderer or menus) in Node, steps it in 0.25 s chunks like
// the web harness, and writes one JSON file per scenario plus rng.json and terrain.json.
// Re-run it whenever web/ is updated, and commit the new golden files with the port change.
'use strict';
const fs = require('fs'), path = require('path'), os = require('os'), vm = require('vm');
const [html, outDir] = process.argv.slice(2);
if (!html || !outDir) { console.error('usage: node tools/web_trace.js <web.html> <out_dir>'); process.exit(2); }

// --- load the SIM script out of the single-file game, in its own context ---
const page = fs.readFileSync(html, 'utf8');
const simSrc = [...page.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]).find(s => s.includes('SIMULATION CORE'));
if (!simSrc) throw new Error('No SIMULATION CORE script in ' + html);
const ctx = { module: { exports: {} }, console };
vm.createContext(ctx);
vm.runInContext(simSrc, ctx, { filename: 'web-sim.js' });
const SIM = ctx.module.exports;
const version = (page.match(/GAME_VERSION=\{number:'([^']+)'/) || [])[1] || '?';

const CHUNK = 0.25;          // G.update() caps each call at 0.25 s
const r6 = v => Math.round(v * 1e6) / 1e6;
fs.mkdirSync(outDir, { recursive: true });
const write = (name, obj) => fs.writeFileSync(path.join(outDir, name), JSON.stringify(obj) + '\n');

// --- terrain: heights and passability on a coarse grid, per map (phase 1 checks) ---
function terrain(mapId, seed) {
  const G = SIM.createGame({ map: mapId, seed });
  const pts = [];
  const nx = 24, nz = 24;
  for (let i = 0; i <= nx; i++) for (let j = 0; j <= nz; j++) {
    const x = G.X0 + G.WORLD_W * i / nx, z = G.Z0 + G.WORLD_H * j / nz;
    pts.push([r6(x), r6(z), r6(G.heightAt(x, z)), G.passable(x, z) ? 1 : 0]);
  }
  return { map: mapId, seed, W: G.WORLD_W, H: G.WORLD_H, X0: G.X0, Z0: G.Z0, GW: G.GW, GH: G.GH,
    zones: G.zones.map(z => ({ id: z.id, type: z.type, x: r6(z.x), z: r6(z.z), r: r6(z.r), owner: z.owner })),
    units0: G.units.length, hash0: G.stateHash(), pts };
}

// --- battle trace: snapshot every second ---
function trace(name, opts, seconds) {
  const G = SIM.createGame(opts);
  const events = {};
  for (const ev of ['shot', 'death', 'spawn', 'zone', 'produced', 'end', 'eliminated', 'impact', 'missile'])
    G.on(ev, () => { events[ev] = (events[ev] || 0) + 1; });
  const snaps = [];
  const snap = () => snaps.push({
    t: r6(G.time), hash: G.stateHash(),
    units: G.units.filter(u => u.alive).length,
    money: G.factions ? G.factions.map(f => r6(f.money)) : null,
    owners: G.zones.map(z => z.owner == null ? -1 : z.owner),
    first: G.units.filter(u => u.alive).slice(0, 12).map(u => [u.id, u.type, u.f, r6(u.x), r6(u.z), r6(u.hp)]),
    events: Object.assign({}, events)
  });
  snap();
  const per = Math.round(1 / CHUNK);
  for (let s = 1; s <= seconds && !G.over; s++) {
    for (let k = 0; k < per; k++) G.update(CHUNK);
    snap();
  }
  write(name + '.json', { name, opts, chunk: CHUNK, seconds, web: version, over: !!G.over, snaps });
  const last = snaps[snaps.length - 1];
  console.log(`${name}: ${snaps.length - 1}s, units ${last.units}, hash ${last.hash}, events ${JSON.stringify(last.events)}`);
}

// --- rng: the seeded generator the whole SIM depends on ---
// mulberry32 is private inside the SIM, so this is a byte-for-byte copy of the web source line.
function mulberry32(a){return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};}
const rng = {};
for (const seed of [1, 7, 20261017, (20261017 ^ 0x9e3779b9) | 0, -5]) { const r = mulberry32(seed); rng[seed] = Array.from({ length: 16 }, r); }
write('rng.json', { web: version, mulberry32: rng });

const maps = Object.keys(SIM.MAPS).filter(k => !SIM.MAPS[k].carrier && !SIM.MAPS[k].chaos);
write('terrain.json', { web: version, maps: maps.map(m => terrain(m, 20261017)) });
console.log('terrain:', maps.join(' '));

trace('skirmish_dawgs_s1', { map: 'dawgs', seed: 1 }, 180);
trace('skirmish_twinreach_s7', { map: 'twinreach', seed: 7 }, 180);
trace('carrier_1v1_s3', { map: 'seawar', seed: 3 }, 120);
console.log('web v' + version + ' -> ' + outDir);
