const {chromium}=require('playwright');const fs=require('fs');
const src=fs.readFileSync('/home/claude/vu/patches/flags.js','utf8');
const html=`<html><body style="background:#333;margin:0"><canvas id=c width=900 height=420></canvas><script>${src}
const c=document.getElementById('c').getContext('2d');FLAGS.KEYS.forEach((k,i)=>{FLAGS.draw(c,k,20+i*175,20,160,107,1);FLAGS.draw(c,k,20+i*175,145,160,107,i?2:1);FLAGS.emblem(c,k,100+i*175,330,60);});</script></body></html>`;
fs.writeFileSync('/tmp/ct/fl.html',html);
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:900,height:420}});await p.goto('file:///tmp/ct/fl.html');await p.waitForTimeout(500);await p.screenshot({path:'/tmp/ct/flags.png'});await b.close();})();
