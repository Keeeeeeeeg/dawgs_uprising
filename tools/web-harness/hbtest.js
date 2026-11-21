// ships under / troops over the high bridges
const S=require('./load.js')(process.argv[2]);const map=process.argv[3]||'twinvalleys';
const n=S.MAPS[map].maxPlayers,ai=[];for(let i=0;i<n-1;i++)ai.push({p:i%4});
const G=S.createGame({map,mode:'ffa',ai,seed:3});for(const F of G.factions)F.ai=null;
const res=[];
for(const D of G.decks){const mid=(D.s0+D.s1)/2,cx=D.ax+D.ux*mid,cz=D.az+D.uz*mid;
  // a tank from one end of the deck to the other
  const e0=[D.ax+D.ux*(D.r0-14),D.az+D.uz*(D.r0-14)],e1=[D.ax+D.ux*(D.r1+14),D.az+D.uz*(D.r1+14)];
  const t=G.spawnUnit('mtank',0,e0[0],e0[1]);G.orderAs(0,'move',[t.id],e1[0],e1[1]);
  // a gunboat across the channel under the middle of the span
  const b=G.spawnUnit('boat',0,cx-D.nx*45,cz-D.nz*45);G.orderAs(0,'move',[b.id],cx+D.nx*45,cz+D.nz*45);
  let ymax=0,bUnder=false;for(let k=0;k<240;k++){G.update(.25);const y=G.unitY(t);if(y>ymax)ymax=y;if(Math.abs((b.x-D.ax)*D.nx+(b.z-D.az)*D.nz)<3)bUnder=true;}
  res.push({deck:[Math.round(D.s0),Math.round(D.s1)],tank:Math.round(Math.hypot(t.x-e1[0],t.z-e1[1])),tankYmax:+ymax.toFixed(1),boatAt:Math.round(Math.hypot(b.x-cx-D.nx*45,b.z-cz-D.nz*45)),bUnder,boatY:G.unitY(b)});
  t.alive=false;b.alive=false;t.hp=0;b.hp=0;}
console.log(map,JSON.stringify(res));
