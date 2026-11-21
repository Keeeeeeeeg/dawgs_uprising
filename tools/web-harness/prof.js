const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam(),get R(){return renderer;},get S(){return scene;}};");
fs.writeFileSync('/tmp/ct/pf.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760}});p.setDefaultTimeout(400000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file:///tmp/ct/pf.html');await p.waitForTimeout(1500);await p.evaluate(()=>document.querySelector('#playBtn').click());await p.waitForTimeout(3000);await p.evaluate(()=>document.querySelector('#startGame').click());await p.waitForFunction(()=>window.__cam,null,{timeout:120000});
await p.waitForTimeout(4000);
const r=await p.evaluate(async()=>{const out=[];const R=__cam.R,S=__cam.S,c=__cam.cam,G=__cam.G;const z=G.zones.find(q=>q.owner===0);
  // scene census
  let meshes=0,vis=0,tris=0,shadowCasters=0;const byMat=new Map();S.traverse(o=>{if(o.isMesh||o.isInstancedMesh){meshes++;if(o.visible){vis++;if(o.castShadow)shadowCasters++;}}});
  for(const [d,pitch] of [[60,.98],[160,.98],[420,1.1]]){c.x=z.x;c.z=z.z;c.d=d;c.pitch=pitch;__cam.applyCam();await new Promise(r=>setTimeout(r,2500));R.info.autoReset=false;R.info.reset();await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
    out.push({d,calls:R.info.render.calls,tris:R.info.render.triangles,geos:R.info.memory.geometries,tex:R.info.memory.textures,progs:R.info.programs.length});R.info.autoReset=true;}
  return {meshes,vis,shadowCasters,out};});
console.log(JSON.stringify(r,null,1));console.log(errs.slice(0,3));await b.close();})();
