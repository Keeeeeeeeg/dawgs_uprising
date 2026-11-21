const SIM=require('./load.js')(process.argv[2]);
const G=SIM.createGame({map:'dawgs',mode:'ffa',ai:[{p:0,team:0}]});
for(const t of ['fortress','hq','town','airbase']){const z=t==='hq'?G.zones[G.homes[0]]:G.zones.find(z=>z.type===t&&z.owner==null||z.type===t);
  for(const u of G.units)if(u.garrison===z.id)u.alive=false;
  z.owner=0;z.contested=false;const us=[];for(let i=0;i<20;i++)us.push(G.spawnUnit(i%4?'rifle':'mg',0,z.x+z.r+8+i*.3,z.z+5));us.push(G.spawnUnit('how',0,z.x+z.r+9,z.z+8));
  const r=G.applyCmd(0,{k:'man',zid:z.id,ids:us.map(u=>u.id)});
  for(let s=0;s<50;s+=.25)G.update(.25);
  const L=G.manLayout(z);const post=us.filter(u=>u.man&&u.man.ph==='post');
  console.log(t,'layout',L.walls.length,'+',L.pits.length,'cmd',r.n,'posted',post.length,'heights',[...new Set(post.map(u=>G.unitY(u).toFixed(1)))].join(','));
  G.applyCmd(0,{k:'order',kind:'move',ids:us.map(u=>u.id),a:z.x+z.r+20,b:z.z});for(let s=0;s<30;s+=.25)G.update(.25);
  console.log(' after order manned',us.filter(u=>u.man).length,'alive',us.filter(u=>u.alive).length);}
