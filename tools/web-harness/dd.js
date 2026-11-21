const S=require('./load.js')(process.argv[2]);
const G=S.createGame({map:'twinvalleys',mode:'ffa',ai:[{p:0},{p:1}],seed:1});for(const F of G.factions)F.ai=null;
const a=G.spawnUnit('rifle',0,0,0),b=G.spawnUnit('rifle',1,20,0);
console.log(!!a,!!b,a&&[a.x,a.z,a.alive],b&&[b.x,b.z]);
globalThis.DBG=1;for(let i=0;i<4;i++)G.update(.25);globalThis.DBG=0;
console.log(a.hp,b.hp,a.target&&a.target.id,a.mode,G.time,G.factions.length,G.over,G.phase);
console.log('stance',a.stance,'sight',a.def.sight,'host',G.hostile&&G.hostile(0,1),G.allied&&G.allied(0,1),'team',G.factions.map(f=>f.team),'acq',a.acqT,'cd',a.cd, 'hgt',G.heightAt(0,0),G.passable(0,0));
console.log('emerge',a.emerge,'man',a.man,'guard',a.guard,'target b',b.target&&b.target.id,'dist',Math.hypot(a.x-b.x,a.z-b.z),'ret',a.stance);
