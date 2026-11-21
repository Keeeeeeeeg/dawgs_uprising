const S=require('./load.js')(process.argv[2]);
for(const map of process.argv[3].split(',')){const G=S.createGame({map,mode:'ffa',ai:[{p:0},{p:1},{p:2},{p:3}],seed:+(process.argv[4]||1)});const o=[];
 for(const L of G.rails){const P=L.pts,n=P.length;let c=0,at=[];
  const X=(a,b,c2,d)=>{const d1=(b[0]-a[0])*(c2[1]-a[1])-(b[1]-a[1])*(c2[0]-a[0]),d2=(b[0]-a[0])*(d[1]-a[1])-(b[1]-a[1])*(d[0]-a[0]),d3=(d[0]-c2[0])*(a[1]-c2[1])-(d[1]-c2[1])*(a[0]-c2[0]),d4=(d[0]-c2[0])*(b[1]-c2[1])-(d[1]-c2[1])*(b[0]-c2[0]);return d1*d2<0&&d3*d4<0;};
  for(let i=0;i<n;i++)for(let j=i+2;j<n;j++){if(i===0&&j===n-1)continue;if(X(P[i],P[(i+1)%n],P[j],P[(j+1)%n])){c++;at.push(P[i].map(v=>v.toFixed(0)).join(','));}}
  o.push('S'+L.sector+':'+L.stops.length+(c?' X'+c+'@'+at.join(' '):''));}
 console.log(map,G.sectors.length+'sec',G.rails.length+'rails |',o.join(' | '));}
