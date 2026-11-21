const SIM=require('./load.js')(process.argv[2]);
for(const [id,m] of Object.entries(SIM.MAPS)){let G;try{G=SIM.createGame({map:id,mode:'ffa',ai:[{p:0,team:0}]});}catch(e){console.log(id,'ERR',e.message);continue;}
  let worst=1e9,wn='';for(const z of G.zones)if(z.type==='fortress')for(const o of G.zones)if(o!==z){const d=Math.hypot(o.x-z.x,o.z-z.z)-(o.r+13.5);if(d<worst){worst=d;wn=z.name+'~'+o.name;}}
  console.log(id,G.zones.filter(z=>z.type==='fortress').length,worst.toFixed(1),wn);}
