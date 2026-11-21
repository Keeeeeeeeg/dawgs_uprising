const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam(),FX:CITY_FX};");
fs.writeFileSync('/tmp/ct/h.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:900,height:560}});p.setDefaultTimeout(400000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));
await p.goto('file:///tmp/ct/h.html');await p.waitForTimeout(1500);await p.evaluate(()=>document.querySelector('#playBtn').click());await p.waitForTimeout(3000);await p.evaluate(()=>document.querySelector('#startGame').click());await p.waitForFunction(()=>window.__cam);
await p.waitForTimeout(8000);
await p.evaluate(()=>{const G=__cam.G;const h=G.zones[G.homes[0]];let x=h.x,z=h.z;for(let a=0;a<6.28;a+=.2){const X=h.x+Math.cos(a)*40,Z=h.z+Math.sin(a)*40;let ok=true;for(let i=-12;i<=12;i+=2)for(let j=-12;j<=12;j+=2)if(!G.passable(X+i,Z+j)||G.heightAt(X+i,Z+j)<1)ok=false;if(ok){x=X;z=Z;break;}}
  const v=G.spawnUnit('vtol',0,x,z);window.__v=v;window.__adv=n=>{for(let i=0;i<n;i++)G.update(.25);};
  const H=G.heightAt(x,z),p=.6;Object.assign(__cam.cam,{x,z:z-(H+4)/Math.tan(p),d:(H+22)/Math.sin(p),pitch:p,yaw:.4});__cam.applyCam();window.__H=H;});
await p.waitForTimeout(3000);
await p.evaluate(()=>{__v.hp=1;__cam.G.spawnUnit('flak',1,__v.x+12,__v.z);__adv(2);});
for(const [k,w] of [[0,1200],[1,2500],[2,3500]]){await p.waitForTimeout(w);await p.screenshot({path:'vc'+k+'.png',clip:{x:100,y:20,width:700,height:500},timeout:400000});console.log('k',k);}
console.log(errs.slice(0,3));await b.close();})();