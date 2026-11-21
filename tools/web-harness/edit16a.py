p='/home/claude/vu/v16.html';s=open(p).read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(a[:80],s.count(a));s=s.replace(a,b)

rep("planes:2, terminals:3, runway:24},","planes:2, terminals:3, runway:44},")

# ---- coves in buildMap
rep("""  const pass=new Uint8Array(GW*GH),wpass=new Uint8Array(GW*GH);
  for(let j=0;j<GH;j++)for(let i=0;i<GW;i++){""","""  // coastal bases sit on a cove: a sheltered inlet cut from the sea toward the base, deep enough for boats to come in
  const coves=[];
  if(!MAP.noWater){const hvAt=(x,z)=>{const i=Math.max(0,Math.min(GW,Math.round((x-X0)/CELL))),j=Math.max(0,Math.min(GH,Math.round((z-Z0)/CELL)));return hv[j*VW+i];};
    ZONES_DEF.forEach((zd,zi)=>{if(!zd[4]||zd[1]==='airbase')return;
      const r=ZTYPES[zd[1]].r,cx=zd[2],cz=zd[3];let best=null;
      for(let k=0;k<48;k++){const a=k/48*6.2832;for(let d=r+8;d<r+48;d+=2){if(hvAt(cx+Math.cos(a)*d,cz+Math.sin(a)*d)<-.9){if(!best||d<best.d)best={a,d};break;}}}
      if(!best)return;
      const ux=Math.cos(best.a),uz=Math.sin(best.a),R=8.5,head=r+14,mouth=Math.max(head+6,best.d+6);
      const ax=cx+ux*head,az=cz+uz*head,bx=cx+ux*mouth,bz=cz+uz*mouth;
      if(ZONES_DEF.some(o=>o!==zd&&segDist(o[2],o[3],ax,az,bx,bz)<ZTYPES[o[1]].r+R+14))return;
      if(NECKS.some(N=>segDist(N.a[0],N.a[1],ax,az,bx,bz)<R+10||segDist(N.b[0],N.b[1],ax,az,bx,bz)<R+10))return;
      for(let j=Math.max(0,Math.floor((Math.min(az,bz)-R-6-Z0)/CELL));j<=Math.min(GH,Math.ceil((Math.max(az,bz)+R+6-Z0)/CELL));j++)
        for(let i=Math.max(0,Math.floor((Math.min(ax,bx)-R-6-X0)/CELL));i<=Math.min(GW,Math.ceil((Math.max(ax,bx)+R+6-X0)/CELL));i++){
          const d=segDist(X0+i*CELL,Z0+j*CELL,ax,az,bx,bz);if(d>R+5)continue;const t=smooth(R-2.5,R+5,d),k=j*VW+i;hv[k]=Math.min(hv[k],hv[k]*t-2.4*(1-t));}
      coves.push({zone:zi,ax,az,bx,bz,ux,uz,R});});}
  const pass=new Uint8Array(GW*GH),wpass=new Uint8Array(GW*GH);
  for(let j=0;j<GH;j++)for(let i=0;i<GW;i++){""")
rep("  return {hv,VW,VH,pass,wpass,props};","  return {hv,VW,VH,pass,wpass,props,coves};")

# ---- airbase: long runway on the best line, taxiway, corridor flattening
old_air=s[s.index("  // airbases: a runway across the base (pointing at the map centre), terminals along one side"):s.index("  // ---- build plots: each base grows like a small settlement")]
s=s.replace(old_air,"")
rep("""  const allPlots=[],streets=[];G.streets=streets;
  const PORT=BALANCE.port,TAU=6.2832;
  const angD=(a,b)=>Math.abs(Math.atan2(Math.sin(a-b),Math.cos(a-b)));""","""  const allPlots=[],streets=[];G.streets=streets;
  const PORT=BALANCE.port,TAU=6.2832;
  const angD=(a,b)=>Math.abs(Math.atan2(Math.sin(a-b),Math.cos(a-b)));
  for(const c of map.coves)G.zones[c.zone].cove=c;
  // ground levelling: blend the heightfield toward H with weight w(x,z) in a box, then recheck which cells troops can cross
  const touched=new Set();
  function level(x0,z0,x1,z1,w,H){
    for(let j=Math.max(0,Math.floor((z0-Z0)/CELL));j<=Math.min(GH,Math.ceil((z1-Z0)/CELL));j++)for(let i=Math.max(0,Math.floor((x0-X0)/CELL));i<=Math.min(GW,Math.ceil((x1-X0)/CELL));i++){
      const t=w(X0+i*CELL,Z0+j*CELL);if(t<=0)continue;const k=j*VW+i;hv[k]=hv[k]*(1-t)+H*t;
      for(const [a,b] of [[0,0],[-1,0],[0,-1],[-1,-1]])touched.add((j+b)*GW+(i+a));}}
  const nearProp=(x,z)=>map.props.some(q=>q.circles.some(c=>Math.hypot(c.x-x,c.z-z)<=c.r+.6));
  function repass(){for(const k of touched){if(k<0||k>=GW*GH)continue;const i=k%GW,j=(k-i)/GW;
      const a=hv[j*VW+i],b=hv[j*VW+i+1],c=hv[(j+1)*VW+i],d=hv[(j+1)*VW+i+1],mx=Math.max(a,b,c,d),mn=Math.min(a,b,c,d),av=(a+b+c+d)/4;
      const ok=mn>.15&&av<7.2&&mx-mn<3.2;if(!ok)pass[k]=0;else if(!pass[k]&&!nearProp(X0+(i+.5)*CELL,Z0+(j+.5)*CELL))pass[k]=1;}
    touched.clear();}
  // airbases, laid out like an airport diagram: a long runway on the flattest open line through the base, a parallel
  // taxiway with links at both ends and the middle, and the apron with its terminal stands on the far side of the taxiway.
  // In runway coordinates (s along it, q across it, runway centre q=0): taxiway q=5.5, stands q=11, terminal q=16.5.
  const airCorr=[];G.airCorr=airCorr;
  const AQ0=-6,AQ1=18;   // the cleared strip across the runway
  function inCorr(x,z,pad){for(const A of airCorr){const s=(x-A.cx)*A.ux+(z-A.cz)*A.uz,q=(x-A.cx)*A.nx+(z-A.cz)*A.nz;
    if(Math.abs(s)<=A.L/2+6+pad&&q>=AQ0-pad&&q<=AQ1+pad)return true;}return false;}
  for(const z of G.zones){if(z.type!=='airbase')continue;
    const AB=ZTYPES.airbase,L=AB.runway,half=L/2+6,toC=Math.atan2(-z.z,-z.x);
    let best=toC,bs=1e9;
    for(let k=0;k<24;k++){const ang=k/24*TAU,ux=Math.cos(ang),uz=Math.sin(ang),nx=-uz,nz=ux,cx=z.x-nx*6,cz=z.z-nz*6;let sc=angD(ang,toC)*.4;
      for(let t=-half;t<=half;t+=4)for(const q of [AQ0,0,6,12,AQ1]){const x=cx+ux*t+nx*q,zz=cz+uz*t+nz*q;
        if(x<X0+6||x>X0+WORLD_W-6||zz<Z0+6||zz>Z0+WORLD_H-6){sc+=20;continue;}
        const h=heightAt(x,zz);sc+=Math.abs(h-z.y)*.6+(h<.7?8:0)+(passable(x,zz)?0:1.5);
        for(const o of G.zones)if(o!==z&&Math.hypot(o.x-x,o.z-zz)<o.r+10)sc+=60;}
      if(sc<bs){bs=sc;best=ang;}}
    const ang=best,ux=Math.cos(ang),uz=Math.sin(ang),nx=-uz,nz=ux,cx=z.x-nx*6,cz=z.z-nz*6;
    const terms=[];for(let k=0;k<AB.terminals;k++){const o=(k-(AB.terminals-1)/2)*6.5;terms.push({x:cx+nx*11+ux*o,z:cz+nz*11+uz*o,u:null});}
    z.air={ang,ux,uz,nx,nz,L,cx,cz,a:{x:cx-ux*L/2,z:cz-uz*L/2},b:{x:cx+ux*L/2,z:cz+uz*L/2},tx:cx+nx*5.5,tz:cz+nz*5.5,terms,rwyT:0};
    airCorr.push(z.air);
    // level the strip (full inside, easing out over 7 m)
    const ext=half+12,H=z.y;
    level(cx-ext-20,cz-ext-20,cx+ext+20,cz+ext+20,(x,zz)=>{const s=Math.abs((x-cx)*ux+(zz-cz)*uz),q=(x-cx)*nx+(zz-cz)*nz;
      const ds=Math.max(0,s-half),dq=Math.max(0,AQ0-q,q-AQ1),d=Math.hypot(ds,dq);return d>=7?0:1-smooth(0,7,d);},H);
  }
  repass();""")

# pads & streets avoid the airfields
rep("""    for(const s of streets)if(streetDist(s,x,z)<s.w/2+2.4)return false;
    return true;""","""    for(const s of streets)if(streetDist(s,x,z)<s.w/2+2.4)return false;
    if(inCorr(x,z,3))return false;
    return true;""")
rep("""        if(Math.hypot(nx-zone.x,nz-zone.z)<zone.r+1)continue;""","""        if(Math.hypot(nx-zone.x,nz-zone.z)<zone.r+1||inCorr(nx,nz,2))continue;""")

# airbase plot layout
rep("""      const A=z.air;z.gate=Math.atan2(A.nz,A.nx);
      // apron row beyond the terminals, a guard post at each runway end, more along the far side
      for(const o of [0,-8,8,-16,16])out.push({x:z.x+A.nx*(z.r+5.5)+A.ux*o,z:z.z+A.nz*(z.r+5.5)+A.uz*o,ang:z.gate,tag:'apron'});
      for(const e of [1,-1])for(const s of [0,6,-6])out.push({x:z.x+A.ux*e*(z.r+7)+A.nx*s,z:z.z+A.uz*e*(z.r+7)+A.nz*s,ang:Math.atan2(A.uz*e,A.ux*e),tag:'end'});
      for(const o of [-9,9,0])out.push({x:z.x-A.nx*(z.r+6)+A.ux*o,z:z.z-A.nz*(z.r+6)+A.uz*o,ang:z.gate+Math.PI,tag:'far'});""","""      const A=z.air;z.gate=Math.atan2(A.nz,A.nx);
      // a row behind the terminal, guard posts past each runway end, more along the far side of the runway
      for(const o of [0,-8,8,-16,16,-24,24])out.push({x:A.cx+A.nx*(AQ1+6)+A.ux*o,z:A.cz+A.nz*(AQ1+6)+A.uz*o,ang:z.gate,tag:'apron'});
      for(const e of [1,-1])for(const q of [0,7,-7])out.push({x:A.cx+A.ux*e*(A.L/2+11)+A.nx*q,z:A.cz+A.uz*e*(A.L/2+11)+A.nz*q,ang:Math.atan2(A.uz*e,A.ux*e),tag:'end'});
      for(const o of [-10,10,0,-20,20])out.push({x:A.cx+A.nx*(AQ0-6.5)+A.ux*o,z:A.cz+A.nz*(AQ0-6.5)+A.uz*o,ang:z.gate+Math.PI,tag:'far'});""")
# airbase access road starts behind the terminal
rep("""      const s=addStreet(z,z.gate,22,3);if(s)lineStreet(s,out,{start:0});""","""      const s=addStreet(z,z.gate,22,3,null,[A.cx+A.nx*(AQ1+2.5),A.cz+A.nz*(AQ1+2.5)]);if(s){s.pts.unshift([A.cx+A.nx*16,A.cz+A.nz*16]);lineStreet(s,out,{start:0});}""")

# ports: quays along the cove
rep("""      if(wa!=null){const q=addStreet(z,wa+.9,16,3,null,[z.x+Math.cos(wa)*(z.r+3),z.z+Math.sin(wa)*(z.r+3)]);if(q)lineStreet(q,out,{tag:'quay'});}""","""      if(z.cove)coveQuays(z,out,16);
      else if(wa!=null){const q=addStreet(z,wa+.9,16,3,null,[z.x+Math.cos(wa)*(z.r+3),z.z+Math.sin(wa)*(z.r+3)]);if(q)lineStreet(q,out,{tag:'quay'});}""")
rep("""      if(wa!=null){
        // waterfront""","""      if(z.cove)coveQuays(z,out,T==='hq'?26:22);
      else if(wa!=null){
        // waterfront""")
rep("""  function layout(z,n){
    const out=[],T=z.type;let wa=(z.coastal&&PORT_TYPES.has(T))?waterDir(z):null;""","""  // a quay down each side of the base's cove, running out toward the sea at a steady height above the water
  function coveQuays(z,out,len){const c=z.cove,px=-c.uz,pz=c.ux;
    for(const sd of [1,-1]){const sx=c.ax+px*sd*(c.R+3.5)-c.ux*3,sz=c.az+pz*sd*(c.R+3.5)-c.uz*3;if(!passable(sx,sz))continue;
      const q=addStreet(z,Math.atan2(c.uz,c.ux),len,3,(x,zz)=>Math.abs(heightAt(x,zz)-1.4)*1.2,[sx,sz]);if(q){q.quay=true;lineStreet(q,out,{start:4,tag:'quay',sides:[-sd]});}}}
  function layout(z,n){
    const out=[],T=z.type;let wa=(z.coastal&&PORT_TYPES.has(T))?(z.cove?Math.atan2(z.cove.uz,z.cove.ux):waterDir(z)):null;""")

# plot levelling: use shared helper, wider flat yard (no plate clipping)
old_lv=s[s.index("  // level the ground under every plot and recheck which cells troops can cross"):s.index("  // ---- units ----")]
s=s.replace(old_lv,"""  // level the ground under every plot (a flat yard a little wider than the plate) and recheck which cells troops can cross
  for(const p of allPlots){let sm=0,c=0;for(let b=0;b<TAU;b+=1.05){sm+=heightAt(p.x+Math.cos(b)*2.5,p.z+Math.sin(b)*2.5);c++;}const H=Math.max(.8,sm/c);
    level(p.x-7.5,p.z-7.5,p.x+7.5,p.z+7.5,(x,zz)=>{const d=Math.hypot(x-p.x,zz-p.z);return d>7.5?0:1-smooth(4.2,7.5,d);},H);}
  repass();
  for(const p of allPlots)p.y=heightAt(p.x,p.z);

""")

# taxi routes along the taxiway
rep("""      if(m){u.mission=m;u.pstate='taxiOut';releaseTerminal(u);}""","""      if(m){u.mission=m;u.pstate='taxiOut';u.wps=null;releaseTerminal(u);}""")
rep("""    if(u.pstate==='taxiOut'){u.landed=true;
      if(taxiTo(u,A.a.x,A.a.z,dt)&&A.rwyT<=G.time){A.rwyT=G.time+AIR.runwayHold;u.pstate='takeoff';u.ang=A.ang;u.v=AIR.taxi;u.roll=0;}
      return;}""","""    if(u.pstate==='taxiOut'){u.landed=true;   // onto the taxiway, along it to the runway end, then onto the threshold
      if(!u.wps)u.wps=[twPoint(A,twS(A,u.x,u.z)),twPoint(A,-A.L/2),{x:A.a.x,z:A.a.z}];
      if(followWps(u,dt)&&A.rwyT<=G.time){A.rwyT=G.time+AIR.runwayHold;u.pstate='takeoff';u.ang=A.ang;u.v=AIR.taxi;u.roll=0;u.wps=null;}
      return;}""")
rep("""      if(u.v<=AIR.taxi||u.roll>=A.L)u.pstate='taxiIn';""","""      if(u.v<=AIR.taxi||u.roll>=A.L){u.pstate='taxiIn';u.wps=null;}""")
rep("""    if(u.pstate==='taxiIn'){u.landed=true;const t=A.terms[u.term];
      if(taxiTo(u,t.x,t.z,dt)){""","""    if(u.pstate==='taxiIn'){u.landed=true;const t=A.terms[u.term];   // off the runway at the nearest link, along the taxiway, into the stand
      if(!u.wps)u.wps=[twPoint(A,twS(A,u.x,u.z)),twPoint(A,twS(A,t.x,t.z)),{x:t.x,z:t.z}];
      if(followWps(u,dt)){u.wps=null;""")
rep("""  function scramble(u){releaseTerminal(u);""","""  function twS(A,x,z){return (x-A.tx)*A.ux+(z-A.tz)*A.uz;}
  function twPoint(A,s){s=Math.max(-A.L/2,Math.min(A.L/2,s));return {x:A.tx+A.ux*s,z:A.tz+A.uz*s};}
  function followWps(u,dt){if(!u.wps||!u.wps.length)return true;const w=u.wps[0];if(taxiTo(u,w.x,w.z,dt))u.wps.shift();return !u.wps.length;}
  function scramble(u){u.wps=null;releaseTerminal(u);""")
open(p,'w').write(s)
print('ok')
