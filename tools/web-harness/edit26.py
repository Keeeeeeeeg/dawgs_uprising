p='/home/claude/vu/v22.html';s=open(p).read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(s.count(a),a[:80]);s=s.replace(a,b)
rep("const UGEO={};for(const t in UTYPES){","""// ---- interceptor: a stealthy cranked-delta fighter in grey-and-white splinter camouflage; the army colour is only an accent ----
const INTC=(()=>{
  const camo=canvasTex(256,256,(c,w,h)=>{const r=rng(31);c.fillStyle='#7f8a98';c.fillRect(0,0,w,h);
    const blot=(col,n,s0)=>{c.fillStyle=col;for(let i=0;i<n;i++){const x=r()*w,y=r()*h,k=3+Math.floor(r()*4);c.beginPath();for(let j=0;j<k;j++){const a=j/k*6.283+r()*.8,d=s0*(.4+r());c.lineTo(x+Math.cos(a)*d,y+Math.sin(a)*d);}c.closePath();c.fill();}};
    blot('#5b6676',70,9);blot('#d9dde3',150,7);blot('#f2f3f5',90,5);blot('#46505e',40,4);},[1,1]);
  camo.wrapS=camo.wrapT=THREE.RepeatWrapping;
  const geo=(g,x,y,z,rx,ry,rz,sx,sy,sz)=>{g=g.index?g.toNonIndexed():g;if(sx)g.scale(sx,sy,sz);if(rx)g.rotateX(rx);if(rz)g.rotateZ(rz);if(ry)g.rotateY(ry);g.translate(x,y,z);return g;};
  const mergeUV=gs=>{let n=0;for(const g of gs)n+=g.attributes.position.count;const P=new Float32Array(n*3),N=new Float32Array(n*3),U=new Float32Array(n*2);let o=0;
    for(const g of gs){const c=g.attributes.position.count;P.set(g.attributes.position.array,o*3);N.set(g.attributes.normal.array,o*3);if(g.attributes.uv)U.set(g.attributes.uv.array,o*2);o+=c;}
    const b=new THREE.BufferGeometry();b.setAttribute('position',new THREE.BufferAttribute(P,3));b.setAttribute('normal',new THREE.BufferAttribute(N,3));b.setAttribute('uv',new THREE.BufferAttribute(U,2));return b;};
  // planform (nose +x, span along z): long chined nose, cranked leading edge, sawtooth trailing edge
  const sh=new THREE.Shape(),pts=[[3,0],[1.6,.22],[.6,.42],[-.1,.62],[-1.3,2.15],[-1.62,2.2],[-1.25,1.25],[-1.75,1.0],[-1.55,.62],[-2.2,.42],[-2.2,0]];
  sh.moveTo(pts[0][0],pts[0][1]);for(const [x,y] of pts.slice(1))sh.lineTo(x,y);for(const [x,y] of pts.slice(1,-1).reverse())sh.lineTo(x,-y);sh.closePath();
  const wing=new THREE.ExtrudeGeometry(sh,{depth:.12,bevelEnabled:true,bevelThickness:.05,bevelSize:.05,bevelSegments:1});
  // UVs from the planform so the camo lies across the whole aircraft
  {const P=wing.attributes.position,U=wing.attributes.uv;for(let i=0;i<P.count;i++)U.setXY(i,P.getX(i)*.16,P.getY(i)*.16);}
  const body=mergeUV([geo(wing,0,-.06,0,HALF,0,0),
    geo(new THREE.SphereGeometry(1,16,10),0,.12,0,0,0,0,2.7,.32,.48),     // blended fuselage spine
    geo(new THREE.SphereGeometry(1,12,8),-1.6,.14,.3,0,0,0,.8,.2,.26),geo(new THREE.SphereGeometry(1,12,8),-1.6,.14,-.3,0,0,0,.8,.2,.26), // engine humps
    geo(new THREE.CylinderGeometry(.01,.24,.9,10),2.55,.1,0,0,0,-HALF)]);    // nose cone
  {const P=body.attributes.position,U=body.attributes.uv;for(let i=0;i<P.count;i++)U.setXY(i,P.getX(i)*.16+.5,P.getZ(i)*.16+.5);}
  const canopy=geo(new THREE.SphereGeometry(1,14,8),1.15,.3,0,0,0,0,.75,.17,.2);
  // accents in the army colour: wingtip caps, canted fin tips and a nose band
  const acc=[];
  for(const s of [-1,1]){acc.push(geo(new THREE.BoxGeometry(.5,.08,.16),-1.46,-.02,s*2.17,0,s*.35,0));
    const fin=geo(new THREE.BoxGeometry(.75,.55,.05),-1.55,.42,s*.55,s*.55,0,0);acc.push(fin);}
  acc.push(geo(new THREE.CylinderGeometry(.2,.22,.14,10),2.08,.1,0,0,0,-HALF));
  const camoMat=new THREE.MeshPhongMaterial({map:camo,shininess:35,specular:0x50555c});
  const glass=new THREE.MeshPhongMaterial({color:0x1d2c3a,shininess:120,specular:0xbfd6e6});
  return {body,canopy,accent:mergeUV(acc),camoMat,glass};})();
// engine flame: an outer orange cone and a white-blue core (additive), pointing out of the nozzle along -x
const JET_GEO=new THREE.ConeGeometry(.2,1.5,10,1,true).rotateZ(HALF).translate(-.75,0,0),JET_CORE=new THREE.ConeGeometry(.1,.9,8,1,true).rotateZ(HALF).translate(-.45,0,0);
const jetMat=new THREE.MeshBasicMaterial({color:0xff9a3c,transparent:true,opacity:.75,blending:THREE.AdditiveBlending,depthWrite:false});
const jetCore=new THREE.MeshBasicMaterial({color:0xcfe6ff,transparent:true,opacity:.9,blending:THREE.AdditiveBlending,depthWrite:false});
const trailMat=new THREE.LineBasicMaterial({vertexColors:true,transparent:true,opacity:.85,blending:THREE.AdditiveBlending,depthWrite:false});
// where each plane type has its exhaust and its wingtips (body coordinates)
const PLANE_FX={intc:{jets:[[-2.2,.08,.3],[-2.2,.08,-.3]],tips:[[-1.5,0,2.2],[-1.5,0,-2.2]]},
  cas:{jets:[[-1.35,.35,.75],[-1.35,.35,-.75]],tips:[[.1,-.05,3.1],[.1,-.05,-3.1]]},
  bomb:{jets:[],tips:[[.3,0,5.5],[.3,0,-5.5]]}};
const TRAIL_N=36;
const UGEO={};for(const t in UTYPES){""")
rep("""    m=new THREE.Group();const body=new THREE.Mesh(UGEO[u.type][u.f],unitMat);body.castShadow=true;m.add(body);m.userData.body=body;""",
"""    m=new THREE.Group();let body;
    if(u.type==='intc'){body=new THREE.Group();const b=new THREE.Mesh(INTC.body,INTC.camoMat),cp=new THREE.Mesh(INTC.canopy,INTC.glass),ac=new THREE.Mesh(INTC.accent,teamAccent(u.f));
      for(const o of [b,cp,ac]){o.castShadow=true;body.add(o);}}
    else{body=new THREE.Mesh(UGEO[u.type][u.f],unitMat);body.castShadow=true;}
    m.add(body);m.userData.body=body;
    const PF=PLANE_FX[u.type]||{jets:[],tips:[]};m.userData.jets=PF.jets.map(([x,y,z])=>{const j=new THREE.Group();j.position.set(x,y,z);j.add(new THREE.Mesh(JET_GEO,jetMat),new THREE.Mesh(JET_CORE,jetCore));body.add(j);return j;});
    // wingtip vapour trails: a fading line per tip, fed while the plane is airborne
    m.userData.tips=PF.tips.map(t=>new THREE.Vector3(...t));
    m.userData.trails=PF.tips.map(()=>{const g=new THREE.BufferGeometry(),P=new Float32Array(TRAIL_N*3),C=new Float32Array(TRAIL_N*3);
      for(let i=0;i<TRAIL_N;i++){const k=(1-i/TRAIL_N)*.8;C[i*3]=C[i*3+1]=C[i*3+2]=k;}
      g.setAttribute('position',new THREE.BufferAttribute(P,3));g.setAttribute('color',new THREE.BufferAttribute(C,3));g.setDrawRange(0,0);
      const l=new THREE.Line(g,trailMat);l.frustumCulled=false;scene.add(l);return {l,g,n:0};});""")
rep("""    if(u.def.plane){const y=G.unitY(u);m.position.set(u.x,y,u.z);m.rotation.y=-u.ang;
      const b=m.userData.body;b.rotation.x=u.landed?0:-(u.bank||0)*.9;b.rotation.z=u.landed?0:.05;""","""    if(u.def.plane){const y=G.unitY(u);m.position.set(u.x,y,u.z);m.rotation.y=-u.ang;
      const b=m.userData.body;b.rotation.x=u.landed?0:-(u.bank||0)*.9;b.rotation.z=u.landed?0:.05;
      // engines: idle glow on the ground, full flame (and afterburner on take-off) in the air
      const air=!u.landed,burn=u.pstate==='takeoff'?1.6:air?1:.25;
      for(const j of m.userData.jets){j.visible=dt>0||air;const f=burn*(.85+Math.random()*.3);j.scale.set(f,Math.min(1,.6+burn*.4),Math.min(1,.6+burn*.4));}
      m.updateMatrixWorld(true);
      m.userData.trails.forEach((t,k)=>{const P=t.g.attributes.position.array;
        if(air&&u.altK>.25){P.copyWithin(3,0,(TRAIL_N-1)*3);const w=b.localToWorld(m.userData.tips[k].clone());P[0]=w.x;P[1]=w.y;P[2]=w.z;if(t.n<TRAIL_N)t.n++;}
        else if(t.n>0){P.copyWithin(0,3,TRAIL_N*3);t.n--;}   // trails fade out after landing
        t.g.setDrawRange(0,t.n);t.g.attributes.position.needsUpdate=true;t.l.visible=t.n>1;});""")
rep("    if(m&&m.userData.shadow)scene.remove(m.userData.shadow);","    if(m&&m.userData.trails)for(const t of m.userData.trails){scene.remove(t.l);t.g.dispose();}\n    if(m&&m.userData.shadow)scene.remove(m.userData.shadow);")
rep("    const m=meshes.get(u.id);if(m){scene.remove(m);meshes.delete(u.id);}","    const m=meshes.get(u.id);if(m){scene.remove(m);meshes.delete(u.id);if(m.userData.trails&&!(u.f===ME||G.visibleToPlayer(u.x,u.z)))for(const t of m.userData.trails)scene.remove(t.l);}")
rep("  for(const m of meshes.values())scene.remove(m);meshes.clear();","  for(const m of meshes.values()){scene.remove(m);if(m.userData.trails)for(const t of m.userData.trails)scene.remove(t.l);}meshes.clear();")
# team accent material cache
rep("function makeUnitMesh(u){","const _accMats=[];function teamAccent(f){return _accMats[f]||(_accMats[f]=new THREE.MeshPhongMaterial({color:FACTIONS[f].color,shininess:60,specular:0x333333}));}\nfunction makeUnitMesh(u){")
rep("const CHANGELOG=[\n","""const CHANGELOG=[
  {v:'17.1',name:'New interceptor',date:'2026-10-30',changes:[
    'The Interceptor is a new stealth fighter: long chined nose, cranked delta wing and sawtooth tail, in grey-and-white splinter camouflage. Your army colour shows only on the wingtips, the canted fins and a band at the nose.',
    'Jet aircraft show engine flames (with an afterburner kick on take-off), and every aircraft draws vapour trails from its wingtips while flying.',
  ]},
""",1)
rep("const GAME_VERSION={number:'17.0',name:'Bigger battlefields',date:'2026-10-30'};","const GAME_VERSION={number:'17.1',name:'New interceptor',date:'2026-10-30'};")
open(p,'w').write(s)
