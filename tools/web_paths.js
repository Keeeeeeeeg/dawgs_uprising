// Golden pathfinding from the web game: G.findPath on the battle's real ground grid (after setup),
// for random start/goal pairs, plus the grid itself so the SIM tests run on exactly the same cells.
//   node tools/web_paths.js web/dawgs_uprising_v22.5.html tests/golden/paths.json
'use strict';
const fs = require('fs'), vm = require('vm');
const [html, out] = process.argv.slice(2);
if (!out) { console.error('usage: node tools/web_paths.js <web.html> <out.json>'); process.exit(2); }
const page = fs.readFileSync(html, 'utf8');
const simSrc = [...page.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]).find(s => s.includes('SIMULATION CORE'));
const ctx = { module: { exports: {} }, console };
vm.createContext(ctx);
require('./v8_pow.js').install(ctx);   // V8 12.4's Math.pow, so the recording is the same on any Node version
vm.runInContext(simSrc, ctx, { filename: 'web-sim.js' });
const SIM = ctx.module.exports;
const version = (page.match(/GAME_VERSION=\{number:'([^']+)'/) || [])[1] || '?';
const dv = new DataView(new ArrayBuffer(8));
const hex = x => { dv.setFloat64(0, x); return dv.getBigUint64(0).toString(16).padStart(16, '0'); };

let s = 4242;
const rnd = () => { s = (s * 1103515245 + 12345) % 2147483648; return s / 2147483648; };
const res = {};
for (const [name, opts, n] of [['dawgs_s1', { map: 'dawgs', seed: 1 }, 250], ['twinreach_s7', { map: 'twinreach', seed: 7 }, 150]]) {
  const G = SIM.createGame(opts);
  const pass = G.map.pass;
  const qs = [];
  for (let k = 0; k < n; k++) {
    const W = G.WORLD_W, H = G.WORLD_H;
    let sx = G.X0 + rnd() * W, sz = G.Z0 + rnd() * H, tx, tz;
    if (k % 3 === 0) { tx = sx + (rnd() - 0.5) * 60; tz = sz + (rnd() - 0.5) * 60; }   // short hops (line of sight)
    else { tx = G.X0 + rnd() * W; tz = G.Z0 + rnd() * H; }
    const p = G.findPath(sx, sz, tx, tz, pass);
    qs.push([hex(sx), hex(sz), hex(tx), hex(tz), p ? p.map(q => [hex(q.x), hex(q.z)]) : null]);
  }
  res[name] = { opts, W: G.WORLD_W, H: G.WORLD_H, GW: G.GW, GH: G.GH, X0: G.X0, Z0: G.Z0, CELL: G.CELL,
    pass: Buffer.from(pass).toString('base64'), queries: qs };
  console.log(`${name}: ${n} queries, ${qs.filter(q => q[4]).length} found, longest ${Math.max(...qs.map(q => q[4] ? q[4].length : 0))} waypoints`);
}
fs.writeFileSync(out, JSON.stringify({ web: version, runs: res }) + '\n');
