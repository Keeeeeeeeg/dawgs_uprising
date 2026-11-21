const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam(),sel:id=>{selected.clear();for(const i of [].concat(id))selected.add(i);refreshSel();}};");
fs.writeFileSync('/tmp/ct/fb2.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1100,height:640}});p.setDefaultTimeout(400000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));
await p.goto('file:///tmp/ct/fb2.html');await p.waitForTimeout(1500);await p.evaluate(()=>document.querySelector('#playBtn').click());await p.waitForTimeout(3000);await p.evaluate(()=>document.querySelector('#startGame').click());await p.waitForFunction(()=>window.__cam,null,{timeout:120000});
await p.waitForTimeout(3000);
await p.evaluate(()=>{const G=__cam.G;for(const F of G.factions)F.ai=null;const z=G.zones.find(q=>q.owner===0);let x=0,zz=0;for(let r=z.r+10;r<z.r+80;r+=3){let ok=false;for(let a=0;a<6.28;a+=.3){const X=z.x+Math.cos(a)*r,Z=z.z+Math.sin(a)*r;if(G.passable(X,Z)&&G.heightAt(X,Z)>1&&G.passable(X+10,Z+6)&&G.passable(X-6,Z+6)){x=X;zz=Z;ok=true;break;}}if(ok)break;}
  const a=G.spawnUnit('flagb',0,x,zz);const w=G.spawnUnit('flagb',0,x+7,zz+4);const mv=G.spawnUnit('flagb',0,x-6,zz+5);for(let i=0;i<4;i++)G.spawnUnit('rifle',0,x+5+i*1.2,zz+7);
  G.orderAs(0,'wave',[w.id],true);G.orderAs(0,'move',[mv.id],x+40,zz+5);window.__fb={a,w,mv,x,zz};const c=__cam.cam;c.x=x+2;c.z=zz+4;c.yaw=.5;c.pitch=.7;c.d=26;__cam.applyCam();__cam.sel([a.id]);});
await p.evaluate(()=>{for(const id of ['hud','cmd','topbar'])void id;document.querySelectorAll('#cmd,#top,.hudTop,#armies,#toast').forEach(e=>e.style.visibility='hidden');});
for(let i=0;i<3;i++){await p.evaluate(i=>{for(let k=0;k<2;k++)__cam.G.update(.25);const f=__fb,c=__cam.cam,u=[f.w,f.a,f.mv][i];c.x=u.x;c.z=u.z;c.yaw=.9;c.pitch=.95;c.d=17;__cam.applyCam();},i);await p.waitForTimeout(5000);await p.screenshot({path:'/tmp/ct/fbb'+i+'.png'});}
console.log('errs',errs.slice(0,4));await b.close();})();
