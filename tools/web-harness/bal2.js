const S=require('./load.js')(process.argv[2]);const UT=S.UTYPES;
const G=S.createGame({map:'twinvalleys',mode:'ffa',ai:[{p:0},{p:1}],seed:4});const C=G.COMBAT;
const L=['rifle','mg','at','sniper','tech','ltank','mtank','htank','spg','how','heli','lheli','vtol','qaa','flak','sam','intc','cas','bomb','airship'];
const dps=(a,b)=>{const d=UT[a],t=UT[b];let s=0;
  if(d.dmg&&(d.range>0||d.weapon==='bomb'))s+=C.hit(d.weapon,d.dmg,t)*(d.guns||1)*(d.volley||1)*(d.acc||1)/(d.rof||1);
  for(const M of d.mounts||[])s+=C.hit(M.weapon,M.dmg,t)*M.n*(M.acc||1)/M.rof;return s;};
console.log('DPS (expected, per unit):');console.log(['att\\tgt',...L].map(x=>x.padStart(7)).join(''));
for(const a of L)console.log([a,...L.map(b=>dps(a,b).toFixed(1))].map(x=>String(x).padStart(7)).join(''));
console.log('\nEqual-cost Lanchester advantage log2 (row vs col; + = row wins; 0 if neither can hurt):');console.log(['',...L].map(x=>x.padStart(7)).join(''));
for(const a of L)console.log([a,...L.map(b=>{const A=dps(a,b),Bd=dps(b,a);if(!A&&!Bd)return '.';if(!Bd)return 'INF';if(!A)return '-INF';
  const ca=UT[a].cost,cb=UT[b].cost,r=(A*UT[a].hp/ca/ca)/(Bd*UT[b].hp/cb/cb);return Math.log2(r).toFixed(1);})].map(x=>String(x).padStart(7)).join(''));
console.log('\nHP/$ and ranges:');for(const a of L){const d=UT[a];console.log(a.padEnd(8),'$'+d.cost,'mp'+d.mp,'hp/$',(d.hp/d.cost).toFixed(2),'rng',d.range,'spd',d.speed.toFixed(1),'arm',C.armorOf(d),'cls',d.armor);}
