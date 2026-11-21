  // airbases: a runway across the base (pointing at the map centre), terminals along one side
  for(const z of G.zones){if(z.type!=='airbase')continue;
    const A=ZTYPES.airbase,ang=Math.atan2(-z.z,-z.x),ux=Math.cos(ang),uz=Math.sin(ang),nx=-uz,nz=ux,L=A.runway,cx=z.x-nx*3,cz=z.z-nz*3;
    const terms=[];for(let k=0;k<A.terminals;k++){const o=(k-(A.terminals-1)/2)*6.5;terms.push({x:z.x+nx*5+ux*o,z:z.z+nz*5+uz*o,u:null});}
    z.air={ang,ux,uz,nx,nz,L,cx,cz,a:{x:cx-ux*L/2,z:cz-uz*L/2},b:{x:cx+ux*L/2,z:cz+uz*L/2},terms,rwyT:0};}

  // ---- build plots: each base grows like a small settlement that follows the ground ----
  // Towns put plots along three streets leaving their wall gaps, Ports string them along the waterfront, Fortresses keep a
  // tight ring of bastions with a short approach road, Airbases line the apron and runway ends, and HQs spread a district
  // along their gate avenues. Streets bend around slopes and water; every plot is levelled into the ground.
  const plotSave=new Map();
  function blockArea(x,z,r,on){
    for(let j=Math.floor((z-r-Z0)/CELL);j<=Math.floor((z+r-Z0)/CELL);j++)for(let i=Math.floor((x-r-X0)/CELL);i<=Math.floor((x+r-X0)/CELL);i++){
      if(i<0||j<0||i>=GW||j>=GH)continue;const k=j*GW+i,cx=X0+(i+.5)*CELL,cz=Z0+(j+.5)*CELL;if(Math.hypot(cx-x,cz-z)>r)continue;
      if(on){if(!plotSave.has(k))plotSave.set(k,pass[k]);pass[k]=0;}else if(plotSave.has(k)){pass[k]=plotSave.get(k);plotSave.delete(k);}
    }
  }
  const allPlots=[],streets=[];G.streets=streets;
  const PORT=BALANCE.port,TAU=6.2832;
  const angD=(a,b)=>Math.abs(Math.atan2(Math.sin(a-b),Math.cos(a-b)));
  function streetDist(s,x,z){let d=1e9;for(let i=1;i<s.pts.length;i++)d=Math.min(d,segDist(x,z,s.pts[i-1][0],s.pts[i-1][1],s.pts[i][0],s.pts[i][1]));return d;}
  function padFits(x,z,zone){
    if(!passable(x,z)||heightAt(x,z)<.75)return false;
    let lo=1e9,hi=-1e9;
    for(let b=0;b<TAU;b+=.785){const px=x+Math.cos(b)*2.8,pz=z+Math.sin(b)*2.8;if(!passable(px,pz))return false;const h=heightAt(px,pz);if(h<lo)lo=h;if(h>hi)hi=h;}
    if(hi-lo>1.7)return false;
    for(const p of allPlots)if(Math.abs(p.x-x)<6.6&&Math.hypot(p.x-x,p.z-z)<6.6)return false;
    for(const o of G.zones)if(Math.hypot(o.x-x,o.z-z)<o.r+(o===zone?3.6:6))return false;
    for(const s of streets)if(streetDist(s,x,z)<s.w/2+2.4)return false;
    return true;
  }
  // walk a street outward from (x,z): each 3 m step picks the bend that keeps it level and on dry, open ground
  function walkStreet(zone,x,z,a,len,score){
    const pts=[[x,z]];let L=0;
    while(L<len){let best=null,bs=1e9;const h0=heightAt(x,z);
      for(const da of [-.4,-.2,0,.2,.4]){const na=a+da,nx=x+Math.cos(na)*3,nz=z+Math.sin(na)*3;
        if(!passable(nx,nz))continue;const h=heightAt(nx,nz);if(h<.75)continue;
        let clash=false;for(const o of G.zones)if(o!==zone&&Math.hypot(o.x-nx,o.z-nz)<o.r+9){clash=true;break;}if(clash)continue;
        if(Math.hypot(nx-zone.x,nz-zone.z)<zone.r+1)continue;
        let sc=Math.abs(h-h0)*4+Math.abs(da)*1.1+(score?score(nx,nz,na):0);
        for(const sd of [1.571,-1.571])if(!passable(nx+Math.cos(na+sd)*4,nz+Math.sin(na+sd)*4))sc+=1.2;
        if(sc<bs){bs=sc;best=[na,nx,nz];}}
      if(!best)break;[a,x,z]=best;pts.push([x,z]);L+=3;}
    return pts;
  }
  const walkCache=new Map();
  function streetQuality(zone,a,len){const k=zone.id+':'+Math.round(a*40)+':'+len;if(walkCache.has(k))return walkCache.get(k);
    const p=walkStreet(zone,zone.x+Math.cos(a)*(zone.r+.5),zone.z+Math.sin(a)*(zone.r+.5),a,len);
    let open=0;for(const [x,z] of p)for(const sd of [1.571,-1.571])if(passable(x+Math.cos(a+sd)*5.5,z+Math.sin(a+sd)*5.5))open++;
    const q=(p.length-1)*3/len+open/(2*Math.max(1,p.length))*.6;walkCache.set(k,q);return q;}
  function addStreet(zone,a,len,w,score,from){
    const sx=from?from[0]:zone.x+Math.cos(a)*(zone.r+.5),sz=from?from[1]:zone.z+Math.sin(a)*(zone.r+.5);
    const pts=walkStreet(zone,sx,sz,a,len,score);if(pts.length<3)return null;
    if(!from)pts.unshift([zone.x+Math.cos(a)*zone.r*.45,zone.z+Math.sin(a)*zone.r*.45]); // run in through the gate
    const s={zone:zone.id,pts,w};streets.push(s);return s;
  }
  // plot spots either side of a street, every ~7 m (sides: +1 left, -1 right)
  function lineStreet(s,out,o){o=o||{};let acc=o.start||3;
    for(let i=1;i<s.pts.length;i++){const [x0,z0]=s.pts[i-1],[x1,z1]=s.pts[i];acc+=Math.hypot(x1-x0,z1-z0);if(acc<(o.every||7))continue;acc=0;
      const dir=Math.atan2(z1-z0,x1-x0);
      for(const sd of o.sides||[1,-1]){const na=dir+sd*1.571,off=o.off||5.6;out.push({x:x1+Math.cos(na)*off,z:z1+Math.sin(na)*off,ang:na+Math.PI,tag:o.tag||'street'});}}}
  function ringSpots(zone,out,radii,n,tag,skip){
    for(const rr of radii)for(let k=0;k<n;k++){const a=zone.gate+(k+.5)/n*TAU+(rr%2)*.13;if(skip&&skip(a))continue;
      out.push({x:zone.x+Math.cos(a)*rr,z:zone.z+Math.sin(a)*rr,ang:a,tag});}}
  // best rotation for a set of gate directions (offsets), judged by how far and how openly streets can run
  function pickGate(zone,offs,len,bias){let best=0,bs=-1e9;
    for(let k=0;k<36;k++){const g=k/36*TAU;let q=0;offs.forEach((o,i)=>{q+=streetQuality(zone,g+o,len)*(i===0?1.4:1);});if(bias)q+=bias(g);if(q>bs){bs=q;best=g;}}
    return best;}
  function waterDir(zone){let best=null,bd=1e9;
    for(let k=0;k<32;k++){const a=k/32*TAU;for(let d=zone.r+2;d<zone.r+46;d+=2){if(passable(zone.x+Math.cos(a)*d,zone.z+Math.sin(a)*d,wpass)){if(d<bd){bd=d;best=a;}break;}}}
    return best;}
  function layout(z,n){
    const out=[],T=z.type;let wa=(z.coastal&&PORT_TYPES.has(T))?waterDir(z):null;
    z.gate=0;
    if(T==='airbase'){
      const A=z.air;z.gate=Math.atan2(A.nz,A.nx);
      // apron row beyond the terminals, a guard post at each runway end, more along the far side
      for(const o of [0,-8,8,-16,16])out.push({x:z.x+A.nx*(z.r+5.5)+A.ux*o,z:z.z+A.nz*(z.r+5.5)+A.uz*o,ang:z.gate,tag:'apron'});
      for(const e of [1,-1])for(const s of [0,6,-6])out.push({x:z.x+A.ux*e*(z.r+7)+A.nx*s,z:z.z+A.uz*e*(z.r+7)+A.nz*s,ang:Math.atan2(A.uz*e,A.ux*e),tag:'end'});
      for(const o of [-9,9,0])out.push({x:z.x-A.nx*(z.r+6)+A.ux*o,z:z.z-A.nz*(z.r+6)+A.uz*o,ang:z.gate+Math.PI,tag:'far'});
      const s=addStreet(z,z.gate,22,3);if(s)lineStreet(s,out,{start:0});
    }else if(T==='fortress'){
      // one gate and a short approach road; bastions hug the walls, the rest sit just outside on level ground
      z.gate=pickGate(z,[0],18,wa!=null?g=>-angD(g,wa)*.15:null);
      const s=addStreet(z,z.gate,20,3);if(s)lineStreet(s,out,{start:2});
      if(wa!=null){const q=addStreet(z,wa+.9,16,3,null,[z.x+Math.cos(wa)*(z.r+3),z.z+Math.sin(wa)*(z.r+3)]);if(q)lineStreet(q,out,{tag:'quay'});}
      ringSpots(z,out,[z.r+5,z.r+9.5,z.r+14],11,'ring',a=>angD(a,z.gate)<.38);
    }else{
      // Towns and HQs: streets through the gates; Ports add a waterfront street
      const offs=T==='hq'?[0,1.571,3.1416,4.712]:[0,2.513,5.027];
      const len=T==='hq'?34:28;
      z.gate=pickGate(z,offs,len,wa!=null?g=>-angD(g,wa+Math.PI)*.12:null);
      const ranked=offs.map(o=>z.gate+o).sort((a,b)=>streetQuality(z,b,len)-streetQuality(z,a,len));
      if(wa!=null){
        // waterfront: start on the shore side and run both ways along the coast, holding a steady height above the sea
        const sx=z.x+Math.cos(wa)*(z.r+4),sz=z.z+Math.sin(wa)*(z.r+4);
        for(const sd of [1.571,-1.571]){const q=addStreet(z,wa+sd,T==='hq'?26:22,3,(x,zz)=>Math.abs(heightAt(x,zz)-1.5)*1.2,[sx,sz]);if(q)lineStreet(q,out,{start:4,tag:'quay'});}
      }
      ranked.forEach((a,i)=>{const s=addStreet(z,a,i===0?len:len*.75,i===0?3.4:3);if(s)lineStreet(s,out,{start:i===0?3:1});});
      ringSpots(z,out,[z.r+6,z.r+11],T==='hq'?14:10,'ring');
    }
    ringSpots(z,out,[z.r+6,z.r+8,z.r+10.5,z.r+13,z.r+16],16,'fallback');
    return out;
  }
  for(const z of G.zones){
    const ZT=ZTYPES[z.type],want=Object.assign({},ZT.slots);
    if(z.coastal&&z.type==='fortress')want.fort+=PORT.fortressFortSlots;   // Port Fortress: coastal defences
    const n=want.mil+want.eco+want.fort;
    z.plots=[];
    for(const c of layout(z,n)){if(z.plots.length>=n)break;if(!padFits(c.x,c.z,z))continue;
      const pl={i:z.plots.length,x:c.x,z:c.z,y:0,ang:c.ang,fac:null,tag:c.tag};
      {const wc=nearestPassCell(cellOf(c.x,c.z),wpass);if(wc>=0){const w=cellCenter(wc);if(Math.hypot(w.x-c.x,w.z-c.z)<(z.coastal?BALANCE.mapMix.portFallbackReach+15:30))pl.water=w;}}
      z.plots.push(pl);allPlots.push(pl);}
    // plot kinds: defences take the outskirts, spread around the base; economy the plots nearest the centre;
    // military the rest (a Port keeps its military plot nearest the water for the Dockyard)
    const have=z.plots.length,kinds=['fort','mil','eco'],share={};
    let left=have;for(const k of kinds){share[k]=Math.floor(want[k]*have/n);left-=share[k];}
    for(const k of kinds.slice().sort((a,b)=>(want[b]*have/n-share[b])-(want[a]*have/n-share[a])))if(left>0){share[k]++;left--;}
    const free=z.plots.slice(),dc=p=>Math.hypot(p.x-z.x,p.z-z.z),take=p=>free.splice(free.indexOf(p),1);
    z.port=PORT_TYPES.has(z.type)&&z.coastal&&z.plots.some(pl=>pl.water);
    if(z.port&&share.mil>0){const w=free.filter(p=>p.water).sort((a,b)=>Math.hypot(a.water.x-a.x,a.water.z-a.z)-Math.hypot(b.water.x-b.x,b.water.z-b.z))[0];w.kind='mil';take(w);share.mil--;}
    const maxD=Math.max(1,...free.map(dc)),chosen=[];
    for(let k=0;k<share.fort;k++){let best=null,bs=-1e9;
      for(const p of free){const a=Math.atan2(p.z-z.z,p.x-z.x);let sep=TAU;for(const q of chosen)sep=Math.min(sep,angD(a,Math.atan2(q.z-z.z,q.x-z.x)));
        const s=dc(p)/maxD*1.2+(chosen.length?sep:0)+(p.tag==='end'||p.tag==='ring'?.25:0);if(s>bs){bs=s;best=p;}}
      if(!best)break;best.kind='fort';chosen.push(best);take(best);}
    free.sort((a,b)=>dc(a)-dc(b));
    for(let k=0;k<share.eco&&free.length;k++){const p=free.shift();p.kind='eco';}
    for(const p of free)p.kind='mil';
    z.slots={mil:0,eco:0,fort:0};for(const pl of z.plots)z.slots[pl.kind]++;
  }
  // level the ground under every plot and recheck which cells troops can cross
  {const VWv=VW,touched=new Set();
    for(const p of allPlots){let s=0,c=0;for(let b=0;b<TAU;b+=1.05){s+=heightAt(p.x+Math.cos(b)*2,p.z+Math.sin(b)*2);c++;}const H=Math.max(.8,s/c);
      for(let j=Math.floor((p.z-6-Z0)/CELL);j<=Math.ceil((p.z+6-Z0)/CELL);j++)for(let i=Math.floor((p.x-6-X0)/CELL);i<=Math.ceil((p.x+6-X0)/CELL);i++){
        if(i<0||j<0||i>GW||j>GH)continue;const d=Math.hypot(X0+i*CELL-p.x,Z0+j*CELL-p.z);if(d>6)continue;const t=1-smooth(3.3,6,d),k=j*VWv+i;hv[k]=hv[k]*(1-t)+H*t;
        for(const [a,b] of [[0,0],[-1,0],[0,-1],[-1,-1]])touched.add((j+b)*GW+(i+a));}}
    const nearProp=(x,z)=>map.props.some(q=>q.circles.some(c=>Math.hypot(c.x-x,c.z-z)<=c.r+.6));
    for(const k of touched){if(k<0||k>=GW*GH)continue;const i=k%GW,j=(k-i)/GW;if(i>=GW-1&&false)continue;
      const a=hv[j*VWv+i],b=hv[j*VWv+i+1],c=hv[(j+1)*VWv+i],d=hv[(j+1)*VWv+i+1],mx=Math.max(a,b,c,d),mn=Math.min(a,b,c,d),av=(a+b+c+d)/4;
      const ok=mn>.15&&av<7.2&&mx-mn<3.2;if(!ok)pass[k]=0;else if(!pass[k]&&!nearProp(X0+(i+.5)*CELL,Z0+(j+.5)*CELL))pass[k]=1;}
    for(const p of allPlots)p.y=heightAt(p.x,p.z);
  }

