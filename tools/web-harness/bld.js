const SIM=require('./load.js')(process.argv[2]);
const G=SIM.createGame({map:'dawgs',mode:'ffa',ai:[{p:0},{p:1},{p:2}],seed:4});
const z=G.zones[G.homes[0]];const bk=z.plots.find(p=>p.fac.type==='barracks');
console.log('body',bk.body&&bk.body.hp,'unitCount',G.unitCount(0));
// hostile tanks parked by the barracks, only target available is the building
for(const u of G.units)if(u.f===0&&!u.def.struct&&!u.def.static)u.alive=false;
for(const z2 of G.zones)if(z2!==z)continue;
const ts=[];for(let i=0;i<4;i++){const t=G.units.find(u=>u.f===1&&u.alive&&!u.def.static&&!u.def.air&&u.garrison===null&&!u.def.builder&&!ts.includes(u));if(t){ts.push(t);t.x=bk.x+6+i;t.z=bk.z+4;t.ax=t.x;t.az=t.z;}}
G.orderAs(1,'attack',ts.map(t=>t.id),bk.body);console.log('attackers',ts.map(t=>t.type).join(','));let destroyed=false;G.on&&G.on('facility',(p)=>{if(p===bk&&p.gone)destroyed=G.time;});
for(let t=0;t<1500&&!destroyed;t++)G.update(.1);
console.log('barracks destroyed at',destroyed,'plots now',z.plots.map(p=>p.fac.type).join(','));
console.log('body hp',bk.body&&bk.body.hp,'alive',bk.body&&bk.body.alive,'attackers',ts.map(t=>[t.alive,t.mode,Math.round(Math.hypot(t.x-bk.x,t.z-bk.z)),t.target&&t.target.type].join(':')).join(' '));
