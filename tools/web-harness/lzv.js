const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam()};");fs.writeFileSync('/tmp/ct/lz.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760}});p.setDefaultTimeout(300000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());const errs=[];p.on('pageerror',e=>errs.push(e.message+' @ '+(e.stack||'').split('\n').slice(1,3).join(' | ')));
await p.goto('file:///tmp/ct/lz.html');await p.waitForTimeout(1500);await p.evaluate(()=>{document.querySelector('#hordeBtn').click();});await p.waitForTimeout(600);
await p.evaluate(()=>{const f=document.querySelector('#hordeFog');if(f.checked)f.click();document.querySelector('#hordeStart').click();});await p.waitForFunction(()=>window.__cam&&window.__cam.G,null,{timeout:250000});await p.waitForTimeout(5000);
const info=await p.evaluate(()=>{const G=__cam.G,z=G.zones.find(z=>z.owner===0)||G.zones[0];const x=z.x+30,zz=z.z+30;
  const a=G.spawnUnit('at',0,x,zz);const HF=G.factions.length-1;const t=G.spawnUnit('ltank',HF,x+14,zz+2);window.__t=t;window.__a=a;
  const c=__cam.cam;c.x=x+6;c.z=zz+1;c.d=22;c.pitch=.75;c.yaw=.3;__cam.applyCam();return {x,zz,a:!!a,t:!!t,at:a&&a.type,HF};});
console.log(JSON.stringify(info));
for(let k=0;k<6;k++){await p.evaluate(()=>{for(let i=0;i<4;i++)__cam.G.update(.25);});await p.waitForTimeout(400);}
await p.screenshot({path:'/tmp/ct/lz_on.png'});
const st=await p.evaluate(()=>({tgt:__a.target&&__a.target.type,hp:__t.hp}));console.log(JSON.stringify(st));
await p.evaluate(()=>{__t.hp=0;__t.alive=false;});
for(let k=0;k<2;k++){await p.evaluate(()=>{__cam.G.update(.25);});await p.waitForTimeout(150);}
await p.screenshot({path:'/tmp/ct/lz_mid.png'});
for(let k=0;k<8;k++){await p.evaluate(()=>{__cam.G.update(.25);});await p.waitForTimeout(250);}
await p.screenshot({path:'/tmp/ct/lz_off.png'});
console.log('ERRS',JSON.stringify(errs.slice(0,5)));await b.close();})();
