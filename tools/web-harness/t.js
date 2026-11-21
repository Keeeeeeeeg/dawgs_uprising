let t=Date.now();const SIM=require('./load.js')(process.argv[2]);console.log('load',Date.now()-t);
t=Date.now();const G=SIM.createGame({map:'dawgs',mode:'ffa',ai:[{p:0},{p:1},{p:2}],seed:1234});console.log('game',Date.now()-t, G.GW,G.GH);
