p='/home/claude/vu/v18.html';s=open(p).read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(s.count(a),a[:80]);s=s.replace(a,b)
rep("""  if(c.k==='units')return [['orders','Orders'],['recruit','Recruit']];""","""  if(c.k==='units')return c.us.some(u=>u.def.builder)?(c.us.every(u=>u.def.builder)?[['construct','Build'],['orders','Orders']]:[['orders','Orders'],['construct','Build']]):[['orders','Orders'],['recruit','Recruit']];""")
rep("""  if(c.k==='base'){if(!city||city.zid!==c.z.id){city={zid:c.z.id,sel:Math.max(0,c.z.plots.findIndex(p=>!p.fac))};tutEv.city=true;}}
  else city=null;}""","""  if(c.k==='base'){if(!city||city.zid!==c.z.id){city={zid:c.z.id,sel:c.z.plots.length?c.z.plots[0].i:null};tutEv.city=true;}
    if(city.sel!=null&&!G.plotOf(c.z,city.sel))city.sel=c.z.plots.length?c.z.plots[0].i:null;}
  else city=null;
  // rovers selected: show the construction ring of the base they build for
  roverZone=c.k==='units'&&c.us.some(u=>u.def.builder)?roverBase(c.us.filter(u=>u.def.builder)):null;
  if(roverZone&&(!placing))showBuildRing(roverZone);}""")
# base: list of buildings (no empty pads any more)
rep("""      body+=`<div class="plotGrid">`+z.plots.map(p=>{const f=p.fac;return `<button class="plot k-${p.kind}${city&&p.i===city.sel?' on':''}${f?' full':''}" data-plot="${p.i}" title="${SLOT_LABEL[p.kind]} pad${p.water?', by the water':''} (key ${p.i+1<10?p.i+1:''})"><span class="pn num">${p.i+1}</span><span class="pk">${SLOT_TAG[p.kind]}</span><span class="pi">${f?FAC_ICON[f.type]:'+'}</span><span class="pt">${f?FAC[f.type].name+(f.level>1?' II':''):'Empty'}</span><i class="pb" id="pb${p.i}"></i></button>`;}).join('')+`</div>`;""",
"""      body+=`<div class="zrow"><span>Buildings <b class="num">${z.plots.length}/${z.budget}</b></span>${G.roverCount(ME)?'':'<span style="color:var(--warn)">No Construction Rover: recruit one at your HQ (E)</span>'}</div>`;
      body+=z.plots.length?`<div class="plotGrid">`+z.plots.map((p,k)=>{const f=p.fac;const wait=f&&f.state==='building'&&!f.crew;return `<button class="plot k-${p.kind}${city&&p.i===city.sel?' on':''} full" data-plot="${p.i}" title="${FAC[f.type].name}${wait?': waiting for a Construction Rover':''}"><span class="pn num">${k+1}</span><span class="pk">${SLOT_TAG[p.kind]}</span><span class="pi">${FAC_ICON[f.type]}</span><span class="pt">${FAC[f.type].name+(f.level>1?' II':'')}</span><i class="pb" id="pb${p.i}"></i></button>`;}).join('')+`</div>`
        :`<p class="hint" style="margin-top:6px">No buildings yet. Select a Construction Rover and open its Build tab to put one up near ${z.name}.</p>`;""")
rep("""  }else if(cardTab==='build'){
    const z=c.z,p=z.plots[city.sel];
    if(!p){sig='b-';grid='';}
    else if(!p.fac){""","""  }else if(cardTab==='construct'){
    const rov=c.us.filter(u=>u.def.builder),z=roverZone||roverBase(rov);
    const opts=z?FAC_KEYS.filter(k=>{const D=FAC[k];return !(D.only&&!D.only.includes(z.type))&&!(D.port&&!z.port);}):[];
    sig='c'+(z?z.id:-1)+'|'+rov.length+'|'+(placing?placing.type:'')+'|'+opts.map(k=>G.canPlaceType(ME,z.id,k)||'').join('|');
    if(sig!==cardSig){
      top=z?`<span class="lbl">Build at</span><button data-cmd="rzprev" aria-label="Previous base">‹</button><b>${z.name}</b><button data-cmd="rznext" aria-label="Next base">›</button><span class="lbl num">${z.plots.length}/${z.budget}</span>`:'<span class="lbl">You hold no base</span>';
      for(const k of opts){const D=FAC[k],err=G.canPlaceType(ME,z.id,k);
        grid+=cb({attrs:`data-place="${k}"`,icon:`<span class="ic">${FAC_ICON[k]}</span>`,name:D.name,cost:`$${D.cost}·${D.time}s`,dis:!!err,pressed:placing&&placing.type===k,hint:`<b>${D.name}</b>: ${D.desc}${err?` <span class="why">${err}</span>`:''}`});}
      hint=z?`Pick a building, move the hologram inside the yellow ring, turn it with the wheel and click to build. Right-click a site to send rovers to help.`:'';
    }
  }else if(cardTab==='build'){
    const z=c.z,p=G.plotOf(z,city.sel);
    if(!p){sig='b-'+z.plots.length;if(sig!==cardSig){hint=`Select one of ${z.name}'s buildings to upgrade or demolish it. New buildings are put up by Construction Rovers.`;}}
    else if(!p.fac){""")
rep("""        top=`<span class="lbl">Pad ${p.i+1}</span><b>${D.name}${f.level>1?' II':''}</b>`;""","""        top=`<b>${D.name}${f.level>1?' II':''}</b>`;""")
rep("  if(cardTab==='build'&&city){const p=G.zones[city.zid].plots[city.sel],e=document.getElementById('cStatus');","  if(cardTab==='build'&&city){const p=G.plotOf(G.zones[city.zid],city.sel),e=document.getElementById('cStatus');")
rep("  if(d.rec)doRecruit(d.rec,c.k==='base'?c.z.id:deployZone);","""  if(d.rec)doRecruit(d.rec,c.k==='base'?c.z.id:deployZone);
  else if(d.place){const z=roverZone||roverBase(selUnits().filter(u=>u.def.builder));if(z){if(placing&&placing.type===d.place)stopPlacing();else startPlacing(d.place,z.id);}}""")
rep("cardTop.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;if(b.dataset.cmd==='dprev')cycleDeploy(-1);else if(b.dataset.cmd==='dnext')cycleDeploy(1);});",
"""cardTop.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;if(b.dataset.cmd==='dprev')cycleDeploy(-1);else if(b.dataset.cmd==='dnext')cycleDeploy(1);
  else if(b.dataset.cmd==='rzprev'||b.dataset.cmd==='rznext'){const own=G.zones.filter(z=>z.owner===ME);if(!own.length)return;let i=own.indexOf(roverZone);i=(i+(b.dataset.cmd==='rznext'?1:-1)+own.length)%own.length;
    const z=own[i];roverZone=z;showBuildRing(z);if(placing)placing.zid=z.id;cam.x=z.x;cam.z=z.z;
    const ids=selUnits().filter(u=>u.def.builder).map(u=>u.id);A.order('move',ids,z.x+Math.cos(.7)*(z.r+6),z.z+Math.sin(.7)*(z.r+6));cardSig='';refreshSel();}});""")
# the chosen base sticks while the rovers stay selected
rep("  roverZone=c.k==='units'&&c.us.some(u=>u.def.builder)?roverBase(c.us.filter(u=>u.def.builder)):null;",
    "  const rs=c.k==='units'?c.us.filter(u=>u.def.builder):[];\n  roverZone=rs.length?(roverZone&&roverZone.owner===ME&&roverSig===rs.map(u=>u.id).join()?roverZone:roverBase(rs)):null;roverSig=rs.map(u=>u.id).join();\n  if(!rs.length&&placing)stopPlacing();")
rep("let roverZone=null;","let roverZone=null,roverSig='';")
# facility status: construction waits for a rover
rep("  if(f.state==='building')return `Building… ${Math.floor(f.t/f.T*100)}%`;","  if(f.state==='building')return f.crew?`Building… ${Math.floor(f.t/f.T*100)}% · ${f.crew} rover${f.crew>1?'s':''} at work`:`${Math.floor(f.t/f.T*100)}% · waiting for a Construction Rover`;")
# map labels over sites that have no rover
rep("      if(f&&f.state!=='ready'){const w=46;","""      if(f&&f.state==='building'&&!f.crew&&z.owner===ME){octx.font='600 9px "Chakra Petch", sans-serif';octx.fillStyle='#ffd25a';octx.fillText('NEEDS A ROVER',q.x,q.y-10);}
      if(f&&f.state!=='ready'){const w=46;""")
rep("        const on=p.i===city.sel,txt=f?FAC[f.type].name.toUpperCase()+(f.level>1?' II':''):'+ BUILD';","        const on=p.i===city.sel,txt=FAC[f.type].name.toUpperCase()+(f.level>1?' II':'');")
rep("        octx.font='600 10px \"JetBrains Mono\", monospace';octx.fillText(String(p.i+1),q.x-w/2+8,q.y);","        octx.font='600 10px \"JetBrains Mono\", monospace';octx.fillText(String(z.plots.indexOf(p)+1),q.x-w/2+8,q.y);")
# help + tutorial
rep("<kbd>Click your base</kbd><span>Its build pads show in the bottom bar: pick a pad, then a building in the command card. Double-click or G zooms in. What you can build depends on the base type</span>",
    "<kbd>Construction Rover (E at an HQ)</kbd><span>Select it and open its Build tab: pick a building, move the hologram inside the base's yellow ring, mouse wheel to turn it, click to build. Rovers must stay at the site while it goes up; more rovers build faster. Right-click a site to send rovers to it. Up to 3 rovers</span>\n      <kbd>Click your base</kbd><span>Lists its buildings (each base holds a limited number): upgrade or demolish them from the command card. Double-click or G zooms in</span>")
rep("""  {title:'Build in your base',body:`<p><b>Click</b> your Home Fort. Its <b>build pads</b> appear in the bottom bar and its <b>Build</b> tab in the command card. Double-click it (or press <kbd>G</kbd>) to zoom in.</p>""",
    """  {title:'Build in your base',body:`<p>Buildings are put up by your <b>Construction Rover</b>, the yellow-armed truck by Home Fort. Recruit more at your HQ with <kbd>E</kbd> (up to 3).</p>
    <p><b>Select the rover</b> and open its <b>Build</b> tab. Pick a building, then move its <b>hologram</b> inside the yellow ring around the base. The <b>mouse wheel</b> turns it, a <b>click</b> places it, right-click cancels. The rover drives over and builds; it has to stay there until it's done.</p>""")
rep("    <p>Each base has build plots of three kinds: <b>MIL</b> (barracks, tank works, helipad…), <b>ECO</b> (supply depot, market, housing) and <b>FORT</b> (pillboxes and AA guns). Click a pad (in the bar, on the map, or press its number), then pick a building in the command card.</p>",
    "    <p>Buildings come in three kinds: <b>MIL</b> (barracks, tank works, helipad…), <b>ECO</b> (supply depot, market, housing) and <b>FORT</b> (pillboxes and AA guns). Each base holds a limited number of buildings in all.</p>")
rep("goal:'Select your base and build anything.'","goal:'Select the Construction Rover and build anything.'")
open(p,'w').write(s)
