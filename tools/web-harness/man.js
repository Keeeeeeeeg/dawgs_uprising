const SIM=require('./load.js')(process.argv[2]);const id=Object.keys(SIM.MAPS)[0];
const G=SIM.createGame({map:id,mode:'ffa',ai:[{p:0,team:0}]});
const z=G.zones.find(z=>z.type==='fortress');z.owner=0;z.contested=false;
const us=[];for(let i=0;i<5;i++)us.push(G.spawnUnit('rifle',0,z.x+20+i,z.z+20));us.push(G.spawnUnit('how',0,z.x+22,z.z+24));
console.log('man',JSON.stringify(G.applyCmd(0,{k:'man',zid:z.id,ids:us.map(u=>u.id)})));
for(let t=0;t<60;t+=.25){G.update(.25);}
for(const u of us)console.log(u.type,u.alive,u.man&&u.man.ph,u.man&&u.man.k,(u.man&&u.man.my||0).toFixed(2),G.unitY(u).toFixed(2),'d',Math.hypot(u.x-z.x,u.z-z.z).toFixed(1));
G.applyCmd(0,{k:'order',kind:'move',ids:us.map(u=>u.id),a:z.x+40,b:z.z});
for(let t=0;t<30;t+=.25)G.update(.25);
for(const u of us)console.log('after',u.type,u.man&&u.man.ph,G.unitY(u).toFixed(2),'d',Math.hypot(u.x-z.x-40,u.z-z.z).toFixed(1));
// AI fortress auto-manning
let n=0;for(let t=0;t<240;t+=.25)G.update(.25);
for(const q of G.zones)if(q.type==='fortress'&&q.posts)n+=q.posts.filter(v=>v!=null).length;
console.log('auto-manned slots across fortresses',n,'units',G.units.length);
