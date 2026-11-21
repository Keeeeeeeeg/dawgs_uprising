const SIM=require('./load.js')(process.argv[2]);
const G=SIM.createGame({map:'starfall1',mode:'teams',horde:{diff:'normal'},ai:[]});
const HF=G.horde.f;G.horde.t=1e9;const z=G.zones.find(q=>q.wall&&!q.wall.light&&q.owner===0);console.log('target',z.name,z.type,'gate hp',z.gateU&&z.gateU.hp);
for(const u of G.units)if(u.alive&&u.f===0&&!u.def.struct&&!u.def.static&&u.gateOf==null&&!u.def.bturret)u.alive=false;   // no defenders: watch the gate
const g=G.wallWorld(z,z.wall.front+40,0);const us=[];
for(let i=0;i<14;i++){us.push(G.spawnUnit(i<10?'husk':i<12?'brute':'spitter',HF,g.x+(i%5-2)*2,g.z+Math.floor(i/5)*2));}
for(let t=0;t<900;t++){G.update(.1);if(t%150===0)console.log('t',t/10,'gate',z.gateU?Math.round(z.gateU.hp):'down','breached',!!z.breached,'near gate',us.filter(u=>u.alive&&Math.hypot(u.x-z.gateU?.x,u.z-z.gateU?.z)<8).length,'attacking',us.filter(u=>u.alive&&u.target&&u.target.gateOf!=null).length);}
