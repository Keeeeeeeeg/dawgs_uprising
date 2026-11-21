const SIM=require('./load.js')(process.argv[2]);
for(const id of (process.argv[3]||'twinvalleys').split(',')){const G=SIM.createGame({map:id,mode:'ffa',ai:[{p:0,team:0}]});
  const R=G.rails||[];let tot=0;for(const L of R)tot+=L.len;
  console.log(id,'sectors',G.sectors.length,'lines',R.length,'len',tot.toFixed(0),R.map(L=>L.stops.length+'st/'+L.len.toFixed(0)+(L.open?'o':'c')).join(' '),
    'dupStations',R.some(L=>new Set(L.stops.map(s=>s.zid)).size!==L.stops.length));
  // give player 0 a whole sector and watch its train
  const S=G.sectors.find(S=>S.rail!=null);if(!S)continue;for(const zi of S.zones)G.zones[zi].owner=0;
  const seen=[];G.on('trainStop',(u,stp)=>seen.push(stp.zid));
  for(let t=0;t<400;t+=.25)G.update(.25);
  console.log('  stops visited',seen.join(','));}
