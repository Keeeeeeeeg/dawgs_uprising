const SIM=require('./load.js')(process.argv[2]);
for(const id of Object.keys(SIM.MAPS).slice(0,12)){let G;try{G=SIM.createGame({map:id,mode:'ffa',ai:[{p:0,team:0},{p:1,team:0}]});}catch(e){console.log(id,'ERR',e.message.slice(0,120));continue;}
 const t=G.zones.filter(z=>z.type==='town');console.log(id,'towns',t.length,'cities',t.filter(z=>z.city).map(z=>z.name).join(','),'cityBlocks',(G.city||[]).filter(c=>!c.gone).length,'small walls',t.filter(z=>!z.city&&z.wall&&!z.wall.mega).length);}
