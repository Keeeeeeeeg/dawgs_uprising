const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});
for(const idx of [1,3,5,9]){const p=await b.newPage({viewport:{width:1280,height:760}});
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));
await p.goto('file://'+require('path').resolve(process.argv[2]));await p.waitForTimeout(1000);await p.click('#playBtn');await p.waitForTimeout(400);
const nm=await p.evaluate(i=>{const c=document.querySelectorAll('#mapCards > *');if(!c[i])return 'none';c[i].click();return c[i].innerText.split('\n')[0]+' /'+c.length;},idx);
await p.click('#startGame');await p.waitForTimeout(9000);console.log(nm,errs.slice(0,3));await p.close();}
await b.close();})();
