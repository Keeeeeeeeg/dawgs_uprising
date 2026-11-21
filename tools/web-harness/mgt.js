const SIM=require('./load.js')(process.argv[2]);
const G=SIM.createGame({map:'dawgs',mode:'ffa',ai:[{p:0,team:0}]});for(const u of G.units)u.alive=false;
const x=0,z=0;const m=G.spawnUnit('mg',0,x,z);const t=G.spawnUnit('rover',1,x+14,z);t.hp=t.maxHp=1e6;
let shots=[],bursts=0;G.on('shot',u=>{if(u===m)shots.push(G.time.toFixed(2));});G.on('burst',u=>{if(u===m)bursts++;});
let firstShot=null;for(let s=0;s<12;s+=.05){G.update(.05);if(shots.length&&firstShot==null)firstShot=G.time;}
console.log('first shot at',firstShot&&firstShot.toFixed(2),'shots',shots.length,'bursts',bursts,'per s',(shots.length/(12-firstShot)).toFixed(2),'deployed',m.deployed,'alive',m.alive);
console.log(shots.slice(0,14).join(' '));
G.applyCmd(0,{k:'order',kind:'move',ids:[m.id],a:x-20,b:z});const p0=[m.x,m.z];for(let s=0;s<1;s+=.05)G.update(.05);console.log('moved after 1s',Math.hypot(m.x-p0[0],m.z-p0[1]).toFixed(2),'deployed',m.deployed,'alive',m.alive);
