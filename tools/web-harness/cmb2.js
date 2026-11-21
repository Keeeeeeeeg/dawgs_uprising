const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},get meshes(){return meshes;},proj:(x,y,z)=>proj(x,y,z),pick:(x,y,f)=>pickUnit(x,y,f),shown:u=>shown(u),insp:()=>inspectId,applyCam:()=>applyCam()};");
{const i=h.indexOf('cityBridges,cityHit,cityFall,zoneMult');h=h.slice(0,i)+'damage,'+h.slice(i);}
fs.writeFileSync('/tmp/ct/cmb.html',h);const which=process.argv[3]||'abcde';
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760},deviceScaleFactor:1.5});p.setDefaultTimeout(400000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));p.on('console',m=>{const t=m.text();if(/WebGLProgram|shader error/i.test(t))errs.push('CONSOLE '+t.slice(0,300));});
await p.goto('file:///tmp/ct/cmb.html');await p.waitForTimeout(1500);await p.evaluate(()=>{document.querySelector('#hordeBtn').click();});await p.waitForTimeout(600);
await p.evaluate(()=>{const f=document.querySelector('#hordeFog');if(f.checked)f.click();document.querySelector('#hordeStart').click();});await p.waitForFunction(()=>window.__cam&&window.__cam.G,null,{timeout:300000});await p.waitForTimeout(9000);
await p.evaluate(()=>{const G=__cam.G,z=G.zones[G.home];G.horde.t=1e9;window.X0=z.x+40;window.Z0=z.z-60;
  window.focus=(ids,d)=>{const us=ids.map(i=>G.units.find(u=>u.id===i)).filter(u=>u&&u.alive);if(!us.length)return;let x=0,zz=0;for(const u of us){x+=u.x;zz+=u.z;}x/=us.length;zz/=us.length;const c=__cam.cam;c.x=x;c.z=zz-2;c.d=d||11;c.pitch=.6;c.yaw=0;__cam.applyCam();};
  window.at=(x,z,d)=>{const c=__cam.cam;c.x=x;c.z=z-2;c.d=d||11;c.pitch=.6;c.yaw=0;__cam.applyCam();};});
const shot=async(n,clip)=>{await p.screenshot({path:'/tmp/ct/c2_'+n+'.png',clip:clip||{x:240,y:60,width:800,height:400}});};
if(which.includes('a')){ // bodies: soldiers and creatures killed where they stand
  await p.evaluate(()=>{const G=__cam.G,HF=G.horde.f;window.A=[];['rifle','mg','at','rifle','rifle'].forEach((t,i)=>{const u=G.spawnUnit(t,0,X0+i*1.8,Z0);u.ang=Math.PI/2;A.push(u);});
    ['husk','runner','spitter','quill','brute'].forEach((t,i)=>{const u=G.spawnUnit(t,HF,X0+i*2.4-80,Z0);u.ang=Math.PI/2;A.push(u);});at(X0+3.6,Z0,11);
    for(const u of A)if(u.f!==0)G.damage(u,1e6,0,u.x,u.z-3,null,'bullet');});
  await p.waitForTimeout(700);await shot('a0');
  await p.evaluate(()=>{const G=__cam.G;for(const u of A)G.damage(u,1e6,u.f===0?G.horde.f:0,u.x,u.z-3,null,'bullet');});await p.waitForTimeout(1500);await shot('a1');
  await p.evaluate(()=>{at(X0-80+4.8,Z0,13);});await p.waitForTimeout(600);await shot('a2');}
if(which.includes('b')){ // firefight seen close from the soldiers' side
  await p.evaluate(()=>{const G=__cam.G,HF=G.horde.f;window.S=[];['rifle','rifle','mg','at','rifle','rifle'].forEach((t,i)=>{const u=G.spawnUnit(t,0,X0+i*1.7+60,Z0);u.ang=-Math.PI/2;S.push(u.id);});
    for(let i=0;i<5;i++){const u=G.spawnUnit(i<3?'quill':'husk',HF,X0+60+i*2,Z0-16);u.hp=u.maxHp=900;}focus(S,13);});
  for(let i=0;i<5;i++){await p.waitForTimeout(650);await p.evaluate(()=>focus(S,13));await shot('b'+i);}}
if(which.includes('c')){ // helicopter overhead
  await p.evaluate(()=>{const G=__cam.G,HF=G.horde.f;window.S2=[];for(let i=0;i<5;i++){const u=G.spawnUnit('rifle',0,X0+i*1.7+140,Z0);u.ang=-Math.PI/2;S2.push(u.id);}const hq=G.spawnUnit('heli',HF,X0+144,Z0-7);hq.hp=hq.maxHp=99999;focus(S2,13);});
  for(let i=0;i<3;i++){await p.waitForTimeout(900);await p.evaluate(()=>focus(S2,13));await shot('c'+i);}}
if(which.includes('d')){ // click a creature: its card
  await p.evaluate(()=>{const G=__cam.G,HF=G.horde.f;const u=G.spawnUnit('quill',HF,X0+30,Z0);window.Q=u.id;at(X0+30,Z0,11);});await p.waitForTimeout(500);
  await p.evaluate(()=>{const G=__cam.G,u=G.units.find(u=>u.id===Q);u.hold=1;u.mode='idle';let best=null;for(let o=-14;o<=14;o+=2){at(u.x,u.z+o,11);const q=__cam.proj(u.x,G.heightAt(u.x,u.z)+.8,u.z);const d=Math.abs(q.y-330)+Math.abs(q.x-640)*.2;if(q.ok&&(!best||d<best.d))best={o,d};}at(u.x,u.z+best.o,11);});await p.waitForTimeout(150);
  const pt2=await p.evaluate(()=>{const G=__cam.G,u=G.units.find(u=>u.id===Q);return __cam.proj(u.x,G.heightAt(u.x,u.z)+.8,u.z);});
  await p.mouse.move(pt2.x,pt2.y);await p.mouse.down();await p.mouse.up();await p.waitForTimeout(500);
  console.log(await p.evaluate(([x,y])=>{const G=__cam.G,u=G.units.find(u=>u.id===Q),e=document.elementFromPoint(x,y),pk=__cam.pick(x,y,o=>o.f!==0);return JSON.stringify({alive:u.alive,ux:u.x,uz:u.z,shown:__cam.shown(u),el:e&&(e.id||e.tagName+'.'+e.className),pk:pk&&pk.type,insp:__cam.insp()});},[pt2.x,pt2.y]));
  console.log('card',JSON.stringify(pt2),await p.evaluate(()=>document.querySelector('#selHead').textContent.slice(0,80)+' | '+document.querySelector('#selBody').textContent.slice(0,300)));
  await p.screenshot({path:'/tmp/ct/c2_card.png',clip:{x:540,y:660,width:740,height:100}});await p.screenshot({path:'/tmp/ct/c2_cardfull.png'});}
console.log(JSON.stringify(errs.slice(0,8)));await b.close();})();
