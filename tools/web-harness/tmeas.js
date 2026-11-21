const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760}});
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file:///tmp/t_dawgs.html');await p.waitForTimeout(1200);await p.click('#playBtn');await p.waitForTimeout(400);
const t0=Date.now();await p.click('#startGame');await p.waitForFunction(()=>window.__cam,null,{timeout:60000});console.log('boot ms',Date.now()-t0);
await p.evaluate(()=>{__cam.cam.x=0;__cam.cam.z=0;__cam.cam.d=330;__cam.applyCam();});await p.waitForTimeout(1500);await p.screenshot({path:'tr_wide.png'});
console.log(errs);await b.close();})();
