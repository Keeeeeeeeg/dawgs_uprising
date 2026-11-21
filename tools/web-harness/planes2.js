const SIM=require('./load.js')(process.argv[2]);let bad=0,n=0;
for(const map of ['dawgs','ember','thorn']){const G=SIM.createGame({map,mode:'ffa',ai:[{p:0},{p:1},{p:2}],seed:7});
for(let t=0;t<4000;t++){G.update(.1);
  for(const u of G.units)if((u.pstate==='taxiOut'||u.pstate==='taxiIn')&&u.homeZone&&u.homeZone.air){const A=u.homeZone.air;n++;
    const q=(u.x-A.cx)*A.nx+(u.z-A.cz)*A.nz,s=(u.x-A.cx)*A.ux+(u.z-A.cz)*A.uz;
    if((Math.abs(s)<10.5&&q>14.6&&q<18.4)||(Math.abs(s-6)<1.5&&Math.abs(q+4.4)<1.5))bad++;}}}
console.log('taxi samples',n,'through terminal/tower',bad);
