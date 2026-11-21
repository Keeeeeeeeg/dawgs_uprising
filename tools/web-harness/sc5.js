const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace("const cam=Object.assign({pitch:.98},CAM0());","const cam=Object.assign({pitch:.98},CAM0());window.__cam={cam,get G(){return G;},applyCam:()=>applyCam()};");
fs.writeFileSync('/tmp/sc5.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760}});
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file:///tmp/sc5.html');await p.waitForTimeout(1200);await p.click('#playBtn');await p.waitForTimeout(400);await p.click('#startGame');await p.waitForFunction(()=>window.__cam);
// put a rifleman, light tank, medium tank side by side near home
await p.evaluate(()=>{const G=__cam.G;const z=G.zones.find(z=>z.home===0);G.factions[0].money=5000;G.factions[0].hr=500;
  for(const t of ['rifle','ltank','mtank','htank','tech'])G.applyCmd(0,{k:'recruit',type:t,zid:z.id,to:{x:z.x+20,z:z.z+4,amove:false}});
  __cam.cam.x=z.x+12;__cam.cam.z=z.z;__cam.cam.d=55;__cam.applyCam();});
await p.waitForTimeout(9000);await p.screenshot({path:'scale.png'});console.log(errs);await b.close();})();
