p='/home/claude/vu/v19.html';s=open(p).read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(s.count(a),a[:80]);s=s.replace(a,b)
# --- sim
rep("    aa:       {name:'AA Emplacement',","    radar:    {name:'Radar Station',   cost:150,time:24,slot:'fort',radar:140,                         desc:'Spinning dish that picks up every enemy unit within 140 m as an unidentified blip, even under the fog. Knocked out by bombing like other buildings. Upgrading reaches further.'},\n    aa:       {name:'AA Emplacement',")
rep("  const knowsPlot=(f,p)=>","""  // radar: ready, working Radar Stations of a team show where enemy units are (not what they are), through the fog
  const radarCache=[];
  function radarsOf(f){let c=radarCache[f];if(c&&G.time-c.t<.5)return c.l;const l=[];
    for(const z of G.zones)if(z.owner!==null&&allied(z.owner,f))for(const p of z.plots){const fc=p.fac;if(fc&&fc.state!=='building'&&FACILITIES[fc.type].radar&&!(fc.downT>G.time))l.push({x:p.x,z:p.z,r:FACILITIES[fc.type].radar*(fc.level>1?1.3:1)});}
    radarCache[f]={t:G.time,l};return l;}
  function onRadar(f,x,z){for(const r of radarsOf(f))if((x-r.x)*(x-r.x)+(z-r.z)*(z-r.z)<=r.r*r.r)return true;return false;}
  // the AI reacts to radar contacts the way a player would: it knows something is there
  const senses=(f,x,z)=>sees(f,x,z)||onRadar(f,x,z);
  const knowsPlot=(f,p)=>""")
rep("  function enemyAir(f){let n=0;for(const o of G.units)if(o.alive&&isAir(o)&&hostile(o.f,f)&&sees(f,o.x,o.z))n++;return n;}","  function enemyAir(f){let n=0;for(const o of G.units)if(o.alive&&isAir(o)&&hostile(o.f,f)&&senses(f,o.x,o.z))n++;return n;}")
rep("      query(z.x,z.z,z.r+AIB.qrfPad,u=>{if(hostile(u.f,fac.id)&&sees(fac.id,u.x,u.z)){threat+=","      query(z.x,z.z,z.r+AIB.qrfPad,u=>{if(hostile(u.f,fac.id)&&senses(fac.id,u.x,u.z)){threat+=")
rep("    for(const u of G.units)if(u.alive&&hostile(u.f,f)&&!isAir(u)&&sees(f,u.x,u.z))cands.push(u);","    for(const u of G.units)if(u.alive&&hostile(u.f,f)&&!isAir(u)&&senses(f,u.x,u.z))cands.push(u);")
rep("      let s=0;query(pt.x,pt.z,MSL.splash*MSL.aiAim,o=>{if(hostile(o.f,f)&&!isAir(o)&&sees(f,o.x,o.z))s+=","      let s=0;query(pt.x,pt.z,MSL.splash*MSL.aiAim,o=>{if(hostile(o.f,f)&&!isAir(o)&&senses(f,o.x,o.z))s+=")
rep("watchtower:FOG&&!n('watchtower')?.35:0,","watchtower:FOG&&!n('watchtower')?.35:0,radar:FOG&&(z.type==='hq'||z.type==='fortress')&&!n('radar')&&G.time>240?.3:0,")
rep("Object.assign(G,{canPlace,","Object.assign(G,{onRadar,radarsOf,canPlace,")
# --- renderer: dish model that spins
rep("const FAC_ICON={watchtower:'W',","const FAC_ICON={radar:'R',watchtower:'W',")
rep("  if(type==='watchtower'){","""  if(type==='radar'){ // lattice mast, equipment hut and a rotating parabolic dish
    add(g,B(2.2,1.6,1.6),M.house,-1.1,1,1.2);add(g,B(2.4,.2,1.8),M.concDark,-1.1,1.9,1.2);lattice(g,.6,-.4,.2,4.2,1.6,M.metal);
    const spin=new THREE.Group();spin.position.set(.6,4.6,-.4);spin.userData.spin=level>1?1.6:1.1;g.add(spin);
    const dish=new THREE.Mesh(new THREE.SphereGeometry(1.7,18,8,0,Math.PI*2,0,Math.PI/3.2).rotateX(-HALF),M.white);dish.material=M.white;dish.position.z=.3;dish.rotation.x=-.25;
    const arm=new THREE.Mesh(B(.12,.12,1.4),M.dark);arm.position.set(0,.15,1.2);const hub=new THREE.Mesh(Cy(.3,.5,8),M.metal);hub.position.y=-.2;
    for(const o of [dish,arm,hub]){o.castShadow=true;o.userData.dynamic=true;spin.add(o);}
    spin.userData.dynamic=true;
  }else if(type==='watchtower'){""")
rep("    scene.add(m);v.fac=m;}\n}","    scene.add(m);v.fac=m;m.traverse(o=>{if(o.userData.spin)spinners.push(o);});}\n}")
rep("function rebuildAllPlots(){G.zones.forEach(buildPlotVis);}","""function rebuildAllPlots(){G.zones.forEach(buildPlotVis);}
// spinning radar dishes (stopped while their station is knocked out)
let spinners=[];
function spinDishes(dt){spinners=spinners.filter(o=>{let p=o;while(p.parent)p=p.parent;return p===scene;});for(const o of spinners)o.rotation.y+=dt*o.userData.spin;}
// radar blips: enemy units your team's radar picks up but nobody can see. Position drifts a little, type is unknown
function radarBlips(){const out=[];if(!G.fog)return out;if(!G.radarsOf(ME).length)return out;
  const t=performance.now()/1000;
  for(const u of G.units){if(!u.alive||G.allied(u.f,ME)||u.def.static||G.visibleToPlayer(u.x,u.z)||!G.onRadar(ME,u.x,u.z))continue;
    out.push({x:u.x+Math.sin(t*.6+u.id*1.7)*2.6,z:u.z+Math.cos(t*.5+u.id*2.3)*2.6,air:!!u.def.air,id:u.id});}
  return out;}""")
# draw blips on the map and minimap; show coverage on the minimap
rep("  drawCityOverlay();\n","""  drawCityOverlay();
  {const bl=radarBlips(),t=performance.now()/1000;
    for(const b of bl){const p=proj(b.x,G.heightAt(b.x,b.z)+(b.air?14:1.2),b.z);if(!p.ok)continue;const k=.6+.4*Math.sin(t*5+b.id);
      octx.globalAlpha=k;octx.fillStyle='#ff4a32';octx.beginPath();octx.moveTo(p.x,p.y-5);octx.lineTo(p.x+5,p.y);octx.lineTo(p.x,p.y+5);octx.lineTo(p.x-5,p.y);octx.closePath();octx.fill();
      octx.strokeStyle='#ffd2c8';octx.lineWidth=1;octx.stroke();octx.globalAlpha=1;}}
""",1)
rep("  const now=performance.now();pings=pings.filter(p=>now-p.t<2500);","""  if(G.fog){mctx.strokeStyle='rgba(124,201,79,.45)';mctx.setLineDash([3,3]);mctx.lineWidth=1;for(const r of G.radarsOf(ME)){mctx.beginPath();mctx.arc(sx(r.x),sz(r.z),r.r*MK,0,6.3);mctx.stroke();}mctx.setLineDash([]);
    mctx.fillStyle='#ff4a32';for(const b of radarBlips()){mctx.beginPath();mctx.arc(sx(b.x),sz(b.z),2,0,6.3);mctx.fill();}}
  const now=performance.now();pings=pings.filter(p=>now-p.t<2500);""")
rep("  syncScene(dt);updateFX(dt);updateMarkers(dt);updateBeacons(dt);","  syncScene(dt);updateFX(dt);updateMarkers(dt);updateBeacons(dt);spinDishes(planning?0:dt);")
rep("  if(FAC[f.type].vision)return `Lifting the fog","  if(FAC[f.type].radar)return G.fog?`Radar sweeping ${Math.round(FAC[f.type].radar*(f.level>1?1.3:1))} m: enemy units show as red blips`:'Radar on (fog of war is off, so everything is in view anyway)';\n  if(FAC[f.type].vision)return `Lifting the fog")
# help + changelog
rep("      <kbd>H</kbd><span>Halt</span>\n","      <kbd>H</kbd><span>Halt</span>\n      <kbd>Radar Station</kbd><span>With fog on, enemy units inside its range show as red blips on the map and minimap, without saying what they are. Its range is the dashed circle on the minimap</span>\n")
rep("const GAME_VERSION={number:'16.7',name:'Construction rovers',date:'2026-10-30'};","const GAME_VERSION={number:'16.8',name:'Radar',date:'2026-10-30'};")
rep("const CHANGELOG=[\n","""const CHANGELOG=[
  {v:'16.8',name:'Radar',date:'2026-10-30',changes:[
    'New building: Radar Station (FORT, $150, built by a rover). With fog of war on, every enemy unit within 140 m (180 m upgraded) shows as a pulsing red blip on the map and minimap, through the fog. Blips drift a little and do not say what the unit is: send someone to look.',
    'Radar range shows as a dashed green circle on the minimap. A bombed station stops sweeping until it is repaired.',
    'The AI builds radar too and reacts to radar contacts (incoming attacks, enemy aircraft, missile targets), but still has to see a base to know its defences.',
  ]},
""",1)
open(p,'w').write(s)
