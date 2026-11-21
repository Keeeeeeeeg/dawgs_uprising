const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace("const cam=Object.assign({pitch:.98},CAM0());","const cam=Object.assign({pitch:.98},CAM0());window.__cam={cam,get G(){return G;},applyCam:()=>applyCam(),sel:ids=>{selected=new Set(ids);refreshSel();},proj:(x,y,z)=>proj(x,y,z)};");
fs.writeFileSync('/tmp/rov.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760}});
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
const errs=[];p.on('pageerror',e=>errs.push(e.message+' @'+(e.stack||'').split('\n').slice(1,3).join('|')));
await p.goto('file:///tmp/rov.html');await p.waitForTimeout(1200);await p.click('#playBtn');await p.waitForTimeout(400);await p.click('#startGame');await p.waitForFunction(()=>window.__cam);await p.waitForTimeout(800);
const r=await p.evaluate(()=>{const G=__cam.G;const rv=G.units.find(u=>u.f===0&&u.def.builder);const z=G.zones[G.homes[0]];__cam.sel([rv.id]);
  __cam.cam.x=z.x+20;__cam.cam.z=z.z+10;__cam.cam.d=80;__cam.applyCam();return {rv:rv.id,z:z.name};});
await p.waitForTimeout(800);await p.screenshot({path:'rov_0.png'});
await p.evaluate(()=>{const b=document.querySelector('[data-place="depot"]');b&&b.click();});await p.waitForTimeout(300);
// move the mouse around to find a valid spot
const spots=await p.evaluate(()=>{const G=__cam.G;const z=G.zones[G.homes[0]];return z.spots.filter(s=>!s.used).map(s=>{const q=__cam.proj(s.x,G.heightAt(s.x,s.z),s.z);return [q.x,q.y];});});
let ok=false;for(const [x,y] of spots){if(x<20||y<80||x>1260||y>480)continue;await p.mouse.move(x,y);await p.waitForTimeout(150);
  const t=await p.evaluate(()=>document.querySelector('#modeTag').textContent);if(t.includes('click to build')){ok=true;break;}}
await p.mouse.wheel(0,100);await p.waitForTimeout(200);
await p.screenshot({path:'rov_1holo.png'});
console.log('valid spot found',ok,await p.evaluate(()=>document.querySelector('#modeTag').textContent));
if(ok){const pos=await p.evaluate(()=>0);await p.mouse.down();await p.mouse.up();}
await p.waitForTimeout(500);
for(let i=0;i<6;i++){await p.waitForTimeout(2500);}
await p.screenshot({path:'rov_2build.png'});
console.log(await p.evaluate(()=>{const G=__cam.G;const z=G.zones[G.homes[0]];return z.plots.map(p=>p.fac.type+':'+p.fac.state+':'+Math.round(p.fac.t)+'/'+p.fac.T+' crew '+p.fac.crew);}));
console.log(errs);await b.close();})();
