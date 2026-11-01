// Golden battle setup from the web game, captured at checkpoints inside createGame (test-only hooks
// in a copy of the SIM source; nothing is published). Each checkpoint records how many numbers the
// battle's random generator has drawn so far, so a port that drifts shows at which step.
//   node tools/web_setup.js web/dawgs_uprising_v22.5.html tests/golden/setup.json
'use strict';
const fs = require('fs'), vm = require('vm');
const [html, out] = process.argv.slice(2);
if (!out) { console.error('usage: node tools/web_setup.js <web.html> <out.json>'); process.exit(2); }
const page = fs.readFileSync(html, 'utf8');
let src = [...page.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]).find(s => s.includes('SIMULATION CORE'));
const hook = (at, code) => { if (!src.includes(at)) throw new Error('hook point not found: ' + at); src = src.replace(at, code + at); };
// count the battle generator's draws
const RND = 'const rnd=mulberry32((opts.rngSeed||seed)^0x9e3779b9);';
if (!src.includes(RND)) throw new Error('rnd definition not found');
src = src.replace(RND, 'const __r=mulberry32((opts.rngSeed||seed)^0x9e3779b9);let __rc=0;const rnd=()=>{__rc++;return __r();};globalThis.__cp={};');
// checkpoint 2: build plots laid out (streets, runways, plots, levelled ground)
hook('  // ---- buildings: placed by Construction Rovers', "globalThis.__cp.plots={rc:__rc,zones:structuredClone(G.zones.map(z=>({id:z.id,gate:z.gate,budget:z.budget,port:z.port,slots:z.slots,spots:z.spots,air:z.air,cove:z.cove,y:z.y}))),streets:structuredClone(streets),hv:require_sha(hv),pass:require_sha(pass)};\n");
// checkpoint 3: starting forces (walls, courtyards, gates, garrisons, squads, starting buildings)
hook('  // ---- campaign: pre-battle bonuses', "globalThis.__cp.forces={rc:__rc,nextId:G.nextId," +
  "units:G.units.map(u=>({id:u.id,type:u.type,f:u.f,x:u.x,z:u.z,ang:u.ang,hp:u.hp,maxHp:u.maxHp,cd:u.cd,acqT:u.acqT,ax:u.ax,az:u.az,lx:u.lx,lz:u.lz," +
  "garrison:u.garrison,zoneMade:u.zoneMade??null,home:u.home??null,roverHome:u.roverHome??null,gateOf:u.gateOf??null,garFlag:!!u.garFlag})),"  +
  "zones:G.zones.map(z=>({id:z.id,walled:!!z.walled,breached:!!z.breached,gateOpen:z.gateOpen??null,gateU:z.gateU?z.gateU.id:null," +
  "wallCells:z.wallCells?require_sha(new Int32Array(z.wallCells)):null,yard:z.yard?require_sha(new Int32Array(z.yard)):null,msl:z.msl,mslT:z.mslT," +
  "used:z.spots.map(s=>!!s.used),plots:z.plots.map(p=>({i:p.i,x:p.x,z:p.z,y:p.y,ang:p.ang,kind:p.kind,zone:p.zone,water:p.water||null,body:p.body?p.body.id:null," +
  "fac:p.fac&&{type:p.fac.type,level:p.fac.level,state:p.fac.state,t:p.fac.t,T:p.fac.T,prodT:p.fac.prodT,prodI:p.fac.prodI,pstate:p.fac.pstate}}))}))," +
  "props:map.props.filter(p=>p.town!=null).map(p=>structuredClone(p)),pass:require_sha(pass),cellZone:require_sha(cellZone),wallCell:require_sha(wallCell)," +
  "teamPass:teamPass.map(require_sha)};\n");
// checkpoint 1: armies and bases set up (before build plots)
hook('  // ---- build plots: each base grows', 'globalThis.__cp.zones={rc:__rc,factions:structuredClone(F),zones:structuredClone(G.zones),home:G.home,homes:G.homes.slice()};\n');
const crypto = require('crypto');
const require_sha = a => crypto.createHash('sha256').update(Buffer.from(a.buffer, a.byteOffset, a.byteLength)).digest('hex');
const ctx = { module: { exports: {} }, console, structuredClone, require_sha };
vm.createContext(ctx);
require('./v8_pow.js').install(ctx);   // V8 12.4's Math.pow, so the recording is the same on any Node version
vm.runInContext(src, ctx, { filename: 'web-sim.js' });
const SIM = ctx.module.exports;
const version = (page.match(/GAME_VERSION=\{number:'([^']+)'/) || [])[1] || '?';
const dv = new DataView(new ArrayBuffer(8));
const hex = x => { dv.setFloat64(0, x); return dv.getBigUint64(0).toString(16).padStart(16, '0'); };
const exact = v => typeof v === 'number' ? (Object.is(v, -0) || !Number.isInteger(v) ? '#' + hex(v) : v)
  : Array.isArray(v) ? v.map(exact) : v && typeof v === 'object' ? Object.fromEntries(Object.entries(v).map(([k, x]) => [k, exact(x)])) : v;

const RUNS = [
  ['dawgs_s1', { map: 'dawgs', seed: 1 }],
  ['tutorial', { map: 'tutorial', seed: 3 }],
  ['twinreach_teams', { map: 'twinreach', seed: 5, mode: 'teams', ai: [{ p: 0, team: 1 }, { p: 1, team: 2 }, { p: 2, team: 2, diff: 'easy' }, { p: 3, team: 3, diff: 'normal' }] }],
  ['crown_8', { map: 'crown', seed: 11, ai: Array.from({ length: 7 }, (_, i) => ({ p: i, team: i + 2 })) }],
  ['chaos_s8', { map: 'chaos', seed: 8 }],
];
const res = {};
for (const [name, opts] of RUNS) {
  SIM.createGame(opts);
  const cp = ctx.__cp;
  res[name] = { opts, checkpoints: exact(cp) };
  console.log(`${name}: ` + Object.entries(cp).map(([k, v]) => `${k} after ${v.rc} draws`).join(', '));
}
fs.writeFileSync(out, JSON.stringify({ web: version, runs: res }) + '\n');
