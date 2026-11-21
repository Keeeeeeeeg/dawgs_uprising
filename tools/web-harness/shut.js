const S=require('./load.js')(process.argv[2]);const G=S.createGame({map:'fourcrowns',mode:'ffa',ai:[{p:0},{p:1},{p:2}],seed:3});for(const F of G.factions)F.ai=null;
const sec=G.sectors.find(s=>s.zones.length===2);const L=G.rails[sec.rail];console.log(sec.name,'open',L.open,'len',L.len.toFixed(0),'stops',L.stops.map(s=>s.s.toFixed(0)));
for(const zi of sec.zones){const z=G.zones[zi];z.owner=0;}let mn=1e9,mx=-1;
for(let i=0;i<1200;i++){G.update(.25);const tr=G.units.find(u=>u.alive&&u.rail===L.id);if(tr){mn=Math.min(mn,tr.rs);mx=Math.max(mx,tr.rs);}}
console.log('train rs range',mn.toFixed(0),mx.toFixed(0));
