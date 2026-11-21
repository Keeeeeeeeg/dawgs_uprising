const S=require('./load.js')(process.argv[2]);const B=S.BALANCE,UT=S.UTYPES;
const G=S.createGame({map:'twinvalleys',mode:'ffa',ai:[{p:0},{p:1}],seed:4});
const C=G.COMBAT;
const skip=t=>{const d=UT[t];return d.static&&!d.bturret?true:d.rail||d.carrier||t.startsWith('bt')||t.startsWith('cv')||d.struct;};
const T=['rifle','mg','at','tech','ltank','mtank','htank','spg','heli','lheli','cas','bomb','airship'].filter(t=>UT[t]);
const rows=[];
for(const t of Object.keys(UT)){if(skip(t))continue;const d=UT[t];
  const shots=(d.guns||1)*(d.volley||1),acc=d.acc||1,dps=x=>{if(!d.dmg||!(d.range>0||d.weapon==='bomb'))return 0;const e=C.eff(d.weapon,d.dmg,UT[x]);return e*shots*acc/(d.rof||1);};
  let mt=0;if(d.mounts)for(const M of d.mounts){}
  rows.push({t,name:d.name,cost:d.cost,mp:d.mp,hp:d.hp,arm:Math.round(C.armorOf(d)),cls:d.armor,w:d.weapon,dmg:d.dmg,rof:d.rof,rng:d.range,spd:d.speed,
    dps:Object.fromEntries(T.map(x=>[x,+dps(x).toFixed(1)]))});}
console.log(['type','cost','mp','hp','arm','cls','weapon','dmg','rof','rng','spd',...T].join('\t'));
for(const r of rows)console.log([r.t,r.cost,r.mp,r.hp,r.arm,r.cls,r.w,r.dmg,r.rof,r.rng,r.spd,...T.map(x=>r.dps[x])].join('\t'));
