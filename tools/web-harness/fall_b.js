const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam(),FX:CITY_FX,cft:d=>cityFallTick(d),st:()=>CFALLS.length+'/'+CBURN.length+'/'+scene.children.filter(o=>o.isGroup&&o.visible&&o.children.length&&o.children[0].geometry===(RUB_K[0]||RUB_K[1]||RUB_K[2]||RUB_K[3]||{}).b).length};");
fs.writeFileSync('/tmp/ct/h.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760}});p.setDefaultTimeout(120000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));
await p.goto('file:///tmp/ct/h.html');await p.waitForTimeout(1500);await p.evaluate(()=>document.querySelector('#playBtn').click());await p.waitForTimeout(3000);await p.evaluate(()=>document.querySelector('#startGame').click());await p.waitForFunction(()=>window.__cam);
await p.waitForTimeout(3000);
await p.evaluate(()=>{const G=__cam.G;const z=G.zones.filter(z=>z.type==='town'&&z.city)[0];let i=-1,bz=-1e9;G.city.forEach((c,k)=>{if(!c.gone&&c.zone===z.id&&c.tier===2&&c.z-z.z>bz&&Math.abs(c.x-z.x)<25){bz=c.z-z.z;i=k;}});G.setFog&&0;window.__ci=i;const c=G.city[i];
  const L=()=>{Object.assign(__cam.cam,{x:c.x,z:c.z+6,d:60,pitch:.42});__cam.applyCam();requestAnimationFrame(L);};L();});
await p.waitForTimeout(3000);await p.screenshot({path:'fall0.png',clip:{x:140,y:40,width:1000,height:560}});
await p.evaluate(()=>{__cam.G.cityFall(__ci);});
for(let k=1;k<6;k++){await p.evaluate(k=>{for(let i=0;i<[0,3,4,4,10,120][k];i++)__cam.cft(.25);},k);await p.waitForTimeout(2500);await p.screenshot({path:'fall'+k+'.png',clip:{x:140,y:40,width:1000,height:560}});console.log('shot',k,await p.evaluate(()=>__cam.st()));}
console.log(errs.slice(0,3));await b.close();})();