const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam()};");
fs.writeFileSync('/tmp/ct/rg.html',h);const map=process.argv[3]||'twinvalleys';
const process_yaw=+(process.argv[4]||0.8);(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760}});p.setDefaultTimeout(400000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));
await p.goto('file:///tmp/ct/rg.html');await p.waitForTimeout(1500);await p.evaluate(()=>document.querySelector('#playBtn').click());await p.waitForTimeout(1500);
await p.evaluate(m=>{const c=document.querySelector('[data-map="'+m+'"]');if(c)c.click();},map);await p.waitForTimeout(500);
await p.evaluate(()=>document.querySelector('#startGame').click());await p.waitForFunction(()=>window.__cam&&window.__cam.G,null,{timeout:300000});await p.waitForTimeout(2000);
const info=await p.evaluate((process_yaw)=>{const G=__cam.G;const z=G.zones.find(q=>q.air&&q.owner===0)||G.zones.find(q=>q.air);z.owner=0;const A=z.air;
  for(const k of [0,1]){const t=A.terms[k];const u=G.spawnUnit(k?'bomb':'cas',z.owner==null?0:z.owner,t.x,t.z);u.homeZone=z;u.pstate='ground';u.landed=true;u.altK=0;u.term=k;t.u=u;u.ang=A.ang+Math.PI/2;u.rearmT=u.rearmMax=999;u.repairRate=0;u.manual=true;}
  const t=A.terms[0],c=__cam.cam;c.x=t.x+A.nx*1.5+A.ux*-3;c.z=t.z+A.nz*1.5+A.uz*-3;c.d=20;c.pitch=.6;c.yaw=Math.atan2(A.uz,A.ux)+(+process_yaw);__cam.applyCam();
  let c2=document.querySelector('canvas');while(c2&&c2!==document.body){for(const e of c2.parentElement.children)if(e!==c2&&e.tagName!=='SCRIPT')e.style.visibility='hidden';c2=c2.parentElement;}
  return z.name;},process_yaw);
console.log(info);
for(const [i,w] of [[0,1500],[1,4000],[2,3000]]){await p.waitForTimeout(w);await p.screenshot({path:'/tmp/ct/rig_'+i+'.png'});}
console.log(errs.slice(0,4));await b.close();})();
