const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam()};");
h=h.replace('let selected=new Set(),groups={}','let selected=new Set(),groups={};window.__selS=()=>selected;let __x0');fs.writeFileSync('/tmp/ct/rv.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760},deviceScaleFactor:1.5});p.setDefaultTimeout(300000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());const errs=[];p.on('pageerror',e=>errs.push(e.message+' @ '+(e.stack||'').split('\n').slice(1,3).join(' | ')));p.on('console',m=>{const t=m.text();if(/WebGLProgram|shader error/i.test(t))errs.push('CONSOLE '+t.slice(0,300));});
await p.goto('file:///tmp/ct/rv.html');await p.waitForTimeout(1500);await p.evaluate(()=>{document.querySelector('#hordeBtn').click();});await p.waitForTimeout(600);
await p.evaluate(()=>{const f=document.querySelector('#hordeFog');if(f.checked)f.click();document.querySelector('#hordeStart').click();});await p.waitForFunction(()=>window.__cam&&window.__cam.G,null,{timeout:250000});await p.waitForTimeout(8000);
await p.evaluate(()=>{const G=__cam.G,z=G.zones[G.home];G.horde.t=1e9;window.X=z.x+40;window.Z=z.z-60;
  window.S=[];['rifle','sniper','mg'].forEach((t,i)=>{const u=G.spawnUnit(t,0,X+i*7,Z);u.ang=-Math.PI/2;S.push(u);});
  const HF=G.factions.length-1;window.E=G.spawnUnit('brute',HF,X+7,Z-30);E.hp=E.maxHp=1e7;E.def=Object.assign({},E.def,{dmg:0,speed:0});
  window.step=n=>{for(let i=0;i<n;i++)G.update(.05);};});
const shot=async(n,x,z,d,pitch,yaw)=>{await p.evaluate(([x,z,d,pitch,yaw])=>{const c=__cam.cam;c.x=x;c.z=z;c.d=d;c.pitch=pitch;c.yaw=yaw;__cam.applyCam();},[x,z,d,pitch,yaw]);await p.waitForTimeout(300);await p.screenshot({path:'/tmp/ct/id_'+n+'.png'});};
let X=await p.evaluate(()=>X),Z=await p.evaluate(()=>Z);
await p.evaluate(()=>step(40));await p.waitForTimeout(800);await shot('snp',X+7,Z,4.5,.4,-1.2);
await p.evaluate(()=>{E.alive=false;});
for(let i=0;i<6;i++){await p.evaluate(()=>step(30));await p.waitForTimeout(2500);await shot('sq'+i,X,Z,4.5,.35,-1.0);}
console.log(JSON.stringify(errs.slice(0,5)));await b.close();})();