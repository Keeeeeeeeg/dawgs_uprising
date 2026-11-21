const S=require('./load.js')(process.argv[2]);const fs=require('fs');
const G=S.createGame({map:process.argv[3],mode:'ffa',ai:[{p:0},{p:1},{p:2},{p:3}],seed:1});
fs.writeFileSync(process.argv[4],JSON.stringify({rails:G.rails.map(L=>({s:L.sector,pts:L.pts,st:L.stops.map(q=>[q.st.E,q.st.S,q.st.Pl,q.st.E2,q.st.Pl2])})),zones:G.zones.map(z=>[z.x,z.z,z.r,z.sector])}));
