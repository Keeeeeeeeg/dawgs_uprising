const SIM=require('./load.js')(process.argv[2]);
const G=SIM.createGame({map:'dawgs',mode:'ffa',ai:[{p:0},{p:1},{p:2}],seed:4});
const z=G.zones[G.homes[0]];const gar=()=>G.units.filter(u=>u.alive&&u.zoneMade===z.id);
console.log('start made',gar().length,'cap',SIM.ZTYPES[z.type].garrison);
// move all garrison away
G.applyCmd(0,{k:'order',kind:'move',ids:gar().map(u=>u.id),a:z.x+60,b:z.z});
for(let t=0;t<1200;t++)G.update(.1);
console.log('after 120s moved away: made',gar().length,'in garrison',G.garrisonCount(z));
for(const u of gar().slice(0,3)){u.alive=false;}
for(let t=0;t<1500;t++)G.update(.1);
console.log('after killing 3 + 150s: made',gar().length);
G.factions[0].money=1000;console.log('drill',JSON.stringify(G.applyCmd(0,{k:'drill',zid:z.id})),z.drillUp);
for(let t=0;t<400;t++)G.update(.1);console.log('drill level',z.drill);
