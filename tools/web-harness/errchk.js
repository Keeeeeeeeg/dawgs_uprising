const {chromium}=require('playwright');const fs=require('fs');
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760}});
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());const errs=[];p.on('pageerror',e=>errs.push(e.message+' | '+(e.stack||'').split('\n').slice(1,3).join(' ')));
await p.goto('file://'+process.argv[2]);await p.waitForTimeout(2500);
await p.evaluate(()=>{const b=[...document.querySelectorAll('button')].find(b=>/skirmish/i.test(b.textContent));if(b)b.click();});await p.waitForTimeout(800);
await p.evaluate(()=>{const b=[...document.querySelectorAll('button')].find(b=>/^\s*(start|begin|deploy|fight)/i.test(b.textContent)&&b.offsetParent);if(b)b.click();});
await p.waitForTimeout(60000);console.log(JSON.stringify(errs.slice(0,5),null,1));await b.close();})();
