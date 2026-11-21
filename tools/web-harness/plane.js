const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam(),sel:id=>{selected.clear();selected.add(id);refreshSel();}};");
fs.writeFileSync('/tmp/ct/pl.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1100,height:640}});p.setDefaultTimeout(400000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));
await p.goto('file:///tmp/ct/pl.html');await p.waitForTimeout(1500);await p.evaluate(()=>document.querySelector('#playBtn').click());await p.waitForTimeout(3000);await p.evaluate(()=>document.querySelector('#startGame').click());await p.waitForFunction(()=>window.__cam,null,{timeout:120000});
await p.waitForTimeout(3000);
const id=await p.evaluate(()=>{const G=__cam.G;const z=G.zones.find(q=>q.owner!=null&&q.owner!==0)||G.zones[3];
  const tk=G.spawnUnit('mtank',z.owner||1,z.x+30,z.z+30);const u=G.spawnUnit('cas',0,tk.x-90,tk.z);u.pstate='out';u.landed=false;u.altK=1;u.ang=0;u.ammo=u.def.ammo;u.mission={type:'cas',target:tk,x:tk.x,z:tk.z};
  window.__u=u;return u.id;});
for(let i=0;i<3;i++){await p.evaluate(()=>{const G=__cam.G;for(let k=0;k<(window.__k||12);k++)G.update(.25);window.__k=4;const u=__u,c=__cam.cam;c.x=u.x;c.z=u.z+4;c.yaw=0;c.pitch=.2;c.d=40;__cam.applyCam();__cam.sel(u.id);});
  await p.waitForTimeout(5000);const info=await p.evaluate(()=>({agl:(__cam.G.unitY(__u)-__cam.G.heightAt(__u.x,__u.z)).toFixed(1),vy:(__u.vy||0).toFixed(1),gun:!!__u.gun}));console.log(info);
  await p.screenshot({path:'/tmp/ct/plane'+i+'.png'});}
console.log('errs',errs.slice(0,4));await b.close();})();
