// jack.js: tight turn-backs on each railway ring: net heading change over any 30 m stretch
const S=require('./load.js')(process.argv[2]);
for(const map of process.argv[3].split(',')){for(const seed of (process.argv[4]||'1').split(',')){const G=S.createGame({map,mode:'ffa',ai:[{p:0},{p:1},{p:2},{p:3}],seed:+seed});const o=[];let bad=0;
 for(const L of G.rails){const W=30,hd=s=>G.railAt(L,s).ang;let worst=0,at=null;
  for(let s=0;s<(L.open?L.len-W:L.len);s+=2){const a=Math.abs(Math.atan2(Math.sin(hd(s+W)-hd(s)),Math.cos(hd(s+W)-hd(s))));if(a>worst){worst=a;at=G.railAt(L,s);}}
  const d=worst*57.3;if(d>100)bad++;o.push('S'+L.sector+':'+d.toFixed(0)+(d>100?'@'+at.x.toFixed(0)+','+at.z.toFixed(0):''));}
 console.log(map,seed,'bad',bad,'|',o.join(' '));}}
