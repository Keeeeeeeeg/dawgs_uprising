const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam(),FX:CITY_FX};");
fs.writeFileSync('/tmp/ct/h.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:900,height:560}});p.setDefaultTimeout(400000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));
await p.goto('file:///tmp/ct/h.html');await p.waitForTimeout(1500);await p.evaluate(()=>document.querySelector('#playBtn').click());await p.waitForTimeout(3000);await p.evaluate(()=>document.querySelector('#startGame').click());await p.waitForFunction(()=>window.__cam);
await p.waitForTimeout(8000);
await p.evaluate(()=>{const G=__cam.G;const h=G.zones[G.homes[0]];let x=h.x,z=h.z;for(let a=0;a<6.28;a+=.2){const X=h.x+Math.cos(a)*45,Z=h.z+Math.sin(a)*45;let ok=true;for(let i=-16;i<=16;i+=2)for(let j=-16;j<=16;j+=2)if(!G.passable(X+i,Z+j)||G.heightAt(X+i,Z+j)<1)ok=false;if(ok){x=X;z=Z;break;}}
  const t1=G.spawnUnit('htank',0,x-10,z),t2=G.spawnUnit('htank',0,x-10,z+6);window.__t=[t1,t2];G.applyCmd(0,{k:'order',kind:'move',ids:[t1.id,t2.id],a:x+6,b:z+3});
  for(let i=0;i<3;i++)G.spawnUnit('mtank',1,x+24,z+i*4-4);window.__adv=n=>{for(let i=0;i<n;i++)G.update(.25);};
  const Y=G.heightAt(x,z),p=.62,yw=.7;const L=()=>{const t=t1.alive?t1:{x,z},o=Y/Math.tan(p)-6;Object.assign(__cam.cam,{x:t.x+4-Math.sin(yw)*o,z:t.z+2-Math.cos(yw)*o,d:(Y+12)/Math.sin(p),pitch:p,yaw:yw});__cam.applyCam();requestAnimationFrame(L);};L();});
for(const [k,n] of [[0,10],[1,14]]){await p.evaluate(n=>__adv(n),n);await p.waitForTimeout(2500);await p.screenshot({path:'ht'+k+'.png',clip:{x:60,y:20,width:780,height:500},timeout:400000});console.log('k',k);}
console.log(errs.slice(0,3));await b.close();})();