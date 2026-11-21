p='/home/claude/vu/v17.html';s=open(p).read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(s.count(a),a[:70]);s=s.replace(a,b)
transit=r"""// ---------- roads and railways between bases (purely visual, with ambient traffic) ----------
// Roads join every base on a landmass (a spanning tree plus a few shortcuts), railways join HQs and Towns. Each line is
// routed over open land by A* on the terrain grid: gentle slopes, around other bases, build pads and airfields.
const TRANSIT={roads:[],rails:[],mask:new Uint8Array(GW*GH)};
// height of the drawn terrain surface (same triangle split as the terrain mesh), so overlays never sink into it
const surfH=(x,z)=>{const gx=Math.max(0,Math.min(GW-1e-4,(x-X0)/CELL)),gz=Math.max(0,Math.min(GH-1e-4,(z-Z0)/CELL)),i=Math.floor(gx),j=Math.floor(gz),fx=gx-i,fz=gz-j,V=GW+1;
  const ha=map.hv[j*V+i],hd=map.hv[j*V+i+1],hb=map.hv[(j+1)*V+i],hc=map.hv[(j+1)*V+i+1];
  return fx+fz<=1?ha+(hd-ha)*fx+(hb-ha)*fz:hc+(hb-hc)*(1-fx)+(hd-hc)*(1-fz);};
if(!MOON){
  const N=GW*GH,V=GW+1,hv=map.hv,cellOf=(x,z)=>Math.max(0,Math.min(GH-1,Math.floor((z-Z0)/CELL)))*GW+Math.max(0,Math.min(GW-1,Math.floor((x-X0)/CELL)));
  const cx=k=>X0+(k%GW+.5)*CELL,cz=k=>Z0+(Math.floor(k/GW)+.5)*CELL;
  // per-cell base cost: slope, bases, pads and airfields; water and cliffs are closed
  const slope=new Float32Array(N),pen=new Float32Array(N);
  for(let k=0;k<N;k++){const i=k%GW,j=(k-i)/GW,a=hv[j*V+i],b=hv[j*V+i+1],c=hv[(j+1)*V+i],d=hv[(j+1)*V+i+1];
    slope[k]=Math.max(a,b,c,d)-Math.min(a,b,c,d);if(!map.pass[k]||Math.min(a,b,c,d)<.6)pen[k]=Infinity;}
  const stamp=(x,z,r,v)=>{const i0=Math.floor((x-r-X0)/CELL),i1=Math.floor((x+r-X0)/CELL),j0=Math.floor((z-r-Z0)/CELL),j1=Math.floor((z+r-Z0)/CELL);
    for(let j=Math.max(0,j0);j<=Math.min(GH-1,j1);j++)for(let i=Math.max(0,i0);i<=Math.min(GW-1,i1);i++){const k=j*GW+i;if(Math.hypot(cx(k)-x,cz(k)-z)<=r&&pen[k]!==Infinity)pen[k]+=v;}};
  for(const z of G.zones){stamp(z.x,z.z,z.r+2,60);for(const p of z.plots)stamp(p.x,p.z,4.2,30);
    if(z.air){const A=z.air;for(let t=-A.L/2-6;t<=A.L/2+6;t+=3)for(let q=-6;q<=18;q+=3)stamp(A.cx+A.ux*t+A.nx*q,A.cz+A.uz*t+A.nz*q,2.5,40);}}
  for(const p of map.props)for(const c of p.circles)stamp(c.x,c.z,c.r+1.5,25);
  // landmasses
  const comp=new Int32Array(N).fill(-1);let nc=0;
  for(let k=0;k<N;k++){if(comp[k]>=0||pen[k]===Infinity&&!map.pass[k])continue;if(!map.pass[k])continue;const q=[k];comp[k]=nc;
    while(q.length){const c=q.pop(),i=c%GW,j=(c-i)/GW;for(let dj=-1;dj<=1;dj++)for(let di=-1;di<=1;di++){const ni=i+di,nj=j+dj;if(ni<0||nj<0||ni>=GW||nj>=GH)continue;const n=nj*GW+ni;if(comp[n]<0&&map.pass[n]){comp[n]=nc;q.push(n);}}}nc++;}
  const zc=G.zones.map(z=>comp[cellOf(z.x,z.z)]);
  const shared=new Float32Array(N).fill(1);   // roads already laid are cheaper to follow, so lines merge into trunks
  function route(ax,az,bx,bz,slopeW,useShared){
    const s0=cellOf(ax,az),t0=cellOf(bx,bz),g=new Float64Array(N).fill(Infinity),from=new Int32Array(N).fill(-1),done=new Uint8Array(N);
    const H=[];const push=(f,k)=>{H.push([f,k]);let i=H.length-1;while(i>0){const p=(i-1)>>1;if(H[p][0]<=H[i][0])break;[H[p],H[i]]=[H[i],H[p]];i=p;}};
    const pop=()=>{const r=H[0],l=H.pop();if(H.length){H[0]=l;let i=0;for(;;){let a=2*i+1,b=a+1,m=i;if(a<H.length&&H[a][0]<H[m][0])m=a;if(b<H.length&&H[b][0]<H[m][0])m=b;if(m===i)break;[H[m],H[i]]=[H[i],H[m]];i=m;}}return r;};
    const tx=cx(t0),tz=cz(t0);g[s0]=0;push(0,s0);let it=0;
    while(H.length&&it++<N*3){const [,k]=pop();if(done[k])continue;done[k]=1;if(k===t0)break;const i=k%GW,j=(k-i)/GW;
      for(let dj=-1;dj<=1;dj++)for(let di=-1;di<=1;di++){if(!di&&!dj)continue;const ni=i+di,nj=j+dj;if(ni<0||nj<0||ni>=GW||nj>=GH)continue;const n=nj*GW+ni;
        const pn=n===t0?0:pen[n];if(pn===Infinity||done[n])continue;
        const step=(di&&dj?1.414:1)*CELL*(1+slope[n]*slopeW+pn*.1+Math.abs(hv[nj*V+ni]-hv[j*V+i])*slopeW*.5)*(useShared?shared[n]:1);
        const ng=g[k]+step;if(ng<g[n]){g[n]=ng;from[n]=k;push(ng+Math.hypot(cx(n)-tx,cz(n)-tz)*.9,n);}}}
    if(from[t0]<0&&t0!==s0)return null;
    const cells=[];for(let k=t0;k>=0;k=from[k]){cells.push(k);if(k===s0)break;}cells.reverse();
    // cell centres, thinned and rounded off (Chaikin) into a drivable curve
    let pts=[[ax,az]];for(let i=2;i<cells.length-1;i+=2)pts.push([cx(cells[i]),cz(cells[i])]);pts.push([bx,bz]);
    for(let r=0;r<3;r++){const o=[pts[0]];for(let i=0;i<pts.length-1;i++){const [x0,z0]=pts[i],[x1,z1]=pts[i+1];o.push([x0*.75+x1*.25,z0*.75+z1*.25],[x0*.25+x1*.75,z0*.25+z1*.75]);}o.push(pts[pts.length-1]);pts=o;}
    for(const k of cells)shared[k]=.45;
    return pts;}
  function finish(pts,w){const cum=[0];for(let i=1;i<pts.length;i++)cum.push(cum[i-1]+Math.hypot(pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1]));
    const L={pts,w,cum,len:cum[cum.length-1]};
    for(let s0=0;s0<=L.len;s0+=1){const p=lineAt(L,s0),k=cellOf(p.x,p.z);TRANSIT.mask[k]=1;}
    return L;}
  // spanning tree (shortest first) over the given zones of one landmass, plus shortcuts where the tree goes the long way round
  function plan(zs,extra){const out=[],par=zs.map((_,i)=>i),f=i=>par[i]===i?i:(par[i]=f(par[i]));const pairs=[];
    for(let a=0;a<zs.length;a++)for(let b=a+1;b<zs.length;b++)if(zc[zs[a].id]===zc[zs[b].id]&&zc[zs[a].id]>=0)pairs.push([Math.hypot(zs[a].x-zs[b].x,zs[a].z-zs[b].z),a,b]);
    pairs.sort((p,q)=>p[0]-q[0]);const deg=zs.map(()=>0);
    for(const [d,a,b] of pairs){if(f(a)!==f(b)){par[f(a)]=f(b);out.push([zs[a],zs[b]]);deg[a]++;deg[b]++;}}
    if(extra)for(const [d,a,b] of pairs){if(d>130||out.some(e=>(e[0]===zs[a]&&e[1]===zs[b])||(e[0]===zs[b]&&e[1]===zs[a])))continue;if(deg[a]<2||deg[b]<2){out.push([zs[a],zs[b]]);deg[a]++;deg[b]++;}}
    return out;}
  const ends=(a,b,off)=>{const d=Math.hypot(b.x-a.x,b.z-a.z)||1,ux=(b.x-a.x)/d,uz=(b.z-a.z)/d;return [a.x+ux*(a.r+off),a.z+uz*(a.r+off),b.x-ux*(b.r+off),b.z-uz*(b.r+off)];};
  for(const [a,b] of plan(G.zones,true)){const [x0,z0,x1,z1]=ends(a,b,2.5);const pts=route(x0,z0,x1,z1,3,true);if(pts)TRANSIT.roads.push(finish(pts,3.4));}
  const railZ=G.zones.filter(z=>z.type==='hq'||z.type==='town');
  for(const [a,b] of plan(railZ,false)){if(Math.hypot(a.x-b.x,a.z-b.z)>300)continue;const [x0,z0,x1,z1]=ends(a,b,7);const pts=route(x0,z0,x1,z1,9,false);
    if(pts){const L=finish(pts,2.2);L.a=a;L.b=b;TRANSIT.rails.push(L);}}
}
function lineAt(L,s){s=Math.max(0,Math.min(L.len,s));let lo=0,hi=L.cum.length-1;while(hi-lo>1){const m=(lo+hi)>>1;if(L.cum[m]<=s)lo=m;else hi=m;}
  const a=L.pts[lo],b=L.pts[Math.min(L.pts.length-1,lo+1)],seg=(L.cum[lo+1]-L.cum[lo])||1,t=(s-L.cum[lo])/seg;
  return {x:a[0]+(b[0]-a[0])*t,z:a[1]+(b[1]-a[1])*t,ang:Math.atan2(b[1]-a[1],b[0]-a[0])};}
const nearTransit=(x,z)=>{const i=Math.floor((x-X0)/CELL),j=Math.floor((z-Z0)/CELL);for(let dj=-1;dj<=1;dj++)for(let di=-1;di<=1;di++){const ii=i+di,jj=j+dj;if(ii>=0&&jj>=0&&ii<GW&&jj<GH&&TRANSIT.mask[jj*GW+ii])return true;}return false;};
"""
rep("// ---------- countryside and harbour flavour",transit+"// ---------- countryside and harbour flavour")
# farms / harbour avoid roads and rails; farms line up with roads too
rep("  const nearStreet=(x,z,m)=>{for(const st of G.streets)","  const LINES=G.streets.concat(TRANSIT.roads,TRANSIT.rails);\n  const nearStreet=(x,z,m)=>{for(const st of LINES)")
rep("  const streetDir=(x,z)=>{let bd=1e9,ba=null;for(const st of G.streets)","  const streetDir=(x,z)=>{let bd=1e9,ba=null;for(const st of LINES)")
# terrain: paint roads like streets, rails as a gravel bed
rep("  for(const z of zdef)for(const p of z.plots)paint(yardM,p.x,p.z,p.x,p.z,3,2);",
"""  for(const z of zdef)for(const p of z.plots)paint(yardM,p.x,p.z,p.x,p.z,3,2);
  for(const L of TRANSIT.roads)for(let i=1;i<L.pts.length;i+=2){const a=L.pts[i-1],b=L.pts[Math.min(L.pts.length-1,i+1)];paint(roadM,a[0],a[1],b[0],b[1],1.3,1.4);}
  const railM=new Float32Array(n);
  for(const L of TRANSIT.rails)for(let i=1;i<L.pts.length;i+=2){const a=L.pts[i-1],b=L.pts[Math.min(L.pts.length-1,i+1)];paint(railM,a[0],a[1],b[0],b[1],1.2,1);}""")
rep("    if(roadM[k]>0&&h>0)c.lerp(C.road,roadM[k]*.85);","    if(roadM[k]>0&&h>0)c.lerp(C.road,roadM[k]*.85);\n    if(railM[k]>0&&h>0)c.lerp(C.ballast,railM[k]*.8);")
rep("pad:hexC(0xb39a74),padLine:hexC(0xf0e6cc),road:hexC(0x6d665a)};","pad:hexC(0xb39a74),padLine:hexC(0xf0e6cc),road:hexC(0x6d665a),ballast:hexC(0x8c8274)};")
rep("pad:hexC(0x6f6c66),padLine:hexC(0xd8d4c8),road:hexC(0x55534e)}","pad:hexC(0x6f6c66),padLine:hexC(0xd8d4c8),road:hexC(0x55534e),ballast:hexC(0x5d5b56)}")
# trees off roads and rails
rep("    if(FLAV.keep.some(t=>","    if(nearTransit(x,z))continue;\n    if(FLAV.keep.some(t=>")

meshes=r"""
// ---------- railway track, stations and ambient traffic ----------
const TRAFFIC=[];   // {inst,line,s,v,dir,wait,kind,k,len,gap,n}
if(!MOON&&(TRANSIT.roads.length||TRANSIT.rails.length)){
  const m4=new THREE.Matrix4(),q4=new THREE.Quaternion(),v3=new THREE.Vector3(),one=new THREE.Vector3(1,1,1),Y=new THREE.Vector3(0,1,0);
  // track: two rails and sleepers, instanced along every line
  let nSeg=0;for(const L of TRANSIT.rails)nSeg+=Math.ceil(L.len/1.2)+1;
  if(nSeg){const sl=new THREE.InstancedMesh(B(2,.12,.34),mat(0x5a4a3a),nSeg),rl=new THREE.InstancedMesh(B(1.3,.12,.1),mat(0x8d8f90,70),nSeg*2);let a=0,b=0;
    for(const L of TRANSIT.rails)for(let s0=0;s0<=L.len;s0+=1.2){const p=lineAt(L,s0),y=surfH(p.x,p.z)+.1;q4.setFromAxisAngle(Y,-p.ang);
      m4.compose(v3.set(p.x,y,p.z),q4,one);sl.setMatrixAt(a++,m4);
      for(const sd of [-.55,.55]){m4.compose(v3.set(p.x-Math.sin(p.ang)*sd,y+.11,p.z+Math.cos(p.ang)*sd),q4,one);rl.setMatrixAt(b++,m4);}}
    sl.count=a;rl.count=b;sl.receiveShadow=rl.receiveShadow=true;scene.add(sl,rl);
    // a small station at each end of a line
    const st=new THREE.Group();scene.add(st);
    for(const L of TRANSIT.rails)for(const e of [0,L.len]){const p=lineAt(L,e),nx=-Math.sin(p.ang),nz=Math.cos(p.ang),side=1;
      const g=new THREE.Group();g.position.set(p.x+nx*2.6*side,surfH(p.x+nx*2.6,p.z+nz*2.6),p.z+nz*2.6*side);g.rotation.y=-p.ang;st.add(g);
      add(g,B(7,.4,1.8),M.conc,0,.2,0);add(g,B(3.4,1.8,1.6),M.house,0,1.3,.5);add(g,B(3.8,.2,2.1),M.tile,0,2.3,.4);}
    bakeGroup(st);}
  // vehicle shapes (white parts take each instance's colour)
  const W=hexC(0xffffff),Dk=hexC(0x2b2e30),Gl=hexC(0x8fb3c0);
  const carG=merge([part(B(1.9,.55,1),W,0,.42,0),part(B(1,.42,.9),W,-.1,.88,0),part(B(.05,.32,.8),Gl,.42,.86,0),part(Cy(.2,1.04,8),Dk,.6,.2,0,HALF),part(Cy(.2,1.04,8),Dk,-.6,.2,0,HALF)]);
  const truckG=merge([part(B(1,1,1.2),W,1.2,.7,0),part(B(.05,.4,1),Gl,1.71,.95,0),part(B(2.4,1.2,1.3),hexC(0xb8b2a2),-.6,.85,0),part(B(3.6,.2,1.1),Dk,0,.25,0),
    part(Cy(.26,1.24,8),Dk,1.2,.26,0,HALF),part(Cy(.26,1.24,8),Dk,-.4,.26,0,HALF),part(Cy(.26,1.24,8),Dk,-1.2,.26,0,HALF)]);
  const locoG=merge([part(B(3.6,1.3,1.3),W,0,.95,0),part(B(1,.5,1.32),Gl,1.2,1.35,0),part(B(3.8,.25,1.4),Dk,0,.25,0),part(Cy(.18,.6,8),Dk,-1,1.8,0)]);
  const wagG=merge([part(B(3.3,1.15,1.25),W,0,.9,0),part(B(3.4,.22,1.35),Dk,0,.25,0),part(B(3.4,.12,1.3),hexC(0x5b4c3c),0,1.53,0)]);
  const vmat=new THREE.MeshLambertMaterial({vertexColors:true});
  const R=rng(77),pick=a=>a[Math.floor(R()*a.length)];
  const carCols=[0xc0392b,0x2e5e9e,0xe6e1d3,0x3f4a3a,0xd9a43a,0x7a7f86],truckCols=[0x56663a,0x8a4a2a,0x2f5f7a,0xd9cfb8],trainCols=[0x3d5a3a,0x7a2e26,0x2a3f5c];
  const cars=[],trucks=[],trains=[];
  for(const L of TRANSIT.roads){const n=Math.max(1,Math.round(L.len/70));for(let i=0;i<n;i++)(R()<.35?trucks:cars).push({L,s:R()*L.len,v:5+R()*4,dir:R()<.5?1:-1,wait:0,col:0});}
  for(const L of TRANSIT.rails)if(L.len>40)trains.push({L,s:R()*(L.len-14),v:9,dir:1,wait:R()*4,n:4,gap:3.7,col:pick(trainCols)});
  const mk=(geo,list,cols,per)=>{if(!list.length)return null;const im=new THREE.InstancedMesh(geo,vmat,list.length*(per||1));const c=new THREE.Color();
    for(let i=0;i<list.length*(per||1);i++){c.set(per?list[Math.floor(i/per)].col:pick(cols));im.setColorAt(i,c);}im.castShadow=true;im.instanceMatrix.setUsage(THREE.DynamicDrawUsage);scene.add(im);return im;};
  const imCar=mk(carG,cars,carCols),imTruck=mk(truckG,trucks,truckCols);
  const locos=trains.map(t=>t),imLoco=mk(locoG,trains,null,2),imWag=mk(wagG,trains,null,2);
  const place=(im,i,x,z,ang)=>{q4.setFromAxisAngle(Y,-ang);m4.compose(v3.set(x,surfH(x,z)+.05,z),q4,one);im.setMatrixAt(i,m4);};
  function drive(list,im,dt){if(!im)return;list.forEach((c,i)=>{
      if(c.wait>0)c.wait-=dt;else{c.s+=c.v*c.dir*dt;if(c.s>=c.L.len||c.s<=0){c.s=Math.max(0,Math.min(c.L.len,c.s));c.dir*=-1;c.wait=1.5+Math.random()*4;}}
      const p=lineAt(c.L,c.s),ang=c.dir>0?p.ang:p.ang+Math.PI,off=.9;   // keep right
      place(im,i,p.x-Math.sin(ang)*off,p.z+Math.cos(ang)*off,ang);});im.instanceMatrix.needsUpdate=true;}
  function run(dt){
    drive(cars,imCar,dt);drive(trucks,imTruck,dt);
    // push-pull trains: a locomotive at each end, so they simply run back the way they came
    trains.forEach((t,i)=>{const span=(t.n-1)*t.gap,max=t.L.len-span;
      if(t.wait>0)t.wait-=dt;else{t.s+=t.v*t.dir*dt;if(t.s>=max||t.s<=0){t.s=Math.max(0,Math.min(max,t.s));t.dir*=-1;t.wait=4+Math.random()*5;}}
      for(let k=0;k<t.n;k++){const p=lineAt(t.L,t.s+k*t.gap),end=k===0||k===t.n-1,ang=p.ang+(k===0?Math.PI:0);
        if(end)place(imLoco,i*2+(k?1:0),p.x,p.z,ang);else place(imWag,i*2+(k-1),p.x,p.z,p.ang);}});
    if(imLoco)imLoco.instanceMatrix.needsUpdate=true;if(imWag)imWag.instanceMatrix.needsUpdate=true;}
  run(0);TRAFFIC.run=run;
}
"""
rep("// ---------- countryside and harbour meshes ----------",meshes.strip()+"\n// ---------- countryside and harbour meshes ----------")
rep("  syncScene(dt);updateFX(dt);updateMarkers(dt);","  syncScene(dt);updateFX(dt);updateMarkers(dt);\n  if(TRAFFIC.run)TRAFFIC.run(NET?dt:(modalOpen?0:dt*speed));")
open(p,'w').write(s)
