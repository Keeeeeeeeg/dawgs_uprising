const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam(),meshes,facMesh:(t)=>facMesh(t,1,M.metal),SS:STRUCT_SCALE,zoneVis,THREE};");
fs.writeFileSync('/tmp/meas.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:800,height:500}});
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
await p.goto('file:///tmp/meas.html');await p.waitForTimeout(1200);await p.click('#playBtn');await p.waitForTimeout(400);await p.click('#startGame');await p.waitForFunction(()=>window.__cam);
await p.click('#planGo').catch(()=>{});
const out=await p.evaluate(async()=>{const C=__cam,G=C.G,T=C.THREE,res={units:{},facs:{},zones:{}};const z0=G.zones[G.homes[0]];
  const types=['rifle','mg','at','rover','tech','ltank','mtank','htank','spg','how','flak','sam','lheli','heli','airship','boat','monitor','intc','cas','bomb'];
  const us={};for(const t of types){try{const u=G.spawnUnit(t,0,z0.x+40,z0.z+40);us[t]=u;}catch(e){}}
  await new Promise(r=>setTimeout(r,1500));
  for(const t in us){const m=C.meshes.get(us[t].id);if(!m)continue;const bx=new T.Box3().setFromObject(m),s=new T.Vector3();bx.getSize(s);res.units[t]={L:+Math.max(s.x,s.z).toFixed(2),W:+Math.min(s.x,s.z).toFixed(2),H:+s.y.toFixed(2)};}
  for(const f of Object.keys(G.FACILITIES)){try{const m=C.facMesh(f);m.scale.setScalar(C.SS);const bx=new T.Box3().setFromObject(m),s=new T.Vector3();bx.getSize(s);res.facs[f]={L:+Math.max(s.x,s.z).toFixed(2),W:+Math.min(s.x,s.z).toFixed(2),H:+s.y.toFixed(2)};}catch(e){}}
  for(const ty of ['hq','fortress','town','airbase']){const z=ty==='hq'?z0:G.zones.find(q=>q.type===ty);const v=C.zoneVis[z.id];const bx=new T.Box3().setFromObject(v.g),s=new T.Vector3();bx.getSize(s);res.zones[ty]={L:+Math.max(s.x,s.z).toFixed(1),W:+Math.min(s.x,s.z).toFixed(1),H:+s.y.toFixed(1),r:z.r,wall:z.wall?{walkY:ty==='hq'?2.91:2.4,keepTop:z.wall.keepTop,thick:z.wall.thick}:null};}
  return res;});
fs.writeFileSync('measure.json',JSON.stringify(out,null,1));console.log(JSON.stringify(out));await b.close();})();
