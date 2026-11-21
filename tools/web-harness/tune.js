// tune.js <html> <patch.json>: apply unit/weapon overrides to the SIM's UTYPES/BALANCE in memory and print the matchup report
const S=require('./load.js')(process.argv[2]);const UT=S.UTYPES,B=S.BALANCE;
const P=process.argv[3]?JSON.parse(require('fs').readFileSync(process.argv[3],'utf8')):{};
for(const [k,v] of Object.entries(P.units||{})){if(!UT[k])throw k;Object.assign(UT[k],v);if(B.units[k])Object.assign(B.units[k],v);}
for(const [k,v] of Object.entries(P.weapons||{})){const W=B.weapons[k];for(const [a,b] of Object.entries(v)){if(a==='mods')Object.assign(W.mods,b);else W[a]=b;}}
for(const [k,v] of Object.entries(P.mounts||{})){const M=UT.airship.mounts.find(m=>m.key===k);Object.assign(M,v);}
const G=S.createGame({map:'twinvalleys',mode:'ffa',ai:[{p:0},{p:1}],seed:4});const C=G.COMBAT;
const L=['rifle','mg','at','sniper','tech','ltank','mtank','htank','spg','how','heli','lheli','vtol','qaa','flak','sam','intc','cas','bomb','airship'];
const dps=(a,b)=>{const d=UT[a],t=UT[b];let s=0;
  if(d.dmg&&(d.range>0||d.weapon==='bomb'))s+=C.hit(d.weapon,d.dmg,t)*(d.guns||1)*(d.volley||1)*(d.acc||1)/(d.rof||1)*(d.splash&&t.armor==='inf'?1+Math.min(1.5,d.splash/2.5):1);
  for(const M of d.mounts||[])s+=C.hit(M.weapon,M.dmg,t)*M.n*(M.acc||1)/M.rof;return s;};
const adv=(a,b)=>{const A=dps(a,b),Bd=dps(b,a);if(!A&&!Bd)return null;if(!Bd)return 9;if(!A)return -9;const ca=UT[a].cost,cb=UT[b].cost;return Math.log2((A*UT[a].hp/ca/ca)/(Bd*UT[b].hp/cb/cb));};
const f=x=>x==null?'.':x>=9?'INF':x<=-9?'-INF':x.toFixed(1);
const sel=P.show||L;
console.log(['',...sel].map(x=>x.slice(0,6).padStart(6)).join(''));
for(const a of sel)console.log([a.slice(0,6),...sel.map(b=>f(adv(a,b)))].map(x=>String(x).padStart(6)).join(''));
// targets: [a,b,lo,hi]
let bad=0;for(const [a,b,lo,hi] of P.targets||[]){const v=adv(a,b);const ok=v!=null&&v>=lo&&v<=hi;if(!ok){bad++;console.log('MISS',a,'vs',b,f(v),'want',lo,'..',hi);}}
console.log('misses',bad,'/',(P.targets||[]).length);
// pace: mean time for $400 of a to kill $400 of b (Lanchester-free: total hp / total dps)
if(P.pace)for(const [a,b] of P.pace){const na=400/UT[a].cost,nb=400/UT[b].cost;console.log('pace',a,'kills $400 of',b,'in',(nb*UT[b].hp/(na*dps(a,b))).toFixed(1),'s');}
