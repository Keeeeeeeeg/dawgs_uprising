const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam(),FX:CITY_FX,meshes};");
h=h.replace("let zepSub=nullXX;","let zepSub=null;window.__zc=(u,k)=>{zepSub=k?{id:u.id,key:k}:null;return ucardHTML(u);};");
fs.writeFileSync('/tmp/ct/h.html',h);
const hide=`let c=document.querySelector('canvas');while(c&&c!==document.body){for(const e of c.parentElement.children)if(e!==c&&e.tagName!=='SCRIPT')e.style.visibility='hidden';c=c.parentElement;}`;
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:900,height:560}});p.setDefaultTimeout(400000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));
await p.goto('file:///tmp/ct/h.html');await p.waitForTimeout(1500);await p.evaluate(()=>document.querySelector('#playBtn').click());await p.waitForTimeout(3000);await p.evaluate(()=>document.querySelector('#startGame').click());await p.waitForFunction(()=>window.__cam,null,{timeout:60000}).catch(e=>{console.log('ERRS',errs);process.exit(1);});
await p.waitForTimeout(4000);
const r=await p.evaluate(()=>{const G=__cam.G;const h=G.zones[G.homes[0]];let x=h.x,z=h.z;for(let a=0;a<6.28;a+=.2){const X=h.x+Math.cos(a)*55,Z=h.z+Math.sin(a)*55;let ok=true;for(let i=-16;i<=16;i+=2)for(let j=-16;j<=16;j+=2)if(!G.passable(X+i,Z+j)||G.heightAt(X+i,Z+j)<1)ok=false;if(ok){x=X;z=Z;break;}}
  const v=G.spawnUnit('airship',1,x,z);window.__v=v;const q=G.spawnUnit('htank',2,x-14,z+6);window.__q=q;q.ang=1;const s=G.spawnUnit('how',0,x-10,z-8);window.__s=s;
  
  window.__shots={};G.on('shot',(u,p)=>{const k=u.type+':'+(p&&p.zm!=null?(p.zm>=10?'aa':'ball'):p.wpn);__shots[k]=(__shots[k]||0)+1;});return 1;});
await p.evaluate(()=>{for(let i=0;i<60;i++)__cam.G.update(.1);});
await p.evaluate(hide);
const shot=async(n,u,yaw,pitch,d)=>{await p.evaluate(([u,yaw,pitch,d])=>{const U=window[u],c=__cam.cam,Y=__cam.G.unitY(U);c.x=U.x-Math.sin(yaw)*Y/Math.tan(pitch);c.z=U.z-Math.cos(yaw)*Y/Math.tan(pitch);c.yaw=yaw;c.pitch=pitch;c.d=d+Y/Math.sin(pitch);__cam.applyCam();},[u,yaw,pitch,d]);await p.waitForTimeout(5000);await p.screenshot({path:'/tmp/ct/'+n+'.png'});};
await shot('fz1','__v',1.6,.35,40);
await p.evaluate(()=>{for(let i=0;i<20;i++)__cam.G.update(.1);});
await shot('fz2','__q',2.0,.45,10);
await p.evaluate(()=>{__s.deployed=false;});
await shot('fz3','__s',.8,.5,14);
await p.evaluate(()=>{const G=__cam.G,h=G.zones[G.homes[0]],c=__cam.cam;c.x=h.x;c.z=h.z;c.yaw=.5;c.pitch=.5;c.d=40;__cam.applyCam();});await p.waitForTimeout(5000);await p.screenshot({path:'/tmp/ct/fz4.png'});
console.log('errs',errs.slice(0,6));await b.close();})();
