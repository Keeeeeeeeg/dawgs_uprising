p='/home/claude/vu/v24.html';s=open(p).read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(s.count(a),a[:80]);s=s.replace(a,b)
# --- Base Upgrades: silo button
rep("    const z=c.z;sig='bu'+z.id+'|'+(z.drill||1)+'|'+!!z.drillUp+'|'+(G.canDrill(ME,z.id)||'')+'|'+!!z.hosp+'|'+!!z.hospUp+'|'+(G.canHosp(ME,z.id)||'');",
    "    const z=c.z;sig='bu'+z.id+'|'+(z.drill||1)+'|'+!!z.drillUp+'|'+(G.canDrill(ME,z.id)||'')+'|'+!!z.hosp+'|'+!!z.hospUp+'|'+(G.canHosp(ME,z.id)||'')+'|'+!!z.silo+'|'+!!z.siloUp+'|'+(G.canSilo(ME,z.id)||'');")
rep("      top=`<span class=\"lbl\">${z.name}</span>`;","""      if(z.type==='hq'){const err=G.canSilo(ME,z.id),M2=G.MISSILE;
        grid+=cb({attrs:'data-cmd="silo"',bar:'ubSilo',icon:'<span class="ic">☢</span>',name:z.silo?'Missile Silo':z.siloUp?'Silo…':'Missile Silo',cost:z.silo||z.siloUp?'':`$${M2.siloCost}`,dis:!!err&&!z.siloUp,pressed:!!z.silo,
          hint:`<b>Missile Silo</b> (endgame): an ICBM silo sunk into the HQ. It builds a ballistic missile every ${Math.round(M2.every/60)} minutes (up to ${M2.max}) that flattens everything in ${M2.splash} m. ${z.silo?'Built: press Q or Missile to fire.':z.siloUp?`Under construction… ${Math.floor(z.siloUp.t/z.siloUp.T*100)}%`:`$${M2.siloCost}, ${M2.siloTime} s to build.`}${err&&!z.silo&&!z.siloUp?` <span class="why">${err}</span>`:''}`});}
      top=`<span class="lbl">${z.name}</span>`;""")
rep("for(const [id,u] of [['ubDrill',c.z.drillUp],['ubHosp',c.z.hospUp]])","for(const [id,u] of [['ubDrill',c.z.drillUp],['ubHosp',c.z.hospUp],['ubSilo',c.z.siloUp]])")
rep("  else if(d.cmd==='drill'&&selZone!=null){","  else if(d.cmd==='silo'&&selZone!=null){const r=A.silo(selZone);if(!r.ok)toast(r.err);else toast('Missile Silo under construction',true);}\n  else if(d.cmd==='drill'&&selZone!=null){")
rep("  drill:zid=>act({k:'drill',zid},()=>G.canDrill(ME,zid)),","  drill:zid=>act({k:'drill',zid},()=>G.canDrill(ME,zid)),\n  silo:zid=>act({k:'silo',zid},()=>G.canSilo(ME,zid)),")
rep("$('#bMissile').onclick=()=>{if(G.missileStock(ME)<=0){const n=G.missileNext(ME);toast(n==null?'You hold no HQ to launch from.':`No missile ready. Next one in ${fmtT(n)}.`);return;}",
    "$('#bMissile').onclick=()=>{if(G.missileStock(ME)<=0){const n=G.missileNext(ME);toast(!G.hasSilo(ME)?'No Missile Silo. Build one at your HQ: select it, Base Upgrades.':n==null?'Silo full.':`No missile ready. Next one in ${fmtT(n)}.`);return;}")
rep("    $('#mslN').textContent=n;$('#mslT').textContent=nx==null?(n?'full':'—'):fmtT(nx);","    $('#mslN').textContent=n;$('#mslT').textContent=!G.hasSilo(ME)?'no silo':nx==null?(n?'full':'—'):fmtT(nx);")
# --- silo on the HQ, built into zoneDecor
rep("function zoneDecor(z){const v=zoneVis[z.id];if(!v)return;const L=z.owner===null?1:(z.drill||1),H=z.owner!==null&&!!z.hosp,key=L+'|'+H;\n  v.scaf.visible=!!(z.drillUp||z.hospUp);",
    "function zoneDecor(z){const v=zoneVis[z.id];if(!v)return;const L=z.owner===null?1:(z.drill||1),H=z.owner!==null&&!!z.hosp,SI=z.owner!==null&&!!z.silo,key=L+'|'+H+'|'+SI;\n  v.scaf.visible=!!(z.drillUp||z.hospUp||z.siloUp);")
rep("  const d=v.decor;while(d.children.length)d.remove(d.children[0]);const y=z.y,R=z.r+.9,gold=mat(0xd9ad2b,90),gate=z.gate||0;",
"""  const d=v.decor;while(d.children.length)d.remove(d.children[0]);const y=z.y,R=z.r+.9,gold=mat(0xd9ad2b,90),gate=z.gate||0;v.silo=null;
  if(SI){   // ICBM silo: a concrete collar with hazard stripes, two blast doors on hinges, a dark shaft with the missile inside
    const sp=G.siloSpot(z),q=new THREE.Group();q.position.set(sp.x-z.x,y,sp.z-z.z);d.add(q);
    add(q,new THREE.CylinderGeometry(2.3,2.6,.5,8),M.conc,0,.25,0);add(q,new THREE.CylinderGeometry(2.35,2.35,.12,8),M.hazard,0,.52,0);
    add(q,new THREE.CircleGeometry(1.6,16).rotateX(-HALF),M.dark,0,.56,0);
    const doors=[];for(const s0 of [-1,1]){const hinge=new THREE.Group();hinge.position.set(s0*1.6,.62,0);q.add(hinge);const dm=add(hinge,B(1.6,.18,3.1),M.concDark,-s0*.8,0,0);dm.userData.dynamic=true;hinge.userData.s=s0;doors.push(hinge);}
    const ms=icbmMesh();ms.position.set(0,-5,0);ms.visible=false;q.add(ms);
    for(const [ax,az] of [[2.6,1.4],[-2.6,-1.4]]){add(q,Cy(.08,2.2,6),M.metal,ax,1.1,az);add(q,new THREE.SphereGeometry(.18,8,6),mat(0xff3a2a),ax,2.25,az);}
    v.silo={q,doors,ms,anim:null};}""")
# --- ICBM model, launch animation, flight mesh
rep("function zoneDecor(z){","""// ICBM: white body, black roll bands, a sharp nose and four tail fins; built along +Y
const ICBM_GEO=(()=>{const W=hexC(0xf2f2ee),K=hexC(0x1d1f22),R=hexC(0xb8382c);
  return merge([part(Cy(.32,4.2,14),W,0,2.1,0),part(Cy(.34,.35,14),K,0,1.2,0),part(Cy(.33,.25,14),K,0,3.1,0),part(new THREE.ConeGeometry(.32,1.3,14),W,0,4.85,0),part(new THREE.ConeGeometry(.12,.35,10),R,0,5.45,0),
    part(B(.06,.9,.9),K,0,.45,.4),part(B(.06,.9,.9),K,0,.45,-.4),part(B(.9,.9,.06),K,.4,.45,0),part(B(.9,.9,.06),K,-.4,.45,0),part(Cy(.26,.3,12),K,0,-.1,0)]);})();
const icbmMat=new THREE.MeshPhongMaterial({vertexColors:true,shininess:60,specular:0x666666});
const ICBM_FLAME=new THREE.ConeGeometry(.3,2.4,10,1,true).translate(0,-1.2,0).rotateX(Math.PI);
function icbmMesh(){const g=new THREE.Group();const b=new THREE.Mesh(ICBM_GEO,icbmMat);b.castShadow=true;b.userData.dynamic=true;g.add(b);
  const fl=new THREE.Mesh(ICBM_FLAME,jetMat);fl.position.y=-.2;fl.userData.dynamic=true;fl.visible=false;g.add(fl);g.userData.flame=fl;g.userData.dynamic=true;return g;}
const launches=[],flights=new Map();
// launch: doors swing open, steam bursts out, the missile rises out of the shaft slowly, then the flight takes over
function startLaunch(hq,p){const v=zoneVis[hq.id];if(!v||!v.silo)return;launches.push({v,hq,p,t:0});}
function updateLaunches(dt){
  for(let i=launches.length-1;i>=0;i--){const L=launches[i],S=L.v.silo,hq=L.hq,D=G.MISSILE.launchDelay;L.t+=dt;if(!S){launches.splice(i,1);continue;}
    const open=Math.min(1,L.t/1.1),close=L.t>D+2.5?Math.min(1,(L.t-D-2.5)/1.5):0,ang=1.95*(open-close);
    for(const h of S.doors)h.rotation.z=-h.userData.s*ang;
    const wp=new THREE.Vector3();S.q.getWorldPosition(wp);
    if(L.t>.5&&L.t<D+.6&&Math.random()<dt*14)fx(wp.x+(Math.random()-.5)*2.6,wp.y+.8+Math.random()*1.5,wp.z+(Math.random()-.5)*2.6,0xf2f4f6,2.2+Math.random()*1.6,1.6+Math.random(),false);   // steam
    const ms=S.ms;
    if(L.t>1&&L.t<D){ms.visible=true;const k=(L.t-1)/(D-1);ms.position.y=-5+k*k*7;ms.userData.flame.visible=k>.55;if(k>.55&&Math.random()<dt*20)fx(wp.x,wp.y+.4,wp.z,0xffc070,1.4,.35,true);}
    else ms.visible=false;
    if(L.t>D+4.2){for(const h of S.doors)h.rotation.z=0;launches.splice(i,1);}}}
// the missile in flight: slow off the pad, building speed along its arc
function missilePos(p){const k0=Math.max(0,Math.min(1,p.t/p.T)),k=Math.pow(k0,1.55),d=Math.hypot(p.ex-p.sx,p.ez-p.sz),arc=Math.max(45,d*.55);
  return {k,x:p.sx+(p.ex-p.sx)*k,y:p.sy+(p.ey-p.sy)*k+Math.sin(k*Math.PI)*arc,z:p.sz+(p.ez-p.sz)*k};}
const _up=new THREE.Vector3(0,1,0),_dir=new THREE.Vector3();
function updateFlights(){const live=new Set();
  for(const p of G.projectiles){if(p.wpn!=='missile'||p.t<0)continue;live.add(p);
    if(p.f!==ME&&!G.visibleToPlayer(p.sx,p.sz)&&!G.visibleToPlayer(p.ex,p.ez)){const m=flights.get(p);if(m)m.visible=false;continue;}
    let m=flights.get(p);if(!m){m=icbmMesh();m.userData.flame.visible=true;scene.add(m);flights.set(p,m);}m.visible=true;
    const a=missilePos(p),b=missilePos({...p,t:Math.min(p.T,p.t+.05)});_dir.set(b.x-a.x,b.y-a.y,b.z-a.z);if(_dir.lengthSq()<1e-6)_dir.set(0,1,0);_dir.normalize();
    m.position.set(a.x,a.y,a.z);m.quaternion.setFromUnitVectors(_up,_dir);m.scale.setScalar(1.15);m.userData.flame.scale.set(1,1+Math.random()*.5,1);}
  for(const [p,m] of flights)if(!live.has(p)){scene.remove(m);flights.delete(p);}}
function zoneDecor(z){""")
# tracer loop: missiles use the flight path (and nothing before launch)
rep("    const k=Math.min(1,p.t/p.T);const x=p.sx+(p.ex-p.sx)*k,z=p.sz+(p.ez-p.sz)*k;","    if(p.t<0)continue;   // still on the pad\n    const k=p.wpn==='missile'?missilePos(p).k:Math.min(1,p.t/p.T);const x=p.sx+(p.ex-p.sx)*k,z=p.sz+(p.ez-p.sz)*k;")
rep("  G.on('missile',(p,hq)=>{fx(hq.x,hq.y+2,hq.z,0xfff0c0,4,.5,true);fx(hq.x,hq.y+3,hq.z,0x8a8680,5,3,false);","  G.on('missile',(p,hq)=>{startLaunch(hq,p);")
rep("  syncScene(dt);upgradeFX(planning?0:dt);","  syncScene(dt);updateLaunches(dt);updateFlights();upgradeFX(planning?0:dt);")
rep("    if(z.drillUp||z.hospUp){zoneDecor(z);","    if(z.drillUp||z.hospUp||z.siloUp){zoneDecor(z);")
open(p,'w').write(s)
