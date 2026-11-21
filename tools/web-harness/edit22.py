p='/home/claude/vu/v20.html';s=open(p).read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(s.count(a),a[:80]);s=s.replace(a,b)
# facility card: production buildings can train their units right here
rep("""      sig='bf'+z.id+'|'+p.i+'|'+f.type+f.state+f.level+'|'+uerr+'|'+(f.mode||'cycle');""",
"""      const trains=D.prod&&f.state!=='building'?[...new Set(D.prod.seq)].filter(t=>G.canField(z,t)&&UTYPES[t]&&!UTYPES[t].noRecruit):[];
      sig='bf'+z.id+'|'+p.i+'|'+f.type+f.state+f.level+'|'+uerr+'|'+(f.mode||'cycle')+'|'+trains.map(t=>G.canRecruit(ME,t,z.id)||'').join('|');""")
rep("""        top=`<b>${D.name}${f.level>1?' II':''}</b>`;
        if(f.level<2)""","""        top=`<b>${D.name}${f.level>1?' II':''}</b><span class="lbl">${z.name}</span>`;
        for(const t of trains){const T=UTYPES[t],err=G.canRecruit(ME,t,z.id);
          grid+=cb({attrs:`data-rec="${t}"`,icon:ICONS[t],name:T.name,cost:`$${T.cost}·${T.hr}`,key:T.hot,dis:!!err,hint:`<b>Train ${T.name}</b> here now · $${T.cost}, ${T.hr} manpower. The ${D.name} also turns them out on its own over time.${err?` <span class="why">${err}</span>`:''}`});}
        if(f.level<2)""")
# click a building on the map to select it directly
rep("  if(city){const i=pickPlot(e.clientX,e.clientY);if(i>=0){city.sel=i;cardTab='build';selSig=cardSig='';refreshSel();lastClick={t:now,id:null,zone:city.zid};return;}}",
"""  if(city){const i=pickPlot(e.clientX,e.clientY);if(i>=0){city.sel=i;cardTab='build';selSig=cardSig='';refreshSel();lastClick={t:now,id:null,zone:city.zid};return;}}
  {const hit=pickBuilding(e.clientX,e.clientY);if(hit){selected.clear();setFight(false);selZone=hit.z.id;city={zid:hit.z.id,sel:hit.p.i};cardTab='build';
    if(ZTYPES[hit.z.type].recruit)deployZone=hit.z.id;selSig=cardSig='';lastCtx='base';refreshSel();lastClick={t:now,id:null,zone:hit.z.id};return;}}""")
rep("function pickPlot(sx,sy){","""// any of your buildings under the cursor (its body, not just its foot)
function pickBuilding(sx,sy){let best=null,bd=26;
  for(const z of G.zones){if(z.owner!==ME)continue;for(const p of z.plots){
    for(const h of [.6,2]){const q=proj(p.x,p.y+h,p.z);if(!q.ok)continue;const d=Math.hypot(q.x-sx,q.y-sy);if(d<bd){bd=d;best={z,p};}}}}
  return best;}
function pickPlot(sx,sy){""")
rep("Drag a box around your units, or click one of your bases to see its build pads.","Drag a box around your units, or click one of your bases or buildings.")
rep("    'Little cargo ships now ply shipping lanes","    'Click any of your buildings on the map to select it straight away. Barracks, tank works and the other production buildings can train their units right from the command card.',\n    'Little cargo ships now ply shipping lanes")
open(p,'w').write(s)
