const SIM=require('./load.js')(process.argv[2]);
for(const id of ['dawgs','brine','coral','ember','twinreach']){const G=SIM.createGame({map:id,mode:'ffa',ai:[{p:0}],seed:1});
 console.log(id,G.zones.filter(z=>z.cove).map(z=>z.type+' '+z.cove.ax.toFixed(0)+','+z.cove.az.toFixed(0)+'->'+z.cove.bx.toFixed(0)+','+z.cove.bz.toFixed(0)).join(' | '),'coastal',G.zones.filter(z=>z.port).length);}
