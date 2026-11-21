// alt.js: fly each plane type at a target and log its height profile
const S=require('./load.js')(process.argv[2]);
const G=S.createGame({map:'twinvalleys',mode:'ffa',ai:[{p:0},{p:1}],seed:3});for(const F of G.factions)F.ai=null;
const z1=G.zones.find(z=>z.owner===1)||G.zones[1];
console.log('cruiseY',G.cruiseY.toFixed(1),'cities',G.zones.filter(z=>z.city).map(z=>z.y.toFixed(1)+'/'+z.r).join(' '));
function run(type,mk,label){
  const u=G.spawnUnit(type,0,z1.x-140,z1.z);u.pstate='out';u.landed=false;u.altK=1;u.ang=0;u.sortieT=0;u.ammo=u.def.ammo;u.mission=mk(u);
  const log=[];for(let t=0;t<24;t+=.25){G.update(.25);if(!u.alive)break;if(t%1<.01){const tg=u.target||u.mission&&u.mission.target;
    log.push(`${t.toFixed(0)}:${(G.unitY(u)-G.heightAt(u.x,u.z)).toFixed(0)}${tg&&tg.alive?'/'+Math.hypot(tg.x-u.x,tg.z-u.z).toFixed(0):''}${u.gun?'G':''}${u.dropping?"B":""}${u.reatk?"r":""}${u.pstate[0]}`);}}
  console.log(label.padEnd(8),log.join(' '));u.alive=false;}
const tank=G.spawnUnit('mtank',1,z1.x+10,z1.z+5);
run('cas',u=>({type:'cas',target:tank,x:tank.x,z:tank.z}),'cas');
run('bomb',u=>({type:'bomb',x:z1.x,z:z1.z}),'bomb');
const zep=G.spawnUnit('airship',1,z1.x,z1.z);if(zep){zep.altK=1;}
const hz=zep?G.unitY(zep):0;console.log('zep AGL',zep&&(hz-G.heightAt(zep.x,zep.z)).toFixed(0));
for(let i=0;i<2;i++)run('intc',u=>({type:'intercept',target:zep,x:zep.x,z:zep.z,manual:true}),'intc'+i);
