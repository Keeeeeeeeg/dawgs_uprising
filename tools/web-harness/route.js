const SIM=require('./load.js')(process.argv[2]);
const G=SIM.createGame({map:'dawgs',mode:'ffa',ai:[{p:0,team:0}]});
for(const t of ['fortress','hq']){const z=t==='hq'?G.zones[G.homes[0]]:G.zones.find(z=>z.type===t);for(const u of G.units)if(u.garrison===z.id)u.alive=false;z.owner=0;
 const us=[];for(let i=0;i<20;i++)us.push(G.spawnUnit('rifle',0,z.x+z.r+6,z.z+i*.5));G.applyCmd(0,{k:'man',zid:z.id,ids:us.map(u=>u.id)});
 const c=Math.cos(z.gate),s=Math.sin(z.gate),loc=p=>{const dx=p.x-z.x,dz=p.z-z.z;return [(dx*c+dz*s).toFixed(1),p.y.toFixed(1),(dz*c-dx*s).toFixed(1)].join(',');};
 for(const u of us.slice(0,20))if(u.man)console.log(t,u.man.i,u.man.pts.map(loc).join(' > '));}
