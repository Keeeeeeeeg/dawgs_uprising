const SIM=require('./load.js')(process.argv[2]);
const G=SIM.createGame({map:'dawgs',mode:'ffa',ai:[{p:0,team:0}]});for(const u of G.units)u.alive=false;
const z=G.zones.filter(z=>z.type==='town'&&z.city)[0];z.owner=0;let ev=[];G.on('cityFall',(c,i)=>ev.push(i));
const us=[];for(let i=0;i<16;i++)us.push(G.spawnUnit('rifle',0,z.x+3+(i%4),z.z+3+(i/4|0)));G.applyCmd(0,{k:'man',zid:z.id,ids:us.map(u=>u.id)});
for(let s=0;s<60;s+=.25)G.update(.25);
const routes=us.filter(u=>u.man).map(u=>u.man.route);console.log('routes',routes.join(','));
const B=routes.find(r=>r&&r[0]==='B'),ci=+B.slice(1),c=G.city[ci];
const victim=G.spawnUnit('rifle',1,c.x+c.br+.5,c.z);
let n=0;while(!c.gone&&n<100){G.cityHit(c.x,c.z,4,500);n++;}
console.log('hits',n,'gone',c.gone,'events',ev,'victim hp',victim.hp.toFixed(0),victim.alive,'passable centre',G.passable?G.passable(c.x,c.z):'?');
const on=us.filter(u=>u.man&&u.man.route===B);console.log('posted via fallen',on.length);
G.applyCmd(0,{k:'order',kind:'move',ids:us.map(u=>u.id),a:z.x,b:z.z});
for(let s=0;s<60;s+=.25)G.update(.25);
console.log('after: manned',us.filter(u=>u.man).length,'near centre',us.filter(u=>Math.hypot(u.x-z.x,u.z-z.z)<9).length,'routesNow',on.map(u=>u.man&&u.man.route).join(','));
// manning again avoids the fallen tower
G.applyCmd(0,{k:'man',zid:z.id,ids:us.map(u=>u.id)});for(let s=0;s<5;s+=.25)G.update(.25);
console.log('re-man routes',[...new Set(us.filter(u=>u.man).map(u=>u.man.route))].join(','));
// random shelling across the city
let t0=G.city.filter(c=>c.gone).length;for(let k=0;k<400;k++)G.cityHit(z.x+(Math.random()-.5)*60,z.z+(Math.random()-.5)*60,3,140);
console.log('400 howitzer-ish hits felled',G.city.filter(c=>c.gone).length-t0,'of',G.city.filter(c=>c.zone===z.id).length);
