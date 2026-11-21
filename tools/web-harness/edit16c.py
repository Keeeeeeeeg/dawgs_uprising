p='/home/claude/vu/v16.html';s=open(p).read()
def rep(a,b):
    global s
    assert s.count(a)==1,a[:80];s=s.replace(a,b)

plan=r"""// ---------- countryside and harbour flavour (purely visual: farms round towns, cranes, piers and boats at ports) ----------
// fields: {x,z,w,d,ang,crop}; farm buildings and harbour pieces: {kind,x,z,ang,...}; keep: circles trees stay out of
const FLAV={fields:[],things:[],keep:[]};
if(!MOON){
  const R=rng(4242),hA=(x,z)=>G.heightAt(x,z);
  const passAt=(x,z)=>{const i=Math.floor((x-X0)/CELL),j=Math.floor((z-Z0)/CELL);return i>=0&&j>=0&&i<GW&&j<GH&&map.pass[j*GW+i]===1;};
  const sDist=(px,pz,ax,az,bx,bz)=>{const dx=bx-ax,dz=bz-az;let t=((px-ax)*dx+(pz-az)*dz)/(dx*dx+dz*dz||1);t=Math.max(0,Math.min(1,t));return Math.hypot(px-(ax+dx*t),pz-(az+dz*t));};
  const allPlots=[];for(const z of G.zones)for(const p of z.plots)allPlots.push(p);
  const inAir=(x,z,pad)=>G.zones.some(o=>{const A=o.air;if(!A)return false;const s=(x-A.cx)*A.ux+(z-A.cz)*A.uz,q=(x-A.cx)*A.nx+(z-A.cz)*A.nz;return Math.abs(s)<=A.L/2+6+pad&&q>=-6-pad&&q<=18+pad;});
  const nearStreet=(x,z,m)=>{for(const st of G.streets)for(let i=1;i<st.pts.length;i++){const a=st.pts[i-1],b=st.pts[i];if(Math.abs(a[0]-x)>30&&Math.abs(b[0]-x)>30)continue;if(sDist(x,z,a[0],a[1],b[0],b[1])<st.w/2+m)return true;}return false;};
  const streetDir=(x,z)=>{let bd=1e9,ba=null;for(const st of G.streets)for(let i=1;i<st.pts.length;i++){const a=st.pts[i-1],b=st.pts[i],d=sDist(x,z,a[0],a[1],b[0],b[1]);if(d<bd){bd=d;ba=Math.atan2(b[1]-a[1],b[0]-a[0]);}}return bd<26?ba:null;};
  const taken=[];   // circles already used by flavour
  const free=(x,z,r,ownZ)=>{
    if(G.zones.some(o=>Math.hypot(o.x-x,o.z-z)<o.r+(o===ownZ?3:6)+r))return false;
    if(allPlots.some(p=>Math.abs(p.x-x)<r+4&&Math.hypot(p.x-x,p.z-z)<r+3.6))return false;
    if(taken.some(t=>Math.hypot(t.x-x,t.z-z)<t.r+r+.8))return false;
    if(map.props.some(p=>p.circles.some(c=>Math.hypot(c.x-x,c.z-z)<c.r+r+1)))return false;
    return !inAir(x,z,r+1);};
  // a level, dry rectangle clear of streets
  function rectOK(x,z,w,d,ang){const ca=Math.cos(ang),sa=Math.sin(ang);let lo=1e9,hi=-1e9;
    for(let a=-1;a<=1;a+=.5)for(let b=-1;b<=1;b+=.5){const px=x+ca*a*w/2-sa*b*d/2,pz=z+sa*a*w/2+ca*b*d/2;
      if(!passAt(px,pz))return false;const h=hA(px,pz);if(h<1)return false;lo=Math.min(lo,h);hi=Math.max(hi,h);
      if(nearStreet(px,pz,.9))return false;}
    return hi-lo<1.6;}
  const CROPS=4;
  // farms: a farmstead (house, barn, silo) with fields around it. Towns get the most, capitals some, fortresses a lone field and shed
  const FARMS={town:[3,2],hq:[2,2],fortress:[1,1],airbase:[0,0]};
  for(const z of G.zones){const [nF,nB]=FARMS[z.type]||[0,0];if(!nF)continue;
    let farms=0;const zr=rng(z.id*131+7);
    for(let k=0;k<160&&farms<nF;k++){const a=zr()*6.2832,r=z.r+14+zr()*24,x=z.x+Math.cos(a)*r,zz=z.z+Math.sin(a)*r;
      const sa=streetDir(x,zz),ang=sa!=null?sa:a+1.571;
      if(!rectOK(x,zz,7,6,ang)||!free(x,zz,5,z))continue;
      const ca=Math.cos(ang),si=Math.sin(ang);
      // the buildings of the farmstead in an L around a yard
      const fort=z.type==='fortress';
      const parts=fort?[['shed',0,0]]:[['farmhouse',-1.6,-1.2],['barn',2,.2],['silo',3.6,-2.6]];
      if(nB<2&&!fort)parts.pop();
      for(const [kind,lx,lz] of parts)FLAV.things.push({kind,x:x+ca*lx-si*lz,z:zz+si*lx+ca*lz,ang});
      taken.push({x,z:zz,r:5});farms++;
      // fields fanning out from the farmstead, rows along the street
      const want=fort?1:2+(zr()<.5?1:0);let got=0;
      for(let t=0;t<40&&got<want;t++){const fa=ang+(zr()<.5?0:1.571)+(zr()<.5?0:Math.PI),dist=9+zr()*8;
        const fx=x+Math.cos(fa)*dist,fz=zz+Math.sin(fa)*dist,w=9+zr()*6,d=6+zr()*4,fang=ang+(zr()-.5)*.25;
        const fr=Math.hypot(w,d)/2;if(!rectOK(fx,fz,w,d,fang)||!free(fx,fz,fr*.82,z))continue;
        FLAV.fields.push({x:fx,z:fz,w,d,ang:fang,crop:Math.floor(zr()*CROPS),hedge:zr()<.6});taken.push({x:fx,z:fz,r:fr*.82});got++;}
    }
  }
  // harbours: every port gets a big gantry crane on its waterfront; cove ports also get piers with moored boats along the quays
  // and a lighthouse on the point at the cove mouth
  const shoreFrom=(x,z,dx,dz,max)=>{for(let d=0;d<max;d+=.5){if(hA(x+dx*d,z+dz*d)<.55)return d;}return null;};
  for(const z of G.zones){if(!z.port)continue;const c=z.cove;const cands=[];
    if(c){const L=Math.hypot(c.bx-c.ax,c.bz-c.az),px=-c.uz,pz=c.ux;
      for(let t=.05;t<=.7;t+=.05)for(const sd of [1,-1]){const ax=c.ax+c.ux*L*t,az=c.az+c.uz*L*t;
        // walk out from the cove's centre line until the ground rises above the waterline
        let d=0;while(d<c.R+10&&hA(ax+px*sd*d,az+pz*sd*d)<.7)d+=.5;if(d>=c.R+10||d<3)continue;
        const x=ax+px*sd*(d+1.6),zz=az+pz*sd*(d+1.6);cands.push({x,z:zz,ang:Math.atan2(-pz*sd,-px*sd)});}}
    else for(let k=0;k<48;k++){const a=k/48*6.2832,dx=Math.cos(a),dz=Math.sin(a);const d=shoreFrom(z.x+dx*(z.r+2),z.z+dz*(z.r+2),dx,dz,40);
      if(d==null||d<2)continue;const x=z.x+dx*(z.r+2+d-1.6),zz=z.z+dz*(z.r+2+d-1.6);cands.push({x,z:zz,ang:a});}
    let best=null,bs=1e9;
    for(const q of cands){if(hA(q.x,q.z)<.6||!free(q.x,q.z,2.4,z))continue;const ox=q.x+Math.cos(q.ang)*7,oz=q.z+Math.sin(q.ang)*7;if(hA(ox,oz)>-.3)continue;
      const sc=Math.hypot(q.x-z.x,q.z-z.z);if(sc<bs){bs=sc;best=q;}}
    if(best){FLAV.things.push({kind:'crane',x:best.x,z:best.z,ang:best.ang,y:hA(best.x,best.z)});taken.push({x:best.x,z:best.z,r:2.6});
      // a stack of containers just inland of the crane
      const bx=best.x-Math.cos(best.ang)*4.6,bz=best.z-Math.sin(best.ang)*4.6;
      if(hA(bx,bz)>.8&&free(bx,bz,1.8,z)&&!nearStreet(bx,bz,.3)){FLAV.things.push({kind:'containers',x:bx,z:bz,ang:best.ang+1.571});taken.push({x:bx,z:bz,r:1.9});}}
    if(!c)continue;
    // piers off the quay streets, a boat tied to most of them
    let piers=0;
    for(const st of G.streets){if(st.zone!==z.id||!st.quay)continue;let acc=4;
      for(let i=1;i<st.pts.length&&piers<5;i++){const a=st.pts[i-1],b=st.pts[i];acc+=Math.hypot(b[0]-a[0],b[1]-a[1]);if(acc<8)continue;
        const dir=Math.atan2(b[1]-a[1],b[0]-a[0]);
        for(const sd of [1,-1]){const nx=Math.cos(dir+sd*1.571),nz=Math.sin(dir+sd*1.571);const d=shoreFrom(b[0],b[1],nx,nz,9);if(d==null)continue;
          const sx=b[0]+nx*(d-1),sz=b[1]+nz*(d-1),ex=sx+nx*7,ez=sz+nz*7;if(hA(ex,ez)>-.8)continue;
          const mx=(sx+ex)/2,mz=(sz+ez)/2;if(taken.some(t=>Math.hypot(t.x-mx,t.z-mz)<t.r+3.5))continue;
          FLAV.things.push({kind:'pier',x:sx,z:sz,ang:dir+sd*1.571,len:7,boat:vnoise(sx,sz)<.75});taken.push({x:mx,z:mz,r:3.2});piers++;acc=0;break;}}}
    // lighthouse on whichever side of the cove mouth has dry land
    const px=-c.uz,pz=c.ux;
    for(const sd of [1,-1]){let ok=null;for(let d=c.R+2;d<c.R+12;d+=1){const x=c.bx-c.ux*4+px*sd*d,zz=c.bz-c.uz*4+pz*sd*d;if(hA(x,zz)>.9&&free(x,zz,1.6,z)&&!nearStreet(x,zz,.6)){ok=[x,zz];break;}}
      if(ok){FLAV.things.push({kind:'lighthouse',x:ok[0],z:ok[1],ang:0});taken.push({x:ok[0],z:ok[1],r:1.8});break;}}
  }
  for(const t of taken)FLAV.keep.push(t);
}
"""
rep("// ---------- terrain ----------\n",plan+"// ---------- terrain ----------\n")

# trees stay off fields, farms, harbour pieces and the airfield
rep("    if(map.props.some(p=>p.circles.some(c=>Math.hypot(c.x-x,c.z-z)<c.r+3)))continue;\n    if(Math.abs(G.heightAt(x+1.5,z)-h)>1.2)continue;",
"""    if(map.props.some(p=>p.circles.some(c=>Math.hypot(c.x-x,c.z-z)<c.r+3)))continue;
    if(FLAV.keep.some(t=>Math.abs(t.x-x)<t.r+2&&Math.hypot(t.x-x,t.z-z)<t.r+1.5))continue;
    if(G.zones.some(o=>{const A=o.air;if(!A)return false;const s=(x-A.cx)*A.ux+(z-A.cz)*A.uz,q=(x-A.cx)*A.nx+(z-A.cz)*A.nz;return Math.abs(s)<A.L/2+14&&q>-12&&q<22;}))continue;
    if(Math.abs(G.heightAt(x+1.5,z)-h)>1.2)continue;""")

meshes=r"""
// ---------- countryside and harbour meshes ----------
if(!MOON){
  const fg=new THREE.Group();scene.add(fg);const hA=(x,z)=>G.heightAt(x,z);
  // crop textures: ploughed earth, young green rows, ripe wheat, lavender-ish clover
  const cropTex=[['#7a5a3a','#5e4428'],['#7fa043','#5f8232'],['#d4b25a','#b8933e'],['#8f9c4f','#a7b15c']].map(([a,b],k)=>canvasTex(64,64,(c,w,h)=>{
    c.fillStyle=a;c.fillRect(0,0,w,h);c.fillStyle=b;for(let y=0;y<h;y+=8)c.fillRect(0,y,w,k===0?3:4);
    const r=rng(k+20);for(let i=0;i<160;i++){c.fillStyle=`rgba(0,0,0,${r()*.08})`;c.fillRect(r()*w,r()*h,2,2);}},[1,1]));
  const cropMat=cropTex.map(t=>new THREE.MeshLambertMaterial({map:t,polygonOffset:true,polygonOffsetFactor:-2,polygonOffsetUnits:-2}));
  const hedgeM=new THREE.MeshLambertMaterial({color:0x3f6b2a,flatShading:true});
  for(const f of FLAV.fields){
    const nx=Math.max(2,Math.ceil(f.w/2.5)),nz=Math.max(2,Math.ceil(f.d/2.5));const geo=new THREE.PlaneGeometry(f.w,f.d,nx,nz).rotateX(-HALF);
    const P=geo.attributes.position,U=geo.attributes.uv,ca=Math.cos(f.ang),sa=Math.sin(f.ang);
    for(let k=0;k<P.count;k++){const lx=P.getX(k),lz=P.getZ(k),wx=f.x+ca*lx-sa*lz,wz=f.z+sa*lx+ca*lz;P.setXYZ(k,wx,hA(wx,wz)+.06,wz);U.setXY(k,lx/4,lz/4);}
    geo.computeVertexNormals();cropTex[f.crop].wrapS=cropTex[f.crop].wrapT=THREE.RepeatWrapping;
    const m=new THREE.Mesh(geo,cropMat[f.crop]);m.receiveShadow=true;fg.add(m);
    if(f.hedge)for(let t=-f.w/2+1;t<f.w/2;t+=2){const lx=t+.5,lz=f.d/2+.5,wx=f.x+ca*lx-sa*lz,wz=f.z+sa*lx+ca*lz;
      add(fg,B(2.1,.9,.8),hedgeM,wx,hA(wx,wz)+.35,wz,0,-f.ang,0);}
  }
  const red=mat(0x8e3a2c),cream=mat(0xe8dcc0),rustRoof=mat(0x6f5a48),craneM=mat(0xd2552c,30),craneW=mat(0xeae6dc,30);
  const contC=[mat(0x2f6f8f),mat(0xb8432e),mat(0xd9a43a),mat(0x4f7a3c),mat(0x9a9a92)];
  for(const t of FLAV.things){const y=t.y!=null?t.y:hA(t.x,t.z),q=new THREE.Group();q.position.set(t.x,y,t.z);q.rotation.y=-t.ang;fg.add(q);
    if(t.kind==='farmhouse')house(q,0,0,0,3,2.6,2,M.tile,0);
    else if(t.kind==='barn'){add(q,B(4.2,2.4,3),red,0,1.2,0);const rf=add(q,new THREE.CylinderGeometry(.01,1,1,4,1),rustRoof,0,3,0,0,Math.PI/4,0);rf.scale.set(3.2,1.3,2.3);
      add(q,B(1.4,1.7,.06),cream,0,.85,1.52);}
    else if(t.kind==='silo'){add(q,Cy(.9,4.6,12),M.tank,0,2.3,0);add(q,new THREE.SphereGeometry(.9,12,6,0,6.283,0,1.571),M.metal,0,4.6,0);}
    else if(t.kind==='shed'){add(q,B(3,1.6,2.2),M.corr,0,.8,0);add(q,B(3.3,.15,2.5),M.concDark,0,1.65,0);drums(q,2,-.4,0,2);}
    else if(t.kind==='crane'){
      // ship-to-shore gantry crane: four legs straddling the quay, a high boom reaching out over the water, counterweight behind
      for(const [lx,lz] of [[-1.6,-1.6],[1.6,-1.6],[-1.6,1.6],[1.6,1.6]])add(q,B(.38,7,.38),craneM,lx,3.5,lz);
      for(const lz of [-1.6,1.6])add(q,B(3.6,.45,.4),craneM,0,6.8,lz);
      for(const lx of [-1.6,1.6])add(q,B(.4,.4,3.6),craneW,lx,1.4,0);
      add(q,B(12.5,.6,.9),craneW,3.2,7.5,0);add(q,B(12.5,.2,.2),craneM,3.2,7.9,-.38);add(q,B(12.5,.2,.2),craneM,3.2,7.9,.38);
      add(q,B(2.4,1.5,2.4),craneW,0,8.4,0);add(q,B(1.4,1.1,1.6),M.glass,1,6.6,0);add(q,B(1.8,1,1.8),M.concDark,-2.9,7,0);
      for(const sd of [-1,1])add(q,Cy(.05,4.4,4),M.dark,3,10.4,sd*.4,0,0,sd*.0+(HALF-.32)*0);
      add(q,B(.06,4.2,.06),M.dark,7.2,5.3,0);add(q,B(1.2,.4,1),M.yellow,7.2,3,0);
      add(q,new THREE.SphereGeometry(.14,6,4),mat(0xff3a2a),-3.4,7.6,0);}
    else if(t.kind==='containers'){for(let k=0;k<5;k++){const lx=(k%3-1)*1.15,ly=k<3?0:1.05,lz=0;add(q,B(1.05,1,3),contC[(k+Math.round(t.x))%5],lx+(k>=3?.55:0),ly+.5,lz);}}
    else if(t.kind==='pier'){
      // wooden jetty on piles running out from the quay; a small boat moored alongside
      const L=t.len;add(q,B(L,.22,1.5),M.wood,L/2,.55,0);
      for(let s0=.8;s0<L;s0+=1.8)for(const sd of [-.65,.65])add(q,Cy(.12,2.6,6),M.wood,s0,-.6,sd);
      add(q,Cy(.12,.5,6),M.dark,L-.4,.85,.6);add(q,Cy(.12,.5,6),M.dark,L-.4,.85,-.6);
      if(t.boat){const b=new THREE.Group();b.position.set(L*.6,-y+.05,1.9*(vnoise(t.x,t.z)<.4?-1:1));q.add(b);
        add(b,B(3.8,.7,1.4),vnoise(t.z,t.x)<.5?M.blue:M.red,0,.25,0);add(b,new THREE.CylinderGeometry(.01,.7,1.1,3),M.white,2.3,.25,0,0,0,-HALF).scale.set(1,1,1.4);
        add(b,B(3.6,.12,1.2),M.wood,0,.62,0);add(b,B(1.1,.9,1),M.white,-.6,1.1,0);add(b,Cy(.05,2,5),M.metal,.6,1.6,0);}}
    else if(t.kind==='lighthouse'){add(q,new THREE.CylinderGeometry(.8,1.1,6,12),M.white,0,3,0);
      for(const hy of [1.6,3.8])add(q,new THREE.CylinderGeometry(.93,.98,.8,12),mat(0xb8382c),0,hy,0);
      add(q,Cy(.95,.25,12),M.concDark,0,6.1,0);add(q,Cy(.6,1,10),M.glass,0,6.7,0);add(q,new THREE.ConeGeometry(.75,.8,10),mat(0xb8382c),0,7.6,0);
      add(q,B(2.6,1.2,1.8),M.house,1.7,.6,.6);}
  }
  bakeGroup(fg);
}
"""
rep("G.zones.forEach(z=>zoneVis[z.id]=buildZone(z));\n","G.zones.forEach(z=>zoneVis[z.id]=buildZone(z));\n"+meshes)
open(p,'w').write(s)
