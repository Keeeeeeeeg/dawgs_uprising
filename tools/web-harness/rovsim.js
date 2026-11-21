const SIM=require('./load.js')(process.argv[2]);
const G=SIM.createGame({map:'dawgs',mode:'ffa',ai:[{p:0},{p:1},{p:2}],seed:5});
const z=G.zones[G.homes[0]],rv=G.units.find(u=>u.f===0&&u.def.builder);
const s=z.spots.find(s=>!s.used&&!G.canPlace(0,z.id,'depot',s.x,s.z));
console.log('place',JSON.stringify(G.applyCmd(0,{k:'place',zid:z.id,type:'depot',x:s.x,z:s.z,ang:0,ids:[rv.id]})));
const bad=G.canPlace(0,z.id,'barracks',z.x+z.r+60,z.z);console.log('far:',bad);
for(let t=0;t<600;t++){G.update(.1);if(t%50==0){const p=z.plots[z.plots.length-1];console.log((t/10)+'s',p.fac.state,p.fac.t.toFixed(1),'crew',p.fac.crew,'rover d',Math.hypot(rv.x-p.x,rv.z-p.z).toFixed(1),rv.mode,rv.building);}}
// AI building with rovers
for(let t=0;t<3000;t++)G.update(.1);
for(let f=1;f<4;f++)console.log('AI',f,'rovers',G.units.filter(u=>u.alive&&u.f===f&&u.def.builder).length,'buildings',G.zones.filter(z=>z.owner===f).reduce((a,z)=>a+z.plots.length,0));
