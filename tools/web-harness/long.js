const SIM=require('./load.js')(process.argv[2]);
for(const id of ['dawgs','crown','twinreach']){const t0=Date.now();
const G=SIM.createGame({map:id,mode:'ffa',ai:[{p:0,team:0},{p:1,team:0},{p:2,team:0}]});
let man=0,em=0;G.on('emerge',()=>em++);
for(let t=0;t<600;t+=.25){G.update(.25);}
for(const z of G.zones)if(z.posts)man+=z.posts.filter(v=>v!=null).length+z.pitsU.filter(v=>v!=null).length;
console.log(id,'fallen',G.city?G.city.filter(c=>c.fallen).length+'/'+G.city.length:0,'units',G.units.length,'manned',man,'emerged',em,'ms',Date.now()-t0);}
