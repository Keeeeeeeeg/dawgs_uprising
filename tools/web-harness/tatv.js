const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam(),get R(){return renderer;},get S(){return scene;},get ZV(){return zoneVis;}};");
fs.writeFileSync('/tmp/ct/pf.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760}});p.setDefaultTimeout(400000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file:///tmp/ct/pf.html');await p.waitForTimeout(1500);await p.evaluate(()=>document.querySelector('#playBtn').click());await p.waitForTimeout(3000);await p.evaluate(()=>document.querySelector('#startGame').click());await p.waitForFunction(()=>window.__cam,null,{timeout:120000});
await p.waitForTimeout(4000);
for(const lv of [1,3]){await p.evaluate(lv=>{const G=__cam.G,z=G.zones.find(q=>q.owner===0&&q.type!=='hq')||G.zones.find(q=>q.owner===0);window.__z=z;
  for(let k=0;k<6;k++){z.threatT=G.time;if(lv===3){z.garHp=z.garFull*.2;}G.update(.25);if(lv===3)z.garHp=z.garFull*.2;}
  const v=__cam.ZV[z.id],wp=new THREE.Vector3();v.flag.getWorldPosition(wp);window.__tat=v.tat;const c=__cam.cam;c.x=wp.x+1;c.z=wp.z;c.d=11;c.pitch=.25;c.yaw=1.5;__cam.applyCam();
  let c2=document.querySelector('canvas');while(c2&&c2!==document.body){for(const e of c2.parentElement.children)if(e!==c2&&e.tagName!=='SCRIPT')e.style.visibility='hidden';c2=c2.parentElement;}},lv);
  await p.waitForTimeout(6000);await p.screenshot({path:'/tmp/ct/tat'+lv+'.png'});console.log('tat',await p.evaluate(()=>window.__tat));}
const r=1;
console.log(JSON.stringify(r,null,1));console.log(errs.slice(0,3));await b.close();})();
