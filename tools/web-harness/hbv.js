const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam()};");
fs.writeFileSync('/tmp/ct/hb.html',h);const map=process.argv[3],views=JSON.parse(process.argv[4]||'[[1,0,60,.6,0.9]]');
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760}});p.setDefaultTimeout(400000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));
await p.goto('file:///tmp/ct/hb.html');await p.waitForTimeout(1500);await p.evaluate(()=>document.querySelector('#playBtn').click());await p.waitForTimeout(1500);
await p.evaluate(m=>{const c=document.querySelector('[data-map="'+m+'"]');if(c)c.click();},map);await p.waitForTimeout(500);
const t0=Date.now();await p.evaluate(()=>document.querySelector('#startGame').click());await p.waitForFunction(()=>window.__cam&&window.__cam.G,null,{timeout:300000});console.log('start s',(Date.now()-t0)/1000);
await p.waitForTimeout(3000);
for(let i=0;i<views.length;i++){const [di,off,d,pitch,yaw]=views[i];
  await p.evaluate(([di,off,d,pitch,yaw])=>{const G=__cam.G,D=G.decks[di];const mid=(D.s0+D.s1)/2,x=D.ax+D.ux*mid+D.nx*off,z=D.az+D.uz*mid+D.nz*off;
    if(!window.__boat){window.__boat=1;const b=G.spawnUnit('monitor',0,x-D.nx*6,z-D.nz*6);const t=G.spawnUnit('mtank',0,x+D.ux*4,z+D.uz*4);const r=G.spawnUnit('rifle',0,x-D.ux*3,z-D.uz*3);}
    const c=__cam.cam;c.x=x;c.z=z;c.d=d;c.pitch=pitch;c.yaw=Math.atan2(D.uz,D.ux)+yaw;__cam.applyCam();
    let c2=document.querySelector('canvas');while(c2&&c2!==document.body){for(const e of c2.parentElement.children)if(e!==c2&&e.tagName!=='SCRIPT')e.style.visibility='hidden';c2=c2.parentElement;}},[di,off,d,pitch,yaw]);
  await p.waitForTimeout(5000);await p.screenshot({path:`/tmp/ct/hb_${map}_${i}.png`});}
console.log(errs.slice(0,5));await b.close();})();
