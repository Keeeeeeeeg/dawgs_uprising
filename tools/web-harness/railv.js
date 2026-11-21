const {chromium}=require('playwright');const fs=require('fs');
let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace(/const cam=Object.assign\(\{pitch:.98(,yaw:0)?\},CAM0\(\)\);/,m=>m+"window.__cam={cam,get G(){return G;},applyCam:()=>applyCam()};");
fs.writeFileSync('/tmp/ct/rv.html',h);
const hide=`let c=document.querySelector('canvas');while(c&&c!==document.body){for(const e of c.parentElement.children)if(e!==c&&e.tagName!=='SCRIPT')e.style.visibility='hidden';c=c.parentElement;}`;
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:900,height:560}});p.setDefaultTimeout(600000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));
await p.goto('file:///tmp/ct/rv.html');await p.waitForTimeout(1500);await p.evaluate(()=>document.querySelector('#playBtn').click());await p.waitForTimeout(3000);await p.evaluate(()=>document.querySelector('#startGame').click());await p.waitForFunction(()=>window.__cam,null,{timeout:120000});
await p.waitForTimeout(3000);await p.evaluate(hide);
const spots=await p.evaluate(()=>{const G=__cam.G,out=[];for(const L of G.rails){let best=null,bs=0;for(let s=0;s<L.len;s+=4){const a=G.railAt(L,s),b=G.railAt(L,s+6),sl=Math.abs(G.heightAt(b.x,b.z)-G.heightAt(a.x,a.z));if(sl>bs){bs=sl;best=a;}}out.push({x:best.x,z:best.z,ang:best.ang,sl:bs});}return out.sort((a,b)=>b.sl-a.sl).slice(0,2);});
console.log(spots);
let i=0;for(const s of spots){await p.evaluate(s=>{const c=__cam.cam;c.x=s.x;c.z=s.z;c.yaw=s.ang+1.4;c.pitch=.32;c.d=26;__cam.applyCam();},s);await p.waitForTimeout(6000);await p.screenshot({path:'/tmp/ct/rail'+(i++)+'.png'});}
// a whole loop from above
await p.evaluate(()=>{const G=__cam.G,L=G.rails[0];let x=0,z=0;for(const q of L.pts){x+=q[0];z+=q[1];}const c=__cam.cam;c.x=x/L.pts.length;c.z=z/L.pts.length;c.pitch=1.2;c.d=260;__cam.applyCam();});await p.waitForTimeout(8000);await p.screenshot({path:'/tmp/ct/railtop.png'});
console.log('errs',errs.slice(0,4));await b.close();})();
