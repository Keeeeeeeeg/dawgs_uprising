const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch({args:['--autoplay-policy=no-user-gesture-required']});const p=await b.newPage();
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.goto('file:///home/claude/vu/v19.html');await p.waitForTimeout(1200);
const r=await p.evaluate(async()=>{const a=new Audio('music/battle2.mp3');await new Promise(res=>{a.onloadedmetadata=res;a.onerror=res;setTimeout(res,4000);});return a.duration;});
console.log('duration',r,[...document.querySelectorAll?[]:[]]);
await p.click('#settingsBtn');await p.waitForTimeout(300);console.log(await p.evaluate(()=>document.querySelector('#playlist').innerText.replace(/\n+/g,' | ')));
await b.close();})();
