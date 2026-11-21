// Offline map balancer: picks HQ sites and places/types every base so each HQ gets a fair share.
// node balance.js <html> [mapId] -> writes balanced.json
const SIM=require('./load.js')(process.argv[2]);const only=process.argv[3];
const fs=require('fs');
const SEED=20261017;
const ZR={hq:16,fortress:11,town:10,airbase:13};
const VAL={town:1.15,fortress:1,airbase:1.1};
function rng(a){return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};}
function segDist(px,pz,ax,az,bx,bz){const dx=bx-ax,dz=bz-az;let t=((px-ax)*dx+(pz-az)*dz)/(dx*dx+dz*dz||1);t=Math.max(0,Math.min(1,t));return Math.hypot(px-(ax+dx*t),pz-(az+dz*t));}
function dijkstra(T,srcCells){const {pass,GW,GH,CELL}=T;const d=new Float64Array(GW*GH).fill(1e9);
  const hk=[],hf=[];const push=(f,k)=>{hk.push(k);hf.push(f);let i=hk.length-1;while(i>0){const p=(i-1)>>1;if(hf[p]<=hf[i])break;[hf[p],hf[i]]=[hf[i],hf[p]];[hk[p],hk[i]]=[hk[i],hk[p]];i=p;}};
  const pop=()=>{const k=hk[0],f=hf[0];const lk=hk.pop(),lf=hf.pop();if(hk.length){hk[0]=lk;hf[0]=lf;let i=0;for(;;){let a=2*i+1,b=a+1,m=i;if(a<hk.length&&hf[a]<hf[m])m=a;if(b<hk.length&&hf[b]<hf[m])m=b;if(m===i)break;[hf[m],hf[i]]=[hf[i],hf[m]];[hk[m],hk[i]]=[hk[i],hk[m]];i=m;}}return [f,k];};
  for(const k of srcCells){d[k]=0;push(0,k);}
  const D=[[1,0,1],[-1,0,1],[0,1,1],[0,-1,1],[1,1,1.4142],[1,-1,1.4142],[-1,1,1.4142],[-1,-1,1.4142]];
  while(hk.length){const [f,k]=pop();if(f>d[k])continue;const i=k%GW,j=(k-i)/GW;
    for(const [a,b,w] of D){const ni=i+a,nj=j+b;if(ni<0||nj<0||ni>=GW||nj>=GH)continue;const nk=nj*GW+ni;if(!pass[nk])continue;
      if(a&&b&&(!pass[j*GW+ni]||!pass[nj*GW+i]))continue;const nf=f+w*CELL;if(nf<d[nk]){d[nk]=nf;push(nf,nk);}}}
  return d;}
function analyseTerrain(m){
  const T=SIM.__terrain(m,SEED,[]);const {pass,GW,GH,CELL,X0,Z0,hv}=T;const VW=GW+1;
  const cellOf=(x,z)=>Math.floor((z-Z0)/CELL)*GW+Math.floor((x-X0)/CELL);
  const frac=(x,z,r)=>{let n=0,p=0;for(let dz=-r;dz<=r;dz+=CELL)for(let dx=-r;dx<=r;dx+=CELL){if(dx*dx+dz*dz>r*r)continue;n++;const i=Math.floor((x+dx-X0)/CELL),j=Math.floor((z+dz-Z0)/CELL);if(i>=0&&j>=0&&i<GW&&j<GH&&pass[j*GW+i])p++;}return p/n;};
  const hAt=(x,z)=>{const i=Math.max(0,Math.min(GW,Math.round((x-X0)/CELL))),j=Math.max(0,Math.min(GH,Math.round((z-Z0)/CELL)));return hv[j*VW+i];};
  const srcNear=(x,z,r)=>{const out=[];for(let dz=-r;dz<=r;dz+=CELL)for(let dx=-r;dx<=r;dx+=CELL){if(dx*dx+dz*dz>r*r)continue;const k=cellOf(x+dx,z+dz);if(k>=0&&k<pass.length&&pass[k])out.push(k);}return out;};
  return Object.assign(T,{cellOf,frac,hAt,srcNear});
}
function candidates(m,T,o){
  const out=[];const hw=m.W/2,hh=m.H/2;const step=o.step||10;
  for(let z=-hh+42;z<=hh-42;z+=step)for(let x=-Math.floor((hw-42)/step)*step;x<=hw-42;x+=step){
    const h=T.hAt(x,z);if(h<.9||h>4.8)continue;
    if(SIM.landRaw(m,x,z)<.1)continue;
    if(m.necks.some(n=>segDist(x,z,n.a[0],n.a[1],n.b[0],n.b[1])<24))continue;
    const f14=T.frac(x,z,14);if(f14<.8)continue;const f24=T.frac(x,z,24);if(f24<.5)continue;
    out.push({x,z,f24,hqOK:f24>.8&&T.frac(x,z,30)>.72});
  }
  for(const c of out){c.coast={};for(const t of ['hq','fortress','town'])c.coast[t]=SIM.coastDist(m,c.x,c.z,ZR[t])<Infinity;c.coast.airbase=false;}
  return out;
}
function pickHQs(m,T,cands,k,R,cfg){
  let pool=cands.slice();const hqAllowed=c=>c.hqOK&&!(cfg.fixed||[]).some(f=>Math.hypot(f.x-c.x,f.z-c.z)<150);
  // farthest-point sample of up to 70
  const samp=[];pool.sort((a,b)=>a.x-b.x);samp.push(pool[0]);
  while(samp.length<Math.min(90,pool.length)){let b=null,bd=-1;for(const c of pool){let d=1e9;for(const s of samp)d=Math.min(d,Math.hypot(c.x-s.x,c.z-s.z));if(d>bd){bd=d;b=c;}}samp.push(b);}
  const DF=samp.map(s=>dijkstra(T,T.srcNear(s.x,s.z,8)));
  const n=samp.length,M=[...Array(n)].map((_,i)=>samp.map(s=>DF[i][T.cellOf(s.x,s.z)]));
  const water=!m.noWater;
  const score=set=>{let mn=1e9;const nn=set.map(i=>{let q=1e9;for(const j of set)if(j!==i)q=Math.min(q,M[i][j]);mn=Math.min(mn,q);return q;});
    if(mn>=1e8)return -1e9;
    const terr=set.map(()=>0);for(let q=0;q<n;q++){let b=-1,bd=1e9;for(let a=0;a<set.length;a++){const v=M[set[a]][q];if(v<bd){bd=v;b=a;}}if(b>=0&&bd<1e8)terr[b]++;}
    const tr=Math.max(...terr)-Math.min(...terr);const coastN=set.filter(i=>samp[i].coast.hq).length;
    return mn+.4*nn.reduce((a,b)=>a+b,0)/nn.length-1.4*(Math.max(...nn)-Math.min(...nn))-tr*1600/n+(water?(coastN===k?60:coastN===0?0:-50*Math.min(coastN,k-coastN)):0);};
  let best=null,bs=-1e18;
  for(let t=0;t<3000;t++){const okI=[];for(let i=0;i<n;i++)if(hqAllowed(samp[i]))okI.push(i);let set=[okI[Math.floor(R()*okI.length)]];
    while(set.length<k){let b=-1,bd=-1;for(const i of okI){if(set.includes(i))continue;let q=1e9;for(const j of set)q=Math.min(q,M[i][j]);q*=.8+R()*.4;if(q>bd&&q<1e8){bd=q;b=i;}}if(b<0)break;set.push(b);}
    if(set.length<k)continue;
    let s=score(set);
    for(let it=0;it<150;it++){const a=Math.floor(R()*k),b=okI[Math.floor(R()*okI.length)];if(set.includes(b))continue;const s2=set.slice();s2[a]=b;const q=score(s2);if(q>s){s=q;set=s2;}}
    if(s>bs){bs=s;best=set;}}
  return best.map(i=>samp[i]);
}
function balance(id,m,cfg){
  const R=rng(cfg.seed||id.length*7919+13);
  const T=analyseTerrain(m);const cands=candidates(m,T,{});
  const k=m.maxPlayers;
  let hqs;
  if(cfg.fixedHQ)hqs=m.slots.map(i=>{const z=m.zones[i];const c={x:z[2],z:z[3],name:z[0]};c.coast={hq:SIM.coastDist(m,c.x,c.z,16)<Infinity};return c;});
  else hqs=pickHQs(m,T,cands,k,R,cfg);
  const HD=hqs.map(h=>dijkstra(T,T.srcNear(h.x,h.z,8)));
  for(const c of cands){c.d=HD.map(D=>{let b=1e9;for(const q of T.srcNear(c.x,c.z,5))b=Math.min(b,D[q]);return b;});}
  let pool=cands.filter(c=>c.d.every(v=>v<1e8)&&hqs.every(h=>Math.hypot(h.x-c.x,h.z-c.z)>=(cfg.hqGap||70)));
  const SP=cfg.spacing||54;
  // mirror support (Twin Reach): west-side vars mirrored to the east; centre vars sit on x=0
  const mirror=!!cfg.mirror;
  let groups;
  if(mirror){const west=pool.filter(c=>c.x<=-SP/2),mid=pool.filter(c=>Math.abs(c.x)<1);
    const byKey=new Map(pool.map(c=>[c.x+','+c.z,c]));
    for(const c of west)c.twin=byKey.get((-c.x)+','+c.z)||null;
    groups=[{pool:west.filter(c=>c.twin),n:cfg.side,types:cfg.sideTypes},{pool:mid,n:cfg.mid,types:cfg.midTypes}];}
  else{const n=cfg.n;const nAir=cfg.air!=null?cfg.air:Math.max(2,Math.round(n*.16)),nFort=Math.round(n*.34);
    const types=[];for(let i=0;i<nAir;i++)types.push('airbase');for(let i=0;i<nFort;i++)types.push('fortress');while(types.length<n)types.push('town');
    groups=[{pool,n,types}];}
  // vars
  let vars=[];
  for(const [gi,g] of groups.entries())g.types.forEach(t=>vars.push({g:gi,t,c:null}));
  const fixed=(cfg.fixed||[]).map(f=>{let b=null,bd=1e9;for(const c of cands){const q=Math.hypot(c.x-f.x,c.z-f.z);if(q<bd){bd=q;b=c;}}return {c:b,t:f.t};});
  const expand=vs=>{const out=fixed.slice();for(const v of vs){out.push({c:v.c,t:v.t});if(mirror&&v.g===0)out.push({c:v.c.twin,t:v.t});}return out;};
  const spacingOK=(vs)=>{const e=expand(vs);for(let i=0;i<e.length;i++)for(let j=i+1;j<e.length;j++)if(Math.hypot(e[i].c.x-e[j].c.x,e[i].c.z-e[j].c.z)<SP)return false;return true;};
  // init
  for(let tries=0;;tries++){let ok=true;vars.forEach(v=>v.c=null);
    for(const v of vars){const P=groups[v.g].pool;let placed=false;for(let t=0;t<400;t++){const c=P[Math.floor(R()*P.length)];v.c=c;
        const e=expand(vars.filter(q=>q.c));let bad=false;for(const a of e){for(const b of e){if(a!==b&&a.c===b.c&&a!==b){}}}
        if(spacingOK(vars.filter(q=>q.c))){placed=true;break;}}
      if(!placed){ok=false;break;}}
    if(ok)break;if(tries>200)throw new Error(id+': cannot place');}
  // coverage samples
  const cov=[];for(const c of cands)if(Math.round(c.x/30)*30===c.x||true){if(!cov.some(q=>Math.hypot(q.x-c.x,q.z-c.z)<30))cov.push(c);}
  const isPort=e=>(e.t==='town'||e.t==='fortress')&&e.c.coast[e.t];
  const water=!m.noWater;
  function evalJ(vs,detail){
    const e=expand(vs);const K=hqs.length;
    const own=new Array(K).fill(0),reach=new Array(K).fill(0),nPort=new Array(K).fill(1e3),nAir=new Array(K).fill(1e3),nd=[...Array(K)].map(()=>[]);
    const ownT=[...Array(K)].map(()=>({town:0,fortress:0,airbase:0,port:0}));
    for(const z of e){const d=z.c.d,v=VAL[z.t]+(isPort(z)?.3:0);let s=0;const w=d.map(q=>Math.exp(-q/30));const mn=Math.min(...d);for(let h=0;h<K;h++)w[h]=Math.exp(-(d[h]-mn)/30);s=w.reduce((a,b)=>a+b,0);
      for(let h=0;h<K;h++){own[h]+=v*w[h]/s;ownT[h][z.t]+=w[h]/s;if(isPort(z))ownT[h].port+=w[h]/s;reach[h]+=v*Math.exp(-d[h]/130);nd[h].push(d[h]);
        if(isPort(z))nPort[h]=Math.min(nPort[h],d[h]);if(z.t==='airbase')nAir[h]=Math.min(nAir[h],d[h]);}}
    const Rr=a=>(Math.max(...a)-Math.min(...a))/(a.reduce((x,y)=>x+y,0)/a.length||1),rg=a=>Math.max(...a)-Math.min(...a);
    nd.forEach(a=>a.sort((x,y)=>x-y));
    const n1=nd.map(a=>a[0]),n2=nd.map(a=>a[1]),n3=nd.map(a=>a[2]);
    let J=6*Rr(own)+2*Rr(reach)+3*rg(nAir)/120+1.5*rg(n1)/50+1.5*rg(n2)/60+1*rg(n3)/70;
    if(water){const np=nPort.map((v,h)=>hqs[h].coast.hq?Math.min(v,cfg.portSoft||150):v);J+=1.4*rg(np)/120+.8*rg(ownT.map(o=>o.port));for(const v of np)J+=Math.max(0,v-140)/120;}
    for(const v of nAir)J+=Math.max(0,v-150)/80;
    J+=.8*rg(ownT.map(o=>o.town))+.8*rg(ownT.map(o=>o.fortress));
    J+=Math.max(0,n1.reduce((a,b)=>a+b,0)/K-95)/40;
    // coverage
    let cp=0;for(const c of cov){let dm=1e9;for(const z of e)dm=Math.min(dm,Math.hypot(z.c.x-c.x,z.c.z-c.z));for(const h of hqs)dm=Math.min(dm,Math.hypot(h.x-c.x,h.z-c.z));cp+=Math.max(0,dm-80)/80;}
    J+=1.2*cp/cov.length;
    if(detail)return {J,own,reach,nPort,nAir,n1,n2,ownT};
    return J;}
  // SA
  const near=new Map();for(const g of groups)for(const c of g.pool)near.set(c,g.pool.filter(q=>Math.hypot(q.x-c.x,q.z-c.z)<70));
  let J=evalJ(vars),best=vars.map(v=>({...v})),bJ=J;const IT=cfg.iters||120000;
  for(let it=0;it<IT;it++){const Tm=.25*Math.pow(.002/.25,it/IT);const r=R();let undo;
    if(r<.7){const v=vars[Math.floor(R()*vars.length)];const P=r<.58?near.get(v.c):groups[v.g].pool;const c=P[Math.floor(R()*P.length)];if(c===v.c)continue;const old=v.c;v.c=c;if(!spacingOK(vars)){v.c=old;continue;}undo=()=>{v.c=old;};}
    else{const a=vars[Math.floor(R()*vars.length)],b=vars[Math.floor(R()*vars.length)];if(a===b||a.t===b.t||a.g!==b.g)continue;[a.t,b.t]=[b.t,a.t];undo=()=>{[a.t,b.t]=[b.t,a.t];};}
    const J2=evalJ(vars);if(J2<=J||R()<Math.exp((J-J2)/Tm)){J=J2;if(J<bJ){bJ=J;best=vars.map(v=>({...v}));}}else undo();}
  vars=best;const det=evalJ(vars,true);
  return {hqs,zones:expand(vars),det,T};
}
// ---- names ----
const CAT={airbase:/air|field|base|rest|eagle|hawk|kestrel|wing|sky|tern|gull|crow|raven|sparrow/i,
  port:/port|harbou?r|bay|cove|wharf|quay|sound|cay|key|mouth|ferry|haven|landing|tide|oars|ketch|anchor|beach|shore|marsh|reach|lagoon|sluice|lock|weir|pike|herring|row/i,
  fortress:/fort|gate|watch|keep|tor\b|rock|crag|point|head|spur|hold|cliff|ridge|pass|post|crest|cairn|stone|wall|tusk|fang|jaw|barb|prong|brand|pyre|bastion|redoubt|march/i};
function nameZones(list,zones,hqNames){const used=new Set(hqNames);const out=[];
  const pick=(re,avoid)=>{for(const n of list){if(used.has(n))continue;if(re&&!re.test(n))continue;if(avoid&&avoid.some(a=>a.test(n)))continue;used.add(n);return n;}return null;};
  const order=zones.map((z,i)=>i).sort((a,b)=>({airbase:0,port:1,fortress:2,town:3}[zones[a].cat]-{airbase:0,port:1,fortress:2,town:3}[zones[b].cat]));
  for(const i of order){const c=zones[i].cat;const others=Object.keys(CAT).filter(k=>k!==c).map(k=>CAT[k]);
    out[i]=(c!=='town'&&pick(CAT[c]))||pick(null,others)||pick(null)||('Site '+i);}
  return out;}
const CFG={
  ventora:{n:19,iters:70000},
  twinreach:{fixedHQ:true,mirror:true,side:8,mid:5,sideTypes:['airbase','airbase','fortress','fortress','fortress','town','town','town'],midTypes:['airbase','fortress','fortress','town','town'],iters:90000},
  brine:{n:17,air:4},thorn:{n:17},delta:{n:18},coral:{n:16,seed:11,fixed:[{x:0,z:0,t:"fortress"}]},fang:{n:17},ember:{n:17,air:4,fixed:[{x:0,z:0,t:"airbase"}]},
};
const res={};
for(const [id,cfg] of Object.entries(CFG)){if(only&&id!==only)continue;const m=SIM.MAPS[id];const t0=Date.now();
  const r=balance(id,m,cfg);
  // names
  let list=m.zones.map(z=>z[0]);const ns=SIM.NAMESETS[id];if(ns)list=ns.slice();
  const hqNames=cfg.fixedHQ?r.hqs.map(h=>h.name):(()=>{const pool=m.slots.map(i=>m.zones[i][0]);return r.hqs.map((h,i)=>pool[i]||list[i]);})();
  const zl=r.zones.map(z=>({cat:z.t==='airbase'?'airbase':(z.t!=='airbase'&&z.c.coast[z.t])?'port':z.t}));
  const names=nameZones(list.concat(id==='ventora'?['Gullmere','Tarrow','Copperhill','Wexley']:[]),zl,hqNames);
  const zones=r.hqs.map((h,i)=>[hqNames[i],'hq',Math.round(h.x),Math.round(h.z)]).concat(r.zones.map((z,i)=>[names[i],z.t,Math.round(z.c.x),Math.round(z.c.z)]));
  res[id]={slots:r.hqs.map((h,i)=>i),zones};
  const d=r.det,f=a=>a.map(v=>v.toFixed(1)).join(' ');
  console.log(`${id} J=${d.J.toFixed(3)} own=[${f(d.own)}] reach=[${f(d.reach)}] nPort=[${f(d.nPort)}] nAir=[${f(d.nAir)}] n1=[${f(d.n1)}] n2=[${f(d.n2)}] hqCoast=${r.hqs.map(h=>h.coast.hq?'Y':'n').join('')} ${Date.now()-t0}ms`);
}
const file='balanced.json';let prev={};try{prev=JSON.parse(fs.readFileSync(file,'utf8'));}catch(e){}
fs.writeFileSync(file,JSON.stringify(Object.assign(prev,res)));
