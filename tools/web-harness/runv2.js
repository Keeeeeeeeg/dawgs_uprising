const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam()};");
fs.writeFileSync('/tmp/ct/rv.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760},deviceScaleFactor:1.5});p.setDefaultTimeout(300000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());const errs=[];p.on('pageerror',e=>errs.push(e.message));p.on('console',m=>{const t=m.text();if(/WebGLProgram|shader error/i.test(t))errs.push('CONSOLE '+t.slice(0,300));});
await p.goto('file:///tmp/ct/rv.html');await p.waitForTimeout(1500);await p.evaluate(()=>{document.querySelector('#hordeBtn').click();});await p.waitForTimeout(600);
await p.evaluate(()=>{const f=document.querySelector('#hordeFog');if(f.checked)f.click();document.querySelector('#hordeStart').click();});await p.waitForFunction(()=>window.__cam&&window.__cam.G,null,{timeout:250000});await p.waitForTimeout(8000);
await p.evaluate(()=>{const G=__cam.G,z=G.zones[G.home];G.horde.t=1e9;window.X=z.x+40;window.Z=z.z-60;window.S=[];
  ['rifle','rifle','mg','at'].forEach((t,i)=>{const u=G.spawnUnit(t,0,X+i*1.7,Z+(i%2)*1.2);S.push(u);});window.go=()=>G.applyCmd(0,{k:'order',kind:'move',ids:S.map(u=>u.id),a:X+60,b:Z+2.4});});
await p.evaluate(()=>{const c=__cam.cam;c.x=X+2.6;c.z=Z+.6;c.d=5.5;c.pitch=.42;c.yaw=0;__cam.applyCam();});await p.waitForTimeout(800);await p.screenshot({path:'/tmp/ct/rv_still.png',clip:{x:340,y:60,width:600,height:330}});
console.log(await p.evaluate(()=>JSON.stringify(go())));
for(let i=0;i<6;i++){await p.evaluate(()=>{const u=S[0],c=__cam.cam;c.x=u.x;c.z=u.z;c.d=5.5;c.pitch=.42;c.yaw=0;__cam.applyCam();});await p.waitForTimeout(140);await p.screenshot({path:'/tmp/ct/rv'+i+'.png',clip:{x:340,y:60,width:600,height:330}});}
console.log(JSON.stringify(errs.slice(0,5)));await b.close();})();
