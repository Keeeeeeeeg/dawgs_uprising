p='/home/claude/vu/v18.html';s=open(p).read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(s.count(a),a[:80]);s=s.replace(a,b)
# sim: a ping is just broadcast to every machine
rep("      case 'place':return place(","      case 'ping':if(isFinite(c.x)&&isFinite(c.z))emit('ping',f,+c.x,+c.z);return {ok:true};\n      case 'place':return place(")
# bar spans the full width so the minimap sits in the bottom-left corner
rep("width:min(1260px,calc((100% - 16px) / var(--ui)));height:262px;","width:calc((100% - 16px) / var(--ui));height:262px;")
rep("#cmd{left:50%;transform:translateX(-50%) scale(var(--ui));transform-origin:50% 100%;","#cmd{left:8px;transform:scale(var(--ui));transform-origin:0 100%;")
rep("#mapBox{padding:8px;border-right:1px solid var(--line);display:flex;align-items:center}",
    "#mapBox{position:relative;padding:8px;border-right:1px solid var(--line);display:flex;align-items:center}\n#bPing{position:absolute;top:12px;left:12px;z-index:2;font-family:var(--f-display);font-size:10px;letter-spacing:.1em;text-transform:uppercase;padding:3px 7px;background:rgba(20,22,16,.85);border:1px solid var(--line-hi);color:var(--warn)}\n#bPing[aria-pressed=\"true\"]{background:var(--warn);color:var(--ink)}\n#bPing kbd{font-family:var(--f-mono);font-size:9.5px;margin-left:4px;color:inherit;opacity:.8}")
rep('<div id="mapBox"><canvas id="mini"','<div id="mapBox"><button id="bPing" title="Ping: click a spot on the map or the minimap to alert your team (I)">Ping<kbd>I</kbd></button><canvas id="mini"')
# arm, drop, show
rep("function setArm(m){","function setArm(m){$('#bPing').setAttribute('aria-pressed',String(m==='ping'));")
rep("t.textContent=armed==='missile'?","t.textContent=armed==='ping'?'PING · click a spot on the map or minimap · Esc cancels':armed==='missile'?")
rep("function doArmed(g,keep){\n","function doArmed(g,keep){\n  if(armed==='ping'){A.ping(g.x,g.z);setArm(null);return;}\n")
rep("  place:(zid,type,x,z,ang,ids)=>","  ping:(x,z)=>act({k:'ping',x,z}),\n  place:(zid,type,x,z,ang,ids)=>")
rep("mini.addEventListener('pointerdown',e=>{const w=miniToWorld(e);\n","mini.addEventListener('pointerdown',e=>{const w=miniToWorld(e);\n  if(armed==='ping'&&e.button===0){A.ping(w.x,w.z);setArm(null);return;}\n")
rep("$('#autoG').onchange=e=>{A.autogar(e.target.checked);};","$('#autoG').onchange=e=>{A.autogar(e.target.checked);};\n$('#bPing').onclick=()=>{if(placing)stopPlacing();setArm(armed==='ping'?null:'ping');};")
rep("  else if(k==='m'){const m=hooks.toggleMute();","  else if(k==='i'){$('#bPing').click();}\n  else if(k==='m'){const m=hooks.toggleMute();")
rep("  G.on('log',(t,f)=>pushLog(t,f));","""  G.on('log',(t,f)=>pushLog(t,f));
  // pings: shown to you and everyone on your team, with a beacon on the map and the minimap
  G.on('ping',(f,x,z)=>{if(f!==ME&&!G.allied(f,ME))return;
    pings.push({x,z,t:performance.now()});pingBeacon(x,z,FACTIONS[f].color);
    if(f!==ME){pushLog(`${FACTIONS[f].name} pinged the map.`,f,true);hooks.alarm&&hooks.alarm();toast(`${FACTIONS[f].name} pinged a spot: see the minimap`,true);}});""")
rep("let pings=[];","""let pings=[];
// a pulsing column of light where someone pinged
const beacons=[],BEACON_GEO=new THREE.CylinderGeometry(.9,.9,40,16,1,true).translate(0,20,0);
function pingBeacon(x,z,col){const m=new THREE.Mesh(BEACON_GEO,new THREE.MeshBasicMaterial({color:col,transparent:true,opacity:.5,depthWrite:false,blending:THREE.AdditiveBlending,side:THREE.DoubleSide}));
  m.position.set(x,G.heightAt(x,z),z);scene.add(m);beacons.push({m,t:0});marker(x,z,col,3);}
function updateBeacons(dt){for(let i=beacons.length-1;i>=0;i--){const b=beacons[i];b.t+=dt;const k=b.t/6;
  if(k>=1){scene.remove(b.m);b.m.material.dispose();beacons.splice(i,1);continue;}
  b.m.material.opacity=.55*(1-k)*(.6+.4*Math.sin(b.t*8));const s=1+Math.sin(b.t*4)*.25;b.m.scale.set(s,1,s);}}""")
rep("  syncScene(dt);updateFX(dt);updateMarkers(dt);","  syncScene(dt);updateFX(dt);updateMarkers(dt);updateBeacons(dt);")
# help
rep("      <kbd>H</kbd><span>Halt</span>\n","      <kbd>H</kbd><span>Halt</span>\n      <kbd>I or Ping</kbd><span>Ping: click a spot on the map or minimap. Everyone on your team sees a beacon and gets an alert</span>\n")
rep("Click the <b>minimap</b> (bottom left) to jump anywhere.","Click the <b>minimap</b> (bottom left) to jump anywhere; its <b>Ping</b> button marks a spot for your team.")
open(p,'w').write(s)
