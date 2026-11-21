const SIM=require('./load.js')(process.argv[2]);
// two equal skirmishes: one side aggressive vs hold ground; check hold units never wander far from their spot
const G=SIM.createGame({map:'dawgs',mode:'ffa',ai:[{p:0},{p:1},{p:2}],seed:3});
const mine=G.units.filter(u=>u.f===0&&!u.def.static&&!u.def.plane&&!u.def.air);
const ids=mine.map(u=>u.id);G.applyCmd(0,{k:'order',kind:'stance',ids,a:'hold'});
const start=new Map(mine.map(u=>[u.id,[u.x,u.z]]));
for(let t=0;t<3000;t++)G.update(.1);
let maxd=0;for(const u of mine)if(u.alive&&u.garrison===null){const [x,z]=start.get(u.id);maxd=Math.max(maxd,Math.hypot(u.x-x,u.z-z));}
console.log('hold units',mine.filter(u=>u.stance==='hold').length,'max wander (non-garrison)',maxd.toFixed(1));
