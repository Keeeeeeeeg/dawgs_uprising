const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam(),FX:CITY_FX};");
fs.writeFileSync('/tmp/ct/h.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:900,height:560}});p.setDefaultTimeout(400000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));
await p.goto('file:///tmp/ct/h.html');await p.waitForTimeout(1500);await p.evaluate(()=>document.querySelector('#playBtn').click());await p.waitForTimeout(3000);await p.evaluate(()=>document.querySelector('#startGame').click());await p.waitForFunction(()=>window.__cam);
await p.waitForFunction(()=>!document.querySelector('#loading')||getComputedStyle(document.querySelector('#loading')).display==='none').catch(()=>{});await p.waitForTimeout(6000);
await p.evaluate(()=>{const G=__cam.G;const h=G.zones[G.homes[0]];let x=h.x,z=h.z;for(let a=0;a<6.28;a+=.2){const X=h.x+Math.cos(a)*34,Z=h.z+Math.sin(a)*34;let ok=true;for(let i=-3;i<=16;i+=1)for(let j=-4;j<=5;j+=1)if(!G.passable(X+i,Z+j)||G.heightAt(X+i,Z+j)<1)ok=false;if(ok){x=X;z=Z;break;}}window.__us=[];
  for(let i=0;i<3;i++)__us.push(G.spawnUnit('rifle',0,x+i*1.4,z));__us.push(G.spawnUnit('mg',0,x+1,z+2.2));__us.push(G.spawnUnit('at',0,x+3,z+2.2));
  G.spawnUnit('lheli',1,x+10,z-3);for(let i=0;i<3;i++)G.spawnUnit('rifle',1,x+13,z+i*1.5-1);
  const L=()=>{const H=G.heightAt(x,z),p=.85;Object.assign(__cam.cam,{x:x+2,z:z+1-H/Math.tan(p),d:(H+9)/Math.sin(p),pitch:p,yaw:0});__cam.applyCam();requestAnimationFrame(L);};L();});
await p.waitForTimeout(3000);console.log('fps test',await p.evaluate(()=>new Promise(r=>{let n=0;const t0=performance.now();const f=()=>{n++;if(performance.now()-t0<8000)requestAnimationFrame(f);else r(n+' frames in 8s');};requestAnimationFrame(f);})),errs.slice(0,3));
for(let k=0;k<3;k++){await p.waitForTimeout(k?1800:600);await p.screenshot({path:'inf'+k+'.png',clip:{x:100,y:20,width:700,height:500},timeout:400000});console.log('shot',k);}
console.log(errs.slice(0,3));await b.close();})();