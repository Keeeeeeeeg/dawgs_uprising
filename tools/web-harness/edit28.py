p='/home/claude/vu/v22.html';s=open(p).read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(s.count(a),a[:80]);s=s.replace(a,b)
rep("const UGEO={};for(const t in UTYPES){","const UGEO={};for(const t in UTYPES){if(UTYPES[t].struct)continue;")
rep("function makeUnitMesh(u){\n  let m;\n  if(u.def.plane){","function makeUnitMesh(u){\n  let m;\n  if(u.def.struct){m=new THREE.Group();scene.add(m);meshes.set(u.id,m);return m;}   // a building's body: drawn by the building itself\n  if(u.def.plane){")
rep("  G.on('death',u=>{\n","  G.on('death',u=>{\n    if(u.def.struct){meshes.delete(u.id);selected.delete(u.id);return;}   // the building's collapse is drawn by the facility handler\n")
rep("    const p=proj(u.x,G.unitY(u)+(ship?4.2:u.def.air?2:u.def.isVeh||u.def.naval?2.8:2.3),u.z);if(!p.ok)continue;",
    "    const p=proj(u.x,G.unitY(u)+(ship?4.2:u.def.struct?3.6:u.def.air?2:u.def.isVeh||u.def.naval?2.8:2.3),u.z);if(!p.ok)continue;")
rep("  for(const u of G.units){if(!u.alive||!shown(u))continue;mctx.fillStyle=","  for(const u of G.units){if(!u.alive||u.def.struct||!shown(u))continue;mctx.fillStyle=")
# collapse instead of vanishing
rep("  if(p.gone){const v=plotVis[z.id][p.i];if(v){for(const k of ['fac','scaf','plate','hi'])if(v[k])scene.remove(v[k]);delete plotVis[z.id][p.i];}return;}",
    "  if(p.gone){const v=plotVis[z.id][p.i];if(v){const seen=z.owner===ME||G.visibleToPlayer(p.x,p.z);\n      if(p.destroyed&&seen){collapse(v.fac||v.scaf,p.x,p.y,p.z);for(const k of ['plate','hi'])if(v[k])scene.remove(v[k]);}else for(const k of ['fac','scaf','plate','hi'])if(v[k])scene.remove(v[k]);\n      delete plotVis[z.id][p.i];}return;}")
rep("function rebuildAllPlots(){G.zones.forEach(buildPlotVis);}","""function rebuildAllPlots(){G.zones.forEach(buildPlotVis);}
// ---- building destruction: the structure lurches, slumps and sinks while chunks fly off, bounce and settle, then fade into the ground ----
const debris=[],slumping=[],DEB_GEO=new THREE.BoxGeometry(1,1,1),DEB_MATS=()=>[M.conc,M.concDark,M.house,M.rust,M.wood,M.corr];
function collapse(obj,x,y,z){
  if(obj)slumping.push({o:obj,t:0,ax:Math.random()<.5?'x':'z',dir:Math.random()<.5?-1:1});
  const mats=DEB_MATS();
  for(let k=0;k<16;k++){const s0=.25+Math.random()*.9,m=new THREE.Mesh(DEB_GEO,mats[k%mats.length]);m.scale.set(s0*(.6+Math.random()*.8),s0*(.5+Math.random()*.6),s0*(.6+Math.random()*.8));
    m.position.set(x+(Math.random()-.5)*2.4,y+.8+Math.random()*2.4,z+(Math.random()-.5)*2.4);m.castShadow=true;scene.add(m);
    const a=Math.random()*6.283,sp=2+Math.random()*6;
    debris.push({m,v:new THREE.Vector3(Math.cos(a)*sp,4+Math.random()*7,Math.sin(a)*sp),w:new THREE.Vector3((Math.random()-.5)*9,(Math.random()-.5)*9,(Math.random()-.5)*9),t:0,h:m.scale.y/2});}
  fx(x,y+1.6,z,0xffa040,4.5,.8,true);fx(x,y+2.2,z,0xffd27a,2.5,.5,true);for(let k=0;k<4;k++)fx(x+(Math.random()-.5)*3,y+1+k*.6,z+(Math.random()-.5)*3,0x4a4640,4+k,2.4+k*.4,false);}
function updateDebris(dt){if(!dt)return;
  for(let i=debris.length-1;i>=0;i--){const d=debris[i],m=d.m;d.t+=dt;
    if(d.t<7){d.v.y-=20*dt;m.position.addScaledVector(d.v,dt);m.rotation.x+=d.w.x*dt;m.rotation.y+=d.w.y*dt;m.rotation.z+=d.w.z*dt;
      const g=G.heightAt(m.position.x,m.position.z)+d.h;if(m.position.y<g){m.position.y=g;if(d.v.y<0)d.v.y*=-.32;d.v.x*=.55;d.v.z*=.55;d.w.multiplyScalar(.5);if(Math.abs(d.v.y)<.6){d.v.y=0;d.w.multiplyScalar(.2);}}}
    else m.position.y-=dt*.35;
    if(d.t>11){scene.remove(m);debris.splice(i,1);}}
  for(let i=slumping.length-1;i>=0;i--){const s0=slumping[i],o=s0.o;s0.t+=dt;
    o.rotation[s0.ax]+=s0.dir*dt*.55*Math.min(1,s0.t*2);o.position.y-=dt*(.6+s0.t*2.2);o.scale.y=Math.max(.05,o.scale.y*(1-dt*1.1));
    if(Math.random()<dt*8)fx(o.position.x+(Math.random()-.5)*3,o.position.y+1,o.position.z+(Math.random()-.5)*3,0x5a5650,2,1.6,false);
    if(s0.t>1.6){scene.remove(o);slumping.splice(i,1);}}}""")
rep("  syncScene(dt);upgradeFX(planning?0:dt);","  syncScene(dt);upgradeFX(planning?0:dt);updateDebris(dt);")
rep("    'Fixed: the Interface size slider","    'Every building can now be targeted and destroyed. When one falls it lurches and slumps into the ground while chunks of concrete and timber fly off, bounce and settle. Bigger and upgraded buildings take more punishment; units only shoot buildings when nothing that fights back is near.',\n    'Fixed: the Interface size slider")
open(p,'w').write(s)
