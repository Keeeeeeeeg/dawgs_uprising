const S=require('./load.js')(process.argv[2]);const id=process.argv[3]||'twinvalleys';const n=S.MAPS[id].maxPlayers,ai=[];for(let i=1;i<n;i++)ai.push({p:(i-1)%4});
const G=S.createGame({map:id,mode:'ffa',ai,seed:7});
console.log('ports',G.zones.filter(z=>z.port).map(z=>z.name+':'+(z.spots||[]).filter(p=>p.water).length));
for(let t=0;t<8*60*4;t++)G.update(.25);
const c={};for(const z of G.zones)for(const p of z.plots)if(p.fac)c[p.fac.type]=(c[p.fac.type]||0)+1;console.log(c);
console.log('comp',G.factions.map(f=>f.comp&&f.comp.boat));
