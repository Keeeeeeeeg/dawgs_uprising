const SIM=require('./load.js')(process.argv[2]);
const only=process.argv[3];
function bfs(G,sx,sz){const {pass}=G.map,GW=G.GW,GH=G.GH,CELL=G.CELL,X0=G.X0,Z0=G.Z0;
  const d=new Float64Array(GW*GH).fill(1e9);const c=(x,z)=>Math.floor((z-Z0)/CELL)*GW+Math.floor((x-X0)/CELL);
  // seed: nearest pass cell
  let s=c(sx,sz);const q=[];
  for(let j=-10;j<=10;j++)for(let i=-10;i<=10;i++){const k=s+j*GW+i;if(k>=0&&k<pass.length&&pass[k]){q.push(k);d[k]=0;}}
  // dijkstra-lite: BFS with 8-neighbour approx via two passes (use simple BFS with diag cost by bucket)
  const D=[[1,0,1],[-1,0,1],[0,1,1],[0,-1,1],[1,1,1.414],[1,-1,1.414],[-1,1,1.414],[-1,-1,1.414]];
  // simple binary heap
  const H=q.map(k=>[0,k]);const push=(f,k)=>{H.push([f,k]);let i=H.length-1;while(i>0){const p=(i-1)>>1;if(H[p][0]<=H[i][0])break;[H[p],H[i]]=[H[i],H[p]];i=p;}};
  const pop=()=>{const r=H[0],l=H.pop();if(H.length){H[0]=l;let i=0;for(;;){let a=2*i+1,b=a+1,m=i;if(a<H.length&&H[a][0]<H[m][0])m=a;if(b<H.length&&H[b][0]<H[m][0])m=b;if(m===i)break;[H[m],H[i]]=[H[i],H[m]];i=m;}}return r;};
  while(H.length){const [f,k]=pop();if(f>d[k])continue;const i=k%GW,j=(k-i)/GW;
    for(const [di,dj,w] of D){const ni=i+di,nj=j+dj;if(ni<0||nj<0||ni>=GW||nj>=GH)continue;const nk=nj*GW+ni;if(!pass[nk])continue;const nf=f+w*CELL;if(nf<d[nk]){d[nk]=nf;push(nf,nk);}}}
  return (x,z)=>{let s=c(x,z),b=1e9;for(let j=-4;j<=4;j++)for(let i=-4;i<=4;i++){const k=s+j*GW+i;if(k>=0&&k<d.length)b=Math.min(b,d[k]);}return b;};
}
const VAL={town:1.15,fortress:1,airbase:1.1};
for(const [id,m] of Object.entries(SIM.MAPS)){
  if(m.hidden||(only&&id!==only))continue;
  const n=m.maxPlayers;const ai=[];for(let i=1;i<n;i++)ai.push({p:i-1});
  const G=SIM.createGame({map:id,mode:'ffa',ai,seed:1234});
  const hqs=G.zones.filter(z=>z.home!=null);
  const fns=hqs.map(h=>bfs(G,h.x,h.z));
  const reg=hqs.map(()=>({town:0,fortress:0,airbase:0,port:0,val:0,contest:0,n:0,plots:0,near:[]}));
  let unreachable=0;
  for(const z of G.zones){if(z.home!=null)continue;const ds=fns.map(f=>f(z.x,z.z));const sorted=ds.slice().sort((a,b)=>a-b);
    if(sorted[0]>=1e9){unreachable++;continue;}
    const b=ds.indexOf(sorted[0]);const R=reg[b];
    if(sorted[1]-sorted[0]<40){R.contest++;continue;} // contested: roughly equidistant
    R[z.type]++;R.n++;R.val+=VAL[z.type]+(z.port?.3:0);if(z.port)R.port++;R.near.push(Math.round(sorted[0]));}
  const hqInfo=hqs.map((h,i)=>{const others=hqs.filter(o=>o!==h).map(o=>fns[i](o.x,o.z));return Math.round(Math.min(...others));});
  const plots=G.zones.map(z=>z.plots.length+'/'+(z.type==='fortress'&&z.coastal?12:{hq:12,fortress:10,town:9,airbase:6}[z.type]));
  const short=G.zones.filter(z=>{const w=SIM.ZTYPES[z.type].slots;let n=w.mil+w.eco+w.fort;if(z.type==='fortress'&&z.coastal)n+=2;return z.spots.length<n;}).map(z=>z.name+'('+z.type+' '+z.plots.length+')');
  console.log(`\n== ${m.name} (${id}) players=${n} zones=${G.zones.length} mix=${JSON.stringify(m.mix)} unreachable=${unreachable}`);
  hqs.forEach((h,i)=>{const R=reg[i];console.log(`  ${h.name.padEnd(18)} own=${R.n} T${R.town} F${R.fortress} A${R.airbase} P${R.port} val=${R.val.toFixed(1)} contested-adj=${R.contest} nearestEnemyHQ=${hqInfo[i]} ports@HQ=${h.port?'Y':'n'} near=${R.near.sort((a,b)=>a-b).join(',')}`);});
  const vals=reg.map(r=>r.val);console.log(`  spread(max-min val)=${(Math.max(...vals)-Math.min(...vals)).toFixed(1)}  pads short: ${short.join(' ')||'none'}`);
}
