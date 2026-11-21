const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={get meshes(){return meshes;},cam,get G(){return G;},applyCam:()=>applyCam(),proj:(x,y,z)=>proj(x,y,z)};");
fs.writeFileSync('/tmp/ct/fv.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760},deviceScaleFactor:1.5});p.setDefaultTimeout(400000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());const errs=[];p.on('pageerror',e=>console.log('ERR',e.message,(e.stack||'').split('\n')[1]));
await p.goto('file:///tmp/ct/fv.html');await p.waitForTimeout(1500);
await p.evaluate(()=>{const b=[...document.querySelectorAll('button')].find(b=>/skirmish/i.test(b.textContent));if(b)b.click();});await p.waitForTimeout(800);
await p.evaluate(()=>{const b=[...document.querySelectorAll('button')].find(b=>/^\s*(start|begin|deploy|fight)/i.test(b.textContent)&&b.offsetParent);if(b)b.click();});
await p.waitForFunction(()=>window.__cam&&window.__cam.G,null,{timeout:300000});await p.waitForTimeout(9000);
const info=await p.evaluate(()=>{const G=__cam.G,z=G.zones.find(z=>z.type==='hq'&&z.owner===0);window.FZ=z;
  const us=[];for(let i=0;i<10;i++){const q=G.wallWorld(z,4+i*.5,(i-5)*.8);const u=G.spawnUnit('rifle',z.owner==null?0:z.owner,q.x,q.z);us.push(u.id);}
  if(z.owner!==0){z.owner=0;}
  z.drill=3;const r=G.applyCmd(0,{k:'manpos',zid:z.id,ids:us,posts:[0,1,2,3,4,5,6,40,41,42],face:null});return {name:z.name,owner:z.owner,r,gate:z.gate};});
console.log(JSON.stringify(info));
console.log(await p.evaluate(()=>{const S=window.__SETP,c={};for(const P of S.placed)c[P.n]=(c[P.n]||0)+1;return 'placed '+S.placed.length+' '+JSON.stringify(c);}));
const shot=async(n,zf,yaw,pitch,d)=>{await p.evaluate(([zf,yaw,pitch,d])=>{const G=__cam.G,z=G.zones.find(zf==='hq'?(o=>o.type==='hq'&&o.owner===0):zf==='fort'?(o=>o.type==='fortress'):(o=>o.type==='town'&&o.wall&&!o.wall.mega));const c=__cam.cam;c.x=z.x;c.z=z.z;c.d=d;c.pitch=pitch;c.yaw=yaw;__cam.applyCam();},[zf,yaw,pitch,d]);await p.waitForTimeout(1500);await p.screenshot({path:'/tmp/ct/sp_'+n+'.png'});};
const ap=await p.evaluate(()=>{const G=__cam.G,z=G.zones.find(o=>o.type==='hq'&&o.owner===0),f=G.zones.find(o=>o.type==='fortress');return [z,f].map(Z=>{const g=Z.gate||0,R=24;return [Z.x+Math.cos(g)*R,Z.z+Math.sin(g)*R,g];});});
for(let i=0;i<ap.length;i++){const q=ap[i];await p.evaluate(([x,z,g])=>{const c=__cam.cam;c.x=x;c.z=z;c.d=34;c.pitch=.8;c.yaw=-g+Math.PI/2+.5;__cam.applyCam();},q);await p.waitForTimeout(1500);await p.screenshot({path:'/tmp/ct/ap_'+i+'.png'});}
console.log(JSON.stringify(errs.slice(0,8)));await b.close();})();
