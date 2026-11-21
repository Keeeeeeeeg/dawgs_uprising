const SIM=require('./load.js')(process.argv[2]);
const G=SIM.createGame({map:'fourcrowns',mode:'ffa',ai:[{p:0},{p:1},{p:2}]});
G.factions.forEach(f=>{if(f.ai)f.ai=null;});
const z=G.zones[0];const X=z.x+60,Z=z.z+60;
const fl=G.spawnUnit('flamer',0,X,Z);const rs=[];for(let i=0;i<5;i++)rs.push(G.spawnUnit('rifle',1,X+12+i*.6,Z+i*.4));
let mx=0;for(let t=0;t<120;t++){G.update(.25);mx=Math.max(mx,(G.fires||[]).length);}
console.log('fires max',mx,'rifles alive',rs.filter(u=>u.alive).length,'flamer hp',fl.hp|0,'hash',G.stateHash());
