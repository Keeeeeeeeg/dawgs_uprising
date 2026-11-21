const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam(),sel:id=>{selected.clear();for(const i of [].concat(id))selected.add(i);refreshSel();}};");
fs.writeFileSync('/tmp/ct/fb.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1100,height:640}});p.setDefaultTimeout(400000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));
await p.goto('file:///tmp/ct/fb.html');await p.waitForTimeout(1500);await p.evaluate(()=>document.querySelector('#playBtn').click());await p.waitForTimeout(3000);await p.evaluate(()=>document.querySelector('#startGame').click());await p.waitForFunction(()=>window.__cam,null,{timeout:120000});
await p.waitForTimeout(3000);
await p.evaluate(()=>{const G=__cam.G,z=G.zones.find(q=>q.owner===0);let x=0,zz=0;for(let r=z.r+8;r<z.r+60;r+=3){let ok=false;for(let a=0;a<6.28;a+=.3){const X=z.x+Math.cos(a)*r,Z=z.z+Math.sin(a)*r;if(G.passable(X,Z)&&G.heightAt(X,Z)>1&&G.passable(X+4,Z+3)){x=X;zz=Z;ok=true;break;}}if(ok)break;}
  const ids=[];const a=G.spawnUnit('flagb',0,x,zz);a.ang=0.6;const b2=G.spawnUnit('flagb',1,x+3,zz+2);b2.ang=2.2;ids.push(a.id,b2.id);for(let i=0;i<3;i++)G.spawnUnit('rifle',0,x-2+i,zz-2.5);
  G.orderAs(1,'wave',[b2.id],true);window.__fb=[a,b2];const c=__cam.cam;c.x=x+1;c.z=zz;c.yaw=.9;c.pitch=.45;c.d=14;__cam.applyCam();__cam.sel([a.id]);});
await p.evaluate(()=>{let c=document.querySelector('canvas');while(c&&c!==document.body){for(const e of c.parentElement.children)if(e!==c&&e.tagName!=='SCRIPT')e.style.visibility='hidden';c=c.parentElement;}});
for(let i=0;i<2;i++){await p.evaluate(()=>{for(let k=0;k<2;k++)__cam.G.update(.25);const a=__fb[0],c=__cam.cam;c.x=a.x+1.5;c.z=a.z+1;c.yaw=.9;c.pitch=.75;c.d=22;__cam.applyCam();});await p.waitForTimeout(6000);await p.screenshot({path:'/tmp/ct/fb'+i+'.png'});}
console.log('errs',errs.slice(0,4),await p.evaluate(()=>[__fb[0].flagT>__cam.G.time,__fb[1].waving]));await b.close();})();
