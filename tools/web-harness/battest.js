const SIM=require('./load.js')(process.argv[2]);
const G=SIM.createGame({map:'fourcrowns',mode:'ffa',ai:[{p:0},{p:1},{p:2}]});
const z=G.zones.find(z=>z.type==='fortress');z.owner=0;G.factions[0].money=2000;
console.log('buy0',JSON.stringify(G.applyCmd(0,{k:'battery',zid:z.id,i:0})),'buy1',JSON.stringify(G.applyCmd(0,{k:'battery',zid:z.id,i:1})),'again',JSON.stringify(G.applyCmd(0,{k:'battery',zid:z.id,i:0})));
for(let t=0;t<400;t++)G.update(.1);
const guns=G.units.filter(u=>u.alive&&u.type==='fbat');console.log('guns',guns.length,guns.map(u=>Math.round(Math.hypot(u.x-z.x,u.z-z.z))+'m').join(' '),'spgs auto',G.units.filter(u=>u.fortSpg!=null).length);
const e=G.wallWorld(z,50,0);const tg=G.spawnUnit('mtank',1,e.x,e.z);for(let t=0;t<200;t++)G.update(.1);console.log('target hp',Math.round(tg.hp),'/',tg.maxHp,tg.alive);
guns[0].hp=0;G.update(.1);for(let t=0;t<900;t++)G.update(.1);console.log('rebuilt',G.units.filter(u=>u.alive&&u.type==='fbat').length);
