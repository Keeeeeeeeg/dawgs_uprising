const {chromium}=require('playwright');const fs=require('fs');
{let h=fs.readFileSync(process.argv[2],'utf8');h=h.replace("heli:true};}catch(e){console.warn('menu zeppelin',e);ZEP=null;}}","heli:true};window.__Z=ZEP;window.__CAM=camera;}catch(e){console.warn('menu zeppelin',e);ZEP=null;}}");fs.writeFileSync('/tmp/ct/mb.html',h);}
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1200,height:700}});p.setDefaultTimeout(400000);
await p.route('**/three.min.js',r=>r.fulfill({path:__dirname+'/three/package/build/three.min.js',contentType:'application/javascript'}));
await p.route('**/fonts.googleapis.com/**',r=>r.abort());
await p.route('**/tex/*.jpg',r=>{const n=r.request().url().split('/').pop();const fp='/home/claude/vu/tex/'+n;if(fs.existsSync(fp))r.fulfill({path:fp});else r.abort();});
const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').split('\n')[1]));p.on('console',m=>{if(/menu|Error|error/.test(m.text()))errs.push('console: '+m.text().slice(0,300));});
await p.goto('file:///tmp/ct/mb.html');await p.waitForTimeout(6000);
await p.evaluate(()=>{document.querySelector('#modal').style.visibility='hidden';});
for(const i of (process.argv[3]||'0,2,3,4').split(',').map(Number)){await p.evaluate(i=>{MenuBG.scene(i);MenuBG.advance(+(window.ADV||6));},i);await p.waitForTimeout(4500);await p.screenshot({path:'/tmp/ct/mbg'+i+'.png'});console.log('scene',i,await p.evaluate(()=>{const Z=window.__Z,c=window.__CAM;if(!Z)return 'noZ';const v=Z.m.position.clone();v.project(c);return [Z.x.toFixed(1),Z.y.toFixed(1),v.x.toFixed(2),v.y.toFixed(2),Z.m.visible,Z.m.scale.x.toFixed(2)];}));}
console.log('errs',errs.slice(0,8));await b.close();})();
