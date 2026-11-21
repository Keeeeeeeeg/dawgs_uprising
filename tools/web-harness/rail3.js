const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam(),TR:TRANSIT,TF:TRAFFIC};");
h=h.replace("run(0);TRAFFIC.run=run;","run(0);TRAFFIC.run=run;TRAFFIC.dbg={trains,convoys,cargo};");
fs.writeFileSync('/tmp/rail3.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760}});
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));
await p.goto('file:///tmp/rail3.html');await p.waitForTimeout(1200);await p.click('#playBtn');await p.waitForTimeout(400);await p.click('#startGame');await p.waitForFunction(()=>window.__cam);
for(const kind of ['train','convoy']){
 const r=await p.evaluate(kind=>{const D=__cam.TF.dbg;let info='';
  for(let i=0;i<4000;i++){__cam.TF.run(.05);
    if(kind==='train'){const t=D.trains.find(t=>t.wait>6&&D.cargo.length>4);if(t){const st=(t.segs?((((t.S%t.tot)+t.tot)%t.tot)<t.L.len+.1?t.L.stB:t.L.stA):(t.s<1?t.L.stA:t.L.stB));if(st){Object.assign(__cam.cam,{x:st.S[0],z:st.S[1],d:26,pitch:.8,yaw:Math.atan2(st.nx,st.nz)});info='train stop '+i;break;}}}
    else{const C=D.convoys.find(c=>c.wait>7&&D.cargo.length>2);if(C){const t=C.trucks[0];const q=t.L;const D2=C.dir>0?C.DA:C.DB;Object.assign(__cam.cam,{x:D2.x,z:D2.z_,d:24,pitch:.85,yaw:0});info='convoy stop '+i;break;}}}
  __cam.applyCam();return info+' cargo '+D.cargo.length;},kind);
 console.log(r);await p.waitForTimeout(1500);await p.screenshot({path:`r3_${kind}.png`,clip:{x:0,y:75,width:1280,height:370}});}
console.log(errs.slice(0,3));await b.close();})();
