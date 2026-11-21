const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace("const cam=Object.assign({pitch:.98},CAM0());","const cam=Object.assign({pitch:.98},CAM0());window.__cam={cam,get G(){return G;},applyCam:()=>applyCam(),sel:ids=>{selected=new Set(ids);refreshSel();}};");
fs.writeFileSync('/tmp/rd.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760}});
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file:///tmp/rd.html');await p.waitForTimeout(1200);await p.click('#playBtn');await p.waitForTimeout(400);
await p.evaluate(()=>{const c=document.querySelector('#fogChk');if(c&&!c.checked)c.click();});
await p.click('#startGame');await p.waitForFunction(()=>window.__cam);await p.waitForTimeout(500);
const r=await p.evaluate(()=>{const G=__cam.G,z=G.zones[G.homes[0]],rv=G.units.find(u=>u.f===0&&u.def.builder);G.factions[0].money=2000;
  const s=z.spots.find(s=>!s.used&&!G.canPlace(0,z.id,'radar',s.x,s.z));const s2=z.spots.find(q=>q!==s&&!q.used&&!G.canPlace(0,z.id,'market',q.x,q.z)&&Math.hypot(q.x-s.x,q.z-s.z)>8);
  const a=G.applyCmd(0,{k:'place',zid:z.id,type:'radar',x:s.x,z:s.z,ang:.5,ids:[rv.id]});
  for(let i=0;i<300;i++)G.update(.1);for(let i=0;i<6;i++){const e=G.units.find(u=>u.f===1&&!u.def.static&&!u.def.air&&u.garrison===null&&!u.def.builder&&!u.moved);if(e){e.moved=1;e.x=s.x+90+i*4;e.z=s.z+10+i*3;e.ax=e.x;e.az=e.z;}}
  const b2=G.applyCmd(0,{k:'place',zid:z.id,type:'market',x:s2.x,z:s2.z,ang:1,ids:[rv.id]});for(let i=0;i<80;i++)G.update(.1);
  __cam.sel([rv.id]);__cam.cam.x=s.x;__cam.cam.z=s.z;__cam.cam.d=70;__cam.applyCam();return [a,b2,z.plots.map(p=>p.fac.type+':'+p.fac.state)];});
console.log(JSON.stringify(r));await p.waitForTimeout(2500);await p.screenshot({path:'rd.png'});
await p.evaluate(()=>{__cam.cam.d=260;__cam.cam.x+=50;__cam.applyCam();});await p.waitForTimeout(1500);await p.screenshot({path:'rd_far.png'});
console.log(errs);await b.close();})();
