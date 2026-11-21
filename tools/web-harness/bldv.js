const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace("const cam=Object.assign({pitch:.98},CAM0());","const cam=Object.assign({pitch:.98},CAM0());window.__cam={cam,get G(){return G;},applyCam:()=>applyCam()};");
fs.writeFileSync('/tmp/bv.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760}});
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));
await p.goto('file:///tmp/bv.html');await p.waitForTimeout(1200);await p.click('#playBtn');await p.waitForTimeout(400);await p.click('#startGame');await p.waitForFunction(()=>window.__cam);
await p.click('#planGo').catch(()=>{});
await p.evaluate(()=>{const G=__cam.G,z=G.zones[G.homes[0]],bk=z.plots.find(p=>p.fac.type==='barracks');bk.body.hp=.3;window.__bk=bk;
  const ts=G.units.filter(u=>u.f===1&&u.alive&&!u.def.static&&!u.def.air&&!u.def.builder).slice(0,3);ts.forEach((t,i)=>{t.x=bk.x+5+i;t.z=bk.z+3;t.ax=t.x;t.az=t.z;});G.orderAs(1,'attack',ts.map(t=>t.id),bk.body);
  __cam.cam.x=bk.x;__cam.cam.z=bk.z;__cam.cam.d=38;__cam.applyCam();});
for(let i=0;i<200;i++){await p.waitForTimeout(150);const g=await p.evaluate(()=>!!window.__bk.gone);if(g){break;}}
await p.waitForTimeout(450);await p.screenshot({path:'boom1.png'});await p.waitForTimeout(1500);await p.screenshot({path:'boom2.png'});
console.log('gone',await p.evaluate(()=>!!window.__bk.gone),errs.slice(0,3));await b.close();})();
