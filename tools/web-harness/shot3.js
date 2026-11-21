const {chromium}=require('playwright');const fs=require('fs');
const src=process.argv[2],map=process.argv[3]||'dawgs',out=process.argv[4]||'ui';
let h=fs.readFileSync(src,'utf8');h=h.replace("const cam=Object.assign({pitch:.98},CAM0());","const cam=Object.assign({pitch:.98},CAM0());window.__cam={cam,get G(){return G;},applyCam:()=>applyCam()};");
fs.writeFileSync('/tmp/u_'+map+'.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760}});
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));p.on('console',m=>{if(m.type()==='error')errs.push(m.text());});
await p.goto('file:///tmp/u_'+map+'.html');await p.waitForTimeout(1500);
await p.click('#playBtn');await p.waitForTimeout(500);
await p.evaluate(m=>{const c=[...document.querySelectorAll('#mapCards [data-map], #mapCards button, #mapCards .mapcard')].find(e=>(e.dataset.map||'')===m||e.textContent.toLowerCase().includes(m));if(c)c.click();},map);
await p.waitForTimeout(300);await p.click('#startGame');await p.waitForTimeout(3000);
await p.screenshot({path:out+'_0none.png'});
// select all units near home with a drag box
await p.mouse.move(300,150);await p.mouse.down();await p.mouse.move(1000,480,{steps:5});await p.mouse.up();await p.waitForTimeout(500);
await p.screenshot({path:out+'_1units.png'});
await p.evaluate(()=>{const b=document.querySelector('[data-stance="hold"]');if(b)b.click();});await p.waitForTimeout(400);
await p.screenshot({path:out+'_2hold.png'});
const st=await p.evaluate(()=>{const G=__cam.G;return G.units.filter(u=>u.f===0&&u.stance).length;});console.log('units with stance',st);
// select home base by clicking its centre
const pos=await p.evaluate(()=>{const G=__cam.G;const z=G.zones.find(z=>z.home===0);__cam.cam.x=z.x;__cam.cam.z=z.z;__cam.cam.d=90;__cam.applyCam();return {x:z.x,z:z.z};});
await p.waitForTimeout(600);await p.mouse.click(640,300);await p.waitForTimeout(400);
await p.evaluate(()=>{});await p.waitForTimeout(500);
await p.screenshot({path:out+'_3base.png'});
await p.evaluate(()=>{const b=document.querySelector('[data-build]:not([disabled])');if(b)b.click();});await p.waitForTimeout(600);
await p.screenshot({path:out+'_4built.png'});
await p.evaluate(()=>{const b=document.querySelector('[data-tab="recruit"]');if(b)b.click();});await p.waitForTimeout(400);
await p.screenshot({path:out+'_5recruit.png'});
console.log('errors:',errs.slice(0,8));await b.close();})();
