const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam(),FX:CITY_FX};");
fs.writeFileSync('/tmp/ct/h.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760}});p.setDefaultTimeout(120000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));
await p.goto('file:///tmp/ct/h.html');await p.waitForTimeout(1500);await p.evaluate(()=>document.querySelector('#playBtn').click());await p.waitForTimeout(3000);await p.evaluate(()=>document.querySelector('#startGame').click());await p.waitForFunction(()=>window.__cam);
await p.waitForTimeout(4000);
for(let k=0;k<1;k++){await p.evaluate(()=>{const E=__cam.FX[0],f=E.fly.find(f=>f.rot);const L=()=>{const P=f.g.position;Object.assign(__cam.cam,{x:P.x,z:P.z-P.y/Math.tan(1.05),d:P.y/Math.sin(1.05)+14,pitch:1.05});__cam.applyCam();requestAnimationFrame(L);};L();});
await p.waitForTimeout(150);console.log(await p.evaluate(()=>{const E=__cam.FX[0],f=E.fly.find(f=>f.rot);const P=f.g.position;return JSON.stringify({vis:E.fx.visible,par:!!f.g.parent,P:[P.x,P.y,P.z].map(v=>v.toFixed(1)),E:[E.x,E.z],cam:__cam.cam,n:__cam.FX.length});}));await p.screenshot({path:'heli'+k+'.png',clip:{x:340,y:130,width:600,height:420}});await p.waitForTimeout(2500);}
console.log(errs.slice(0,3));await b.close();})();
