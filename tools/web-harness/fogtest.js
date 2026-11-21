const SIM=require('./load.js')(process.argv[2]);
for(const fog of [false,true]){const G=SIM.createGame({map:'dawgs',mode:'ffa',ai:[{p:0},{p:1},{p:2}],seed:9,fog});
 for(let t=0;t<6000;t++)G.update(.1);
 const own=[0,1,2,3].map(f=>G.zones.filter(z=>z.owner===f).length),bld=[1,2,3].map(f=>G.zones.filter(z=>z.owner===f).reduce((a,z)=>a+z.plots.length,0));
 console.log('fog',fog,'zones',own.join(','),'AI buildings',bld.join(','),'units',G.units.filter(u=>u.alive).length);}
