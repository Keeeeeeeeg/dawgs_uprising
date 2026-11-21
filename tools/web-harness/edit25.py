p='/home/claude/vu/v21.html';s=open(p).read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(s.count(a),a[:80]);s=s.replace(a,b)
rep("  return {g,ringMat,beaconMat,capMat,flag};","""  const decor=new THREE.Group();g.add(decor);const scaf=new THREE.Group();scaf.visible=false;g.add(scaf);
  // scaffolding around the ring while a Garrison Drill upgrade goes in
  for(let k=0;k<6;k++){const a=k/6*6.283+.3,x=Math.cos(a)*(z.r+1.6),zz=Math.sin(a)*(z.r+1.6),q=new THREE.Group();q.position.set(x,y,zz);q.rotation.y=-a;scaf.add(q);
    for(const [dx,dz] of [[-.8,-.8],[.8,-.8],[-.8,.8],[.8,.8]])add(q,Cy(.06,3.2,5),M.yellow,dx,1.6,dz);
    for(const h of [1.1,2.3])add(q,B(1.8,.1,1.8),M.wood,0,h,0);}
  return {g,ringMat,beaconMat,capMat,flag,decor,scaf,lvl:1};""")
rep("function buildZone(z){","""// Garrison Drill levels dress a base up: II adds banner poles and floodlights round the ring, III gate arches and gilded finials
function zoneDecor(z){const v=zoneVis[z.id];if(!v)return;const L=z.owner===null?1:(z.drill||1);v.scaf.visible=!!z.drillUp;if(v.lvl===L)return;v.lvl=L;
  const d=v.decor;while(d.children.length)d.remove(d.children[0]);if(L<2)return;const y=z.y,R=z.r+.9,gold=mat(0xd9ad2b,90);
  for(let k=0;k<4;k++){const a=k/4*6.283+.785+(z.gate||0),x=Math.cos(a)*R,zz=Math.sin(a)*R;
    add(d,Cy(.07,4.2,6),M.metal,x,y+2.1,zz);add(d,B(.05,1.5,.9),v.beaconMat,x,y+3.3,zz+.45,0,-a,0);
    const b=a+.39,bx=Math.cos(b)*R,bz=Math.sin(b)*R;add(d,Cy(.1,3.4,6),M.dark,bx,y+1.7,bz);add(d,B(.5,.3,.3),M.metal,bx,y+3.4,bz,0,-b,0);add(d,B(.42,.22,.05),M.glass,bx-Math.cos(b)*.17,y+3.4,bz-Math.sin(b)*.17,0,-b,0);}
  if(L>=3)for(let k=0;k<2;k++){const a=k*Math.PI+(z.gate||0),x=Math.cos(a)*(z.r+.4),zz=Math.sin(a)*(z.r+.4),q=new THREE.Group();q.position.set(x,y,zz);q.rotation.y=-a;d.add(q);
    for(const s of [-1.6,1.6]){add(q,B(.8,3.6,.8),M.conc,0,1.8,s);add(q,new THREE.ConeGeometry(.35,.7,8),gold,0,3.95,s);}
    add(q,B(.9,.7,4),M.conc,0,3.5,0);add(q,B(.06,.5,1.6),v.beaconMat,.48,3.5,0);}}
function buildZone(z){""")
rep("G.zones.forEach(z=>zoneVis[z.id]=buildZone(z));","G.zones.forEach(z=>{zoneVis[z.id]=buildZone(z);zoneDecor(z);});")
rep("  G.on('zone',(z,old,f)=>{paintZones();","  G.on('zoneup',z=>{zoneDecor(z);cardSig='';selSig='';});\n  G.on('zone',(z,old,f)=>{paintZones();zoneDecor(z);")
# construction sparks: drill upgrades and building upgrades
rep("  syncScene(dt);updateFX(dt);","  syncScene(dt);upgradeFX(planning?0:dt);updateFX(dt);")
rep("function rebuildAllPlots(){G.zones.forEach(buildPlotVis);}","""function rebuildAllPlots(){G.zones.forEach(buildPlotVis);}
// sparks and dust over anything being upgraded (that you can see)
function upgradeFX(dt){if(!dt)return;
  for(const z of G.zones){if(z.owner===null||!(z.owner===ME||G.visibleToPlayer(z.x,z.z)))continue;
    if(z.drillUp){zoneDecor(z);if(Math.random()<dt*6){const a=Math.random()*6.283;fx(z.x+Math.cos(a)*(z.r+1.6),z.y+1+Math.random()*2,z.z+Math.sin(a)*(z.r+1.6),Math.random()<.6?0xffd060:0xfff2c0,.2,.35,true);}
      if(Math.random()<dt*1.5)fx(z.x+(Math.random()-.5)*z.r,z.y+.6,z.z+(Math.random()-.5)*z.r,0x9a968e,1.1,1.6,false);}
    else if(zoneVis[z.id]&&zoneVis[z.id].scaf.visible)zoneDecor(z);
    for(const p of z.plots){const f=p.fac;if(!f||f.state!=='upgrading')continue;
      if(Math.random()<dt*5)fx(p.x+(Math.random()-.5)*3.6,p.y+.5+Math.random()*3,p.z+(Math.random()-.5)*3.6,Math.random()<.6?0xffd060:0xfff2c0,.18,.35,true);
      if(Math.random()<dt*1.2)fx(p.x,p.y+3.6,p.z,0x8a8680,.8,1.4,false);}}}""")
# HUD: base tab drill button, garrison line
rep("""      hint='Right-click the ground to set this base\\'s rally point.';
    }
  }""","""      {const L=z.drill||1,err=G.canDrill(ME,z.id);
        grid+=cb({attrs:'data-cmd="drill"',icon:CI.up,name:z.drillUp?'Drilling…':L>=3?'Drill III':`Drill ${L===1?'II':'III'}`,cost:L<3&&!z.drillUp?`$${G.drillCost(z)}`:'',dis:!!err,
          hint:`<b>Garrison Drill</b>: replace fallen garrison troops faster${L<3?` (level ${L+1} of 3)`:' (maxed)'} and dress the base up.${err&&L<3?` <span class="why">${err}</span>`:''}`});}
      hint='Right-click the ground to set this base\\'s rally point.';
    }
  }""")
rep("    const z=c.z;sig='bs'+z.id+'|'+!!z.rally;","    const z=c.z;sig='bs'+z.id+'|'+!!z.rally+'|'+(z.drill||1)+'|'+!!z.drillUp+'|'+(G.canDrill(ME,z.id)||'');")
rep("  else if(d.cmd==='zoom'&&selZone!=null)zoomBase(selZone);","  else if(d.cmd==='zoom'&&selZone!=null)zoomBase(selZone);\n  else if(d.cmd==='drill'&&selZone!=null){const r=A.drill(selZone);if(!r.ok)toast(r.err);else toast('Garrison Drill under way',true);}")
rep("  ping:(x,z)=>act({k:'ping',x,z}),","  ping:(x,z)=>act({k:'ping',x,z}),\n  drill:zid=>act({k:'drill',zid},()=>G.canDrill(ME,zid)),")
rep("      body+=`<div class=\"zrow\"><span>Field ${field}/${P.cap} · ${st}.","      {let made=0;for(const u of G.units)if(u.alive&&u.zoneMade===z.id)made++;\n      body+=`<div class=\"zrow\"><span>Garrison troops ${made}/${ZT.garrison} · Drill ${['I','II','III'][(z.drill||1)-1]}${z.drillUp?` (upgrading ${Math.floor(z.drillUp.t/z.drillUp.T*100)}%)`:''} · ${st}.")
open(p,'w').write(s)
