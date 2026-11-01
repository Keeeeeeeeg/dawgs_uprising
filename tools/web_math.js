// Reference results for the SIM's DMath from V8 itself. Needs Node 22 (V8 12.4), the V8 the port reproduces.
//   node tools/web_math.js tests/golden/math.json
// Inputs and outputs are stored as 64-bit hex patterns so the SIM tests can compare every bit.
'use strict';
if (!process.versions.v8.startsWith('12.4.')) { console.error('web_math.js records V8 Math itself, so it needs the V8 the port matches: Node 22 (V8 12.4). This is V8 ' + process.versions.v8 + '.'); process.exit(2); }
const fs = require('fs');
const out = process.argv[2];
if (!out) { console.error('usage: node tools/web_math.js <out.json>'); process.exit(2); }

const buf = new DataView(new ArrayBuffer(8));
const hex = x => { buf.setFloat64(0, x); return buf.getBigUint64(0).toString(16).padStart(16, '0'); };
// a fixed-seed generator so the file is the same every run
let s = 12345;
const rnd = () => { s = (s * 1103515245 + 12345) % 2147483648; return s / 2147483648; };
const R = (a, b) => a + rnd() * (b - a);

const cases = { sin: [], cos: [], atan2: [], pow: [], hypot: [], hypot3: [], round: [] };
const one = (fn, name, ...args) => cases[name].push([...args.map(hex), hex(fn(...args))]);

const angles = [0, -0, 1e-9, -1e-9, 0.5, 0.785398, 1, Math.PI / 2, Math.PI, 2 * Math.PI, 6.283, 6.28, 3, -3, 10, 100, 1000, 12345.678];
for (let k = -8; k <= 8; k++) angles.push(k * Math.PI / 4, k * Math.PI / 2 + 1e-12);
for (let i = 0; i < 1500; i++) angles.push(R(-30, 30));
for (let i = 0; i < 300; i++) angles.push(R(-3000, 3000));
for (const a of angles) { one(Math.sin, 'sin', a); one(Math.cos, 'cos', a); }

const pairs = [[0, 0], [0, -1], [-0, -1], [1, 0], [-1, 0], [0, 1], [1, 1], [-1, -1], [1, -1], [-1, 1], [3, 4], [1e-300, 1], [1, 1e-300]];
for (let i = 0; i < 1500; i++) pairs.push([R(-500, 500), R(-500, 500)]);
for (let i = 0; i < 200; i++) pairs.push([R(-1, 1), R(-1e-3, 1e-3)]);
for (const [y, x] of pairs) { one(Math.atan2, 'atan2', y, x); one(Math.hypot, 'hypot', y, x); }
for (let i = 0; i < 500; i++) one(Math.hypot, 'hypot3', R(-300, 300), R(-50, 50), R(-300, 300));

const pw = [[2, 10], [2, 0.5], [0, 1.3], [1, 1.3], [-2, 3], [-2, 2], [-8, 1 / 3], [10, -2], [0.5, 1.5], [1e-5, 1.3]];
for (let i = 0; i < 800; i++) pw.push([R(0, 1), 1.3]);
for (let i = 0; i < 400; i++) pw.push([R(0, 1), 1.5]);
for (let i = 0; i < 400; i++) pw.push([R(0, 5), R(-4, 4)]);
for (let i = 0; i < 200; i++) pw.push([R(0.5, 3), R(0, 2)]);
for (const [x, y] of pw) one(Math.pow, 'pow', x, y);

const rd = [0.5, -0.5, 1.5, -1.5, 2.5, -2.5, 0.49999999999999994, -0.49999999999999994, 4503599627370495.5, -4503599627370495.5, 1e20, -1e20, 0, -0];
for (let i = 0; i < 500; i++) rd.push(R(-1000, 1000));
for (let i = 0; i < 100; i++) rd.push(Math.floor(R(-100, 100)) + 0.5);
for (const x of rd) one(Math.round, 'round', x);

fs.writeFileSync(out, JSON.stringify({ v8: process.versions.v8, cases }) + '\n');
console.log('V8', process.versions.v8, Object.entries(cases).map(([k, v]) => k + ' ' + v.length).join(', '));
