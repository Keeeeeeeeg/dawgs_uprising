const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam()};");
fs.writeFileSync('/tmp/emg.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760}});
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));
await p.goto('file:///tmp/emg.html');await p.waitForTimeout(1200);await p.click('#playBtn');await p.waitForTimeout(400);await p.click('#startGame');await p.waitForFunction(()=>window.__cam);
await p.click('#planGo').catch(()=>{});
const mode=process.argv[3]||'hatch';
const r=await p.evaluate((mode)=>{const G=__cam.G,z=G.zones[G.homes[0]];G.factions[0].money=9000;G.factions[0].hr=200;
  const info={plots:z.plots.map(p=>p.fac&&p.fac.type+':'+p.fac.state)};
  let type=mode==='hatch'?'rover':'rifle';
  if(mode!=='hatch'){const want=mode;let p=z.plots.find(p=>p.fac&&p.fac.type===want);
    if(!p){for(let i=0;i<64&&!p;i++){const a=i*.7,r=z.r*(1.05+(i%4)*.12),x=z.x+Math.cos(a)*r,zz=z.z+Math.sin(a)*r;const ce=G.canPlace(0,z.id,want,x,zz);if(ce){info.ce=ce;continue;}
      const rr=G.applyCmd(0,{k:'place',zid:z.id,type:want,x,z:zz,ang:-Math.PI/2,ids:[]});if(rr.ok)p=G.plotOf(z,rr.pi);}}
    if(p){p.fac.state='upgrading';p.fac.t=p.fac.T;G.update(.5);}else{info.err='no '+want;}
    type=mode==='barracks'?'rifle':mode==='motorpool'?'mtank':'heli';}
  const a=G.applyCmd(0,{k:'recruit',type,zid:z.id});
  const n0=G.nextId;for(let i=0;i<4000&&z.rq&&z.rq.length;i++)G.update(.05);
  const u=G.units.filter(u=>u.f===0&&u.type===type&&u.emerge).slice(-1)[0];window.__u=u;
  const e=u&&u.emerge||{};const cx=e.fx??z.x,cz=e.fz??z.z;__cam.cam.x=cx;__cam.cam.z=cz+3;__cam.cam.d=26;__cam.applyCam();
  info.a=a.ok;info.q=z.rq&&z.rq.length;info.exit=z.rq;return info;},mode);
console.log(JSON.stringify(r).slice(0,400));
for(const [ms,f] of [[300,'1'],[700,'2'],[900,'3']]){await p.waitForTimeout(ms);await p.screenshot({path:'emg_'+mode+f+'.png'});console.log(f,await p.evaluate(()=>{const u=__u;return u?JSON.stringify(u.emerge&&{k:u.emerge.k,t:+u.emerge.t.toFixed(2)}):'-'}));}
console.log(errs.slice(0,3));await b.close();})();
