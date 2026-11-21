const SIM=require('./load.js')(process.argv[2]);
const G=SIM.createGame({map:'dawgs',mode:'ffa',ai:[{p:0,team:0}]});for(const u of G.units)u.alive=false;
const h=G.zones[G.homes[0]];let x=h.x,z=h.z;for(let a=0;a<6.28;a+=.2){const X=h.x+Math.cos(a)*40,Z=h.z+Math.sin(a)*40;let ok=true;for(let i=-12;i<=12;i+=2)for(let j=-12;j<=12;j+=2)if(!G.passable(X+i,Z+j)||G.heightAt(X+i,Z+j)<1)ok=false;if(ok){x=X;z=Z;break;}}
const v=G.spawnUnit('vtol',0,x+15,z);const sq=[];for(let i=0;i<10;i++)sq.push(G.spawnUnit(i%3?'rifle':'mg',0,x+(i%5)*1.2,z+(i/5|0)*1.2));
let ev=[];for(const e of ['vtolLand','vtolLift','board','unboard'])G.on(e,()=>ev.push(e));
const r=G.applyCmd(0,{k:'vload',vid:v.id,ids:sq.map(u=>u.id)});console.log('load',JSON.stringify(r));
for(let s=0;s<40;s+=.25){G.update(.25);if(s%5===0)console.log(s,v.tr&&v.tr.ph,'landK',(v.landK||0).toFixed(2),'y',G.unitY(v).toFixed(1),'cargo',(v.cargo||[]).length,'pos',v.x.toFixed(1),v.z.toFixed(1));}
console.log('events',ev.reduce((o,e)=>(o[e]=(o[e]||0)+1,o),{}),'aboard',sq.filter(u=>u.aboard!=null).length);
G.applyCmd(0,{k:'order',kind:'move',ids:[v.id],a:x+60,b:z+10});for(let s=0;s<15;s+=.25)G.update(.25);
console.log('flew to',v.x.toFixed(1),v.z.toFixed(1),'passengers at',sq.filter(u=>u.aboard!=null).map(u=>u.x.toFixed(0)).slice(0,3).join(','));
const r2=G.applyCmd(0,{k:'vunload',vid:v.id});console.log('unload',JSON.stringify(r2));
for(let s=0;s<15;s+=.25)G.update(.25);console.log('after unload cargo',(v.cargo||[]).length,'out',sq.filter(u=>u.aboard==null&&u.alive).length,'landK',v.landK,'tr',!!v.tr);
// shot down with troops aboard
G.applyCmd(0,{k:'vload',vid:v.id,ids:sq.map(u=>u.id)});for(let s=0;s<30;s+=.25)G.update(.25);const n=(v.cargo||[]).length;
v.hp=1;const e=G.spawnUnit('flak',1,v.x+8,v.z);for(let s=0;s<10&&v.alive;s+=.25)G.update(.25);console.log('aboard',n,'vtol alive',v.alive,'squad alive',sq.filter(u=>u.alive).length,'hash',G.stateHash());
