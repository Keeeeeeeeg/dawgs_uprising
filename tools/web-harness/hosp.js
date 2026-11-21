const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam(),zd:z=>zoneDecor(z)};");
fs.writeFileSync('/tmp/ct/hh.html',h);
const hide=`let c=document.querySelector('canvas');while(c&&c!==document.body){for(const e of c.parentElement.children)if(e!==c&&e.tagName!=='SCRIPT')e.style.visibility='hidden';c=c.parentElement;}`;
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:900,height:560}});p.setDefaultTimeout(400000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));
await p.goto('file:///tmp/ct/hh.html');await p.waitForTimeout(1500);await p.evaluate(()=>document.querySelector('#playBtn').click());await p.waitForTimeout(3000);await p.evaluate(()=>document.querySelector('#startGame').click());await p.waitForFunction(()=>window.__cam,null,{timeout:120000});
await p.waitForTimeout(3000);await p.evaluate(hide);
for(const lv of [1,2]){await p.evaluate(lv=>{const G=__cam.G,z=G.zones.find(q=>q.type==='fortress');z.owner=0;z.hosp=lv;__cam.zd(z);const c=__cam.cam,g=z.gate||0;c.x=z.x;c.z=z.z;c.yaw=g+2.6;c.pitch=.75;c.d=34;__cam.applyCam();},lv);
  await p.waitForTimeout(5000);await p.screenshot({path:'/tmp/ct/hosp'+lv+'.png'});}
console.log('errs',errs.slice(0,4));await b.close();})();
