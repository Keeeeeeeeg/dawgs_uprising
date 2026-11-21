const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam()};");
{const i=h.indexOf('cityBridges,cityHit,cityFall,zoneMult');h=h.slice(0,i)+'damage,'+h.slice(i);}
fs.writeFileSync('/tmp/ct/ml.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760},deviceScaleFactor:1.5});p.setDefaultTimeout(300000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));p.on('console',m=>{const t=m.text();if(/WebGLProgram|shader error/i.test(t))errs.push('CONSOLE '+t.slice(0,400));});
await p.goto('file:///tmp/ct/ml.html');await p.waitForTimeout(1500);await p.evaluate(()=>{document.querySelector('#hordeBtn').click();});await p.waitForTimeout(600);
await p.evaluate(()=>{const f=document.querySelector('#hordeFog');if(f.checked)f.click();document.querySelector('#hordeStart').click();});await p.waitForFunction(()=>window.__cam&&window.__cam.G,null,{timeout:250000});await p.waitForTimeout(8000);
await p.evaluate(()=>{const G=__cam.G,z=G.zones[G.home],HF=G.horde.f;G.horde.t=1e9;G.horde.thinkT=1e9;window.X=z.x+40;window.Z=z.z-60;window.M=[];
  ['husk','runner','spitter','quill','brute','mite'].forEach((t,i)=>{const u=G.spawnUnit(t,HF,X+i*2.4,Z);u.ang=Math.PI/2+.5;M.push(u);});
  window.pin=()=>{M.forEach((u,i)=>{if(!u.alive)return;u.x=X+i*2.4;u.z=Z;u.vx=u.vz=0;u.path=null;u.mode='idle';u.target=null;u.ang=Math.PI/2+.5;});};
  const c=__cam.cam;c.x=X+6;c.z=Z-2;c.d=12;c.pitch=.6;c.yaw=0;__cam.applyCam();});
for(let i=0;i<3;i++){await p.evaluate(()=>pin());await p.waitForTimeout(500);await p.screenshot({path:'/tmp/ct/ml'+i+'.png',clip:{x:240,y:40,width:800,height:400}});}
// blast them
await p.evaluate(()=>{const G=__cam.G;for(const u of M)G.damage(u,1e6,0,u.x,u.z+3,null,'shell');});await p.waitForTimeout(300);await p.screenshot({path:'/tmp/ct/ml3.png',clip:{x:240,y:40,width:800,height:400}});
await p.waitForTimeout(2600);await p.screenshot({path:'/tmp/ct/ml4.png',clip:{x:240,y:40,width:800,height:400}});
console.log(JSON.stringify(errs.slice(0,6)));await b.close();})();
