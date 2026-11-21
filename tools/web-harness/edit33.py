p='/home/claude/vu/m12.html';s=open(p).read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(s.count(a),a[:80]);s=s.replace(a,b)
rep("  if(c.k==='base'){const t=ZTYPES[c.z.type].recruit?[['recruit','Recruit'],['base','Base']]:[['base','Base']];",
    "  if(c.k==='base'){const t=ZTYPES[c.z.type].recruit?[['recruit','Recruit'],['upgrades','Base Upgrades'],['base','Base']]:[['upgrades','Base Upgrades'],['base','Base']];")
# split: Base keeps zoom/rally; upgrades get their own tab with progress bars
i=s.index("      {const L=z.drill||1,err=G.canDrill(ME,z.id);");j=s.index("      hint='Right-click the ground to set this base\\'s rally point.';",i)
upg=s[i:j]
s=s[:i]+s[j:]
rep("  }else if(cardTab==='base'){\n    const z=c.z;sig='bs'+z.id+'|'+!!z.rally+'|'+(z.drill||1)+'|'+!!z.drillUp+'|'+(G.canDrill(ME,z.id)||'')+'|'+!!z.hosp+(z.hospUp?Math.floor(z.hospUp.t):'')+'|'+(G.canHosp(ME,z.id)||'');",
"""  }else if(cardTab==='upgrades'){
    // base upgrades: each button shows a progress bar while it goes in
    const z=c.z;sig='bu'+z.id+'|'+(z.drill||1)+'|'+!!z.drillUp+'|'+(G.canDrill(ME,z.id)||'')+'|'+!!z.hosp+'|'+!!z.hospUp+'|'+(G.canHosp(ME,z.id)||'');
    if(sig!==cardSig){
"""+upg.replace("{attrs:'data-cmd=\"drill\"',","{attrs:'data-cmd=\"drill\"',bar:'ubDrill',").replace("{attrs:'data-cmd=\"hosp\"',","{attrs:'data-cmd=\"hosp\"',bar:'ubHosp',")+"""      top=`<span class="lbl">Base upgrades · ${z.name}</span>`;
      hint='Upgrades improve this base for good. A blue bar shows one going in.';
    }
  }else if(cardTab==='base'){
    const z=c.z;sig='bs'+z.id+'|'+!!z.rally;""")
# live bars
rep("  // live status of the selected building\n","""  // live progress of base upgrades
  if(cardTab==='upgrades'&&c.z){for(const [id,u] of [['ubDrill',c.z.drillUp],['ubHosp',c.z.hospUp]]){const e=document.getElementById(id);if(e){e.style.width=u?(Math.min(1,u.t/u.T)*100).toFixed(0)+'%':'0';e.style.background='#8fd0ff';}}}
  // live status of the selected building
""")
rep(".cb .pb{position:absolute;left:0;bottom:0;height:3px;background:var(--warn);width:0}",".cb .pb{position:absolute;left:0;bottom:0;height:4px;background:var(--warn);width:0}")
rep("    'Cleaner base panel:","    'Base upgrades (Garrison Drill, Field Hospital) have their own Base Upgrades tab, and each shows a progress bar while it goes in. The Base tab keeps zoom and rally points.',\n    'Cleaner base panel:")
open(p,'w').write(s)
