const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1280,height:800}});
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
const errs=[];p.on('pageerror',e=>errs.push(e.message));p.on('console',m=>{if(m.type()==='error')errs.push(m.text());});
await p.goto('file://'+process.argv[2]);await p.waitForTimeout(1500);
await p.click('#playBtn');await p.waitForTimeout(500);
const map=process.argv[3]||'ventora';
await p.evaluate(m=>{const c=[...document.querySelectorAll('#mapCards [data-map], #mapCards button, #mapCards .mapcard')].find(e=>(e.dataset.map||'')===m||e.textContent.toLowerCase().includes(m));if(c)c.click();},map);
await p.waitForTimeout(300);if(process.env.FOG)await p.check('#fogChk');await p.click('#startGame');await p.waitForTimeout(4000);
await p.screenshot({path:'shot_'+map+'.png'});
// zoom out with wheel a bit
await p.mouse.move(640,400);for(let i=0;i<4;i++){await p.mouse.wheel(0,400);await p.waitForTimeout(150);}await p.waitForTimeout(800);
await p.screenshot({path:'shot_'+map+'_out.png'});
console.log('errors:',errs.slice(0,5));await b.close();})();
