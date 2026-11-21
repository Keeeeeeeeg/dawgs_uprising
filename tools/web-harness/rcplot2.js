const S=require('./load.js')('/tmp/ct/dbg.html');const fs=require('fs');const [map,seed,cx,cz,r]=process.argv.slice(2).map((v,i)=>i?+v:v);
const G=S.createGame({map,mode:'ffa',ai:[{p:0},{p:1},{p:2},{p:3}],seed});const R=[];
for(let x=cx-r;x<=cx+r;x+=1.5)for(let z=cz-r;z<=cz+r;z+=1.5){const c=G.__cell(x,z);R.push([x,z,c<0||G.__RC[c]===Infinity?1:0]);}
fs.writeFileSync('/tmp/ct/rc2.json',JSON.stringify({R,rails:G.rails.map(L=>({pts:L.pts,st:L.stops.map(q=>[q.st.E,q.st.Pl,q.st.E2,q.st.Pl2])}))}));
