const S=require('./load.js')(process.argv[2]);S.BALANCE.horde.waves=1;S.BALANCE.horde.prep=5;
const G=S.createGame({map:'starfall1',mode:'teams',ai:[],seed:5,horde:{}});let ev=[];G.on('horde',(k,a)=>ev.push(k+a));
for(let t=0;t<400*4&&!G.over;t++)G.update(.25);console.log('over',G.over&&G.over.win,G.over&&G.over.horde);
console.log('cont',G.applyCmd?G.applyCmd(0,{k:'hordeGo'}):G.hordeContinue(),'over now',G.over);for(let t=0;t<120*4&&!G.over;t++)G.update(.25);console.log('wave',G.horde.wave,G.horde.phase,G.horde.cont,ev.join(' '));
