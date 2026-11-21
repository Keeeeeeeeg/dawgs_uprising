const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={get meshes(){return meshes;},cam,get G(){return G;},applyCam:()=>applyCam(),proj:(x,y,z)=>proj(x,y,z)};");
fs.writeFileSync('/tmp/ct/fv.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760},deviceScaleFactor:1.5});p.setDefaultTimeout(400000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());const errs=[];p.on('console',m=>{const t=m.text();if(/error|WebGL/i.test(t))console.log('CON',t.slice(0,500));});p.on('pageerror',e=>console.log('ERR',e.message,(e.stack||'').split('\n')[1]));
await p.goto('file:///tmp/ct/fv.html');await p.waitForTimeout(1500);
await p.evaluate(()=>{const b=[...document.querySelectorAll('button')].find(b=>/skirmish/i.test(b.textContent));if(b)b.click();});await p.waitForTimeout(800);
await p.evaluate(()=>{const b=[...document.querySelectorAll('button')].find(b=>/^\s*(start|begin|deploy|fight)/i.test(b.textContent)&&b.offsetParent);if(b)b.click();});
await p.waitForFunction(()=>window.__cam&&window.__cam.G,null,{timeout:300000});await p.waitForTimeout(9000);
const info=await p.evaluate(()=>{const G=__cam.G,z=G.zones.find(z=>z.type==='hq'&&z.owner===0);window.FZ=z;
  const us=[];for(let i=0;i<10;i++){const q=G.wallWorld(z,4+i*.5,(i-5)*.8);const u=G.spawnUnit('rifle',z.owner==null?0:z.owner,q.x,q.z);us.push(u.id);}
  if(z.owner!==0){z.owner=0;}
  z.drill=3;const r=G.applyCmd(0,{k:'manpos',zid:z.id,ids:us,posts:[0,1,2,3,4,5,6,40,41,42],face:null});return {name:z.name,owner:z.owner,r,gate:z.gate};});
console.log(JSON.stringify(info));
await p.evaluate(()=>{const G=__cam.G,z=FZ;window.X=z.x+45;window.Z=z.z+10;window.FL=G.spawnUnit('flamer',0,X,Z);for(let i=0;i<4;i++){const e=G.spawnUnit('rifle',1,X+10+i*.8,Z+i);e.hp=e.maxHp=1e6;if(!i)FL.forced=e;}});
for(let k=0;k<6;k++){await p.evaluate(()=>{for(let i=0;i<5;i++)__cam.G.update(.1);});await p.waitForTimeout(150);}
console.log(await p.evaluate(()=>'jets '+window.__JETS.size+' tgt '+(FL.target&&FL.target.type)+' em '+JSON.stringify(FL.emerge)+' man '+!!FL.man+' mode '+FL.mode+' alive '+FL.alive+' cd '+FL.cd+' forced '+!!FL.forced+' inUnits '+__cam.G.units.includes(FL)));
for(const [n,y,pi] of [['a',1.57,.3],['b',.5,.6]]){await p.evaluate(([y,pi])=>{const c=__cam.cam;c.x=X+5;c.z=Z+1;c.d=16;c.pitch=pi;c.yaw=y;__cam.applyCam();for(let i=0;i<3;i++)__cam.G.update(.1);for(const J of window.__JETS.values())J.k=50;},[y,pi]);await p.waitForTimeout(2500);await p.screenshot({path:'/tmp/ct/fj_'+n+'.png'});}
console.log(await p.evaluate(()=>JSON.stringify([...window.__JETS.values()].map(J=>({v:J.m.visible,k:J.k,inScene:!!J.m.parent,U:Object.fromEntries(Object.entries(J.m.material.uniforms).map(([k,v])=>[k,v.value&&v.value.toArray?v.value.toArray().map(x=>+x.toFixed(2)):v.value]))})))));console.log(JSON.stringify(errs.slice(0,8)));await b.close();})();
