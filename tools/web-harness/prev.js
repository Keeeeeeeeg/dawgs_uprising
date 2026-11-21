const {chromium}=require('playwright');const fs=require('fs');fs.writeFileSync('/tmp/ct/pv.html',fs.readFileSync(process.argv[2],'utf8'));
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:760}});
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file:///tmp/ct/pv.html');await p.waitForTimeout(1500);await p.evaluate(()=>document.querySelector('#playBtn').click());await p.waitForTimeout(1500);
await p.screenshot({path:'/tmp/ct/setup.png'});console.log(errs);await b.close();})();
