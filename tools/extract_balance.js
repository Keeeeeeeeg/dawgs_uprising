// Regenerate balance data from the web game WITHOUT running it: parses the SIM script, converts the
// BALANCE literal to JSON and lists the SIM's functions. Merge the result into data/balance.json
// by hand (keep the "engine" section, which only the port has).
//   npm i acorn@8 acorn-walk@8
//   node tools/extract_balance.js web/dawgs_uprising_v22.5.html <out_dir>
// Writes <out_dir>/balance.json and <out_dir>/sim_functions.tsv (name, line, lines, chars).
const fs = require('fs'), path = require('path');
const acorn = require('acorn'), walk = require('acorn-walk');
const [src, out] = process.argv.slice(2);
let code = fs.readFileSync(src, 'utf8');
if (src.endsWith('.html')) { // pick the SIM script out of the single-file game
  const sim = [...code.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]).find(s => s.includes('SIMULATION CORE'));
  if (!sim) throw new Error('No SIMULATION CORE script in ' + src);
  code = sim;
}
const ast = acorn.parse(code, { ecmaVersion: 'latest', sourceType: 'script', locations: true });

const consts = {}; // top-level-ish const NAME = literal, for resolving identifiers
const unresolved = [];
let balanceNode = null;
walk.full(ast, n => {
  if (n.type === 'VariableDeclarator' && n.id.type === 'Identifier' && n.init) {
    if (n.id.name === 'BALANCE') balanceNode = n.init;
    else if (!(n.id.name in consts)) consts[n.id.name] = n.init;
  }
});

function lit(n, where) {
  switch (n.type) {
    case 'Literal': return n.value;
    case 'TemplateLiteral': if (!n.expressions.length) return n.quasis[0].value.cooked; break;
    case 'ArrayExpression': return n.elements.map((e, i) => e ? lit(e, where + '[' + i + ']') : null);
    case 'ObjectExpression': {
      const o = {};
      for (const p of n.properties) {
        if (p.type !== 'Property') { unresolved.push(where + ' (spread)'); continue; }
        const k = p.key.type === 'Identifier' && !p.computed ? p.key.name : (p.key.value ?? null);
        if (k == null) { unresolved.push(where + ' (computed key)'); continue; }
        if (p.value.type.includes('Function')) { unresolved.push(where + '.' + k + ' (function)'); continue; }
        o[k] = lit(p.value, where + '.' + k);
      }
      return o;
    }
    case 'UnaryExpression': {
      const v = lit(n.argument, where);
      if (typeof v === 'number') { if (n.operator === '-') return -v; if (n.operator === '+') return v; }
      if (n.operator === '!') return !v;
      break;
    }
    case 'BinaryExpression': {
      const a = lit(n.left, where), b = lit(n.right, where);
      if (typeof a === 'number' && typeof b === 'number') {
        switch (n.operator) { case '*': return a * b; case '/': return a / b; case '+': return a + b; case '-': return a - b; case '**': return a ** b; }
      }
      break;
    }
    case 'MemberExpression':
      if (n.object.name === 'Math' && n.property.name === 'PI') return Math.PI;
      break;
    case 'Identifier':
      if (n.name === 'undefined') return null;
      if (n.name === 'Infinity') return 1e30;
      if (consts[n.name]) return lit(consts[n.name], where + '<' + n.name + '>');
      break;
  }
  unresolved.push(where + ' = ' + code.slice(n.start, Math.min(n.end, n.start + 60)));
  return null;
}

const bal = lit(balanceNode, 'BALANCE');
fs.writeFileSync(path.join(out, 'balance.json'), JSON.stringify(bal, null, 1));

// SIM function inventory: name, line, length in lines
const fns = [];
walk.full(ast, n => {
  if (n.type === 'FunctionDeclaration' && n.id) fns.push([n.id.name, n.loc.start.line, n.loc.end.line - n.loc.start.line + 1, code.slice(n.start, n.end).length]);
  if (n.type === 'VariableDeclarator' && n.id.type === 'Identifier' && n.init && /Function/.test(n.init.type))
    fns.push([n.id.name, n.loc.start.line, n.loc.end.line - n.loc.start.line + 1, code.slice(n.init.start, n.init.end).length]);
});
fs.writeFileSync(path.join(out, 'sim_functions.tsv'), fns.map(f => f.join('\t')).join('\n'));
console.log('BALANCE top-level keys:', Object.keys(bal).length, Object.keys(bal).join(' '));
console.log('JSON bytes:', JSON.stringify(bal).length, ' unresolved:', unresolved.length);
console.log(unresolved.slice(0, 40).join('\n'));
console.log('functions:', fns.length);
