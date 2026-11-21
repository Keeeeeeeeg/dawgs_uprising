const S=require('./load.js')('/tmp/ct/dbg.html');const fs=require('fs');const [map,seed,sec,cx,cz,r]=process.argv.slice(2);
const G=S.createGame({map,mode:'ffa',ai:[{p:0},{p:1},{p:2},{p:3}],seed:+seed});const T=S.__terrain?null:null;
const L=G.rails.find(l=>l.sector==+sec);const pts=[];const R=[];
for(let x=+cx-+r;x<=+cx+ +r;x+=2)for(let z=+cz-+r;z<=+cz+ +r;z+=2){const ok=G.passable(x,z);const h=G.heightAt(x,z);R.push([x,z,h,ok?1:0]);}
fs.writeFileSync('/tmp/ct/rc.json',JSON.stringify({R,pts:L.pts,st:L.stops.map(q=>[q.st.E,q.st.Pl]),zones:G.zones.map(z=>[z.x,z.z,z.r])}));
