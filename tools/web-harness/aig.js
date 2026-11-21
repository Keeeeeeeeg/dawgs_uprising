const S=require('./load.js')(process.argv[2]);
const G=S.createGame({map:'fourcrowns',mode:'ffa',ai:[{p:0},{p:1},{p:2},{p:3}],seed:+(process.argv[3]||7)});
let t=0,k={};G.on('death',u=>{k[u.type]=(k[u.type]||0)+1;});
for(;t<1500&&!G.over;t+=.25)G.update(.25);
console.log('t',t,'over',!!G.over,'units',G.units.filter(u=>u.alive).length,'deaths',JSON.stringify(k));
