const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam(),scene,meshes,THREE,zd:z=>zoneDecor(z)};");
fs.writeFileSync('/tmp/ct/h2.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:600,height:400}});p.setDefaultTimeout(400000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
await p.goto('file:///tmp/ct/h2.html');await p.waitForTimeout(1500);await p.evaluate(()=>document.querySelector('#playBtn').click());await p.waitForTimeout(3000);await p.evaluate(()=>document.querySelector('#startGame').click());await p.waitForFunction(()=>window.__cam,null,{timeout:120000});
await p.waitForTimeout(2000);
const r=await p.evaluate((L)=>{const {G,scene,meshes,THREE}=__cam;const out=[];
  for(const z of [G.zones[G.homes[0]],G.zones.find(q=>q.type==='fortress')]){z.owner=z.owner==null?0:z.owner;z.drill=L;}
  for(let i=0;i<12;i++)G.update(.25);for(const z of G.zones)if(z.drill>=2)__cam.zd(z);
  // let the renderer rebuild decor
  return 1;},+(process.argv[3]||2));
await p.waitForTimeout(4000);
const o=await p.evaluate(()=>{const {G,scene,meshes,THREE}=__cam;const out=[];const ray=new THREE.Raycaster();scene.updateMatrixWorld(true);
  const tm=new Set();for(const u of G.units)if(u.def.bturret){const m=meshes.get(u.id);if(m)m.traverse(o=>tm.add(o));}
  const objs=[];scene.traverse(o=>{if(o.isMesh&&!tm.has(o)&&o.visible)objs.push(o);});
  for(const u of G.units){if(!u.def.bturret)continue;const z=G.zones[u.tzone];
    ray.set(new THREE.Vector3(u.x,u.mountY+2.5,u.z),new THREE.Vector3(0,-1,0));ray.far=8;const h=ray.intersectObjects(objs,false)[0];
    const ga=Math.atan2(u.z-z.z,u.x-z.x);ray.set(new THREE.Vector3(u.x,u.mountY+.5,u.z),new THREE.Vector3(Math.cos(ga),0,Math.sin(ga)));ray.far=6;const f=ray.intersectObjects(objs,false)[0];
    const m=meshes.get(u.id);let bb=null;if(m){const B=new THREE.Box3().setFromObject(m);bb=[+B.min.y.toFixed(2),+B.max.y.toFixed(2)];}
    out.push({zt:z.type,t:u.type,my:+u.mountY.toFixed(2),floor:h?+h.point.y.toFixed(2):null,gap:h?+(u.mountY-h.point.y).toFixed(2):null,front:f?+f.distance.toFixed(2):null,frontTop:null,bb});}
  return out;});
for(const q of o)console.log(JSON.stringify(q));
const hide=`let c=document.querySelector('canvas');while(c&&c!==document.body){for(const e of c.parentElement.children)if(e!==c&&e.tagName!=='SCRIPT')e.style.visibility='hidden';c=c.parentElement;}`;await p.evaluate(hide);await p.setViewportSize({width:900,height:560});
for(const [n,i,yaw,pit,d] of [['g1',4,0.9,.42,7],['g2',4,3.6,.35,7],['g3',0,0.9,.4,7]]){await p.evaluate(([i,yaw,pit,d])=>{const {G}=__cam;const T=G.units.filter(u=>u.def.bturret);const u=T[i],c=__cam.cam,Y=u.mountY;c.x=u.x-Math.sin(yaw)*Y/Math.tan(pit);c.z=u.z-Math.cos(yaw)*Y/Math.tan(pit);c.yaw=yaw;c.pitch=pit;c.d=d+Y/Math.sin(pit);__cam.applyCam();},[i,yaw,pit,d]);await p.waitForTimeout(5000);await p.screenshot({path:'/tmp/ct/'+n+'.png'});}await b.close();})();
