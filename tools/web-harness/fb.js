const S=require('./load.js')(process.argv[2]);const G=S.createGame({map:'twinvalleys',mode:'ffa',ai:[{p:0},{p:1}],seed:2});for(const F of G.factions)F.ai=null;
const z=G.zones.find(q=>q.owner==null&&!q.walled)||G.zones.find(q=>q.owner==null);
const b=G.spawnUnit('flagb',0,z.x-30,z.z);const r=G.spawnUnit('rifle',0,z.x-28,z.z+2);const far=G.spawnUnit('rifle',0,z.x-80,z.z);
for(let t=0;t<2;t+=.25)G.update(.25);
console.log('flagT near',r.flagT>G.time,'far',far.flagT>G.time,'armor bonus vs bullet',G.COMBAT.hit('bullet',10,r.def,{}),G.COMBAT.hit('bullet',10,r.def,{armAdd:3}));
// capture speed with and without waving
function cap(wave){const G2=S.createGame({map:'twinvalleys',mode:'ffa',ai:[{p:0},{p:1}],seed:2});for(const F of G2.factions)F.ai=null;const z2=G2.zones.find(q=>q.id===z.id);
 const us=[];for(let i=0;i<4;i++)us.push(G2.spawnUnit('rifle',0,z2.x+i,z2.z+1).id);const bb=G2.spawnUnit('flagb',0,z2.x,z2.z-1);
 if(wave)G2.orderAs(0,'wave',[bb.id],true);let t=0;for(;t<200&&z2.owner!==0;t+=.25)G2.update(.25);return [t,bb.waving,z2.owner];}
console.log('capture time plain',cap(false),'waving',cap(true));
const G3=S.createGame({map:'twinvalleys',mode:'ffa',ai:[{p:0},{p:1}],seed:2});const bb=G3.spawnUnit('flagb',0,0,0);G3.orderAs(0,'wave',[bb.id],true);console.log('waving',bb.waving);G3.orderAs(0,'move',[bb.id],10,10);console.log('after move',bb.waving);
