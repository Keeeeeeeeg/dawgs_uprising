const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam(),FX:CITY_FX};");
fs.writeFileSync('/tmp/ct/h.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760}});p.setDefaultTimeout(120000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));
await p.goto('file:///tmp/ct/h.html');await p.waitForTimeout(1500);await p.evaluate(()=>document.querySelector('#playBtn').click());await p.waitForTimeout(3000);await p.evaluate(()=>document.querySelector('#startGame').click());await p.waitForFunction(()=>window.__cam);
await p.waitForTimeout(3000);
await p.evaluate(()=>{const G=__cam.G;const z=G.zones.filter(z=>z.type==='town'&&z.city)[0];window.__z=z;for(const u of G.units)if(u.garrison===z.id)u.alive=false;z.owner=0;z.contested=false;
  const us=[];for(let i=0;i<16;i++)us.push(G.spawnUnit(i%4?'rifle':'mg',0,z.x+3+(i%4),z.z+3+(i/4|0)));window.__us=us;G.applyCmd(0,{k:'man',zid:z.id,ids:us.map(u=>u.id)});
  const g=z.gate||0,B=G.cityBridges(z).map(b=>Object.assign(b,{wz:b.ua*Math.sin(g)+b.ub*Math.cos(g)})).sort((a,b)=>a.wz-b.wz)[0],wx=(a,b)=>({x:z.x+a*Math.cos(g)-b*Math.sin(g),z:z.z+a*Math.sin(g)+b*Math.cos(g)});const P=wx(B.ua*(B.r0+3),B.ub*(B.r0+3));window.__adv=n=>{for(let i=0;i<n;i++)G.update(.25);};
  const L=()=>{Object.assign(__cam.cam,{x:P.x,z:P.z,d:55,pitch:1.3});__cam.applyCam();requestAnimationFrame(L);};L();});
for(let k=0;k<3;k++){await p.evaluate(k=>__adv([14,10,40][k]),k);await p.waitForTimeout(4000);console.log(await p.evaluate(()=>JSON.stringify(__us.reduce((o,u)=>{const k=u.man?u.man.ph:'none';o[k]=(o[k]||0)+1;return o;},{}))));
  await p.screenshot({path:'cman'+k+'.png',clip:{x:140,y:60,width:1000,height:560}});}
console.log(errs.slice(0,3));await b.close();})();