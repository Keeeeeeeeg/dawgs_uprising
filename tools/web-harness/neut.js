const S=require('./load.js')(process.argv[2]);const id='fourcrowns',ai=[{p:0},{p:1},{p:2}];
const G=S.createGame({map:id,mode:'ffa',ai,seed:7});for(let t=0;t<15*60*4;t++)G.update(.25);
console.log(G.zones.filter(z=>z.owner==null).map(z=>z.name+' '+z.type+(z.city?' city':'')));
