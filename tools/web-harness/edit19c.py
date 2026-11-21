p='/home/claude/vu/v18.html';s=open(p).read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(s.count(a),a[:80]);s=s.replace(a,b)
# ---------- rover model ----------
rep("  }else if(type==='tech'){","""  }else if(type==='rover'){
    // construction rover: six-wheel chassis in team colour with hazard-yellow bumpers; the crane arm is a separate mesh
    const Y=hexC(0xd9ad2b);
    p.push(part(B(3.4,.5,1.6),D,0,.65,0),part(B(1.1,.9,1.5),T,1.1,1.25,0),part(B(.08,.45,1.3),L,1.66,1.38,0),part(B(1.9,.35,1.55),T,-.55,1.05,0),
      part(B(.25,.3,1.7),Y,1.78,.6,0),part(B(.25,.3,1.7),Y,-1.78,.6,0),part(B(.5,.18,.5),Y,-1.3,1.28,.5),part(Cy(.12,.25,8),hexC(0xff8a20),1.1,1.82,.45));
    for(const x of [-1.15,0,1.15])for(const zz of [.82,-.82])p.push(part(Cy(.36,.3,12),D,x,.36,zz,HALF));
  }else if(type==='tech'){""")
rep("  }else if(u.type==='heli'){","""  }else if(u.type==='rover'){
    m=new THREE.Group();const body=new THREE.Mesh(UGEO.rover[u.f],unitMat);body.castShadow=true;m.add(body);
    const arm=new THREE.Group();arm.position.set(-.6,1.25,0);m.add(arm);const boom=new THREE.Group();boom.position.y=.35;arm.add(boom);
    const am=new THREE.Mesh(ROVER_ARM.base,unitMat);arm.add(am);const bm=new THREE.Mesh(ROVER_ARM.boom,unitMat);bm.castShadow=true;boom.add(bm);
    boom.rotation.z=.45;m.userData.arm=arm;m.userData.boom=boom;m.scale.setScalar(VSCALE.rover||1);
  }else if(u.type==='heli'){""")
rep("const VSCALE={rifle:.7,","const VSCALE={rover:.95,rifle:.7,")
rep("const UGEO={};for(const t in UTYPES){","""// rover crane: a turntable and a lattice boom with a hook (rotates and dips while building)
const ROVER_ARM=(()=>{const Y=hexC(0xd9ad2b),K=hexC(0x2e3032);
  return {base:merge([part(Cy(.4,.35,10),K,0,0,0)]),boom:merge([part(B(2.6,.22,.22),Y,1.2,0,0),part(B(.12,.12,.9),K,2.45,-.45,0),part(B(.3,.2,.3),K,2.45,-.95,0)])};})();
const UGEO={};for(const t in UTYPES){""")
# rover animation
rep("""    else{m.position.set(u.x,G.heightAt(u.x,u.z),u.z);m.rotation.y=-u.ang;
      if(m.userData.legs){""","""    else{m.position.set(u.x,G.heightAt(u.x,u.z),u.z);m.rotation.y=-u.ang;
      if(m.userData.arm){const a=m.userData.arm,b=m.userData.boom;
        if(u.building){a.rotation.y=Math.sin(now*1.3+u.id)*.7;b.rotation.z=.25+Math.sin(now*2.1+u.id)*.2;
          if(u.job&&Math.random()<dt*7){const z=G.zones[u.job.zid],p=G.plotOf(z,u.job.pi);if(p)fx(p.x+(Math.random()-.5)*3,p.y+.6+Math.random()*2.2,p.z+(Math.random()-.5)*3,Math.random()<.5?0xffd060:0xfff2c0,.18,.35,true);}
          if(Math.random()<dt*1.2)fx(u.x,G.heightAt(u.x,u.z)+1.9,u.z,0x8a8680,.5,1.4,false);}
        else{a.rotation.y*=Math.max(0,1-dt*3);b.rotation.z+=(.45-b.rotation.z)*Math.min(1,dt*3);}}
      if(m.userData.legs){""")
rep("const PLURAL={airship:'Heavy Airships',","const PLURAL={rover:'Construction Rovers',airship:'Heavy Airships',")
rep("Object.assign(ICONS,{\n","Object.assign(ICONS,{\n  rover:'<svg viewBox=\"0 0 22 14\"><path d=\"M2 7h13V4h4l2 3v3H2z M6 6l7-5 1 1-6 5z\" fill=\"currentColor\"/><circle cx=\"5\" cy=\"11\" r=\"2\" fill=\"currentColor\"/><circle cx=\"11\" cy=\"11\" r=\"2\" fill=\"currentColor\"/><circle cx=\"17\" cy=\"11\" r=\"2\" fill=\"currentColor\"/></svg>',\n")
# ---------- building visuals: foundation always, removed buildings cleaned up ----------
rep("const plateGeo=(()=>{const C1=hexC(0x9c988c),C2=hexC(0xd9ad2b),p=[part(B(4.8,.22,4.8),C1,0,.11,0)];",
    "const plateGeo=(()=>{const C1=hexC(0x9c988c),C2=hexC(0xd9ad2b),p=[part(B(4.8,.22,4.8),C1,0,.11,0),part(B(4.6,1.8,4.6),hexC(0x7d7a70),0,-.9,0)];")
rep("""function refreshPlotVis(z,p){
  const v=plotVis[z.id][p.i];""","""function refreshPlotVis(z,p){
  plotVis[z.id]=plotVis[z.id]||[];
  if(p.gone){const v=plotVis[z.id][p.i];if(v){for(const k of ['fac','scaf','plate','hi'])if(v[k])scene.remove(v[k]);delete plotVis[z.id][p.i];}return;}
  if(!plotVis[z.id][p.i]){buildPlotVis(z);return;}
  const v=plotVis[z.id][p.i];""")
rep("  const f=p.fac;v.plate.visible=!f||f.state==='building';","  const f=p.fac;v.plate.visible=true;")
# ---------- placement hologram ----------
rep("function rebuildAllPlots(){G.zones.forEach(buildPlotVis);}","""function rebuildAllPlots(){G.zones.forEach(buildPlotVis);}
// ---------- construction: choose a building, move its hologram, wheel to turn it, click to place ----------
let placing=null;   // {type,zid,ang,x,z,err,ids}
const holoOK=new THREE.MeshBasicMaterial({color:0x7cff7a,transparent:true,opacity:.42,depthWrite:false}),holoBad=new THREE.MeshBasicMaterial({color:0xff5a40,transparent:true,opacity:.42,depthWrite:false});
let holo=null;
const buildRing=new THREE.Mesh(new THREE.RingGeometry(.985,1,96).rotateX(-HALF),new THREE.MeshBasicMaterial({color:0xf2c230,transparent:true,opacity:.55,depthWrite:false,side:THREE.DoubleSide}));
buildRing.visible=false;scene.add(buildRing);
function buildRadius(z){return z.r+G.BUILD.radius;}
function showBuildRing(z){if(!z){buildRing.visible=false;return;}const R=buildRadius(z);buildRing.visible=true;buildRing.scale.set(R,1,R);buildRing.position.set(z.x,z.y+.4,z.z);}
function startPlacing(type,zid){
  const ids=selUnits().filter(u=>u.def.builder).map(u=>u.id);if(!ids.length){toast('Select a Construction Rover first.');return;}
  if(holo){scene.remove(holo);holo=null;}
  holo=facMesh(type,1,holoOK);holo.scale.setScalar(STRUCT_SCALE);holo.traverse(o=>{if(o.isMesh){o.material=holoOK;o.castShadow=false;o.receiveShadow=false;}});
  const plate=new THREE.Mesh(B(4.8,.22,4.8),holoOK);plate.position.y=.11;holo.add(plate);scene.add(holo);
  placing={type,zid,ang:placing&&placing.type===type?placing.ang:Math.atan2(cam.z-G.zones[zid].z,cam.x-G.zones[zid].x),x:0,z:0,err:'',ids};setArm('place');updatePlacing();}
function stopPlacing(){if(holo){scene.remove(holo);holo=null;}placing=null;if(armed==='place')setArm(null);}
function updatePlacing(){
  if(!placing||!holo)return;const z=G.zones[placing.zid];
  if(!z||z.owner!==ME){stopPlacing();return;}
  const g=groundAt(mouse.x,mouse.y,true);if(!g){holo.visible=false;return;}holo.visible=true;
  placing.x=g.x;placing.z=g.z;
  let err=G.canPlace(ME,z.id,placing.type,g.x,g.z);
  if(!err&&nearTransit(g.x,g.z))err='Keep the road or railway clear.';
  placing.err=err||'';const mt=err?holoBad:holoOK;holo.traverse(o=>{if(o.isMesh)o.material=mt;});
  holo.position.set(g.x,G.heightAt(g.x,g.z)+.05,g.z);holo.rotation.y=-placing.ang-HALF;showBuildRing(z);
  const t=$('#modeTag');t.textContent=`${FAC[placing.type].name.toUpperCase()} · ${err?err:'click to build'} · wheel turns it · right-click cancels`;t.style.color=t.style.borderColor=err?'#ff6a50':'#9be06a';}
function confirmPlacing(keep){
  if(!placing)return;updatePlacing();if(placing.err){toast(placing.err);return;}
  const ids=selUnits().filter(u=>u.def.builder).map(u=>u.id);
  const r=A.place(placing.zid,placing.type,placing.x,placing.z,placing.ang,ids.length?ids:placing.ids);
  if(!r.ok){toast(r.err);return;}
  marker(placing.x,placing.z,0xf2c230,1.2);toast(`${FAC[placing.type].name}: site marked. ${ids.length>1?'The rovers are':'The rover is'} on the way.`,true);
  if(!keep)stopPlacing();else updatePlacing();cardSig='';refreshSel();}
// the base a group of rovers works for: the one they are inside the construction ring of, else the nearest you own
function roverBase(us){const own=G.zones.filter(z=>z.owner===ME);if(!own.length)return null;
  const cx=us.reduce((a,u)=>a+u.x,0)/us.length,cz=us.reduce((a,u)=>a+u.z,0)/us.length;
  return own.slice().sort((a,b)=>Math.hypot(a.x-cx,a.z-cz)-a.r-Math.hypot(b.x-cx,b.z-cz)+b.r)[0];}
let roverZone=null;""")
# A.place
rep("  hangar:(zid,pi,mode)=>act({k:'hangar',zid,pi,mode}),","  hangar:(zid,pi,mode)=>act({k:'hangar',zid,pi,mode}),\n  place:(zid,type,x,z,ang,ids)=>act({k:'place',zid,type,x,z,ang,ids:[...ids]},()=>G.canPlace(ME,zid,type,x,z)),")
rep("  if(c.k==='order')tutEv[c.kind]=true;\n  if(!NET){const r=G.applyCmd(ME,c)||{ok:true};if(r.ok&&c.k==='build')tutEv.build=true;",
    "  if(c.k==='order')tutEv[c.kind]=true;\n  if(!NET){const r=G.applyCmd(ME,c)||{ok:true};if(r.ok&&(c.k==='build'||c.k==='place'))tutEv.build=true;")
# input: place mode, wheel rotation, right-click cancels; right-click a site sends rovers to help
rep("  if(armed&&!d.on){const g=groundAt(e.clientX,e.clientY,true);if(g)doArmed(g,e.shiftKey);return;}",
    "  if(armed==='place'&&!d.on){confirmPlacing(e.shiftKey);return;}\n  if(armed&&!d.on){const g=groundAt(e.clientX,e.clientY,true);if(g)doArmed(g,e.shiftKey);return;}")
rep("  if(armed){const g=groundAt(e.clientX,e.clientY,true);if(g)doArmed(g,e.shiftKey);return;}\n  const fight=r.fight||fightArmed;",
    "  if(armed==='place'){stopPlacing();return;}\n  if(armed){const g=groundAt(e.clientX,e.clientY,true);if(g)doArmed(g,e.shiftKey);return;}\n  const fight=r.fight||fightArmed;")
rep("""  const g=groundAt(sx,sy,true);if(!g)return;
  planeOrder(planes,null,g);if(!us.length){marker(g.x,g.z,0x9fd6ff);return;}""","""  const g=groundAt(sx,sy,true);if(!g)return;
  // rovers right-clicked onto one of your unfinished buildings go and help build it
  const rov=us.filter(u=>u.def.builder);
  if(rov.length){for(const z of G.zones){if(z.owner!==ME)continue;const p=z.plots.find(p=>p.fac&&p.fac.state==='building'&&Math.hypot(p.x-g.x,p.z-g.z)<4);
    if(p){A.order('assist',rov.map(u=>u.id),z.id,p.i);marker(p.x,p.z,0xf2c230,1.2);const rest=us.filter(u=>!u.def.builder);if(rest.length)A.order(fight?'amove':'move',rest.map(u=>u.id),g.x,g.z);return;}}}
  planeOrder(planes,null,g);if(!us.length){marker(g.x,g.z,0x9fd6ff);return;}""")
rep("ov.addEventListener('wheel',e=>{\n  e.preventDefault();camGoal=null;","ov.addEventListener('wheel',e=>{\n  e.preventDefault();\n  if(placing){placing.ang+=Math.sign(e.deltaY)*Math.PI/12;updatePlacing();return;}\n  camGoal=null;")
rep("  if(drag){drag.x1=e.clientX;drag.y1=e.clientY;","  if(placing)updatePlacing();\n  if(drag){drag.x1=e.clientX;drag.y1=e.clientY;")
rep("function setArm(m){armed=m;if(m)fightArmed=false;tagMode();}","function setArm(m){if(m!=='place'&&armed==='place'&&holo){scene.remove(holo);holo=null;placing=null;}armed=m;if(m)fightArmed=false;tagMode();if(m==='place')updatePlacing();}")
rep("  else if(city&&!e.shiftKey&&/^Digit[1-9]$/.test(e.code)){const i=+e.code.slice(5)-1;if(i<G.zones[city.zid].plots.length){city.sel=i;cardTab='build';selSig=cardSig='';refreshSel();}}\n","")
# frame: keep the hologram under the cursor as the camera moves
rep("  if(TRAFFIC.run)TRAFFIC.run(","  if(placing)updatePlacing();else if(!roverZone)buildRing.visible=false;\n  if(TRAFFIC.run)TRAFFIC.run(")
open(p,'w').write(s)
