const SIM=require('./load.js')(process.argv[2]);
for(const [id,m] of Object.entries(SIM.MAPS)){if(m.hidden)continue;const n=m.maxPlayers;const ai=[];for(let i=1;i<n;i++)ai.push({p:i-1});
const G=SIM.createGame({map:id,mode:'ffa',ai});
const coastal=G.zones.filter(z=>z.coastal&&z.type!=='airbase'),ports=G.zones.filter(z=>z.port);
const tags={};for(const z of G.zones)for(const p of z.plots)tags[p.tag]=(tags[p.tag]||0)+1;
console.log(id,'coastal',coastal.length,'ports',ports.length,'missing:',coastal.filter(z=>!z.port).map(z=>z.name).join(','),'dockyard-water-mil:',ports.filter(z=>z.plots.some(p=>p.water&&p.kind==='mil')).length,'streets',G.streets.length,JSON.stringify(tags));}
