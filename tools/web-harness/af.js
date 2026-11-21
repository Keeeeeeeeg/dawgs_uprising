const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam()};");
h=h.replace("const LIFE={paths:[],lifts:[]};","const LIFE={paths:[],lifts:[]};window.__LIFE=LIFE;");
fs.writeFileSync('/tmp/ct/h.html',h);
const hide=`let c=document.querySelector('canvas');while(c&&c!==document.body){for(const e of c.parentElement.children)if(e!==c&&e.tagName!=='SCRIPT')e.style.visibility='hidden';c=c.parentElement;}`;
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:900,height:560}});p.setDefaultTimeout(400000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file:///tmp/ct/h.html');await p.waitForTimeout(1500);await p.evaluate(()=>document.querySelector('#playBtn').click());await p.waitForTimeout(3000);await p.evaluate(()=>document.querySelector('#startGame').click());await p.waitForFunction(()=>window.__cam,null,{timeout:120000});
await p.waitForTimeout(3000);
const r=await p.evaluate(()=>{const G=__cam.G,on=(x,z,pad)=>G.zones.some(o=>{const A=o.air;if(!A)return false;const s=(x-A.cx)*A.ux+(z-A.cz)*A.uz,q=(x-A.cx)*A.nx+(z-A.cz)*A.nz;return Math.abs(s)<=A.L/2+8+pad&&q>=-6-pad&&q<=18+pad;});
  const ab=G.zones.filter(z=>z.air);const L=__LIFE.lifts;return {airbases:ab.length,lifts:L.length,bad:L.filter(l=>on(l.A.x,l.A.z,0)||on(l.B.x,l.B.z,0)).length,
   nearAB:L.filter(l=>ab.some(z=>Math.hypot(l.A.x-z.x,l.A.z-z.z)<z.r+12)).length,ab0:ab[0]?{x:ab[0].x,z:ab[0].z,ang:ab[0].air.ang}:null};});
console.log(JSON.stringify(r));
if(r.ab0){await p.evaluate(hide);await p.evaluate(a=>{const c=__cam.cam;c.x=a.x;c.z=a.z;c.yaw=0;c.pitch=1.1;c.d=95;__cam.applyCam();},r.ab0);await p.waitForTimeout(6000);await p.screenshot({path:'/tmp/ct/af.png'});}
console.log('errs',errs.slice(0,5));await b.close();})();
