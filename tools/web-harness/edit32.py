p='/home/claude/vu/v23.html';s=open(p).read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(s.count(a),a[:80]);s=s.replace(a,b)
i=s.index("    selHead.innerHTML=`<b style=\"color:${facCss(z.owner)}\">${z.name}</b><span class=\"ztag\">${baseLabel(z)}</span>`+")
j=s.index("    const sig='z'+z.id+'|'+body;")
s=s[:i]+r"""    // header: name, then coloured chips -- blue for upgrades bought, green for bonuses, amber/red for problems
    const chip=(t,c,tt)=>`<span class="chip ${c}"${tt?` title="${tt}"`:''}>${t}</span>`;
    const L=z.drill||1,radar=z.plots.some(p=>p.fac&&FAC[p.fac.type].radar&&p.fac.state!=='building'),tower=z.plots.some(p=>p.fac&&FAC[p.fac.type].vision&&p.fac.state!=='building');
    let chips=chip(baseLabel(z),'');
    if(z.owner!==null){
      if(L>1)chips+=chip('Drill '+['I','II','III'][L-1],'up','Garrison Drill: bigger, better garrison');
      if(z.drillUp)chips+=chip(`Drill ${['','II','III'][L]} ${Math.floor(z.drillUp.t/z.drillUp.T*100)}%`,'busy');
      if(z.hosp)chips+=chip('✚ Hospital','bonus','Heals three times faster, repairs vehicles');else if(z.hospUp)chips+=chip(`✚ Hospital ${Math.floor(z.hospUp.t/z.hospUp.T*100)}%`,'busy');
      if(radar)chips+=chip('Radar','up');if(tower)chips+=chip('Watchtower','up');
      if(z.port&&z.type==='town')chips+=chip('Port trade','bonus','Port Towns earn more from trade');
      if(z.contested)chips+=chip('Under attack: halted','bad');}
    selHead.innerHTML=`<b style="color:${facCss(z.owner)}">${z.name}</b>`+chips;
    const tile=(k,v,sub,cls)=>`<div class="bst${cls?' '+cls:''}"><span class="k">${k}</span><span class="v num">${v}</span>${sub?`<span class="s">${sub}</span>`:''}</div>`;
    const pct=h.max>0?Math.round(Math.min(1,hp)*100):0,hcls=h.now<=0?'bad':hp<.4?'warn':'';
    let body=z.owner===null?'':`<span class="zhp${cls}" title="Health: the garrison plus defences. It must reach zero before the base can be captured."><i style="width:${pct}%"></i></span>`;
    if(!mine){
      body+=`<div class="bstats">`+(z.owner===null?tile('Defenders','none','Walk in to take it'):tile('Defence',pct+'%',`${z.garN} troops · ${z.defN} defences`,hcls))+tile('Income',`+$${(y.income/div.incomeDiv).toFixed(1)}/s`,'if you take it')+`</div>`;
      body+=`<p class="hint" style="margin-top:4px">${z.owner===null?'Unclaimed. Move troops inside the ring to take it.':G.allied(z.owner,ME)?'Held by an ally.':'Enemy held. Destroy its garrison and defences, then stand inside the ring.'}</p>`;}
    else{
      const made=garrisonMade(z),cap=G.garrisonCap(z),pool=G.garrisonPool(z),E=div;
      const baseInc=ZT.income*(z.port&&z.type==='town'?G.BALANCE.port.tradeMult:1),bonusInc=y.income-baseInc,bonusMp=y.mp-ZT.mp;
      const nx=z.nextType&&UTYPES[z.nextType]?UTYPES[z.nextType].name:'—';
      const gst=z.prodState==='building'?`next ${nx} · ${Math.ceil(Math.max(0,z.prodT))}s`:z.prodState==='full'?'full':z.prodState==='paused'?'<em class="bad">halted</em>':'idle';
      const rs=G.roverSlots(z);
      body+=`<div class="bstats">`+
        tile('Defence',pct+'%',`${Math.ceil(h.now)}/${Math.ceil(h.max)} HP${z.defN?` · ${z.defN} defences`:''}`,hcls)+
        tile('Garrison',`${made}/${cap}`,`${gst}<div class="gbar"><i id="gprog"></i></div>`,L>1?'up':'')+
        tile('Income',`+$${(y.income/E.incomeDiv).toFixed(1)}/s`,bonusInc>0?`<em class="bonus">+$${(bonusInc/E.incomeDiv).toFixed(1)} from buildings</em>`:`+${(y.mp/E.manpowerDiv*60).toFixed(0)} manpower/min`,bonusInc>0?'bonus':'')+
        tile('Buildings',`${z.plots.length}/${z.budget}`,`rovers ${rs.n}/${rs.cap}${G.roverCount(ME)?'':' · <em class="warn">none left</em>'}`)+`</div>`;
      // what the garrison is made of: icons of every unit type it can raise at this drill level
      body+=`<div class="gpool"><span class="lbl">Garrisons</span>${pool.map(t=>`<span class="gp" title="${UTYPES[t].name} · $${UTYPES[t].cost}">${ICONS[t]||''}</span>`).join('')}${L<3?`<span class="gnext up" title="Garrison Drill ${['','II','III'][L]} in the Base tab">next drill: ${Math.max(2,Math.round(ZT.garrison*[.5,.75,1][L]))} troops, ${L===1?'up to $135':'any unit'}</span>`:''}</div>`;
      body+=z.plots.length?`<div class="plotGrid">`+z.plots.map((p,k)=>{const f=p.fac;const wait=f&&f.state==='building'&&!f.crew,lv=f.level>1;return `<button class="plot k-${p.kind}${city&&p.i===city.sel?' on':''} full${lv?' lv2':''}" data-plot="${p.i}" title="${FAC[f.type].name}${lv?' (upgraded)':''}${wait?': waiting for a Construction Rover':''}"><span class="pn num">${k+1}</span><span class="pk">${SLOT_TAG[p.kind]}</span><span class="pi">${FAC_ICON[f.type]}</span><span class="pt">${FAC[f.type].name+(lv?' II':'')}</span><i class="pb" id="pb${p.i}"></i></button>`;}).join('')+`</div>`
        :`<p class="hint" style="margin-top:6px">No buildings yet. Select a Construction Rover and open its Build tab to put one up near ${z.name}.</p>`;
      body+=`<p class="hint" style="margin:4px 0 0">${z.rally?'Rally point set.':G.factions[ME].rally?'Using the global rally.':'Right-click the ground to set a rally point.'}</p>`;
    }
"""+s[j:]
# styles
rep(".gbar{height:4px;",""".chip{display:inline-block;font-family:var(--f-display);font-size:10px;letter-spacing:.08em;text-transform:uppercase;padding:1px 6px;border:1px solid var(--line-hi);color:var(--dim);margin-left:4px;line-height:1.5}
.chip.up{color:#8fd0ff;border-color:#3d6a86}.chip.bonus{color:var(--good);border-color:#4f7a3c}.chip.busy{color:var(--warn);border-color:#7a6a2e}.chip.bad{color:var(--bad);border-color:#7a3a2e}
.bstats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:5px;margin-top:5px}
.bst{display:flex;flex-direction:column;gap:1px;padding:4px 7px;background:rgba(255,255,255,.03);border:1px solid var(--line);border-left:3px solid var(--line-hi);min-width:0}
.bst .k{font-family:var(--f-display);font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--dim)}
.bst .v{font-size:15px;font-weight:600;color:var(--text);line-height:1.15}
.bst .s{font-size:10.5px;color:var(--dim);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bst.up{border-left-color:#5aa8d8}.bst.up .v{color:#8fd0ff}.bst.bonus{border-left-color:var(--good)}.bst.bonus .v{color:var(--good)}
.bst.warn{border-left-color:var(--warn)}.bst.warn .v{color:var(--warn)}.bst.bad{border-left-color:var(--bad)}.bst.bad .v{color:var(--bad)}
em.bonus{font-style:normal;color:var(--good)}em.warn{font-style:normal;color:var(--warn)}em.bad{font-style:normal;color:var(--bad)}
.gpool{display:flex;align-items:center;gap:4px;margin-top:5px;flex-wrap:wrap}.gpool .lbl{margin-right:2px}
.gpool .gp{display:inline-flex;padding:1px 3px;border:1px solid var(--line);color:var(--militia)}.gpool .gp svg{width:18px;height:11px}
.gpool .gnext{font-size:10.5px;margin-left:6px}.gpool .gnext.up{color:#8fd0ff}
.plot.lv2{border-color:#5aa8d8}.plot.lv2 .pt{color:#8fd0ff}
.gbar{height:4px;""")
open(p,'w').write(s)
