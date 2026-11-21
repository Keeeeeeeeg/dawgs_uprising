const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam()};");
fs.writeFileSync('/tmp/ct/h.html',h);
const hide=`let c=document.querySelector('canvas');while(c&&c!==document.body){for(const e of c.parentElement.children)if(e!==c&&e.tagName!=='SCRIPT')e.style.visibility='hidden';c=c.parentElement;}`;
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:900,height:560}});p.setDefaultTimeout(400000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.addInitScript(z=>{window.ZT=z;},process.argv[3]||'hq');await p.goto('file:///tmp/ct/h.html');await p.waitForTimeout(1500);await p.evaluate(()=>document.querySelector('#playBtn').click());await p.waitForTimeout(3000);await p.evaluate(()=>document.querySelector('#startGame').click());await p.waitForFunction(()=>window.__cam,null,{timeout:120000});
await p.waitForTimeout(3000);
const info=await p.evaluate(()=>{const G=__cam.G,z=window.ZT==='fortress'?G.zones.find(q=>q.type==='fortress'):G.zones[G.homes[0]];if(window.ZT==='fortress')z.owner=0;z.drill=+(window.LVL||2);for(let i=0;i<12;i++)G.update(.25);
  const T=(z.turrets||[]).filter(Boolean).map(u=>({t:u.type,x:+u.x.toFixed(1),z:+u.z.toFixed(1),my:+u.mountY.toFixed(2)}));return {zx:z.x,zz:z.z,zy:z.y,type:z.type,T};});
console.log(JSON.stringify(info));
await p.evaluate(hide);
const t=info.T[0];await p.evaluate(y=>{window.__TY=y;},t.my);
for(const [n,yaw,pit,d] of [[(process.argv[3]||'hq')+'1',0.6,.5,9],[(process.argv[3]||'hq')+'2',2.4,.3,7]]){await p.evaluate(([x,z,yaw,pit,d])=>{const c=__cam.cam;const Y=window.__TY;c.x=x-Math.sin(yaw)*Y/Math.tan(pit);c.z=z-Math.cos(yaw)*Y/Math.tan(pit);c.d=d+Y/Math.sin(pit);c.yaw=yaw;c.pitch=pit;__cam.applyCam();},[t.x,t.z,yaw,pit,d]);await p.waitForTimeout(5000);await p.screenshot({path:'/tmp/ct/'+n+'.png'});}
console.log('errs',errs.slice(0,4));await b.close();})();
