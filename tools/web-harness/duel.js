// duel.js <html> <patch.json|-> : even-cost fights in the real SIM (spawned 34 m apart on open ground, no AI)
const S=require('./load.js')(process.argv[2]);const UT=S.UTYPES,B=S.BALANCE;
const P=process.argv[3]&&process.argv[3]!=='-'?JSON.parse(require('fs').readFileSync(process.argv[3],'utf8')):{};
for(const [k,v] of Object.entries(P.units||{})){Object.assign(UT[k],v);if(B.units[k])Object.assign(B.units[k],v);}
for(const [k,v] of Object.entries(P.weapons||{})){const W=B.weapons[k];for(const [a,b] of Object.entries(v)){if(a==='mods')Object.assign(W.mods,b);else W[a]=b;}}
const pairs=(process.argv[4]||'rifle:mg,rifle:at,mg:at,at:tech,at:ltank,at:mtank,at:htank,tech:rifle,ltank:rifle,mtank:rifle,htank:rifle,mtank:ltank,htank:mtank,ltank:tech,heli:mtank,heli:rifle,lheli:rifle,qaa:heli,flak:heli,sam:heli,qaa:lheli,spg:mtank,sniper:rifle').split(',').map(s=>s.split(':'));
const BUD=+(process.argv[5]||600);
function duel(a,b,seed){const G=S.createGame({map:'twinvalleys',mode:'ffa',ai:[{p:0},{p:1}],seed});for(const F of G.factions)F.ai=null;
  for(const u of G.units.slice())if(!u.def.static&&!u.def.struct&&!u.def.rail)u.alive=false;
  // an open flat spot far from bases
  let X=0,Z=0,best=-1;for(let k=0;k<400;k++){const x=-150+((k*37)%300),z=-100+((k*53)%200);let ok=1;for(let i=-30;i<=30;i+=5)for(let j=-12;j<=12;j+=4)if(!G.passable(x+i,z+j)||Math.abs(G.heightAt(x+i,z+j)-G.heightAt(x,z))>1.5)ok=0;
    const dz=Math.min(...G.zones.map(q=>Math.hypot(q.x-x,q.z-z)));if(ok&&dz>best){best=dz;X=x;Z=z;}}
  const side=(t,f,dx)=>{const n=Math.max(1,Math.round(BUD/UT[t].cost)),us=[];for(let i=0;i<n;i++){const u=G.spawnUnit(t,f,X+dx+(i%3)*2*Math.sign(dx),Z+(Math.floor(i/3)-n/6)*2.2);if(u){u.ang=dx<0?0:Math.PI;us.push(u);}}return us;};
  const A=side(a,0,-17),Bs=side(b,1,17);G.orderAs(0,'amove',A.map(u=>u.id),X+20,Z);G.orderAs(1,'amove',Bs.map(u=>u.id),X-20,Z);const vA=A.length*UT[a].cost,vB=Bs.length*UT[b].cost;
  let t=0;for(;t<150;t+=.25){G.update(.25);if(!A.some(u=>u.alive)||!Bs.some(u=>u.alive))break;
    if(t%6===0){G.orderAs(0,'amove',A.filter(u=>u.alive&&!u.target).map(u=>u.id),X+20,Z);G.orderAs(1,'amove',Bs.filter(u=>u.alive&&!u.target).map(u=>u.id),X-20,Z);}}
  const left=(L)=>L.filter(u=>u.alive).reduce((s,u)=>s+u.hp/u.maxHp*u.def.cost,0);
  return {t,a:left(A)/vA,b:left(Bs)/vB};}
for(const [a,b] of pairs){let ra=0,rb=0,tt=0;const N=3;for(let s=1;s<=N;s++){const r=duel(a,b,s);ra+=r.a;rb+=r.b;tt+=r.t;}
  console.log((a+' vs '+b).padEnd(16),'left',(ra/N*100).toFixed(0).padStart(4)+'%',(rb/N*100).toFixed(0).padStart(4)+'%','  t',(tt/N).toFixed(0)+'s');}
