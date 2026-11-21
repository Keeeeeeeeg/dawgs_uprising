const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam()};");
h=h.replace("let zepSub=null;","let zepSub=null;window.__zc=(u,k)=>{zepSub=k?{id:u.id,key:k}:null;return ucardHTML(u);};window.__zp=(u,nm)=>{const m=meshes.get(u.id);let t=null;m.traverse(o=>{if(!t&&o.userData.zmount===nm)t=o;});const v=new THREE.Vector3();new THREE.Box3().setFromObject(t).getCenter(v);v.project(camera);return zepPartAt(u,(v.x+1)/2*VW,(1-v.y)/2*VH);};");
fs.writeFileSync('/tmp/ct/h.html',h);
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:900,height:560}});p.setDefaultTimeout(400000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));
await p.goto('file:///tmp/ct/h.html');await p.waitForTimeout(1500);await p.evaluate(()=>document.querySelector('#playBtn').click());await p.waitForTimeout(3000);await p.evaluate(()=>document.querySelector('#startGame').click());await p.waitForFunction(()=>window.__cam);
await p.waitForTimeout(5000);
const r=await p.evaluate(()=>{const G=__cam.G;const h=G.zones[G.homes[0]];const x=h.x+30,z=h.z;
  const v=G.spawnUnit('airship',0,x,z);window.__v=v;const e=[];for(let i=0;i<4;i++)e.push(G.spawnUnit('rifle',1,x+(i-2)*4,z+20));e.push(G.spawnUnit('rifle',1,x+1,z+1));e.push(G.spawnUnit('rifle',1,x+60,z+40));
  __cam.cam.x=x;__cam.cam.z=z;__cam.applyCam();window.__shots={};G.on('shot',(u,p)=>{if(u===v){const k=p&&p.zm!=null?(p.zm>=10?'aa':'ball'):'main';__shots[k]=(__shots[k]||0)+1;}});return e.length;});
await p.evaluate(()=>{for(let i=0;i<250;i++)__cam.G.update(.1);});await p.waitForTimeout(3000);
const o=await p.evaluate(()=>{const v=__v;const c0=__zc(v,null),c1=__zc(v,'ball'),c2=__zc(v,'aa');const s=t=>t.replace(/<[^>]+>/g,' ').replace(/\s+/g,' ').slice(0,260);
  let pa=null,pb=null;try{pa=__zp(v,'ball');pb=__zp(v,'aa');}catch(e){pa='ERR '+e.message;}
  const G=__cam.G;const en=G.units.filter(o=>o.f===1&&o.alive).map(o=>[Math.round(o.x-v.x),Math.round(o.z-v.z),G.hostile?G.hostile(0,1):'?']);return {en,t:G.time,mg:JSON.stringify((v.mg||[]).map(a=>a.map(g=>g.t&&g.t.id))),y0:v.y,mode:v.mode,stance:v.stance,shots:__shots,y:v.y,hp:v.hp,main:s(c0),ball:s(c1),aa:s(c2),pickBall:pa,pickAA:pb};});
console.log(JSON.stringify(o,null,1));console.log('errs',errs.slice(0,5));await b.close();})();
