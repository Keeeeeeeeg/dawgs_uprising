const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam()};");
{const i=h.indexOf('cityBridges,cityHit,cityFall,zoneMult');h=h.slice(0,i)+'damage,'+h.slice(i);}
fs.writeFileSync('/tmp/ct/gore.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760},deviceScaleFactor:1.5});p.setDefaultTimeout(300000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));p.on('console',m=>{const t=m.text();if(/WebGLProgram|shader error/i.test(t))errs.push('CONSOLE '+t.slice(0,400));});
await p.goto('file:///tmp/ct/gore.html');await p.waitForTimeout(1500);await p.evaluate(()=>{document.querySelector('#hordeBtn').click();});await p.waitForTimeout(600);
await p.evaluate(()=>{const f=document.querySelector('#hordeFog');if(f.checked)f.click();document.querySelector('#hordeStart').click();});await p.waitForFunction(()=>window.__cam&&window.__cam.G,null,{timeout:250000});await p.waitForTimeout(8000);
const at=(x,z,d,yaw)=>p.evaluate(([x,z,d,yaw])=>{const c=__cam.cam;c.x=x;c.z=z;c.d=d;c.pitch=.45;c.yaw=yaw||0;__cam.applyCam();},[x,z,d,yaw]);
const P0=await p.evaluate(()=>{const G=__cam.G,z=G.zones[G.home];G.horde.t=1e9;return {x:z.x+40,z:z.z-60};});
// the quill close up: breathing frames
await p.evaluate(([x,z])=>{const G=__cam.G,u=G.spawnUnit('quill',G.horde.f,x,z);u.ang=Math.PI*.15;window.Q=u.id;u.speed=0;},[P0.x,P0.z]);
for(let i=0;i<4;i++){await p.evaluate(([x,z])=>{const G=__cam.G,u=G.units.find(q=>q.id===Q);u.x=x;u.z=z;u.vx=u.vz=0;u.mode='idle';u.path=null;},[P0.x,P0.z]);await at(P0.x+.2,P0.z+2.6,3.2,0);await p.waitForTimeout(450);await p.screenshot({path:'/tmp/ct/gq'+i+'.png',clip:{x:340,y:120,width:600,height:380}});}
// gore: five creatures blown apart
await p.evaluate(([x,z])=>{const G=__cam.G,HF=G.horde.f;window.V=[];['husk','runner','spitter','quill','brute','husk','runner'].forEach((t,i)=>{const u=G.spawnUnit(t,HF,x+60+i*2.6,z);u.ang=Math.PI/2;V.push(u);});
  for(const u of V){G.damage(u,1e6,0,u.x,u.z+3,null,'shell');}},[P0.x,P0.z]);
await at(P0.x+68,P0.z+3,13,0);await p.waitForTimeout(250);await p.screenshot({path:'/tmp/ct/gg0.png',clip:{x:240,y:60,width:800,height:440}});
await p.waitForTimeout(2500);await p.screenshot({path:'/tmp/ct/gg1.png',clip:{x:240,y:60,width:800,height:440}});
console.log(JSON.stringify(errs.slice(0,6)));await b.close();})();
