const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},get meshes(){return meshes;},proj:(x,y,z)=>proj(x,y,z),applyCam:()=>applyCam()};");
fs.writeFileSync('/tmp/ct/cmb.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760},deviceScaleFactor:1.5});p.setDefaultTimeout(400000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));p.on('console',m=>{const t=m.text();if(/WebGLProgram|shader error|THREE\./i.test(t))errs.push('CONSOLE '+t.slice(0,300));});
await p.goto('file:///tmp/ct/cmb.html');await p.waitForTimeout(1500);await p.evaluate(()=>{document.querySelector('#hordeBtn').click();});await p.waitForTimeout(600);
await p.evaluate(()=>{const f=document.querySelector('#hordeFog');if(f.checked)f.click();document.querySelector('#hordeStart').click();});await p.waitForFunction(()=>window.__cam&&window.__cam.G,null,{timeout:300000});await p.waitForTimeout(12000);
const view=async(dx,dz,d)=>p.evaluate(([dx,dz,d])=>{const G=__cam.G,z=G.zones[G.home],c=__cam.cam;c.x=z.x+40+dx;c.z=z.z-60+dz;c.d=d;c.pitch=.6;c.yaw=0;__cam.applyCam();},[dx,dz,d]);
const shot=async(n,clip)=>{await p.screenshot({path:'/tmp/ct/cb_'+n+'.png',clip:clip||{x:240,y:60,width:800,height:420}});};
// 1: line-up of the Mange
await p.evaluate(()=>{const G=__cam.G,z=G.zones[G.home],x=z.x+40,zz=z.z-60,HF=G.horde.f;G.horde.t=1e9;window.__mg=[];['husk','runner','spitter','quill','brute','mite'].forEach((t,i)=>{const u=G.spawnUnit(t,HF,x+i*2.4,zz);u.ang=Math.PI/2+.5;u.hold=1;window.__mg.push(u.id);});});
await view(6,-2,14);await p.waitForTimeout(1200);await shot('line');
// click the quill: card
const pt=await p.evaluate(()=>{const G=__cam.G,u=G.units.find(u=>u.type==='quill'&&u.alive),q=__cam.proj(u.x,G.heightAt(u.x,u.z)+.8,u.z);return q;});
if(pt){await p.mouse.click(pt.x,pt.y);await p.waitForTimeout(500);await p.screenshot({path:'/tmp/ct/cb_card.png'});}
// 2: a fight: riflemen, MG and rocketeer against the creatures, 14 m apart
await p.evaluate(()=>{const G=__cam.G,z=G.zones[G.home],x=z.x+40,zz=z.z-60;for(const id of __mg){const u=G.units.find(q=>q.id===id);if(u)u.z-=1;}
  ['rifle','rifle','mg','at','rifle','rifle','rifle','rifle'].forEach((t,i)=>{const u=G.spawnUnit(t,0,x+i*1.6,zz+13);u.ang=-Math.PI/2;});});
await view(6,4,17);await p.waitForTimeout(1500);await shot('fight1');await p.waitForTimeout(900);await shot('fight2');await p.waitForTimeout(5000);await shot('fight3');
await p.waitForTimeout(9000);await shot('after');
// 3: aircraft overhead
await p.evaluate(()=>{const G=__cam.G,z=G.zones[G.home],x=z.x+40,zz=z.z-60,HF=G.horde.f;for(const u of G.units)if(u.f===HF&&u.alive&&!u.def.struct&&Math.hypot(u.x-x,u.z-zz)<60)u.hp=0;
  for(let i=0;i<6;i++){const u=G.spawnUnit('rifle',0,x+i*1.6,zz+13);u.ang=-Math.PI/2;}const hq=G.spawnUnit('heli',HF,x+5,zz+6);hq.hp=hq.maxHp=99999;hq.hold=1;window.__h=hq.id;});
await p.waitForTimeout(2500);await view(6,6,15);await shot('air1');await p.waitForTimeout(700);await shot('air2');
console.log(JSON.stringify(errs.slice(0,8)));await b.close();})();
