const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam(),sel:(id)=>{selZone=id;}};");
fs.writeFileSync('/tmp/sel.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760}});
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));
await p.goto('file:///tmp/sel.html');await p.waitForTimeout(1200);await p.click('#playBtn');await p.waitForTimeout(400);await p.click('#startGame');await p.waitForFunction(()=>window.__cam);
await p.click('#planGo').catch(()=>{});
for(const [t,f] of [['hq','selhq'],['fortress','selfort'],['town','seltown']]){
  await p.evaluate(t=>{const G=__cam.G;const z=t==='hq'?G.zones[G.homes[0]]:G.zones.find(z=>z.type===t);__cam.sel(z.id);Object.assign(__cam.cam,{x:z.x,z:z.z,d:z.r*4.2,pitch:.85});__cam.applyCam();},t);
  await p.waitForTimeout(1500);await p.screenshot({path:f+'.png',clip:{x:0,y:0,width:1280,height:445}});}
console.log(errs.slice(0,3));await b.close();})();
