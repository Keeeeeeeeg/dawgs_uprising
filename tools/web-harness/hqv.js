const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam(),proj:(x,y,z)=>proj(x,y,z)};");
fs.writeFileSync('/tmp/ct/fv.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760},deviceScaleFactor:1.5});p.setDefaultTimeout(400000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));
await p.goto('file:///tmp/ct/fv.html');await p.waitForTimeout(1500);
await p.evaluate(()=>{const b=[...document.querySelectorAll('button')].find(b=>/skirmish/i.test(b.textContent));if(b)b.click();});await p.waitForTimeout(800);
await p.evaluate(()=>{const b=[...document.querySelectorAll('button')].find(b=>/^\s*(start|begin|deploy|fight)/i.test(b.textContent)&&b.offsetParent);if(b)b.click();});
await p.waitForFunction(()=>window.__cam&&window.__cam.G,null,{timeout:300000});await p.waitForTimeout(9000);
const info=await p.evaluate(()=>{const G=__cam.G,z=G.zones.find(z=>z.type==='hq'&&z.owner===0);window.FZ=z;
  const us=[];for(let i=0;i<10;i++){const q=G.wallWorld(z,4+i*.5,(i-5)*.8);const u=G.spawnUnit('rifle',z.owner==null?0:z.owner,q.x,q.z);us.push(u.id);}
  if(z.owner!==0){z.owner=0;}
  z.drill=3;const r=G.applyCmd(0,{k:'manpos',zid:z.id,ids:us,posts:[0,1,2,3,4,5,6,40,41,42],face:null});return {name:z.name,owner:z.owner,r,gate:z.gate};});
console.log(JSON.stringify(info));
for(let t=0;t<40;t++){await p.waitForTimeout(500);}
const view=async(n,yaw,pitch,d)=>{await p.evaluate(([yaw,pitch,d])=>{const c=__cam.cam,z=FZ;c.x=z.x;c.z=z.z;c.d=d;c.pitch=pitch;c.yaw=yaw;__cam.applyCam();},[yaw,pitch,d]);await p.waitForTimeout(900);await p.screenshot({path:'/tmp/ct/hv_'+n+'.png'});};
await view('a',0.6,.75,70);await view('b',(info.gate||0)+Math.PI/2+.3,.35,55);await view('c',2.6,.5,45);
await p.evaluate(()=>{const G=__cam.G,z=FZ;const e=G.wallWorld(z,40,0);for(let i=0;i<3;i++)G.spawnUnit('rifle',1,e.x+i,e.z);});await p.waitForTimeout(6000);
await view('d',(info.gate||0)+Math.PI/2,.55,24);
// hover the wall with soldiers selected
await p.evaluate(()=>{const G=__cam.G;const us=G.units.filter(u=>u.alive&&u.f===0&&u.type==='rifle'&&!u.man).slice(0,4);window.__sel=us.map(u=>u.id);});
console.log(JSON.stringify(errs.slice(0,8)));await b.close();})();
