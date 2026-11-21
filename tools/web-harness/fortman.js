// headless: infantry go up the new Fortress's towers, are hidden inside, take snap posts, shift with a facing, come back down
const SIM=require('./load.js')(process.argv[2]);
const G=SIM.createGame({map:'fourcrowns',mode:'ffa',ai:[{p:0},{p:1},{p:2}]});
const z=G.zones.find(z=>z.type==='fortress');console.log('fortress',z.name,'owner',z.owner,'drill',z.drill,'cap',G.fortCap(z));
z.owner=0;for(const u of G.units)if(u.garrison===z.id&&u.f!==0)u.alive=false;
const us=[];for(let i=0;i<6;i++){const p=G.wallWorld(z,5+i*.6,(i-3)*.8);us.push(G.spawnUnit('rifle',0,p.x,p.z));}
console.log('man',JSON.stringify(G.applyCmd(0,{k:'man',zid:z.id,ids:us.map(u=>u.id)})));
let hid=0;for(let t=0;t<400;t++){G.update(.1);hid=Math.max(hid,us.filter(u=>u.inTower).length);}
console.log('max hidden at once',hid,'phases',us.map(u=>u.man&&u.man.ph+':'+u.man.i+':'+(u.man.route||'')).join(' '));
const post=us.map(u=>u.man&&u.man.i);
console.log('manpos',JSON.stringify(G.applyCmd(0,{k:'manpos',zid:z.id,ids:us.slice(0,3).map(u=>u.id),posts:[20,21,22],face:1.2})));
for(let t=0;t<300;t++)G.update(.1);
console.log('after shift',us.slice(0,3).map(u=>u.man&&u.man.ph+':'+u.man.i+' ang '+u.ang.toFixed(2)+' y '+(u.man.my||0).toFixed(2)).join(' | '));
console.log('move off',JSON.stringify(G.applyCmd(0,{k:'order',kind:'move',ids:us.map(u=>u.id),a:z.x,b:z.z})||null));
for(let t=0;t<400;t++)G.update(.1);
console.log('down',us.map(u=>(u.man?'M':'-')+(u.inTower?'T':'')+' '+Math.round(Math.hypot(u.x-z.x,u.z-z.z))).join(' '));
const sp=G.units.filter(u=>u.alive&&u.fortSpg!=null);console.log('fortress guns',sp.length,sp.map(u=>u.man?u.man.k+':'+u.man.ph:'-').join(' '),'fortresses',G.zones.filter(z=>z.type==='fortress'&&z.owner!=null).length);
