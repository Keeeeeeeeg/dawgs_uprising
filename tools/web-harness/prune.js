// greedily drop coves that change territory ownership or starve pads
const fs=require('fs');const file=process.argv[2];
const src=fs.readFileSync('/home/claude/tools/analyze.js','utf8');
const bfs=new Function(src.slice(src.indexOf('function bfs'),src.indexOf('const VAL'))+'return bfs;')();
const h=fs.readFileSync(file,'utf8');const s=h.indexOf('const SIM = (function');const e=h.indexOf('})();',h.indexOf('return {BALANCE,baseMix'))+5;
const SIM=new Function(h.slice(s,e).replace('return {BALANCE,baseMix','return {COVE_SKIP,BALANCE,baseMix')+'\nreturn SIM;')();
function sig(id){const m=SIM.MAPS[id];const n=m.maxPlayers;const ai=[];for(let i=1;i<n;i++)ai.push({p:i-1});
  const G=SIM.createGame({map:id,mode:'ffa',ai,seed:1234});const hqs=G.zones.filter(z=>z.home!=null);const fns=hqs.map(h=>bfs(G,h.x,h.z));
  const own=G.zones.map(z=>{if(z.home!=null)return 'H';const ds=fns.map(f=>f(z.x,z.z)),so=ds.slice().sort((a,b)=>a-b);if(so[0]>=1e9)return 'U';if(so[1]-so[0]<40)return 'C';return ds.indexOf(so[0]);});
  const short=G.zones.filter(z=>{const w=SIM.ZTYPES[z.type].slots;let k=w.mil+w.eco+w.fort;if(z.type==='fortress'&&z.coastal)k+=2;return (z.spots||z.plots).length<k*.5;}).length;
  return {own,short,coves:G.zones.map((z,i)=>z.cove?i:-1).filter(i=>i>=0)};}
const diff=(a,b)=>a.own.reduce((n,v,i)=>n+(v!==b.own[i]),0)+a.short*2;
const out={};
for(const id of Object.keys(SIM.MAPS)){const m=SIM.MAPS[id];if(m.hidden||m.noWater||(process.argv[3]&&id!==process.argv[3]))continue;
  SIM.COVE_SKIP[id]=[];const all=sig(id);if(!all.coves.length)continue;
  SIM.COVE_SKIP[id]=all.coves.slice();const base=sig(id);base.short=0;
  // add coves one at a time, keep each that leaves ownership and pads untouched
  const keep=[];for(const c of all.coves){SIM.COVE_SKIP[id]=all.coves.filter(x=>x!==c&&!keep.includes(x));const t=sig(id);if(diff(t,base)===0)keep.push(c);}
  SIM.COVE_SKIP[id]=all.coves.filter(x=>!keep.includes(x));const fin=sig(id);
  console.log(id,'coves',all.coves.length,'kept',keep.length,'final diff',diff(fin,base));
  out[id]=SIM.COVE_SKIP[id];}
console.log(JSON.stringify(out));
