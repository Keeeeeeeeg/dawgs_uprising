global.HYBDBG=[];const S=require('./load.js')(process.argv[2]);
for(const map of process.argv[3].split(',')){HYBDBG.length=0;const t=Date.now();S.createGame({map,mode:'ffa',ai:[{p:0},{p:1}],seed:1});
 const f=HYBDBG.filter(x=>!x[1]);console.log(map,Date.now()-t,'ms legs',HYBDBG.length,'fail',f.length,'avgIt',(HYBDBG.reduce((a,b)=>a+b[0],0)/HYBDBG.length|0));}
