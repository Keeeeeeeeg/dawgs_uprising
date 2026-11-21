const S=require('./load.js')(process.argv[2]);const id=process.argv[3];const n=Math.min(4,S.MAPS[id].maxPlayers),ai=[];for(let i=1;i<n;i++)ai.push({p:(i-1)%4});
const G=S.createGame({map:id,mode:'ffa',ai,seed:7});
for(let t=0;t<15*60*4;t++)G.update(.25);
const c={};for(const z of G.zones)for(const p of z.plots)if(p.fac)c[p.fac.type]=(c[p.fac.type]||0)+1;
console.log(id,'dock',c.dockyard||0,'naval units',G.units.filter(u=>u.alive&&u.def.naval).length,'total facs',Object.values(c).reduce((a,b)=>a+b,0));
