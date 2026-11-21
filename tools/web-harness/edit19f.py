p='/home/claude/vu/v18.html';s=open(p).read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(s.count(a),a[:80]);s=s.replace(a,b)
rep("  const FOG=!!opts.fog; // fog of war: a setup-screen checkbox (off by default)","""  const FOG=!!opts.fog; // fog of war: a setup-screen checkbox (off by default)
  // ---- fog for the AI: with fog on, an army only knows what its own team can see right now (units' sight, bases'
  // surroundings). Enemy buildings and a base's defences are remembered from when they were last seen.
  const visCache=[];
  function teamGrid(f){let c=visCache[f];if(c&&G.time-c.t<.5)return c.g;
    const g=c&&c.g||new Uint8Array(VGW*VGH);g.fill(0);
    const st=(x,z,r)=>{const i0=Math.max(0,Math.floor((x-r-X0)/VC)),i1=Math.min(VGW-1,Math.floor((x+r-X0)/VC)),j0=Math.max(0,Math.floor((z-r-Z0)/VC)),j1=Math.min(VGH-1,Math.floor((z+r-Z0)/VC));
      for(let j=j0;j<=j1;j++)for(let i=i0;i<=i1;i++){const cx=X0+(i+.5)*VC,cz=Z0+(j+.5)*VC;if((cx-x)*(cx-x)+(cz-z)*(cz-z)<=r*r)g[j*VGW+i]=1;}};
    for(const u of G.units)if(u.alive&&allied(u.f,f))st(u.x,u.z,u.def.sight+4);
    for(const z of G.zones)if(z.owner!==null&&allied(z.owner,f))st(z.x,z.z,z.r+16);
    visCache[f]={t:G.time,g};
    // remember what is seen: enemy buildings and each base's defences
    const bit=1<<f;
    for(const z of G.zones){const seen=g[Math.max(0,Math.min(VGH-1,Math.floor((z.z-Z0)/VC)))*VGW+Math.max(0,Math.min(VGW-1,Math.floor((z.x-X0)/VC)))];
      if(seen){z.intel=z.intel||[];z.intel[f]={gar:z.garN,def:z.defN,t:G.time};}
      for(const p of z.plots){const i=Math.floor((p.x-X0)/VC),j=Math.floor((p.z-Z0)/VC);if(i>=0&&j>=0&&i<VGW&&j<VGH&&g[j*VGW+i])p.seen=(p.seen||0)|bit;}}
    return g;}
  function sees(f,x,z){if(!FOG)return true;const g=teamGrid(f),i=Math.floor((x-X0)/VC),j=Math.floor((z-Z0)/VC);return i>=0&&j>=0&&i<VGW&&j<VGH&&g[j*VGW+i]===1;}
  const knowsPlot=(f,p)=>!FOG||!!((p.seen||0)&(1<<f));
  // what an army believes defends a base: live if it can see it, else the last sighting, else a full garrison
  function knownDefence(f,z){if(z.owner===null)return 0;if(sees(f,z.x,z.z))return z.garN+z.defN;const k=z.intel&&z.intel[f];return k?k.gar+k.def:ZTYPES[z.type].garrison;}""")
# AI decisions only use what is seen
rep("  const airborneHostiles=(f)=>G.units.filter(o=>o.alive&&isAir(o)&&!o.landed&&hostile(o.f,f));","  const airborneHostiles=(f)=>G.units.filter(o=>o.alive&&isAir(o)&&!o.landed&&hostile(o.f,f)&&sees(f,o.x,o.z));")
rep("    for(const o of G.units){if(!o.alive||!hostile(o.f,u.f)||isAir(o)||o.def.naval&&false)continue;","    for(const o of G.units){if(!o.alive||!hostile(o.f,u.f)||isAir(o)||!sees(u.f,o.x,o.z))continue;")
rep("        if(!z.plots.some(p=>p.fac&&p.fac.state==='ready')&&z.type!=='airbase')continue;","        if(!z.plots.some(p=>p.fac&&p.fac.state==='ready'&&knowsPlot(u.f,p))&&z.type!=='airbase')continue;")
rep("      const pts=best.plots.filter(p=>p.fac&&p.fac.state==='ready');let cx=0,cz=0;","      const pts=best.plots.filter(p=>p.fac&&p.fac.state==='ready'&&knowsPlot(u.f,p));let cx=0,cz=0;")
rep("    const c=F[f].comp,enemyAir=G.units.some(o=>o.alive&&o.def.plane&&hostile(o.f,f));","    const c=F[f].comp,enemyAir=G.units.some(o=>o.alive&&o.def.plane&&hostile(o.f,f)&&sees(f,o.x,o.z));")
rep("  function enemyAir(f){let n=0;for(const o of G.units)if(o.alive&&isAir(o)&&hostile(o.f,f))n++;return n;}","  function enemyAir(f){let n=0;for(const o of G.units)if(o.alive&&isAir(o)&&hostile(o.f,f)&&sees(f,o.x,o.z))n++;return n;}")
rep("      const def=z.owner!==null?z.garN+z.defN:0;","      const def=knownDefence(fac.id,z);")
rep("      query(z.x,z.z,z.r+AIB.qrfPad,u=>{if(hostile(u.f,fac.id)){threat+=","      query(z.x,z.z,z.r+AIB.qrfPad,u=>{if(hostile(u.f,fac.id)&&sees(fac.id,u.x,u.z)){threat+=")
rep("    for(const u of G.units)if(u.alive&&hostile(u.f,f)&&!isAir(u))cands.push(u);","    for(const u of G.units)if(u.alive&&hostile(u.f,f)&&!isAir(u)&&sees(f,u.x,u.z))cands.push(u);")
rep("      const pl=z.plots.filter(p=>p.fac&&p.fac.state==='ready'&&!isDefence(p.fac.type));","      const pl=z.plots.filter(p=>p.fac&&p.fac.state==='ready'&&!isDefence(p.fac.type)&&knowsPlot(f,p));")
rep("      let s=0;query(pt.x,pt.z,MSL.splash*MSL.aiAim,o=>{if(hostile(o.f,f)&&!isAir(o))s+=MW[o.def.armor]||1;});","      let s=0;query(pt.x,pt.z,MSL.splash*MSL.aiAim,o=>{if(hostile(o.f,f)&&!isAir(o)&&sees(f,o.x,o.z))s+=MW[o.def.armor]||1;});")
rep("        for(const p of z.plots)if(p.fac&&p.fac.state==='ready'&&!isDefence(p.fac.type)&&!(p.fac.downT>G.time)&&Math.hypot(p.x-pt.x,p.z-pt.z)<MSL.splash)s+=MSL.facilityValue;}",
    "        for(const p of z.plots)if(p.fac&&p.fac.state==='ready'&&!isDefence(p.fac.type)&&!(p.fac.downT>G.time)&&knowsPlot(f,p)&&Math.hypot(p.x-pt.x,p.z-pt.z)<MSL.splash)s+=MSL.facilityValue;}")
open(p,'w').write(s)
