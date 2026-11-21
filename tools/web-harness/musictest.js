const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch({args:['--autoplay-policy=no-user-gesture-required']});const p=await b.newPage({viewport:{width:1100,height:800}});
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file://'+process.argv[2]);await p.waitForTimeout(1200);
await p.click('#settingsBtn');await p.waitForTimeout(300);
await p.setInputFiles('#trackFile',[__dirname+'/tone.wav']);await p.waitForTimeout(800);
const st=()=>p.evaluate(()=>[...document.querySelectorAll('#playlist li')].map(li=>li.querySelector('.tn').textContent+':'+li.querySelector('input').checked+':'+li.querySelector('small').textContent).join(' | ')+' || now='+document.querySelector('.nowPlaying').textContent+' msg='+document.querySelector('#plMsg').textContent);
console.log('after add:',await st());
await p.click('#trackSkip');await p.waitForTimeout(600);console.log('after skip:',await st());
await p.waitForTimeout(3500);console.log('after tone ends:',await st());
// disable drum
await p.locator('#playlist li').nth(0).locator('input').uncheck();await p.waitForTimeout(400);console.log('drum off:',await st());
await p.screenshot({path:'settings.png'});
await p.reload();await p.waitForTimeout(1200);await p.click('#settingsBtn');await p.waitForTimeout(500);console.log('after reload:',await st());
await p.locator('#playlist .del').first().click();await p.waitForTimeout(400);console.log('after remove:',await st());
console.log('errors',errs);await b.close();})();
