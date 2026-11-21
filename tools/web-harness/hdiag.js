const S=require('./load.js')(process.argv[2]);S.BALANCE.horde.diff.normal=3;
const G=S.createGame({map:'starfall1',mode:'teams',ai:[],seed:5,horde:{}});const f=G.factions[0];f.player=false;f.diff='hard';f.comp=S.AI_BASE[1].comp;f.prefer=S.AI_BASE[1].prefer;f.ai={t:1,waveT:1e9,groups:[],qrf:{}};
for(let t=0;t<700*4;t++)G.update(.25);
const hs=G.units.filter(u=>u.alive&&u.f===G.horde.f&&!u.def.struct);const hist={};
for(const u of hs){const k=`${u.type} z${Math.round(u.z/40)*40} ${u.mode} tgt:${u.target?u.target.type+(u.target.def.struct?'S':''):'-'}`;hist[k]=(hist[k]||0)+1;}
console.log(Object.entries(hist).sort((a,b)=>b[1]-a[1]).slice(0,25));
console.log(G.zones.map(z=>`${z.name} ${z.owner} gate:${z.gateU?Math.round(z.gateU.hp)+'/'+z.gateU.maxHp+(z.gateU.alive?'':' dead'):'-'} breached:${!!z.breached} cap:${Math.round(z.cap.p)}`));
