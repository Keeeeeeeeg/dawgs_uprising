const S=require('./load.js')(process.argv[2]);
for(const map of process.argv[3].split(',')){const G=S.createGame({map,mode:'ffa',ai:[{p:0},{p:1},{p:2},{p:3}],seed:1});
 for(const L of G.rails){const n=L.pts.length,out=[];for(let i=0;i<n;i++){const a=L.pts[(i+n-1)%n],b=L.pts[i],c=L.pts[(i+1)%n];const t1=Math.atan2(b[1]-a[1],b[0]-a[0]),t2=Math.atan2(c[1]-b[1],c[0]-b[0]);const d=Math.abs(Math.atan2(Math.sin(t2-t1),Math.cos(t2-t1)))*57.3;
   const seg=Math.min(Math.hypot(b[0]-a[0],b[1]-a[1]),Math.hypot(c[0]-b[0],c[1]-b[1]));
   if(d>12){let sd=1e9;for(const sp of L.stops)sd=Math.min(sd,Math.hypot(sp.st.S[0]-b[0],sp.st.S[1]-b[1]));out.push(`${d.toFixed(0)}°@i${i}/${n} seg${seg.toFixed(1)} st${sd.toFixed(0)}`);}}
  if(out.length)console.log(map,'S'+L.sector,out.join(', '));}}
