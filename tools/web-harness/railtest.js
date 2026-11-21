const S=require('./load.js')(process.argv[2]);
for(const map of (process.argv[3]||'').split(',')){try{const G=S.createGame({map,mode:'ffa',ai:[{p:0},{p:1},{p:2},{p:3}],seed:1});
 const rs=G.rails.map(L=>{let maxTurn=0;const n=L.pts.length;for(let i=0;i<n;i++){const a=L.pts[(i+n-1)%n],b=L.pts[i],c=L.pts[(i+1)%n];const t1=Math.atan2(b[1]-a[1],b[0]-a[0]),t2=Math.atan2(c[1]-b[1],c[0]-b[0]);maxTurn=Math.max(maxTurn,Math.abs(Math.atan2(Math.sin(t2-t1),Math.cos(t2-t1))));}
   const gap=Math.hypot(L.pts[0][0]-L.pts[n-1][0],L.pts[0][1]-L.pts[n-1][1]);return `S${L.sector}:${L.stops.length}st len${L.len.toFixed(0)} open${L.open} seam${gap.toFixed(1)} maxTurn${(maxTurn*57.3).toFixed(0)}`;});
 console.log(map,'sectors',G.sectors.length,rs.join(' | '));
 for(let t=0;t<400;t+=.5)G.update(.5);console.log('  trains',G.units.filter(u=>u.alive&&u.rail!=null).length);}catch(e){console.log(map,'ERR',e.stack.split('\n').slice(0,3).join(' '));}}
