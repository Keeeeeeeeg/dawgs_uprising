const {chromium}=require('playwright');const fs=require('fs');
const src=process.argv[2],map=process.argv[3],out=process.argv[4]||'s2';
let h=fs.readFileSync(src,'utf8');h=h.replace("const cam=Object.assign({pitch:.98},CAM0());","const cam=Object.assign({pitch:.98},CAM0());window.__cam={cam,get G(){return G;},applyCam:()=>applyCam()};");
fs.writeFileSync('/tmp/t_'+map+'.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1100,height:700}});
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
const errs=[];p.on('pageerror',e=>errs.push(e.message));p.on('console',m=>{if(m.type()==='error')errs.push(m.text());});
await p.goto('file:///tmp/t_'+map+'.html');await p.waitForTimeout(1500);
await p.click('#playBtn');await p.waitForTimeout(500);
await p.evaluate(m=>{const c=[...document.querySelectorAll('#mapCards [data-map], #mapCards button, #mapCards .mapcard')].find(e=>(e.dataset.map||'')===m||e.textContent.toLowerCase().includes(m));if(c)c.click();},map);
await p.waitForTimeout(300);await p.click('#startGame');await p.waitForTimeout(3500);
const targets=await p.evaluate(()=>{const G=__cam.G;const t=[];
  for(const z of G.zones){if(z.type==='airbase'&&!t.some(q=>q.k==='air'))t.push({k:'air',x:z.x,z:z.z,d:70});
    if(z.cove&&t.filter(q=>q.k==='cove').length<3)t.push({k:'cove',x:(z.x+z.cove.ax)/2,z:(z.z+z.cove.az)/2,d:80,n:z.name});
    if(z.type==='town'&&!z.port&&!t.some(q=>q.k==='town'))t.push({k:'town',x:z.x,z:z.z,d:110});}
  return t;});
let i=0;for(const t of targets){await p.evaluate(t=>{__cam.cam.x=t.x;__cam.cam.z=t.z;__cam.cam.d=t.d;__cam.applyCam();},t);await p.waitForTimeout(1200);
  await p.screenshot({path:`${out}_${i}_${t.k}.png`});i++;}
console.log(JSON.stringify(targets));console.log('errors:',errs.slice(0,5));await b.close();})();
