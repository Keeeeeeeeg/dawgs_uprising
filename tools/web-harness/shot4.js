const {chromium}=require('playwright');const fs=require('fs');
const src=process.argv[2];
let h=fs.readFileSync(src,'utf8');h=h.replace("const cam=Object.assign({pitch:.98},CAM0());","const cam=Object.assign({pitch:.98},CAM0());window.__cam={cam,get G(){return G;},applyCam:()=>applyCam()};");
fs.writeFileSync('/tmp/u_t.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});
const errs=[];
// tutorial: walk to the build step and build via the card
{const p=await b.newPage({viewport:{width:1280,height:760}});p.on('pageerror',e=>errs.push('tut '+e.message));
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.goto('file:///tmp/u_t.html');await p.waitForTimeout(1500);await p.click('#tutBtn');await p.waitForTimeout(3000);
for(let i=0;i<7;i++){await p.click('#tutNext');await p.waitForTimeout(200);}
await p.waitForTimeout(1500);
const z=await p.evaluate(()=>{const G=__cam.G;const z=G.zones.find(z=>z.home===0);__cam.cam.x=z.x;__cam.cam.z=z.z;__cam.cam.d=90;__cam.applyCam();return z.name;});
await p.waitForTimeout(500);await p.mouse.click(640,300);await p.waitForTimeout(500);
await p.evaluate(()=>{const b=document.querySelector('[data-build]:not([disabled])');if(b)b.click();});await p.waitForTimeout(2500);
await p.screenshot({path:'tut_build.png'});
console.log('tut goal:',await p.evaluate(()=>document.querySelector('#tutGoal').textContent),'|',await p.evaluate(()=>document.querySelector('#tutTitle').textContent));
await p.close();}
// planes: give the player an airbase with planes by running a while
{const p=await b.newPage({viewport:{width:1280,height:760}});p.on('pageerror',e=>errs.push('air '+e.message));
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.goto('file:///tmp/u_t.html');await p.waitForTimeout(1500);await p.click('#playBtn');await p.waitForTimeout(400);await p.click('#startGame');await p.waitForTimeout(2500);
const n=await p.evaluate(()=>{const G=__cam.G;const ab=G.zones.find(z=>z.type==='airbase');G.zones.forEach(z=>{if(z===ab){z.owner=0;}});
  for(let i=0;i<3;i++){G.applyCmd&&0;}return ab.name;});
await p.click('#bAir');await p.waitForTimeout(400);
// select a big mixed group to check grouped portraits
await p.evaluate(()=>{});
await p.screenshot({path:'air.png'});await p.close();}
console.log('errors',errs);await b.close();})();
