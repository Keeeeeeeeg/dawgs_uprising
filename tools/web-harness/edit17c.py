p='/home/claude/vu/v17.html';s=open(p).read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(s.count(a),a[:70]);s=s.replace(a,b)
rep("G.on('facility',(p,z)=>{refreshPlotVis(z,p);citySig='';","G.on('facility',(p,z)=>{refreshPlotVis(z,p);cardSig='';selSig='';")
rep("""  for(const t of Object.values(UTYPES).filter(t=>!t.noRecruit)){
    const b=$('#rb_'+t.key),err=G.canRecruit(ME,t.key,deployZone);
    b.disabled=!!err;b.title=err||`Recruit ${t.name}`;
  }
""","")
rep("""    if(!NET)for(const u of selUnits())if(!u.def.plane)u.stance=d.stance==='aggr'?null:d.stance;}""","}")
# input: normal box-select even with a base selected; a click near one of its pads picks the pad
rep("  if(e.button===0&&city){drag={x0:e.clientX,y0:e.clientY,x1:e.clientX,y1:e.clientY,on:false,city:true};}\n  else if(e.button===0)","  if(e.button===0)")
rep("  if(city){const i=pickPlot(e.clientX,e.clientY);if(i>=0){city.sel=i;citySig='';refreshCity();}return;}\n  const u=pickUnit(",
    "  const u=pickUnit(")
rep("""  const z=zoneAtScreen(e.clientX,e.clientY);
  if(z&&z.owner===ME&&lastClick.zone===z.id&&now-lastClick.t<350){enterCity(z.id);lastClick={t:0,id:null};return;}""",
"""  if(city){const i=pickPlot(e.clientX,e.clientY);if(i>=0){city.sel=i;cardTab='build';selSig=cardSig='';refreshSel();lastClick={t:now,id:null,zone:city.zid};return;}}
  const z=zoneAtScreen(e.clientX,e.clientY);
  if(z&&z.owner===ME&&lastClick.zone===z.id&&now-lastClick.t<350){enterCity(z.id);lastClick={t:0,id:null};return;}""")
rep("  else if(k==='q'&&!city){$('#bMissile').click();}","  else if(k==='q'){$('#bMissile').click();}")
rep("  else if(k==='g'){if(city)exitCity();else if(selZone!=null)enterCity(selZone);}","  else if(k==='g'){if(selZone!=null&&G.zones[selZone].owner===ME)enterCity(selZone);}")
rep("  else if(city&&/^Digit[1-9]$/.test(e.code)){const i=+e.code.slice(5)-1;if(i<G.zones[city.zid].plots.length){city.sel=i;citySig='';refreshCity();}}",
    "  else if(city&&!e.shiftKey&&/^Digit[1-9]$/.test(e.code)){const i=+e.code.slice(5)-1;if(i<G.zones[city.zid].plots.length){city.sel=i;cardTab='build';selSig=cardSig='';refreshSel();}}")
rep("    const t=Object.values(UTYPES).find(u=>u.hot&&u.hot.toLowerCase()===k);if(t&&!city)doRecruit(t.key);",
    "    const t=Object.values(UTYPES).find(u=>u.hot&&u.hot.toLowerCase()===k);if(t)doRecruit(t.key);")
rep("  $('#city').hidden=true;$('#cmd').hidden=false;","  $('#cmd').hidden=false;")
rep("$('#tut').classList.remove('shift');","",1)
# pad picking: tighter so units/zones next to pads stay clickable
rep("  if(!city)return -1;const z=G.zones[city.zid];let best=-1,bd=60;","  if(!city)return -1;const z=G.zones[city.zid];let best=-1,bd=34;")
# pad labels only when zoomed in enough to read them
rep("      if(inCity){\n        const on=p.i===city.sel","      if(inCity&&cam.d<120){\n        const on=p.i===city.sel")
# help + tutorial
rep("<kbd>Double-click your base or G</kbd><span>Base view: military, economic and fortification plots. What you can build depends on the base type</span>",
    "<kbd>Click your base</kbd><span>Its build pads show in the bottom bar: pick a pad, then a building in the command card. Double-click or G zooms in. What you can build depends on the base type</span>")
rep("Click the <b>minimap</b> (top right) to jump anywhere.","Click the <b>minimap</b> (bottom left) to jump anywhere.")
rep("""<p>The <b>Deploy at</b> panel (bottom) recruits units at the base shown there. Use <kbd>‹</kbd> <kbd>›</kbd> to pick another base you own.</p>""",
    """<p>The <b>command card</b> (bottom right) has a <b>Recruit</b> tab. With nothing selected it recruits at the base shown under <b>Deploy at</b>; use <kbd>‹</kbd> <kbd>›</kbd> to pick another base you own. With one of your bases selected it recruits right there.</p>""")
rep("""<p><b>Double-click</b> your Home Fort (or select it and press <kbd>G</kbd>) to open the <b>base view</b>.</p>""",
    """<p><b>Click</b> your Home Fort. Its <b>build pads</b> appear in the bottom bar and its <b>Build</b> tab in the command card. Double-click it (or press <kbd>G</kbd>) to zoom in.</p>""")
rep("Click a plot, then pick a building.</p>","Click a pad (in the bar, on the map, or press its number), then pick a building in the command card.</p>")
rep("goal:'Open the base view and build anything.'","goal:'Select your base and build anything.'")
rep("""    <p>Press <kbd>Esc</kbd> to leave the base view first.</p>`,""","""    <p>The <b>Base</b> tab of the command card clears a rally point or sends every base's troops to it.</p>`,""")
open(p,'w').write(s)
