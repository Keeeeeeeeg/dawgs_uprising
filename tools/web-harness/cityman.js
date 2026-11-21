const SIM=require('./load.js')(process.argv[2]);
for(let ci=0;ci<3;ci++){const G=SIM.createGame({map:process.argv[3]||'dawgs',mode:'ffa',ai:[{p:0,team:0}]});for(const u of G.units)u.alive=false;const z=G.zones.filter(z=>z.type==='town'&&z.city)[ci];if(!z)break;const B=G.cityBridges(z);
  for(const u of G.units)if(u.garrison===z.id)u.alive=false;
  z.owner=0;z.contested=false;const us=[];for(let i=0;i<20;i++)us.push(G.spawnUnit(i%4?'rifle':'mg',0,z.x+3+(i%5),z.z+3+(i/5|0)));
  const r=G.applyCmd(0,{k:'man',zid:z.id,ids:us.map(u=>u.id)});
  const L=G.manLayout(z);const ph={};let maxY=0,inB=0;
  for(let s=0;s<70;s+=.25){G.update(.25);for(const u of us)if(u.man&&u.man.ph==='climb'){const st=u.man.pts;maxY=Math.max(maxY,u.man.my);}}
  const post=us.filter(u=>u.man&&u.man.ph==='post');
  const routes=Object.keys(L.routes);
  console.log(z.name,'bridges',B.length,'routes',routes.join(' '),'posts',L.walls.length,'cmd',r.n,'posted',post.length,'phases',JSON.stringify(us.reduce((o,u)=>{const k=u.man?u.man.ph:'none';o[k]=(o[k]||0)+1;return o;},{})),'Y',[...new Set(post.map(u=>(G.unitY(u)-z.y).toFixed(1)))].join(','));
  const u0=post[0];if(u0)console.log('  route of first:',u0.man.pts.map(p=>[(p.x-z.x).toFixed(1),p.y.toFixed(1),(p.z-z.z).toFixed(1)].join('/')).join(' '));
  G.applyCmd(0,{k:'order',kind:'move',ids:us.map(u=>u.id),a:z.x,b:z.z});for(let s=0;s<60;s+=.25)G.update(.25);
  console.log('  after order manned',us.filter(u=>u.man).length,'alive',us.filter(u=>u.alive).length,'near centre',us.filter(u=>Math.hypot(u.x-z.x,u.z-z.z)<8).length);}
