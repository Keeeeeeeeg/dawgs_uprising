const S=require('./load.js')(process.argv[2]);const G=S.createGame({map:'twinvalleys',mode:'ffa',ai:[{p:0}],seed:2});
const z=G.zones.find(q=>q.air&&q.owner===0)||G.zones.find(q=>q.air);z.owner=0;const A=z.air;console.log(z.name,z.owner);
const t=A.terms[0];const u=G.spawnUnit('cas',z.owner==null?0:z.owner,t.x,t.z);u.homeZone=z;u.pstate='ground';u.landed=true;u.altK=0;u.term=0;t.u=u;u.ang=A.ang+Math.PI/2;u.rearmT=u.rearmMax=999;u.repairRate=0;u.manual=true;
for(let i=0;i<20;i++){G.update(.25);}console.log(u.alive,u.pstate,u.term,t.u===u,u.rearmT,Math.hypot(u.x-t.x,u.z-t.z));
