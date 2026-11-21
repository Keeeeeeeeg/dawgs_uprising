const SIM=require('./load.js')(process.argv[2]);
const G=SIM.createGame({map:'dawgs',mode:'ffa',ai:[{p:0},{p:1},{p:2}],seed:7});
const seen={};let maxOff=0;
for(let t=0;t<600*10;t++){G.update(.1);
  for(const u of G.units)if(u.pstate){seen[u.pstate]=(seen[u.pstate]||0)+1;
    if((u.pstate==='taxiOut'||u.pstate==='taxiIn')&&u.homeZone&&u.homeZone.air){const A=u.homeZone.air;const q=(u.x-A.cx)*A.nx+(u.z-A.cz)*A.nz;const s=(u.x-A.cx)*A.ux+(u.z-A.cz)*A.uz;
      if(q<-1||q>12||Math.abs(s)>A.L/2+2){const e=Math.max(-q,q-12,Math.abs(s)-A.L/2);if(e>maxOff){maxOff=e;console.log(u.pstate,s.toFixed(1),q.toFixed(1),JSON.stringify(u.wps));}}}}}
console.log(seen,'max taxi excursion',maxOff.toFixed(2));
