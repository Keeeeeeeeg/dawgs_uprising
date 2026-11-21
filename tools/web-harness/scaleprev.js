const {chromium}=require('playwright');const fs=require('fs');
const mode=process.argv[3];let h=fs.readFileSync(process.argv[2],'utf8');
const R=(a,b)=>{if(!h.includes(a))throw new Error('miss '+a.slice(0,50));h=h.replace(a,b);};
if(mode==='new'){
  R('const STRUCT_SCALE=.74,UNIT_SCALE=.85;','const STRUCT_SCALE=.74,UNIT_SCALE=.6;');
  R('sg.scale.set(k,k,k);sg.position.y=y*(1-k);','sg.scale.set(k,k*1.15,k);sg.position.y=y*(1-k*1.15);');
  R('m.scale.setScalar(STRUCT_SCALE);','m.scale.set(STRUCT_SCALE,STRUCT_SCALE*1.15,STRUCT_SCALE);');
  R("q.position.set(0,z.y,0);q.rotation.y=-(z.gate||0);g.add(q);","q.position.set(0,z.y,0);q.rotation.y=-(z.gate||0);q.scale.y=1.3;g.add(q);");
  R("const dq=new THREE.Group();dq.position.set(0,y,0);","const dq=new THREE.Group();dq.position.set(0,y,0);dq.scale.y=1.3;");
  R("return Math.max(heightAt(u.x,u.z),(z?z.y:0)+u.man.my);","return Math.max(heightAt(u.x,u.z),(z?z.y:0)+u.man.my*1.3);");
}
h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam()};");
fs.writeFileSync('/tmp/sp_'+mode+'.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760}});
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file:///tmp/sp_'+mode+'.html');await p.waitForTimeout(1200);await p.click('#playBtn');await p.waitForTimeout(400);await p.click('#startGame');await p.waitForFunction(()=>window.__cam);
await p.click('#planGo').catch(()=>{});
await p.evaluate(()=>{const G=__cam.G;
  const f=G.zones.find(z=>z.type==='fortress'),t=G.zones.find(z=>z.type==='town');window.__z={f,t,h:G.zones[G.homes[0]]};
  for(const z of [f,t]){for(const u of G.units)if(u.garrison===z.id)u.alive=false;z.owner=0;z.contested=false;}
  const inf=[];for(let i=0;i<12;i++)inf.push(G.spawnUnit(i%3?'rifle':'mg',0,f.x+2+i*.4,f.z+1));G.applyCmd(0,{k:'man',zid:f.id,ids:inf.map(u=>u.id)});
  const w=G.fortW(f,1.5,2.5);G.spawnUnit('mtank',0,w.x,w.z);const w2=G.fortW(f,4,-1);G.spawnUnit('tech',0,w2.x,w2.z);
  const tt=[];for(let i=0;i<6;i++)tt.push(G.spawnUnit('rifle',0,t.x+3+i*.8,t.z+4));G.spawnUnit('ltank',0,t.x-4,t.z+5);
  const hq=__z.h;const ww=G.wallWorld(hq,6,0);G.spawnUnit('htank',0,ww.x,ww.z);
  for(let s=0;s<40;s+=.25)G.update(.25);});
for(const [k,d,pitch,dx,dz,f] of [['f',36,.9,0,0,'fort'],['f',16,.62,3,9,'wall'],['t',24,.85,0,2,'town'],['h',52,.95,0,0,'hq']]){
  await p.evaluate(([k,d,pitch,dx,dz])=>{const z=__z[k];Object.assign(__cam.cam,{x:z.x+dx,z:z.z+dz,d,pitch});__cam.applyCam();},[k,d,pitch,dx,dz]);
  await p.waitForTimeout(1400);await p.screenshot({path:`sp_${f}_${mode}.png`,clip:{x:0,y:75,width:1280,height:370}});}
console.log(mode,errs.slice(0,3));await b.close();})();
