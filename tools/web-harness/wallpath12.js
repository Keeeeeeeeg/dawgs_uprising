const SIM=require('./load.js')(process.argv[2]);const id='dawgs';
const G=SIM.createGame({map:id,mode:'ffa',ai:[{p:0,team:0}]});
const z=G.zones.find(z=>z.type==='fortress');z.owner=0;
let tot=0,arr=0,worst=0;
for(let trial=0;trial<6;trial++){
  const us=[];for(let i=0;i<6;i++){const w=G.wallWorld(z,(-1+i*.6)*1.2,((trial%2?4:-4)+i*.3)*1.2);us.push(G.spawnUnit(i%2?'rifle':'ltank',0,w.x,w.z));}
  // target: behind the side wall (outside), and behind the back wall
  const tw=G.wallWorld(z,(trial<3?-12:2)*1.2,(trial<3?(trial-1)*6:(trial%2?16:-16))*1.2);
  G.applyCmd(0,{k:'order',kind:'move',ids:us.map(u=>u.id),a:tw.x,b:tw.z});
  let t=0;for(;t<60;t+=.25){G.update(.25);if(us.every(u=>u.mode!=='move'))break;}
  const d=us.map(u=>Math.hypot(u.x-tw.x,u.z-tw.z));const ok=d.filter(x=>x<6).length;arr+=ok;tot+=us.length;worst=Math.max(worst,t);
  console.log('trial',trial,'time',t,'arrived',ok,'/',us.length,'maxd',Math.max(...d).toFixed(1));
  for(const u of us)u.alive=false;G.update(.25);}
console.log('arrived',arr,'/',tot,'worst',worst);
for(const tr of [1,2]){const tw=G.wallWorld(z,-12,(tr-1)*6);const pa=G.passable(tw.x,tw.z);const p=G.findPath(z.x,z.z,tw.x,tw.z);console.log('tr',tr,'passable',pa,'path',p&&p.length,p&&JSON.stringify(p.slice(-1)));}
