p='/home/claude/vu/v23.html';s=open(p).read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(s.count(a),a[:80]);s=s.replace(a,b)
i=s.index("function zoneDecor(z){");j=s.index("function buildZone(z){")
s=s[:i]+r"""// Base upgrades show on the base. Garrison Drill II rings it with sandbag walls, two bunkers, banner poles and floodlights;
// Drill III adds concrete bastions with gun slits, tank-trap hedgehogs and gate arches with gilded finials.
// A Field Hospital pitches red-cross tents with a landing cross beside them. While either goes in, scaffolding and sparks.
const RED=new THREE.MeshPhongMaterial({color:0xc0392b,shininess:20}),TENT=new THREE.MeshLambertMaterial({color:0xe9e6dc});
function zoneDecor(z){const v=zoneVis[z.id];if(!v)return;const L=z.owner===null?1:(z.drill||1),H=z.owner!==null&&!!z.hosp,key=L+'|'+H;
  v.scaf.visible=!!(z.drillUp||z.hospUp);if(v.lvl===key)return;v.lvl=key;
  const d=v.decor;while(d.children.length)d.remove(d.children[0]);const y=z.y,R=z.r+.9,gold=mat(0xd9ad2b,90),gate=z.gate||0;
  if(L>=2){
    for(let k=0;k<4;k++){const a=k/4*6.283+.785+gate,x=Math.cos(a)*R,zz=Math.sin(a)*R;
      add(d,Cy(.07,4.2,6),M.metal,x,y+2.1,zz);add(d,B(.05,1.5,.9),v.beaconMat,x,y+3.3,zz+.45,0,-a,0);
      const b=a+.39,bx=Math.cos(b)*R,bz=Math.sin(b)*R;add(d,Cy(.1,3.4,6),M.dark,bx,y+1.7,bz);add(d,B(.5,.3,.3),M.metal,bx,y+3.4,bz,0,-b,0);add(d,B(.42,.22,.05),M.glass,bx-Math.cos(b)*.17,y+3.4,bz-Math.sin(b)*.17,0,-b,0);
      // sandbag breastworks curving round the outside of the ring
      const a0=a-.28,a1=a+.2,RR=z.r+3.2;sandbagLine(d,Math.cos(a0)*RR,Math.sin(a0)*RR,Math.cos(a1)*RR,Math.sin(a1)*RR,y);}
    for(const a of [gate+1.9,gate-1.9]){const x=Math.cos(a)*(z.r+4.4),zz=Math.sin(a)*(z.r+4.4);   // two squat bunkers
      add(d,new THREE.CylinderGeometry(1.2,1.5,1.1,8),M.conc,x,y+.55,zz);add(d,new THREE.CylinderGeometry(1.35,1.35,.2,8),M.concDark,x,y+1.2,zz);add(d,B(.9,.18,.12),M.dark,x+Math.cos(a)*1.2,y+.75,zz+Math.sin(a)*1.2,0,-a+HALF,0);}}
  if(L>=3){
    for(let k=0;k<2;k++){const a=k*Math.PI+gate,x=Math.cos(a)*(z.r+.4),zz=Math.sin(a)*(z.r+.4),q=new THREE.Group();q.position.set(x,y,zz);q.rotation.y=-a;d.add(q);
      for(const s0 of [-1.6,1.6]){add(q,B(.8,3.6,.8),M.conc,0,1.8,s0);add(q,new THREE.ConeGeometry(.35,.7,8),gold,0,3.95,s0);}
      add(q,B(.9,.7,4),M.conc,0,3.5,0);add(q,B(.06,.5,1.6),v.beaconMat,.48,3.5,0);}
    for(let k=0;k<4;k++){const a=k/4*6.283+gate+.4,x=Math.cos(a)*(z.r+5.5),zz=Math.sin(a)*(z.r+5.5),q=new THREE.Group();q.position.set(x,y,zz);q.rotation.y=-a;d.add(q);
      add(q,B(2.4,1.8,2.4),M.conc,0,.9,0,0,Math.PI/4,0);add(q,B(2.6,.25,2.6),M.concDark,0,1.9,0,0,Math.PI/4,0);add(q,B(.12,.22,1.3),M.dark,1.7,1.2,0);   // bastion with a gun slit
      add(q,Cy(.06,2.4,6),M.metal,-.6,3,0);}
    for(let k=0;k<10;k++){const a=k/10*6.283+gate+.15,x=Math.cos(a)*(z.r+7.4),zz=Math.sin(a)*(z.r+7.4);   // tank-trap hedgehogs
      for(const [rx,rz] of [[.6,0],[-.6,.5],[0,-.6]])add(d,B(1.4,.14,.14),M.rust,x,y+.45,zz,rx,k,rz);}}
  if(H){const a=gate+Math.PI*.5,x=Math.cos(a)*(z.r+6),zz=Math.sin(a)*(z.r+6),q=new THREE.Group();q.position.set(x,y,zz);q.rotation.y=-a+HALF;d.add(q);
    for(const s0 of [-1.6,1.6]){add(q,new THREE.CylinderGeometry(.01,1.3,1.4,4),TENT,s0,.7,0,0,Math.PI/4,0).scale.set(1,1,1.6);add(q,B(.6,.12,.12),RED,s0,1.45,0);add(q,B(.12,.12,.6),RED,s0,1.45,0);}
    add(q,new THREE.CircleGeometry(1.5,20).rotateX(-HALF),M.conc,0,.06,2.6);add(q,B(1.6,.02,.36),RED,0,.08,2.6);add(q,B(.36,.02,1.6),RED,0,.08,2.6);
    add(q,Cy(.05,2.6,6),M.metal,-2.6,1.3,-.8);add(q,B(.9,.6,.03),TENT,-2.15,2.25,-.8);add(q,B(.5,.14,.04),RED,-2.15,2.25,-.78);add(q,B(.14,.5,.04),RED,-2.15,2.25,-.78);}
}
"""+s[j:]
rep("    if(z.drillUp){zoneDecor(z);","    if(z.drillUp||z.hospUp){zoneDecor(z);")
# Chris's empire list: name the actual next garrison unit
rep("      const next=UTYPES[P2.seq[z.prodI%P2.seq.length]],","      const next=UTYPES[z.nextType||'rifle'],")
# drill hint: what the next level brings
rep("          hint:`<b>Garrison Drill</b>: replace fallen garrison troops faster${L<3?` (level ${L+1} of 3)`:' (maxed)'} and dress the base up.","          hint:`<b>Garrison Drill</b>${L<3?` ${['','II','III'][L]}: garrison up to ${Math.max(2,Math.round(ZTYPES[z.type].garrison*[.5,.75,1][L]))} troops${L===1?' and units up to $135 (Technicals, Light Tanks, AA)':' of any kind its buildings make'}, replaced faster. Sandbags, bunkers${L===2?', bastions and tank traps':''} go up round the base.`:' (maxed)'} Now garrisons ${G.garrisonPool(z).map(t=>UTYPES[t].name).join(', ')}.")
# rover button shows its slots
rep("        grid+=cb({attrs:`data-rec=\"${t.key}\"`,icon:ICONS[t.key],name:t.name,cost:`$${t.cost}·${t.hr}`,","        const rs=t.builder?G.roverSlots(z):null;\n        grid+=cb({attrs:`data-rec=\"${t.key}\"`,icon:ICONS[t.key],name:t.name+(rs?` ${rs.n}/${rs.cap}`:''),cost:`$${t.cost}·${t.hr}`,")
open(p,'w').write(s)
