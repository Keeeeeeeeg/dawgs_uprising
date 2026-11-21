const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},get meshes(){return meshes;},applyCam:()=>applyCam()};");
fs.writeFileSync('/tmp/ct/iv.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760},deviceScaleFactor:2});p.setDefaultTimeout(400000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));p.on('console',m=>{const t=m.text();if(/WebGLProgram|shader error/i.test(t))errs.push('CONSOLE '+t.slice(0,300));});
await p.goto('file:///tmp/ct/iv.html');await p.waitForTimeout(1500);await p.evaluate(()=>{document.querySelector('#hordeBtn').click();});await p.waitForTimeout(600);
await p.evaluate(()=>{const f=document.querySelector('#hordeFog');if(f.checked)f.click();document.querySelector('#hordeStart').click();});await p.waitForFunction(()=>window.__cam&&window.__cam.G,null,{timeout:300000});await p.waitForTimeout(13000);
await p.evaluate(()=>{let c2=document.querySelector('canvas');while(c2&&c2!==document.body){for(const e of c2.parentElement.children)if(e!==c2&&e.tagName!=='SCRIPT')e.style.visibility='hidden';c2=c2.parentElement;}
  const G=__cam.G,z=G.zones[G.home],c=__cam.cam,x=z.x+40,zz=z.z-60;G.horde.t=1e9;window.__us=[];['rifle','rifle','mg','at','rifle','rifle'].forEach((t,i)=>{const u=G.spawnUnit(t,0,x+i*1.7,zz+(i%2)*1.2);u.ang=Math.PI/2+.4;window.__us.push(u.id);});
  c.x=x+4.2;c.z=zz-2;c.d=11;c.pitch=.6;c.yaw=0;__cam.applyCam();});
await p.waitForTimeout(2500);
const shot=async n=>{await p.screenshot({path:'/tmp/ct/iv_'+n+'.png',clip:{x:330,y:120,width:700,height:240}});};
await shot('a');
// force ambient acts in turn
for(const [n,k] of [['look','look'],['ammo','ammo'],['halt','halt'],['point','point']]){await p.evaluate(k=>{for(const id of __us){const m=__cam.meshes.get(id);if(m){m.userData.amb={k,t:0,face:.6,sd:1};}}},k);await p.waitForTimeout(900);await shot(n);await p.waitForTimeout(2200);}
await p.evaluate(()=>{for(const id of __us){const m=__cam.meshes.get(id);if(m){m.userData.amb=null;m.userData.restKn=true;m.userData.ambAt=1e9;}}});await p.waitForTimeout(2500);await shot('kneel');
console.log(errs.slice(0,6));await b.close();})();
