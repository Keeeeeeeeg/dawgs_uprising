const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam()};");
fs.writeFileSync('/tmp/ct/rv.html',h);
const hide=`let c=document.querySelector('canvas');while(c&&c!==document.body){for(const e of c.parentElement.children)if(e!==c&&e.tagName!=='SCRIPT')e.style.visibility='hidden';c=c.parentElement;}`;
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:900,height:560}});p.setDefaultTimeout(600000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));
await p.goto('file:///tmp/ct/rv.html');await p.waitForTimeout(1500);await p.evaluate(()=>document.querySelector('#playBtn').click());await p.waitForTimeout(3000);await p.evaluate(()=>document.querySelector('#startGame').click());await p.waitForFunction(()=>window.__cam,null,{timeout:120000});
await p.waitForTimeout(3000);await p.evaluate(hide);
const spots=await p.evaluate(()=>{const G=__cam.G,L=G.rails[0],out=[];for(const sp of L.stops.slice(0,2)){const q=sp.st;out.push({x:q.S[0],z:q.S[1],yaw:Math.atan2(q.nz,q.nx)});}
  const z=G.zones.find(q=>q.wall&&q.type==='hq')||G.zones.find(q=>q.wall);out.push({x:z.x+Math.cos(z.gate||0)*(z.r+4),z:z.z+Math.sin(z.gate||0)*(z.r+4),yaw:(z.gate||0)});return out;});
let i=0;for(const s of spots){await p.evaluate(s=>{const c=__cam.cam;c.x=s.x;c.z=s.z;c.yaw=s.yaw+.5;c.pitch=.55;c.d=30;__cam.applyCam();},s);await p.waitForTimeout(7000);await p.screenshot({path:'/tmp/ct/stn'+(i++)+'.png'});}
console.log('errs',errs.slice(0,4));await b.close();})();
