const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam(),FX:CITY_FX};");
fs.writeFileSync('/tmp/ct/h.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1400,height:1000}});p.setDefaultTimeout(400000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));
await p.goto('file:///tmp/ct/h.html');await p.waitForTimeout(1500);await p.evaluate(()=>document.querySelector('#playBtn').click());await p.waitForTimeout(3000);await p.evaluate(()=>document.querySelector('#startGame').click());await p.waitForFunction(()=>window.__cam);
await p.waitForTimeout(8000);
await p.evaluate(()=>{const G=__cam.G;const z=G.zones.filter(z=>z.type==='town'&&z.city)[0];const p=.7;const L=()=>{Object.assign(__cam.cam,{x:z.x-Math.sin(.35)*6,z:z.z-Math.cos(.35)*6,d:85,pitch:.62,yaw:.35});__cam.applyCam();requestAnimationFrame(L);};L();});
for(let k=0;k<1;k++){await p.waitForTimeout(k?4000:3000);await p.screenshot({path:'cc'+k+'.png',clip:{x:0,y:60,width:1400,height:560},timeout:400000});console.log('k',k);}
console.log(errs.slice(0,3));await b.close();})();