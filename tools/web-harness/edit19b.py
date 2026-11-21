p='/home/claude/vu/v18.html';s=open(p).read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(s.count(a),a[:80]);s=s.replace(a,b)
# generation: the laid-out positions become suggested spots (the AI builds on them; the player builds anywhere)
rep("""    z.plots=[];
    for(const c of layout(z,n)){if(z.plots.length>=n)break;if(!padFits(c.x,c.z,z))continue;
      const pl={i:z.plots.length,x:c.x,z:c.z,y:0,ang:c.ang,fac:null,tag:c.tag};""","""    z.plots=[];z.budget=n;
    for(const c of layout(z,n)){if(z.plots.length>=n)break;if(!padFits(c.x,c.z,z))continue;
      const pl={i:z.plots.length,x:c.x,z:c.z,y:0,ang:c.ang,fac:null,tag:c.tag};""")
rep("""    z.slots={mil:0,eco:0,fort:0};for(const pl of z.plots)z.slots[pl.kind]++;
  }""","""    z.slots={mil:0,eco:0,fort:0};for(const pl of z.plots)z.slots[pl.kind]++;
    z.spots=z.plots;z.plots=[];   // buildings are placed freely now; these laid-out spots are suggestions (and the AI's choices)
  }""")
rep("""  for(const p of allPlots)p.y=heightAt(p.x,p.z);
""","""  for(const p of allPlots)p.y=heightAt(p.x,p.z);
  // ---- buildings: placed by Construction Rovers anywhere within range of a base ----
  const BLD=BALANCE.build;let plotSeq=1;
  const plotOf=(z,pi)=>z?z.plots.find(p=>p.i===pi)||null:null;
  function footH(x,zz){let sm=0,c=0;for(let b=0;b<TAU;b+=1.05){sm+=heightAt(x+Math.cos(b)*2.2,zz+Math.sin(b)*2.2);c++;}return Math.max(.8,sm/c);}
  function waterNear(x,zz){const wc=nearestPassCell(cellOf(x,zz),wpass);if(wc<0)return null;const w=cellCenter(wc);return Math.hypot(w.x-x,w.z-zz)<9.5?w:null;}
  function newPlot(z,x,zz,ang,type){const D=FACILITIES[type];
    const p={i:plotSeq++,x,z:zz,y:footH(x,zz),ang,kind:D.slot,fac:null,zone:z.id};
    const w=waterNear(x,zz);if(w)p.water=w;
    z.plots.push(p);return p;}
  function removePlot(z,p){const k=z.plots.indexOf(p);if(k<0)return;
    if(p.fac&&p.fac.unit&&p.fac.unit.alive){p.fac.unit.plot=null;p.fac.unit.alive=false;emit('death',p.fac.unit);}
    if(p.fac&&p.fac.state!=='building')blockArea(p.x,p.z,2.6,false);
    z.plots.splice(k,1);p.fac=null;p.gone=true;
    for(const u of G.units)if(u.job&&u.job.pi===p.i){u.job=null;u.building=false;}
    emit('facility',p,z);}
  // where a building may go: level, dry, open ground in range of the base, clear of other buildings, bases and airfields
  function siteErr(z,x,zz){
    const d=Math.hypot(x-z.x,zz-z.z);
    if(d>z.r+BLD.radius)return `Too far from ${z.name}. Build within the dashed ring.`;
    if(d<z.r+BLD.minFromCentre)return 'Too close to the base itself.';
    if(!passable(x,zz)||heightAt(x,zz)<.75)return 'Needs dry, open ground.';
    let lo=1e9,hi=-1e9;
    for(let b=0;b<TAU;b+=.785){const px=x+Math.cos(b)*2.8,pz=zz+Math.sin(b)*2.8;if(!passable(px,pz))return 'Something is in the way.';const h=heightAt(px,pz);if(h<.6)return 'Too close to the water.';lo=Math.min(lo,h);hi=Math.max(hi,h);}
    if(hi-lo>1.9)return 'The ground is too steep here.';
    for(const o of G.zones){if(o!==z&&Math.hypot(o.x-x,o.z-zz)<o.r+5)return `Too close to ${o.name}.`;
      for(const q of o.plots)if(Math.abs(q.x-x)<BLD.spacing&&Math.hypot(q.x-x,q.z-zz)<BLD.spacing)return 'Too close to another building.';}
    if(inCorr(x,zz,3))return 'Keep the airfield clear.';
    if(nearProp(x,zz))return 'Something is in the way.';
    return null;}
  // can this army put this building at this base at all (ignoring the exact spot)?
  function canPlaceType(f,zid,type){
    const z=G.zones[zid],D=FACILITIES[type];
    if(!z||z.owner!==f)return 'Build near a base you own.';if(!D)return 'Unknown building.';
    if(D.only&&!D.only.includes(z.type))return `Only at: ${D.only.map(t=>ZTYPES[t].label).join(', ')}.`;
    if(D.port&&!z.port)return 'Only Port bases can build this.';
    if(z.contested)return 'Cannot build while the base is under attack.';
    if(z.plots.length>=z.budget)return `${z.name} is full: ${z.budget} buildings.`;
    if(isDefence(type)&&atCap(f))return 'Unit cap reached. Pillboxes and AA emplacements count toward it.';
    if(F[f].money<D.cost)return `Need $${D.cost}.`;
    return null;}
  function canPlace(f,zid,type,x,zz){
    const e=canPlaceType(f,zid,type);if(e)return e;
    const z=G.zones[zid],se=siteErr(z,x,zz);if(se)return se;
    if(FACILITIES[type].coastal&&!waterNear(x,zz))return 'A Dockyard must sit at the water\\'s edge.';
    return null;}
  function place(f,zid,type,x,zz,ang,ids){
    if(!(isFinite(x)&&isFinite(zz)&&isFinite(ang)))return {ok:false,err:'Bad spot.'};
    const err=canPlace(f,zid,type,x,zz);if(err)return {ok:false,err};
    const z=G.zones[zid],D=FACILITIES[type];F[f].money-=D.cost;
    const p=newPlot(z,x,zz,ang,type);p.fac={type,level:1,state:'building',t:0,T:D.time,prodT:0,prodI:0,pstate:'idle',unit:null};
    emit('facility',p,z);assignBuilders(f,ids||[],z,p);return {ok:true,pi:p.i};}
  // send rovers to a site: they drive to its edge and work while they stand there
  function assignBuilders(f,ids,z,p){
    const rs=ids.map(id=>G.units.find(u=>u.id===id)).filter(u=>u&&u.alive&&u.f===f&&u.def.builder);
    rs.forEach((u,k)=>{u.job={zid:z.id,pi:p.i};u.building=false;
      const a=Math.atan2(u.z-p.z,u.x-p.x)+(k-(rs.length-1)/2)*.9;orderMove([u],p.x+Math.cos(a)*(BLD.reach-1.5),p.z+Math.sin(a)*(BLD.reach-1.5),false);u.job={zid:z.id,pi:p.i};});
    return rs.length;}
  function builders(p){let n=0;for(const u of G.units)if(u.alive&&u.building&&u.job&&u.job.pi===p.i)n++;return n;}
  function roverCount(f){let n=0;for(const u of G.units)if(u.alive&&u.f===f&&u.def.builder)n++;return n;}
""")
# start buildings / hangars / fortify / sabotage on spots
rep("""    ST.facilities.forEach((type,k)=>{const p=hq.plots.find(q=>!q.fac&&q.kind===FACILITIES[type].slot);if(!p)return;
      p.fac={type,level:1,state:'ready',t:0,T:1,prodT:ST.facilityFirst+k*ST.facilityStagger,prodI:0,pstate:'idle',unit:null};blockArea(p.x,p.z,2.6,true);});""",
"""    ST.facilities.forEach((type,k)=>{const s=hq.spots.find(q=>!q.used&&q.kind===FACILITIES[type].slot);if(!s)return;s.used=true;const p=newPlot(hq,s.x,s.z,s.ang,type);
      p.fac={type,level:1,state:'ready',t:0,T:1,prodT:ST.facilityFirst+k*ST.facilityStagger,prodI:0,pstate:'idle',unit:null};blockArea(p.x,p.z,2.6,true);});""")
rep("""  if(ST.airbaseHangar)for(const z of G.zones){if(z.type!=='airbase')continue;const p=z.plots.find(q=>!q.fac&&q.kind==='mil');if(!p)continue;
    p.fac=""","""  if(ST.airbaseHangar)for(const z of G.zones){if(z.type!=='airbase')continue;const s=z.spots.find(q=>!q.used&&q.kind==='mil');if(!s)continue;s.used=true;const p=newPlot(z,s.x,s.z,s.ang,'hangar');
    p.fac=""")
rep("""    for(const p of hq.plots){if(k>=want)break;if(p.fac||p.kind!=='fort')continue;
      p.fac=""","""    for(const s of hq.spots){if(k>=want)break;if(s.used||s.kind!=='fort'||hq.plots.length>=hq.budget)continue;s.used=true;const p=newPlot(hq,s.x,s.z,s.ang,k<n?'pillbox':'aa');
      p.fac=""")
rep("""      for(const p of homeOf(g).plots)if(p.fac&&p.fac.type==='depot'){blockArea(p.x,p.z,2.6,false);p.fac=null;}}}""",
    """      for(const p of homeOf(g).plots.slice())if(p.fac&&p.fac.type==='depot')removePlot(homeOf(g),p);}}""")
# capture: defences and unfinished sites are lost
rep("""    for(const p of z.plots){
      if(!p.fac)continue;
      if(isDefence(p.fac.type)||p.fac.state!=='ready'){if(p.fac.unit&&p.fac.unit.alive){p.fac.unit.alive=false;emit('death',p.fac.unit);}blockArea(p.x,p.z,2.6,false);p.fac=null;}
      else{p.fac.state='ready';p.fac.prodT=FACILITIES[p.fac.type].prod?UTYPES[FACILITIES[p.fac.type].prod.seq[0]].build*PR.afterCapture:0;}
      emit('facility',p,z);
    }""","""    for(const p of z.plots.slice()){
      if(!p.fac)continue;
      if(isDefence(p.fac.type)||p.fac.state==='building'){removePlot(z,p);continue;}
      p.fac.state='ready';p.fac.prodT=FACILITIES[p.fac.type].prod?UTYPES[FACILITIES[p.fac.type].prod.seq[0]].build*PR.afterCapture:0;
      emit('facility',p,z);
    }""")
rep("        if(u.alive&&u.f===f&&!u.def.static&&u.garrison===null&&Math.hypot(u.x-z.x,u.z-z.z)<z.r+4){",
    "        if(u.alive&&u.f===f&&!u.def.static&&!u.def.builder&&u.garrison===null&&Math.hypot(u.x-z.x,u.z-z.z)<z.r+4){")
# construction only advances while a rover works the site (upgrades need none)
rep("""        if(f.state!=='ready'){
          if(busy)continue;
          f.t+=dt;if(f.t<f.T)continue;""","""        if(f.state!=='ready'){
          if(busy)continue;
          if(f.state==='building'){const n=builders(p);f.crew=n;if(!n)continue;f.t+=dt*Math.pow(n,BLD.stack);}else f.t+=dt;
          if(f.t<f.T)continue;""")
# old pad build/upgrade/demolish look plots up by id
rep("""  function canBuild(f,zid,pi,type){
    const z=G.zones[zid],p=z&&z.plots[pi],D=FACILITIES[type];""","""  function canBuild(f,zid,pi,type){
    const z=G.zones[zid],p=plotOf(z,pi),D=FACILITIES[type];""")
rep("    const z=G.zones[zid],p=z.plots[pi],D=FACILITIES[type];\n    F[f].money-=D.cost;","    const z=G.zones[zid],p=plotOf(z,pi),D=FACILITIES[type];\n    F[f].money-=D.cost;")
rep("    const z=G.zones[zid],p=z&&z.plots[pi];\n    if(!z||z.owner!==f||!p||!p.fac)return 'Nothing to upgrade.';","    const z=G.zones[zid],p=plotOf(z,pi);\n    if(!z||z.owner!==f||!p||!p.fac)return 'Nothing to upgrade.';")
rep("    const z=G.zones[zid],p=z.plots[pi];F[f].money-=upgradeCost(p);","    const z=G.zones[zid],p=plotOf(z,pi);F[f].money-=upgradeCost(p);")
rep("""    const z=G.zones[zid],p=z&&z.plots[pi];if(!z||z.owner!==f||!p||!p.fac)return {ok:false,err:'Nothing to demolish.'};
    const refund=Math.round(FACILITIES[p.fac.type].cost*(p.fac.state==='building'?BALANCE.demolishRefund.building:BALANCE.demolishRefund.built));F[f].money+=refund;
    if(p.fac.unit&&p.fac.unit.alive){p.fac.unit.plot=null;p.fac.unit.alive=false;emit('death',p.fac.unit);}
    if(p.fac.state!=='building')blockArea(p.x,p.z,2.6,false);
    p.fac=null;emit('facility',p,z);return {ok:true,refund};""","""    const z=G.zones[zid],p=plotOf(z,pi);if(!z||z.owner!==f||!p||!p.fac)return {ok:false,err:'Nothing to demolish.'};
    const refund=Math.round(FACILITIES[p.fac.type].cost*(p.fac.state==='building'?BALANCE.demolishRefund.building:BALANCE.demolishRefund.built));F[f].money+=refund;
    removePlot(z,p);return {ok:true,refund};""")
rep("      case 'hangar':{const z=G.zones[c.zid],p=z&&z.plots[c.pi];","      case 'hangar':{const z=G.zones[c.zid],p=plotOf(z,c.pi);")
rep("      case 'build':return build(f,c.zid,c.pi,c.type);","      case 'build':return build(f,c.zid,c.pi,c.type);\n      case 'place':return place(f,c.zid,c.type,+c.x,+c.z,+c.ang,Array.isArray(c.ids)?c.ids:[]);")
# rover cap
rep("    if(atCap(f))return 'Unit cap reached.';\n    return null;\n  }\n  function recruit(","    if(atCap(f))return 'Unit cap reached.';\n    if(def.builder&&roverCount(f)>=BLD.maxRovers)return `You already have ${BLD.maxRovers} Construction Rovers.`;\n    return null;\n  }\n  function recruit(")
# orders: rovers drop their job on other orders; 'assist' sends them to a site
rep("""    if(kind==='stance'){""","""    if(kind==='assist'){const z=G.zones[a],p=plotOf(z,b);if(z&&z.owner===f&&p&&p.fac&&p.fac.state==='building')assignBuilders(f,us.map(u=>u.id),z,p);return;}
    for(const u of us)if(u.def.builder){u.job=null;u.building=false;}
    if(kind==='stance'){""")
# rover behaviour: unarmed; at its site it works, otherwise it drives
rep("""    if(d.plane){updatePlane(u,dt);return;}
    u.cd-=dt;u.acqT-=dt;""","""    if(d.plane){updatePlane(u,dt);return;}
    if(d.builder){updateRover(u,dt);return;}
    u.cd-=dt;u.acqT-=dt;""")
rep("  function separate(dt){","""  function updateRover(u,dt){
    if(u.job){const z=G.zones[u.job.zid],p=plotOf(z,u.job.pi);
      if(!p||!p.fac||p.fac.state!=='building'||z.owner!==u.f){u.job=null;u.building=false;}
      else{const d=Math.hypot(p.x-u.x,p.z-u.z);
        if(d<=BLD.reach+.5&&u.mode!=='move'){u.building=true;u.ang=angLerp(u.ang,Math.atan2(p.z-u.z,p.x-u.x),dt*4);u.ax=u.x;u.az=u.z;u.cpath=null;return;}
        u.building=false;
        if(u.mode!=='move'){const a=Math.atan2(u.z-p.z,u.x-p.x);orderMove([u],p.x+Math.cos(a)*(BLD.reach-1.5),p.z+Math.sin(a)*(BLD.reach-1.5),false);}}}
    else u.building=false;
    if(u.mode==='move'){followPath(u,dt);return;}
    if(Math.hypot(u.x-u.ax,u.z-u.az)>2.5)goToward(u,u.ax,u.az,dt,1.5);else u.cpath=null;
  }
  function separate(dt){""")
# AI never drafts rovers into attacks
rep("    return G.units.filter(u=>u.alive&&u.f===fac.id&&!u.def.static&&!u.def.guns&&u.garrison===null","    return G.units.filter(u=>u.alive&&u.f===fac.id&&!u.def.static&&!u.def.guns&&!u.def.builder&&u.garrison===null")
# AI construction: keep rovers, put idle ones on stalled sites, and place new buildings on the laid-out spots
rep("""    // construction: invest spare money into facilities
    if(fac.money>AIB.buildMoney&&rnd()<AIB.buildChance){const BW=AIB.buildWeights;
      const zs=G.zones.filter(z=>z.owner===fac.id&&!z.contested&&z.plots.some(p=>!p.fac));""","""    // construction: Construction Rovers build everything
    const myRovers=G.units.filter(u=>u.alive&&u.f===fac.id&&u.def.builder),idleR=myRovers.filter(u=>!u.job&&u.mode!=='move');
    {const hq=G.zones.find(z=>z.owner===fac.id&&z.type==='hq'&&!z.contested);
      if(hq&&myRovers.length<BLD.aiRovers&&fac.money>UTYPES.rover.cost+AIB.buildMoney*.5&&!atCap(fac.id)){fac.money-=UTYPES.rover.cost;const a=rnd()*TAU;spawnUnit('rover',fac.id,hq.x+Math.cos(a)*(hq.r+3),hq.z+Math.sin(a)*(hq.r+3));}}
    for(const u of idleR){let best=null,bd=1e9;
      for(const z of G.zones){if(z.owner!==fac.id)continue;for(const p of z.plots)if(p.fac&&p.fac.state==='building'&&!builders(p)){const d=Math.hypot(p.x-u.x,p.z-u.z);if(d<bd){bd=d;best=[z,p];}}}
      if(best){assignBuilders(fac.id,[u.id],best[0],best[1]);u.mode==='idle';}}
    const freeR=myRovers.filter(u=>!u.job);
    if(freeR.length&&fac.money>AIB.buildMoney&&rnd()<AIB.buildChance){const BW=AIB.buildWeights;
      const zs=G.zones.filter(z=>z.owner===fac.id&&!z.contested&&z.plots.length<z.budget);""")
rep("""        for(const p of z.plots){if(p.fac)continue;for(const k in W){if(!(W[k]>0)||canBuild(fac.id,z.id,p.i,k))continue;
          const w=W[k]*(FACILITIES[k].prod&&n(k)?BW.duplicate:1);opts.push([k,p,w]);tot+=w;}}
        let r=rnd()*tot;for(const [k,p,w] of opts){r-=w;if(r<=0){build(fac.id,z.id,p.i,k);break;}}""","""        for(const k in W){if(!(W[k]>0)||canPlaceType(fac.id,z.id,k))continue;
          // spots of the right kind that are still open (Dockyards on the water)
          const sp=z.spots.filter(s=>(s.kind===FACILITIES[k].slot||!z.spots.some(t=>t.kind===FACILITIES[k].slot))&&!canPlace(fac.id,z.id,k,s.x,s.z));if(!sp.length)continue;
          const w=W[k]*(FACILITIES[k].prod&&n(k)?BW.duplicate:1);opts.push([k,sp[Math.floor(rnd()*sp.length)],w]);tot+=w;}
        let r=rnd()*tot;for(const [k,sp,w] of opts){r-=w;if(r<=0){
          let ro=freeR[0],bd=1e9;for(const u of freeR){const d=Math.hypot(u.x-sp.x,u.z-sp.z);if(d<bd){bd=d;ro=u;}}
          place(fac.id,z.id,k,sp.x,sp.z,sp.ang,[ro.id]);break;}}""")
# expose
rep("Object.assign(G,{orderAs,applyCmd,stepTicks,stateHash,STEP,","Object.assign(G,{canPlace,canPlaceType,plotOf,builders,roverCount,BUILD:BLD,orderAs,applyCmd,stepTicks,stateHash,STEP,")
open(p,'w').write(s)
