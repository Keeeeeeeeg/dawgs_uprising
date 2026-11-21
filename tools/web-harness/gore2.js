const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam(),gb:u=>gibBurst(u),bs:(x,z,r)=>bloodSplat(x,z,r),sp:(x,y,z)=>bloodSpray(x,y,z,1,0,6,1.2),run:n=>{for(let i=0;i<n;i++){FDT=.03;gibTick();}},BLDf:()=>{BLD.mat.uniforms.uF.value=1e5;},BLDd:()=>({i:BLD.i,has:!!BLD.geo,inScene:BLD.geo?scene.children.some(o=>o.geometry===BLD.geo):0,uT:BLD.mat&&BLD.mat.uniforms.uT.value,t0:BLD.geo&&BLD.geo.attributes.t0.array[0],p:BLD.geo&&Array.from(BLD.geo.attributes.position.array.slice(0,6))}),gp:()=>GIBS.map(g=>[+g.m.position.x.toFixed(2),+g.m.position.y.toFixed(2),+g.m.position.z.toFixed(2),g.n,g.lie])};");
fs.writeFileSync('/tmp/ct/h4.html',h);
const hide=`let c=document.querySelector('canvas');while(c&&c!==document.body){for(const e of c.parentElement.children)if(e!==c&&e.tagName!=='SCRIPT')e.style.visibility='hidden';c=c.parentElement;}`;
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:900,height:560}});p.setDefaultTimeout(400000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));
await p.goto('file:///tmp/ct/h4.html');await p.waitForTimeout(1500);await p.evaluate(()=>document.querySelector('#playBtn').click());await p.waitForTimeout(3000);await p.evaluate(()=>document.querySelector('#startGame').click());await p.waitForFunction(()=>window.__cam,null,{timeout:90000}).catch(()=>{console.log('ERRS',errs);process.exit(1);});
await p.waitForTimeout(3000);await p.evaluate(hide);
const r=await p.evaluate(()=>{const G=__cam.G;const h=G.zones[G.homes[0]];let x=h.x,z=h.z;for(let a=0;a<6.28;a+=.2){const X=h.x+Math.cos(a)*55,Z=h.z+Math.sin(a)*55;let ok=true;for(let i=-8;i<=8;i+=2)for(let j=-8;j<=8;j+=2)if(!G.passable(X+i,Z+j)||G.heightAt(X+i,Z+j)<1)ok=false;if(ok){x=X;z=Z;break;}}
  for(let k=0;k<3;k++){__cam.gb({x:x+k*1.2,z:z,f:k,ang:0,killX:x+k*1.2-3,killZ:z+.5});}__cam.bs(x-1.5,z+1,.5);__cam.bs(x-2,z-1,.3);__cam.run(140);__cam.sp(x-1,G.heightAt(x,z)+.5,z);
  __cam.BLDf();const c=__cam.cam;c.x=x+1;c.z=z;c.yaw=.5;c.pitch=.75;c.d=9;__cam.applyCam();return __cam.gp();});
console.log(JSON.stringify(r));await p.waitForTimeout(4000);await p.screenshot({path:'/tmp/ct/gore_e.png'});
await p.evaluate(()=>{const c=__cam.cam;c.pitch=1.2;c.d=7;__cam.applyCam();});await p.waitForTimeout(4000);await p.screenshot({path:'/tmp/ct/gore_f.png'});
console.log(await p.evaluate(()=>{const B=__cam.BLDd();return B;}));console.log('errs',errs.slice(0,5));await b.close();})();
