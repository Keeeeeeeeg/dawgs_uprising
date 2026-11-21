// def.js <html> <patch|-> "def:att:budget,..." : one defence (f1) vs budget $ of attackers (f0) that attack-move onto it
const S=require('./load.js')(process.argv[2]);const UT=S.UTYPES,B=S.BALANCE;
const P=process.argv[3]&&process.argv[3]!=='-'?JSON.parse(require('fs').readFileSync(process.argv[3],'utf8')):{};
for(const [k,v] of Object.entries(P.units||{})){Object.assign(UT[k],v);if(B.units[k])Object.assign(B.units[k],v);}
for(const [k,v] of Object.entries(P.weapons||{})){const W=B.weapons[k];for(const [a,b] of Object.entries(v)){if(a==='mods')Object.assign(W.mods,b);else W[a]=b;}}
for(const [k,v] of Object.entries(P.defs||{}))Object.assign(UT[k],v);
function run(dt,at,bud,seed){const G=S.createGame({map:'twinvalleys',mode:'ffa',ai:[{p:0},{p:1}],seed});for(const F of G.factions)F.ai=null;
  for(const u of G.units.slice())if(!u.def.static&&!u.def.struct&&!u.def.rail)u.alive=false;
  let X=0,Z=0,best=-1;for(let k=0;k<400;k++){const x=-150+((k*37)%300),z=-100+((k*53)%200);let ok=1;for(let i=-30;i<=30;i+=5)for(let j=-12;j<=12;j+=4)if(!G.passable(x+i,z+j)||Math.abs(G.heightAt(x+i,z+j)-G.heightAt(x,z))>1.5)ok=0;
    const dz=Math.min(...G.zones.map(q=>Math.hypot(q.x-x,q.z-z)));if(ok&&dz>best){best=dz;X=x;Z=z;}}
  const D=G.spawnUnit(dt,1,X+12,Z);const n=Math.max(1,Math.round(bud/UT[at].cost)),A=[];
  for(let i=0;i<n;i++){const u=G.spawnUnit(at,0,X-25-(i%3)*2,Z+(Math.floor(i/3)-n/6)*2.2);if(u)A.push(u);}
  let t=0;for(;t<150;t+=.25){if(t%5===0)G.orderAs(0,'amove',A.filter(u=>u.alive).map(u=>u.id),X+12,Z);G.update(.25);if(!D.alive||!A.some(u=>u.alive))break;}
  return {d:D.alive?D.hp/D.maxHp:0,a:A.filter(u=>u.alive).reduce((s,u)=>s+u.hp/u.maxHp,0)/n,t};}
for(const q of process.argv[4].split(',')){const [dt,at,bud]=q.split(':');let d=0,a=0,tt=0;const N=3;for(let s=1;s<=N;s++){const r=run(dt,at,+bud,s);d+=r.d;a+=r.a;tt+=r.t;}
  console.log((dt+' vs $'+bud+' '+at).padEnd(26),'def',(d/N*100).toFixed(0).padStart(4)+'%','att',(a/N*100).toFixed(0).padStart(4)+'%','t',(tt/N).toFixed(0)+'s');}
