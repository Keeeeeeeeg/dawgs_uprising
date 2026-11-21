const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam(),sel:(ids)=>{selected=new Set(ids);}};");
fs.writeFileSync('/tmp/glow.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760}});
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));
await p.goto('file:///tmp/glow.html');await p.waitForTimeout(1200);await p.click('#playBtn');await p.waitForTimeout(400);await p.click('#startGame');await p.waitForFunction(()=>window.__cam);
await p.click('#planGo').catch(()=>{});
for(const t of ['fortress','airbase']){
await p.evaluate(t=>{const G=__cam.G;const z=G.zones.find(z=>z.type===t);for(const u of G.units)if(u.garrison===z.id)u.alive=false;z.owner=0;z.contested=false;
  const us=[];for(let i=0;i<10;i++)us.push(G.spawnUnit('rifle',0,z.x+2+i*.4,z.z+1));G.applyCmd(0,{k:'man',zid:z.id,ids:us.map(u=>u.id)});
  Object.assign(__cam.cam,{x:z.x,z:z.z,d:z.r*3.6,pitch:.95});__cam.applyCam();},t);
await p.waitForTimeout(1500);await p.screenshot({path:'glow_'+t+'.png',clip:{x:0,y:0,width:1280,height:445}});}
console.log(errs.slice(0,3));await b.close();})();
