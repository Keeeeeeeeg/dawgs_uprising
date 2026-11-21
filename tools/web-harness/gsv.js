const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={get meshes(){return meshes;},cam,get G(){return G;},applyCam:()=>applyCam(),proj:(x,y,z)=>proj(x,y,z)};");
fs.writeFileSync('/tmp/ct/fv.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760},deviceScaleFactor:1.5});p.setDefaultTimeout(400000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());const errs=[];p.on('pageerror',e=>console.log('ERR',e.message,(e.stack||'').split('\n')[1]));
await p.goto('file:///tmp/ct/fv.html');await p.waitForTimeout(1500);
await p.evaluate(()=>{const b=[...document.querySelectorAll('button')].find(b=>/skirmish/i.test(b.textContent));if(b)b.click();});await p.waitForTimeout(800);
await p.evaluate(()=>{const b=[...document.querySelectorAll('button')].find(b=>/^\s*(start|begin|deploy|fight)/i.test(b.textContent)&&b.offsetParent);if(b)b.click();});
await p.waitForFunction(()=>window.__cam&&window.__cam.G,null,{timeout:300000});await p.waitForTimeout(9000);
const info=await p.evaluate(()=>{const G=__cam.G,z=G.zones.find(z=>z.type==='hq'&&z.owner===0);window.FZ=z;
  const us=[];for(let i=0;i<10;i++){const q=G.wallWorld(z,4+i*.5,(i-5)*.8);const u=G.spawnUnit('rifle',z.owner==null?0:z.owner,q.x,q.z);us.push(u.id);}
  if(z.owner!==0){z.owner=0;}
  z.drill=3;const r=G.applyCmd(0,{k:'manpos',zid:z.id,ids:us,posts:[0,1,2,3,4,5,6,40,41,42],face:null});return {name:z.name,owner:z.owner,r,gate:z.gate};});
console.log(JSON.stringify(info));
const info2=await p.evaluate(()=>{const G=__cam.G,out=[];for(const kind of ['hq','fortress']){const z=G.zones.find(o=>o.type===kind&&o.owner===0)||G.zones.find(o=>o.type===kind);z.owner=0;z.drill=3;
  const L=G.manLayout(z),idx=[];L.walls.forEach((w,i)=>{if(w[4]==='s'||(Math.abs(w[2])<6&&w[0]>0))idx.push(i);});
  const us=[];for(let k=0;k<idx.length;k++){const q=G.wallWorld(z,4,(k-idx.length/2)*.7);us.push(G.spawnUnit('rifle',0,q.x,q.z).id);}
  G.applyCmd(0,{k:'manpos',zid:z.id,ids:us,posts:idx,face:null});const e=G.wallWorld(z,30,0);const HF=1;const en=G.spawnUnit('rifle',HF,e.x,e.z);en.hp=en.maxHp=1e6;
  out.push({kind,id:z.id,n:idx.length,flags:idx.map(i=>L.walls[i][4]).join('')});}window.__ZS=out;return out;});
console.log(JSON.stringify(info2));
for(let k=0;k<30;k++){await p.evaluate(()=>{for(let i=0;i<4;i++)__cam.G.update(.1);});await p.waitForTimeout(80);}
for(const [n,kind] of [['a','hq'],['b','fortress']]){await p.evaluate((kind)=>{const G=__cam.G,z=G.zones[__ZS.find(q=>q.kind===kind).id],gu=z.gateU,dx=gu.x-z.x,dz=gu.z-z.z;const c=__cam.cam;c.x=gu.x;c.z=gu.z;c.d=22;c.pitch=.33;c.yaw=Math.atan2(dx,dz)+.35;__cam.applyCam();for(let i=0;i<2;i++)G.update(.1);},kind);await p.waitForTimeout(2500);await p.screenshot({path:'/tmp/ct/gs_'+n+'.png'});}
console.log(JSON.stringify(errs.slice(0,8)));await b.close();})();
