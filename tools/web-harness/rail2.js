const {chromium}=require('playwright');const fs=require('fs');
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760}});
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));
await p.goto('file:///tmp/rail.html');await p.waitForTimeout(1200);await p.click('#playBtn');await p.waitForTimeout(400);await p.click('#startGame');await p.waitForFunction(()=>window.__cam);
await p.waitForSelector('#planGo',{state:'visible',timeout:15000}).catch(()=>{});await p.click('#planGo').catch(()=>{});await p.click('button:has-text("3×")').catch(()=>{});
const i=+process.argv[2];
await p.evaluate(i=>{const T=__cam.TR;const L=T.rails[i];const S=L.stA;Object.assign(__cam.cam,{x:S.S[0],z:S.S[1],d:30,pitch:.75,yaw:Math.atan2(S.nx,S.nz)});__cam.applyCam();window.__L=L;},i);
for(let k=0;k<6;k++){await p.waitForTimeout(3500);await p.screenshot({path:`r2_${k}.png`,clip:{x:0,y:75,width:1280,height:370}});}
console.log(errs.slice(0,3));await b.close();})();
