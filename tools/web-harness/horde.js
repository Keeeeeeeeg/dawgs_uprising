// headless horde run: node horde.js file map [minutes] [botPlayer 0/1]
const S=require('./load.js')(process.argv[2]);const map=process.argv[3]||'starfall1',mins=+(process.argv[4]||10),bot=process.argv[5]!=='0';
const n=S.MAPS[map].maxPlayers,ai=[];for(let i=1;i<n;i++)ai.push({p:i-1,diff:'hard'});
if(process.env.HK)S.BALANCE.horde.diff.normal=+process.env.HK;const t0=Date.now();const G=S.createGame({map,mode:'teams',ai,seed:5,horde:{diff:process.env.HD||'normal'}});if(process.env.HK)S.BALANCE.horde.diff.normal=+process.env.HK;
if(bot){const f=G.factions[0];f.player=false;f.diff='hard';f.comp=S.AI_BASE[1].comp;f.prefer=S.AI_BASE[1].prefer;f.ai={t:1,waveT:1e9,groups:[],qrf:{}};}
G.on('horde',(k,a,b)=>{const R=G.horde;if(k==='wave')console.log(`t=${Math.round(G.time)} WAVE ${a} size ${b} budget ${Math.round(G.hordeBudget(a))} | dawgs units ${G.units.filter(u=>u.alive&&u.f!==R.f).length} money ${G.factions.filter(f=>f.id!==R.f).map(f=>Math.round(f.money))}`);
  if(k==='break')console.log(`t=${Math.round(G.time)}   break after ${a}: pay ${JSON.stringify(b)} raised ${R.raised} kills ${R.kills} hordeAlive ${G.units.filter(u=>u.alive&&u.f===R.f&&!u.def.struct).length} zones ${G.zones.filter(z=>z.owner!=null).length}/${G.zones.length}`);
  if(k==='razed')console.log(`t=${Math.round(G.time)}   RAZED ${a.name}`);if(k==='pit')console.log('   pit destroyed, left',b);});
let mx=0;for(let t=0;t<mins*60*4&&!G.over;t++){G.update(.25);if(t%20===0)mx=Math.max(mx,G.units.filter(u=>u.alive).length);}
console.log('gates',G.zones.filter(z=>z.gateU).map(z=>z.name+':'+Math.round(z.gateU.hp)+(z.breached?'B':'')).join(' '));console.log('over',JSON.stringify(G.over),'time',Math.round(G.time),'wave',G.horde.wave,G.horde.phase,'maxUnits',mx,'wall s',((Date.now()-t0)/1000).toFixed(0),'ports',G.zones.filter(z=>z.port).length);
