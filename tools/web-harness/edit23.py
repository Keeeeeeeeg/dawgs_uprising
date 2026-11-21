p='/home/claude/vu/v21.html';s=open(p).read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(s.count(a),a[:80]);s=s.replace(a,b)
# --- recruit categories
rep("""    sig='r'+(z?z.id:-1)+'|'+c.k+'|'+errs;
    if(sig!==cardSig){""","""    // grouped by kind, cheapest first; a category tab only shows when this base fields something in it
    const cats=UNIT_CATS.filter(([k])=>avail.some(t=>unitCat(t)===k));if(cats.length&&!cats.some(([k])=>k===recCat))recCat=cats[0][0];
    const shown=avail.filter(t=>unitCat(t)===recCat).sort((a,b)=>a.cost-b.cost||a.name.localeCompare(b.name));
    sig='r'+recCat+(z?z.id:-1)+'|'+c.k+'|'+errs;
    if(sig!==cardSig){
      if(cats.length>1){const span=Math.max(1,Math.floor(6/cats.length));for(const [k,l] of cats)grid+=`<button class="cbcat" style="grid-column:span ${span}" data-rcat="${k}" aria-pressed="${recCat===k}">${l} <span class="num">${avail.filter(t=>unitCat(t)===k).length}</span></button>`;
        if(span*cats.length<6)grid+=`<span style="grid-column:span ${6-span*cats.length}"></span>`;}""")
rep("""      for(const t of avail){const err=G.canRecruit(ME,t.key,z.id);
        grid+=cb({attrs:`data-rec=""","""      for(const t of shown){const err=G.canRecruit(ME,t.key,z.id);
        grid+=cb({attrs:`data-rec=""")
rep("let roverZone=null,roverSig='',buildCat='mil';","""let roverZone=null,roverSig='',buildCat='mil',recCat='inf';
// recruit categories: foot soldiers, wheeled, tracked, helicopters, planes, boats
const UNIT_CATS=[['inf','Infantry'],['wheel','Wheeled'],['track','Tracked'],['heli','Air'],['plane','Aircraft'],['naval','Naval']];
function unitCat(t){if(t.armor==='inf')return 'inf';if(t.naval)return 'naval';if(t.plane)return 'plane';if(t.air)return 'heli';
  return ['ltank','mtank','htank','spg','sam'].includes(t.key)?'track':'wheel';}""")
rep("  const cat=e.target.closest('.cbcat');if(cat){buildCat=cat.dataset.cat;cardSig='';refreshSel();return;}",
    "  const cat=e.target.closest('.cbcat');if(cat){if(cat.dataset.rcat)recCat=cat.dataset.rcat;else buildCat=cat.dataset.cat;cardSig='';refreshSel();return;}")
# --- health bars always (setting)
rep("    if(!(sel||u.hp<u.maxHp||ship))continue;if(!shown(u))continue;","    if(!(sel||u.hp<u.maxHp||ship||(window.UI_PREFS&&UI_PREFS.hpAlways&&!u.def.static)))continue;if(!shown(u))continue;")
# --- smaller units and buildings
rep("  scene.add(m);meshes.set(u.id,m);return m;","  m.scale.multiplyScalar(UNIT_SCALE);   // every unit a touch smaller than its model\n  scene.add(m);meshes.set(u.id,m);return m;")
rep("const STRUCT_SCALE=.85;   // zone buildings, pad buildings and farmsteads are drawn at this size","const STRUCT_SCALE=.74,UNIT_SCALE=.85;   // zone buildings, base buildings and farmsteads / units are drawn at these sizes")
# settings: health bar toggle
rep("""    <h2 class="plHead">Music rotation</h2>""","""    <label class="tog fogtog"><input type="checkbox" id="hpAlways" checked> Always show unit health bars <small>(otherwise only selected or damaged units)</small></label>
    <h2 class="plHead">Music rotation</h2>""")
rep("// interface size: scales the battle HUD (kept in this browser)","""// health bars over every unit, or only selected / damaged ones (kept in this browser)
window.UI_PREFS=window.UI_PREFS||{hpAlways:true};
{const el=document.getElementById('hpAlways');try{const v=localStorage.getItem('ventora.hpAlways');if(v!=null)UI_PREFS.hpAlways=v==='1';}catch(e){}
  el.checked=UI_PREFS.hpAlways;el.addEventListener('change',()=>{UI_PREFS.hpAlways=el.checked;try{localStorage.setItem('ventora.hpAlways',el.checked?'1':'0');}catch(e){}});}
// interface size: scales the battle HUD (kept in this browser)""")
# changelog: fold into a new entry
rep("const CHANGELOG=[\n","""const CHANGELOG=[
  {v:'17.0',name:'Bigger battlefields',date:'2026-10-30',changes:[
    'Every map is 25% larger: bases sit further apart (they keep their size), and islands, hills and seas grow with them. Balance between starts is unchanged; Ports keep their coves.',
    'Units are drawn 15% smaller and base buildings smaller again, for more open ground.',
    'The Recruit tab is sorted into Infantry, Wheeled, Tracked, Air, Aircraft and Naval (only the ones the base fields), cheapest first.',
    'Every unit now shows a small health bar. Turn it off in Settings to see bars only on selected or damaged units.',
  ]},
""",1)
open(p,'w').write(s)
