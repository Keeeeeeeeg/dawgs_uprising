const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},get R(){return renderer;},get M(){return meshes;},rig:(u,m,dt)=>rigTick(u,m,dt)};");
fs.writeFileSync('/tmp/ct/fbr.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:900,height:600}});p.setDefaultTimeout(400000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file:///tmp/ct/fbr.html');await p.waitForTimeout(1500);await p.evaluate(()=>document.querySelector('#playBtn').click());await p.waitForTimeout(3000);await p.evaluate(()=>document.querySelector('#startGame').click());await p.waitForFunction(()=>window.__cam,null,{timeout:120000});
await p.waitForTimeout(2000);
const shots=await p.evaluate(async()=>{const G=__cam.G,u=G.spawnUnit('flagb',0,0,0);G.update(.25);await new Promise(r=>setTimeout(r,1500));const m=__cam.M.get(u.id);
  const R=__cam.R,sc=new THREE.Scene();sc.background=new THREE.Color(0x9aa8b0);sc.add(new THREE.AmbientLight(0xffffff,.6));const dl=new THREE.DirectionalLight(0xffffff,.8);dl.position.set(3,5,4);sc.add(dl);
  const par=m.parent;const out=[];
  const states=[['rest',()=>{u.waving=false;}],['wave',()=>{u.waving=true;}]];
  for(const [nm,f] of states){f();const R0=m.userData.rig;R0.px=u.x;R0.pz=u.z;for(let k=0;k<6;k++)__cam.rig(u,m,.1);
    const g=m.clone?m:null;sc.add(m);m.position.set(0,0,0);m.rotation.set(0,0,0);m.updateMatrixWorld(true);
    for(const [yaw,lab] of [[0,'side'],[1.57,'front']]){const cam=new THREE.PerspectiveCamera(35,1.5,.1,100);cam.position.set(Math.sin(yaw)*4.5,1.3,Math.cos(yaw)*4.5);cam.lookAt(-.3,1.0,0);R.setRenderTarget(null);R.render(sc,cam);out.push(R.domElement.toDataURL());}
    par.add(m);}
  return out;});
shots.forEach((d,i)=>fs.writeFileSync('/tmp/ct/fbr'+i+'.png',Buffer.from(d.split(',')[1],'base64')));console.log(errs);await b.close();})();
