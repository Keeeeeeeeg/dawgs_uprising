p='/home/claude/vu/v20.html';s=open(p).read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(s.count(a),a[:80]);s=s.replace(a,b)
i=s.index("  for(const [a,b] of plan(G.zones,true)){const [x0,z0,x1,z1]=ends(a,b,2.5);")
j=s.index("\n",i)+1
s=s[:j]+r"""  // shipping lanes: Ports on the same sea are linked (spanning tree plus a few short extras), routed through open water
  {const W=map.wpass,ld=new Float32Array(N).fill(1e9),q=[];
    for(let k=0;k<N;k++)if(!W[k]){ld[k]=0;q.push(k);}
    for(let h=0;h<q.length;h++){const k=q[h],i=k%GW,j=(k-i)/GW;for(const [di,dj] of [[1,0],[-1,0],[0,1],[0,-1]]){const ni=i+di,nj=j+dj;if(ni<0||nj<0||ni>=GW||nj>=GH)continue;const n=nj*GW+ni;if(ld[n]>ld[k]+1){ld[n]=ld[k]+1;q.push(n);}}}
    const sea=new Int32Array(N).fill(-1);let ns=0;
    for(let k=0;k<N;k++){if(sea[k]>=0||!W[k]||ld[k]<2)continue;const st=[k];sea[k]=ns;while(st.length){const c=st.pop(),i=c%GW,j=(c-i)/GW;for(const [di,dj] of [[1,0],[-1,0],[0,1],[0,-1]]){const ni=i+di,nj=j+dj;if(ni<0||nj<0||ni>=GW||nj>=GH)continue;const n=nj*GW+ni;if(sea[n]<0&&W[n]&&ld[n]>=2){sea[n]=ns;st.push(n);}}}ns++;}
    // each port's berth: the nearest open-water cell (two cells off the shore)
    const ports=[];
    for(const z of G.zones){if(!z.port)continue;let best=-1,bd=1e9;const c0=cellOf(z.x,z.z),ci=c0%GW,cj=(c0-ci)/GW,R=Math.ceil((z.r+50)/CELL);
      for(let j=Math.max(0,cj-R);j<=Math.min(GH-1,cj+R);j++)for(let i=Math.max(0,ci-R);i<=Math.min(GW-1,ci+R);i++){const k=j*GW+i;if(sea[k]<0)continue;const d=Math.hypot(cx(k)-z.x,cz(k)-z.z);if(d<bd){bd=d;best=k;}}
      if(best>=0)ports.push({z,k:best,sea:sea[best]});}
    function seaRoute(a,b){const g=new Float64Array(N).fill(Infinity),from=new Int32Array(N).fill(-1),done=new Uint8Array(N);const H=[[0,a]];g[a]=0;
      const push=(f,k)=>{H.push([f,k]);let i=H.length-1;while(i>0){const p=(i-1)>>1;if(H[p][0]<=H[i][0])break;[H[p],H[i]]=[H[i],H[p]];i=p;}};
      const pop=()=>{const r=H[0],l=H.pop();if(H.length){H[0]=l;let i=0;for(;;){let x=2*i+1,y=x+1,m=i;if(x<H.length&&H[x][0]<H[m][0])m=x;if(y<H.length&&H[y][0]<H[m][0])m=y;if(m===i)break;[H[m],H[i]]=[H[i],H[m]];i=m;}}return r;};
      const tx=cx(b),tz=cz(b);
      while(H.length){const [,k]=pop();if(done[k])continue;done[k]=1;if(k===b)break;const i=k%GW,j=(k-i)/GW;
        for(let dj=-1;dj<=1;dj++)for(let di=-1;di<=1;di++){if(!di&&!dj)continue;const ni=i+di,nj=j+dj;if(ni<0||nj<0||ni>=GW||nj>=GH)continue;const n=nj*GW+ni;if(done[n]||sea[n]<0)continue;
          const ng=g[k]+(di&&dj?1.414:1)*CELL*(1+Math.max(0,5-ld[n])*.8);if(ng<g[n]){g[n]=ng;from[n]=k;push(ng+Math.hypot(cx(n)-tx,cz(n)-tz)*.9,n);}}}
      if(from[b]<0)return null;const cells=[];for(let k=b;k>=0;k=from[k]){cells.push(k);if(k===a)break;}cells.reverse();
      let pts=[];for(let i=0;i<cells.length;i+=3)pts.push([cx(cells[i]),cz(cells[i])]);pts.push([cx(b),cz(b)]);
      for(let r=0;r<3;r++){const o=[pts[0]];for(let i=0;i<pts.length-1;i++){const [x0,z0]=pts[i],[x1,z1]=pts[i+1];o.push([x0*.75+x1*.25,z0*.75+z1*.25],[x0*.25+x1*.75,z0*.25+z1*.75]);}o.push(pts[pts.length-1]);pts=o;}
      const cum=[0];for(let i=1;i<pts.length;i++)cum.push(cum[i-1]+Math.hypot(pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1]));return {pts,cum,len:cum[cum.length-1]};}
    const par=ports.map((_,i)=>i),f=i=>par[i]===i?i:(par[i]=f(par[i])),pairs=[],deg=ports.map(()=>0);
    for(let a=0;a<ports.length;a++)for(let b=a+1;b<ports.length;b++)if(ports[a].sea===ports[b].sea)pairs.push([Math.hypot(ports[a].z.x-ports[b].z.x,ports[a].z.z-ports[b].z.z),a,b]);
    pairs.sort((p,q)=>p[0]-q[0]);const lanes=[];
    for(const [d,a,b] of pairs)if(f(a)!==f(b)){par[f(a)]=f(b);lanes.push([a,b]);deg[a]++;deg[b]++;}
    for(const [d,a,b] of pairs)if(d<260&&(deg[a]<2||deg[b]<2)&&!lanes.some(l=>(l[0]===a&&l[1]===b)||(l[0]===b&&l[1]===a))){lanes.push([a,b]);deg[a]++;deg[b]++;}
    TRANSIT.sea=[];for(const [a,b] of lanes){const L=seaRoute(ports[a].k,ports[b].k);if(L&&L.len>30)TRANSIT.sea.push(L);}}
"""+s[j:]
rep("const TRANSIT={roads:[],rails:[],mask:","const TRANSIT={roads:[],rails:[],sea:[],mask:")
rep("if(!MOON&&(TRANSIT.roads.length||TRANSIT.rails.length)){","if(!MOON&&(TRANSIT.roads.length||TRANSIT.rails.length||TRANSIT.sea.length)){")
rep("  for(const g of [carG,truckG,locoG,wagG])g.scale(.8,.8,.8);","""  // little coastal freighter: hull, bow, a deck of containers and a bridge aft
  const shipG=merge([part(B(5.2,.7,1.6),W,0,.15,0),part(new THREE.CylinderGeometry(.01,.8,1.3,3).rotateZ(-HALF).scale(1,.54,1),W,3.2,.15,0),part(B(5.6,.12,1.7),Dk,0,.5,0),
    part(B(1.1,.55,.6),hexC(0xb8432e),.9,.83,.35),part(B(1.1,.55,.6),hexC(0x2f6f8f),.9,.83,-.35),part(B(1.1,.55,.6),hexC(0xd9a43a),-.3,.83,.35),part(B(1.1,.55,.6),hexC(0x4f7a3c),-.3,.83,-.35),
    part(B(1.1,.55,.6),hexC(0x9a9a92),.3,1.38,0),part(B(1,1.1,1.3),hexC(0xe8e2d4),-1.85,1.05,0),part(B(1.05,.2,1.35),Dk,-1.85,1.7,0),part(Cy(.14,.7,8),Dk,-2.2,2,0)]);
  for(const g of [carG,truckG,locoG,wagG])g.scale(.8,.8,.8);""")
rep("  const cars=[],trucks=[],trains=[];","  const cars=[],trucks=[],trains=[],ships=[];\n  for(const L of TRANSIT.sea){const n=L.len>260?2:1;for(let i=0;i<n;i++)ships.push({L,s:R()*L.len,v:2+R()*.8,dir:R()<.5?1:-1,wait:0,col:pick([0x3d4f5c,0x7a2e26,0x2a4a3a,0x5a5248])});}")
rep("  const imCar=mk(carG,cars,carCols),","  const imShip=mk(shipG,ships,null,1),imCar=mk(carG,cars,carCols),")
rep("    drive(cars,imCar,dt);drive(trucks,imTruck,dt);","""    drive(cars,imCar,dt);drive(trucks,imTruck,dt);
    // freighters: sail a lane, lie at the berth a while, sail back; they rock gently on the swell
    if(imShip){const t=performance.now()/1000;ships.forEach((c,i)=>{
      if(c.wait>0)c.wait-=dt;else{c.s+=c.v*c.dir*dt;if(c.s>=c.L.len||c.s<=0){c.s=Math.max(0,Math.min(c.L.len,c.s));c.dir*=-1;c.wait=8+Math.random()*10;}}
      const p=lineAt(c.L,c.s),ang=c.dir>0?p.ang:p.ang+Math.PI;q4.setFromEuler(new THREE.Euler(Math.sin(t*1.1+i)*.04,-ang,Math.sin(t*.8+i*2)*.03,'YXZ'));
      m4.compose(v3.set(p.x-Math.sin(ang)*1.2,-.05+Math.sin(t*1.3+i)*.06,p.z+Math.cos(ang)*1.2),q4,one);imShip.setMatrixAt(i,m4);});imShip.instanceMatrix.needsUpdate=true;}""")
# build menu: categories, then price
rep("""    const opts=z?FAC_KEYS.filter(k=>{const D=FAC[k];return !(D.only&&!D.only.includes(z.type))&&!(D.port&&!z.port);}):[];""",
"""    const all=z?FAC_KEYS.filter(k=>{const D=FAC[k];return !(D.only&&!D.only.includes(z.type))&&!(D.port&&!z.port);}):[];
    // grouped by kind (Military, Economy, Fortification), cheapest first
    const opts=all.filter(k=>FAC[k].slot===buildCat).sort((a,b)=>FAC[a].cost-FAC[b].cost||FAC[a].name.localeCompare(FAC[b].name));""")
rep("    sig='c'+(z?z.id:-1)+'|'+rov.length+'|'+(placing?placing.type:'')+'|'","    sig='c'+buildCat+(z?z.id:-1)+'|'+rov.length+'|'+(placing?placing.type:'')+'|'")
rep("""      for(const k of opts){const D=FAC[k],err=G.canPlaceType(ME,z.id,k);
        grid+=cb({attrs:`data-place="${k}"`""","""      for(const [c,l] of [['mil','Military'],['eco','Economy'],['fort','Fortification']]){const n=all.filter(k=>FAC[k].slot===c).length;
        grid+=`<button class="cbcat" data-cat="${c}" aria-pressed="${buildCat===c}">${l} <span class="num">${n}</span></button>`;}
      for(const k of opts){const D=FAC[k],err=G.canPlaceType(ME,z.id,k);
        grid+=cb({attrs:`data-place="${k}"`""")
rep("let roverZone=null,roverSig='';","let roverZone=null,roverSig='',buildCat='mil';")
rep("  const b=e.target.closest('.cb');if(!b||b.disabled)return;const d=b.dataset,c=selCtx();","  const cat=e.target.closest('.cbcat');if(cat){buildCat=cat.dataset.cat;cardSig='';refreshSel();return;}\n  const b=e.target.closest('.cb');if(!b||b.disabled)return;const d=b.dataset,c=selCtx();")
rep(".cb{position:relative;",".cbcat{grid-column:span 2;align-self:stretch;font-family:var(--f-display);font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;border:1px solid var(--line-hi);color:var(--dim);padding:2px 4px}\n.cbcat[aria-pressed=\"true\"]{background:var(--militia);color:var(--ink);border-color:var(--militia)}\n.cbcat .num{opacity:.7;margin-left:3px}\n#cardGrid:has(.cbcat){grid-template-rows:24px}\n.cb{position:relative;")
# changelog
rep("    'The command card has six columns, so every building fits without scrolling.',\n","    'The rover Build tab is sorted into Military, Economy and Fortification, cheapest first.',\n    'Little cargo ships now ply shipping lanes between the Ports on each sea, lying at each berth a while before sailing back.',\n")
open(p,'w').write(s)
