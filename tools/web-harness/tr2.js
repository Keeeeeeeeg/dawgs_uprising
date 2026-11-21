const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace("const cam=Object.assign({pitch:.98},CAM0());","const cam=Object.assign({pitch:.98},CAM0());window.__cam={cam,get G(){return G;},T:TRANSIT,lineAt,applyCam:()=>applyCam()};");
fs.writeFileSync('/tmp/tr.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760}});
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file:///tmp/tr.html');await p.waitForTimeout(1200);await p.click('#playBtn');await p.waitForTimeout(400);
await p.evaluate(m=>{const c=[...document.querySelectorAll('#mapCards [data-map], #mapCards button, #mapCards .mapcard')].find(e=>(e.dataset.map||'')===m||e.textContent.toLowerCase().includes(m));if(c)c.click();},process.argv[3]||'dawgs');
await p.click('#startGame');await p.waitForFunction(()=>window.__cam,null,{timeout:60000});await p.waitForTimeout(1500);
const info=await p.evaluate(()=>{const T=__cam.T;return {roads:T.roads.length,rails:T.rails.length,rlen:T.rails.map(l=>Math.round(l.len)),roadlen:Math.round(T.roads.reduce((a,l)=>a+l.len,0))};});console.log(JSON.stringify(info));
for(const [i,k] of [[0,'rail'],[1,'road']]){await p.evaluate(k=>{const T=__cam.T;const L=k==='rail'?T.rails[0]:T.roads[2];const q=__cam.lineAt(L,L.len*.5);__cam.cam.x=q.x;__cam.cam.z=q.z;__cam.cam.d=55;__cam.applyCam();},k);
  await p.waitForTimeout(2500);await p.screenshot({path:'tr_'+k+'.png'});}
console.log(errs);await b.close();})();
