const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={get meshes(){return meshes;},cam,get G(){return G;},applyCam:()=>applyCam(),proj:(x,y,z)=>proj(x,y,z)};");
fs.writeFileSync('/tmp/ct/fv.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760},deviceScaleFactor:1.5});p.setDefaultTimeout(400000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));
await p.goto('file:///tmp/ct/fv.html');await p.waitForTimeout(1500);
await p.evaluate(()=>{const b=[...document.querySelectorAll('button')].find(b=>/skirmish/i.test(b.textContent));if(b)b.click();});await p.waitForTimeout(800);
await p.evaluate(()=>{const b=[...document.querySelectorAll('button')].find(b=>/^\s*(start|begin|deploy|fight)/i.test(b.textContent)&&b.offsetParent);if(b)b.click();});
await p.waitForFunction(()=>window.__cam&&window.__cam.G,null,{timeout:300000});await p.waitForTimeout(9000);
const info=await p.evaluate(()=>{const G=__cam.G,z=G.zones.find(z=>z.type==='hq'&&z.owner===0);window.FZ=z;
  const us=[];for(let i=0;i<10;i++){const q=G.wallWorld(z,4+i*.5,(i-5)*.8);const u=G.spawnUnit('rifle',z.owner==null?0:z.owner,q.x,q.z);us.push(u.id);}
  if(z.owner!==0){z.owner=0;}
  z.drill=3;const r=G.applyCmd(0,{k:'manpos',zid:z.id,ids:us,posts:[0,1,2,3,4,5,6,40,41,42],face:null});return {name:z.name,owner:z.owner,r,gate:z.gate};});
console.log(JSON.stringify(info));
await p.evaluate(()=>{const G=__cam.G,z=FZ;window.YD=[];for(let i=0;i<6;i++){const q=G.wallWorld(z,-3+i*1.2,3-i*1.1);const u=G.spawnUnit(['rifle','mg','at','rifle','flagb','rifle'][i],0,q.x,q.z);YD.push(u);}});
await p.waitForTimeout(4000);
const dat=await p.evaluate(()=>{const G=__cam.G;return YD.map(u=>{const m=__cam.meshes.get(u.id);return [u.type,G.heightAt(u.x,u.z).toFixed(3),m&&m.position.y.toFixed(3),m&&m.visible];});});console.log(JSON.stringify(dat));
await p.evaluate(()=>{const c=__cam.cam,u=YD[2];c.x=u.x;c.z=u.z;c.d=9;c.pitch=.35;c.yaw=.7;__cam.applyCam();});await p.waitForTimeout(1200);await p.screenshot({path:'/tmp/ct/hy_a.png'});
await p.evaluate(()=>{const c=__cam.cam,u=YD[2];c.x=u.x;c.z=u.z;c.d=14;c.pitch=.75;c.yaw=2.2;__cam.applyCam();});await p.waitForTimeout(1200);await p.screenshot({path:'/tmp/ct/hy_b.png'});
console.log(JSON.stringify(errs.slice(0,8)));await b.close();})();
