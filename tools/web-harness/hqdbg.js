const SIM=require('./load.js')(process.argv[2]);
const G=SIM.createGame({map:'dawgs',mode:'ffa',ai:[{p:0,team:0}]});
const z=G.zones[G.homes[0]];for(const u of G.units)if(u.garrison===z.id)u.alive=false;
for(const [k,r] of Object.entries(G.manLayout(z).routes)){const w=G.wallWorld(z,r[0][0],r[0][2]);console.log(k,'foot passable',G.passable(w.x,w.z));}
const us=[];for(let i=0;i<16;i++)us.push(G.spawnUnit('rifle',0,z.x+z.r+8+i*.3,z.z+5));
G.applyCmd(0,{k:'man',zid:z.id,ids:us.map(u=>u.id)});for(let s=0;s<80;s+=.25)G.update(.25);
for(const u of us)if(!u.man||u.man.ph!=='post'){const m=u.man;const p=m&&m.pts[0];console.log(u.alive,m&&m.ph,m&&m.i,G.manLayout(z).walls[m.i][3],'d foot',p&&Math.hypot(u.x-p.x,u.z-p.z).toFixed(1),u.mode);}
