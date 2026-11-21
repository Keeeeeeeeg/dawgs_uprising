const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam()};");
fs.writeFileSync('/tmp/ct/pf.html',h);const map=process.argv[3];
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760}});p.setDefaultTimeout(400000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file:///tmp/ct/pf.html');await p.waitForTimeout(1500);await p.evaluate(()=>document.querySelector('#playBtn').click());await p.waitForTimeout(1500);
await p.evaluate(m=>{const c=document.querySelector('[data-map="'+m+'"]');if(c)c.click();},map);await p.waitForTimeout(500);
await p.evaluate(()=>document.querySelector('#startGame').click());await p.waitForFunction(()=>window.__cam&&window.__cam.G,null,{timeout:300000});await p.waitForTimeout(3000);
const hide=()=>{let c2=document.querySelector('canvas');while(c2&&c2!==document.body){for(const e of c2.parentElement.children)if(e!==c2&&e.tagName!=='SCRIPT')e.style.visibility='hidden';c2=c2.parentElement;}};
const shots=[['bridge',q=>q.sp],['bank',q=>q.bank]];
const info=await p.evaluate(()=>{const T=window.dawgsR.TRANSIT,sp=T.bridgesRail||[],G=__cam.G;let bank=null,bh=0;
  for(const L of T.rails){if(!L.profY)continue;for(let i=1;i<L.pts.length;i++){const [x,z]=L.pts[i],g=G.heightAt(x,z);if(g<.8)continue;const d=L.profY(L.cum[i])-g;if(d>bh&&d<3){bh=d;const [x0,z0]=L.pts[i-1];bank=[x,0,z,Math.atan2(z-z0,x-x0)];}}}
  return {n:sp.length,sp:sp[Math.floor(sp.length/3)],bank,bh};});
console.log(info.n);
console.log('bank',info.bh);for(const [nm,q] of [['bridge',info.sp],['bank',info.bank]]){if(!q)continue;
await p.evaluate(([q])=>{const c=__cam.cam;c.x=q[0];c.z=q[2];c.d=35;c.pitch=.4;c.yaw=q[3]+1.1;__cam.applyCam();},[q]);await p.evaluate(hide);await p.waitForTimeout(6000);await p.screenshot({path:'/tmp/ct/rb_'+map+'_'+nm+'.png'});}
console.log(errs.slice(0,3));await b.close();})();
