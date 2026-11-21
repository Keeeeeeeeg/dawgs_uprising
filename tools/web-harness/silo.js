const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam()};");
fs.writeFileSync('/tmp/silo.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760}});
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));
await p.goto('file:///tmp/silo.html');await p.waitForTimeout(1200);await p.click('#playBtn');await p.waitForTimeout(400);await p.click('#startGame');await p.waitForFunction(()=>window.__cam);
await p.click('#planGo').catch(()=>{});
const r=await p.evaluate(()=>{const G=__cam.G,z=G.zones[G.homes[0]];G.factions[0].money=5000;const a=G.applyCmd(0,{k:'silo',zid:z.id});for(let i=0;i<950;i++)G.update(.1);z.msl=1;
  const sp=G.siloSpot(z);__cam.cam.x=sp.x;__cam.cam.z=sp.z;__cam.cam.d=40;__cam.applyCam();window.__z=z;return [a,z.silo,z.siloUp];});
console.log(JSON.stringify(r));await p.waitForTimeout(1500);await p.screenshot({path:'silo0.png'});
await p.evaluate(()=>{const G=__cam.G,z=window.__z,t=G.zones.find(q=>q.owner!==0);window.__fire=G.applyCmd(0,{k:'missile',x:t.x,z:t.z});});
for(const [ms,f] of [[3000,"silo1"],[2500,"silo2"],[2000,"silo3"]]){await p.waitForTimeout(ms);await p.screenshot({path:f+'.png'});console.log(f,await p.evaluate(()=>{const G=__cam.G;return G.time.toFixed(1)}));}
console.log(await p.evaluate(()=>JSON.stringify(window.__fire&&window.__fire.ok)),errs.slice(0,3));await b.close();})();
