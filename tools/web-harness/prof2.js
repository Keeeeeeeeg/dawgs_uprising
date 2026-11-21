const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam(),get R(){return renderer;},get S(){return scene;}};");
fs.writeFileSync('/tmp/ct/pf.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760}});p.setDefaultTimeout(400000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file:///tmp/ct/pf.html');await p.waitForTimeout(1500);await p.evaluate(()=>document.querySelector('#playBtn').click());await p.waitForTimeout(3000);await p.evaluate(()=>document.querySelector('#startGame').click());await p.waitForFunction(()=>window.__cam,null,{timeout:120000});
await p.waitForTimeout(4000);
const r=await p.evaluate(()=>{const S=__cam.S,list=[];S.traverse(o=>{if(!(o.isMesh||o.isInstancedMesh||o.isPoints||o.isLine)||!o.visible)return;let v=o.visible,q=o.parent;while(q){if(!q.visible){v=false;break;}q=q.parent;}if(!v)return;
  const g=o.geometry;let t=g.index?g.index.count/3:(g.attributes.position?g.attributes.position.count/3:0);if(g.drawRange&&g.drawRange.count!==Infinity)t=Math.min(t,g.drawRange.count/3);const n=o.isInstancedMesh?o.count:1;
  let nm=o.name||'';let q2=o;while(!nm&&q2.parent){q2=q2.parent;nm=q2.name||'';}
  list.push({t:Math.round(t*n),n,sh:o.castShadow,mat:(o.material&&o.material.type)||'',nm,pos:o.isInstancedMesh?'inst':[o.position.x|0,o.position.y|0,o.position.z|0].join(',')});});
  list.sort((a,b)=>b.t-a.t);const tot=list.reduce((a,b)=>a+b.t,0),sh=list.filter(x=>x.sh).reduce((a,b)=>a+b.t,0);
  // group by geometry size buckets
  return {tot,sh,n:list.length,top:list.slice(0,30)};});
console.log(JSON.stringify(r,null,1));console.log(errs.slice(0,3));await b.close();})();
