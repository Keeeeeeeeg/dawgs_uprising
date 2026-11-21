p='/home/claude/vu/v17.html';s=open(p).read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(s.count(a),a[:70]);s=s.replace(a,b)
i=s.index("const recBtns=$('#recBtns');");j=s.index("// base health for the HUD: garrison HP plus")
new=r"""Object.assign(ICONS,{
  airship:'<svg viewBox="0 0 22 14"><ellipse cx="10" cy="6" rx="9" ry="4" fill="currentColor"/><path d="M17 3l4-2v10l-4-2z M8 10h5v3H8z" fill="currentColor"/></svg>',
  intc:'<svg viewBox="0 0 22 14"><path d="M1 7l6-1 3-5h2l-1 5h7l2-2h1l-1 3 1 3h-1l-2-2h-7l1 5h-2l-3-5z" fill="currentColor"/></svg>',
  cas:'<svg viewBox="0 0 22 14"><path d="M1 6h7l2-5h3l-1 5h6l2-2h1v6h-1l-2-2h-6l1 5h-3l-2-5H1z" fill="currentColor"/></svg>',
  bomb:'<svg viewBox="0 0 22 14"><path d="M1 6h6l1-5h4l-1 5h6l3-3h1v8h-1l-3-3h-6l1 5H8l-1-5H1z" fill="currentColor"/></svg>',
  pillbox:'<svg viewBox="0 0 22 14"><path d="M3 12V7a8 5 0 0 1 16 0v5z" fill="currentColor"/></svg>',
  aagun:'<svg viewBox="0 0 22 14"><path d="M4 12h14v1H4z M7 9h8v3H7z M10 9l8-8 1 1-7 8z" fill="currentColor"/></svg>',
});
// command-card glyphs for orders and stances
const CI={
  fight:'<svg viewBox="0 0 22 14"><path d="M3 1l7 6-7 6V9H1V5h2z M12 2h2l6 5-6 5h-2l6-5z" fill="currentColor"/></svg>',
  stop:'<svg viewBox="0 0 22 14"><rect x="6" y="2" width="10" height="10" fill="currentColor"/></svg>',
  aggr:'<svg viewBox="0 0 22 14"><path d="M11 1l9 6-9 6-9-6z M11 4l-4.5 3L11 10l4.5-3z" fill="currentColor"/></svg>',
  hold:'<svg viewBox="0 0 22 14"><path d="M5 1h12v6c0 3-3 5-6 6-3-1-6-3-6-6z" fill="currentColor"/></svg>',
  ret:'<svg viewBox="0 0 22 14"><path d="M8 2L2 7l6 5V9h6a3 3 0 0 0 0-6h-2V1h2a5 5 0 0 1 0 10H8z" fill="currentColor"/></svg>',
  auto:'<svg viewBox="0 0 22 14"><circle cx="11" cy="7" r="5.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M11 3v4l3 2" stroke="currentColor" stroke-width="1.6" fill="none"/></svg>',
  manual:'<svg viewBox="0 0 22 14"><path d="M11 1v12M5 7h12" stroke="currentColor" stroke-width="2"/><circle cx="11" cy="7" r="3.5" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>',
  zoom:'<svg viewBox="0 0 22 14"><circle cx="9" cy="6" r="4.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12.5 9.5L17 13" stroke="currentColor" stroke-width="2.2"/></svg>',
  rally:'<svg viewBox="0 0 22 14"><path d="M7 1h1v12H7z M8 1h9l-3 3 3 3H8z" fill="currentColor"/></svg>',
  clear:'<svg viewBox="0 0 22 14"><path d="M6 2l10 10M16 2L6 12" stroke="currentColor" stroke-width="2.2"/></svg>',
  up:'<svg viewBox="0 0 22 14"><path d="M11 1l7 7h-4v5H8V8H4z" fill="currentColor"/></svg>',
};
const STANCES=[['aggr','Aggressive','Engage anything in sight and give chase (default).'],['hold','Hold ground','Fire at enemies in range but never leave the spot.'],['ret','Return fire','Hold fire unless shot at, then shoot back from where they stand.']];
const RECRUITABLE=Object.values(UTYPES).filter(t=>!t.noRecruit);
// which base types field a unit ("Fortress, HQ" / "Port Town")
function fieldedAt(k){const out=[];for(const ZT of Object.values(ZTYPES)){if(ZT.roster.includes(k))out.push(ZT.label);else if(ZT.naval&&ZT.naval.includes(k))out.push('Port '+ZT.label);}return out.join(', ');}
function doRecruit(type,zid){
  const z=G.zones[zid==null?deployZone:zid];if(!z){return;}
  // newly recruited units move up to the rally point, or just outside the zone toward the camera focus
  const R=G.rallyOf(z),a=Math.atan2(cam.z-z.z,cam.x-z.x);
  const to=R?{x:R.x+(Math.random()-.5)*6,z:R.z+(Math.random()-.5)*6,amove:true}:{x:z.x+Math.cos(a)*(z.r+5)+(Math.random()-.5)*4,z:z.z+Math.sin(a)*(z.r+5)+(Math.random()-.5)*4,amove:false};
  const r=A.recruit(type,z.id,to);
  if(!r.ok){toast(r.err);return;}
}
function recruitZones(){return G.zones.filter(z=>z.owner===ME&&ZTYPES[z.type].recruit);}
function pickDeploy(){const l=recruitZones();return l.length?l[0].id:0;}
function cycleDeploy(d){const l=recruitZones();if(!l.length)return;let i=l.findIndex(z=>z.id===deployZone);i=(i+d+l.length)%l.length;deployZone=l[i].id;
  const z=G.zones[deployZone];cam.x=z.x;cam.z=z.z;cardSig='';refreshSel();}
function refreshDeploy(){}
$('#autoG').onchange=e=>{A.autogar(e.target.checked);};
$('#bMissile').onclick=()=>{if(G.missileStock(ME)<=0){const n=G.missileNext(ME);toast(n==null?'You hold no HQ to launch from.':`No missile ready. Next one in ${fmtT(n)}.`);return;}setArm(armed==='missile'?null:'missile');};
$('#autoM').onchange=e=>{A.automsl(e.target.checked);toast(e.target.checked?'Missiles fire on their own at the juiciest target':'Missiles wait for your order',true);};
$('#bRallyG').onclick=()=>setArm(armed==='rally'?null:'rally');
$('#bRallyGx').onclick=()=>{A.grally(null);toast('Global rally cleared. New troops muster at their own zone.',true);refreshSel();};
$('#bAir').onclick=()=>{const ps=G.units.filter(u=>u.alive&&u.f===ME&&u.def.plane);if(!ps.length){toast('You have no aircraft. Capture an Airbase: its Hangar builds planes.');return;}selected=new Set(ps.map(u=>u.id));selZone=null;refreshSel();};

// ---------- selection box + command card ----------
// context: units selected / one of your bases / someone else's base / nothing. The card's tabs depend on it.
let cardTab=null,selSig='',cardSig='',hintHold=null;
const selHead=$('#selHead'),selBody=$('#selBody'),cardTabs=$('#cardTabs'),cardTop=$('#cardTop'),cardGrid=$('#cardGrid'),cardHint=$('#cardHint');
function selCtx(){const us=selUnits();if(us.length)return {k:'units',us};
  if(selZone!=null&&G.zones[selZone]){const z=G.zones[selZone];return {k:z.owner===ME?'base':'zone',z};}
  return {k:'none'};}
function tabsFor(c){
  if(c.k==='units')return [['orders','Orders'],['recruit','Recruit']];
  if(c.k==='base')return ZTYPES[c.z.type].recruit?[['build','Build'],['recruit','Recruit'],['base','Base']]:[['build','Build'],['base','Base']];
  return [['recruit','Recruit']];}
// the base whose pads are showing (one of yours, selected): the pads in the bar and the 3D highlights follow city.sel
function syncCity(c){
  if(c.k==='base'){if(!city||city.zid!==c.z.id){city={zid:c.z.id,sel:Math.max(0,c.z.plots.findIndex(p=>!p.fac))};tutEv.city=true;}}
  else city=null;}
function stanceOf(us){const s=new Set(us.filter(u=>!u.def.plane).map(u=>u.stance||'aggr'));return s.size===1?[...s][0]:null;}
function hpCol(k){return k>.6?'var(--good)':k>.3?'var(--warn)':'var(--bad)';}

function refreshSel(){
  const c=selCtx();syncCity(c);
  const tabs=tabsFor(c);if(!cardTab||!tabs.some(t=>t[0]===cardTab))cardTab=tabs[0][0];
  renderSelBox(c);renderCard(c,tabs);
}
function renderSelBox(c){
  if(c.k==='units'){
    const us=c.us,planes=us.filter(u=>u.def.plane),g=us.filter(u=>u.garrison!==null).length;
    const sig='u'+us.map(u=>u.id).join(',')+(planes.length?'p':'');
    if(sig!==selSig){selSig=sig;
      selHead.innerHTML=`<b>${us.length} selected</b>${g?`<span class="dim">${g} on garrison duty</span>`:''}<span class="dim">Click a portrait to pick it · Shift-click to drop it · Ctrl-click for every one of that type</span>`;
      if(planes.length){selBody.innerHTML=airPanelHTML(us,planes);}
      else if(us.length<=36){
        const sorted=us.slice().sort((a,b)=>a.type<b.type?-1:a.type>b.type?1:a.id-b.id);
        selBody.innerHTML=`<div class="ports">${sorted.map(u=>`<button class="pt" data-uid="${u.id}" title="${u.def.name}${u.garrison!==null?' (garrison)':''}">${ICONS[u.type]||''}${u.garrison!==null?'<span class="gar">G</span>':''}<span class="hp"><i id="ph${u.id}"></i></span></button>`).join('')}</div>`;}
      else{const by={};for(const u of us)(by[u.type]=by[u.type]||[]).push(u);
        selBody.innerHTML=`<div class="ports">${Object.entries(by).map(([t,l])=>`<button class="pt" data-type="${t}" title="${l.length} ${l.length>1?PLURAL[t]:UTYPES[t].name}">${ICONS[t]||''}<span class="cnt">${l.length}</span><span class="hp"><i id="pt_${t}"></i></span></button>`).join('')}</div>`;}
    }
    // live health
    if(planes.length)updateAirPanel(planes);
    else if(us.length<=36){for(const u of us){const e=document.getElementById('ph'+u.id);if(e){const k=u.hp/u.maxHp;e.style.width=(k*100).toFixed(0)+'%';e.style.background=hpCol(k);}}}
    else{const by={};for(const u of us){const b=by[u.type]=by[u.type]||[0,0];b[0]+=u.hp;b[1]+=u.maxHp;}
      for(const [t,[h,m]] of Object.entries(by)){const e=document.getElementById('pt_'+t);if(e){e.style.width=(h/m*100).toFixed(0)+'%';e.style.background=hpCol(h/m);}}}
    return;
  }
  if(c.k==='base'||c.k==='zone'){
    const z=c.z,mine=c.k==='base',P=ZTYPES[z.type].prod,ZT=ZTYPES[z.type];
    let field=0;for(const u of G.units)if(u.alive&&u.home===z.id&&u.garrison===null)field++;
    const st=z.prodState==='building'?`building ${UTYPES[P.seq[z.prodI%P.seq.length]].name} (${Math.ceil(Math.max(0,z.prodT))}s)`:z.prodState==='full'?'mustered, waiting':z.prodState==='paused'?'halted under attack':'idle';
    const h=baseHealth(z),used=k=>z.plots.filter(p=>p.kind===k&&p.fac).length,y=G.zoneYield(z),div=G.BALANCE.economy;
    const hp=h.max>0?h.now/h.max:0,cls=h.now<=0?' gone':hp<.4?' low':'';
    selHead.innerHTML=`<b style="color:${facCss(z.owner)}">${z.name}</b><span class="ztag">${baseLabel(z)}</span>`+
      (z.contested?'<span style="color:var(--bad)">Under attack: building and production halted</span>':'');
    let body=(z.owner===null?'':`<span class="zhp${cls}" title="Health: the garrison plus pillboxes and AA. It must reach zero before the base can be captured."><i style="width:${(Math.min(1,hp)*100).toFixed(0)}%"></i></span>`)+
      `<div class="zrow">${z.owner===null?'<span>No defenders</span>':`<span>Health <b class="num">${Math.ceil(h.now)}/${Math.ceil(h.max)}</b></span><span>Garrison <b class="num">${z.garN}/${ZT.garrison}</b></span>${z.defN?`<span>Defences <b class="num">${z.defN}</b></span>`:''}`}`+
      `<span>Fort <b class="num">${used('fort')}/${z.slots.fort}</b></span><span>Eco <b class="num">${used('eco')}/${z.slots.eco}</b></span><span>Mil <b class="num">${used('mil')}/${z.slots.mil}</b></span><span>+$${(y.income/div.incomeDiv).toFixed(1)}/s</span>${z.type==='airbase'?`<span>Planes <b class="num">${G.planesAt(z)}/${G.planeCap(z)}</b></span>`:''}</div>`;
    if(!mine){body+=`<p class="hint" style="margin-top:6px">${z.owner===null?'Unclaimed. Move troops inside the ring to take it.':G.allied(z.owner,ME)?'Held by an ally.':'Enemy held. Destroy its garrison and defences, then stand inside the ring.'}</p>`;}
    else{
      body+=`<div class="zrow"><span>Field ${field}/${P.cap} · ${st}. ${z.rally?'Rally set.':G.factions[ME].rally?'Using the global rally.':'Right-click the ground to set a rally point.'}</span></div>`;
      body+=`<div class="plotGrid">`+z.plots.map(p=>{const f=p.fac;return `<button class="plot k-${p.kind}${city&&p.i===city.sel?' on':''}${f?' full':''}" data-plot="${p.i}" title="${SLOT_LABEL[p.kind]} pad${p.water?', by the water':''} (key ${p.i+1<10?p.i+1:''})"><span class="pn num">${p.i+1}</span><span class="pk">${SLOT_TAG[p.kind]}</span><span class="pi">${f?FAC_ICON[f.type]:'+'}</span><span class="pt">${f?FAC[f.type].name+(f.level>1?' II':''):'Empty'}</span><i class="pb" id="pb${p.i}"></i></button>`;}).join('')+`</div>`;
    }
    const sig='z'+z.id+'|'+body;
    if(sig!==selSig){selSig=sig;selBody.innerHTML=body;}
    if(mine)for(const p of z.plots){const b=document.getElementById('pb'+p.i);if(!b)continue;const f=p.fac;let w=0;
      if(f&&f.state!=='ready')w=f.t/f.T;else if(f&&FAC[f.type].prod&&f.pstate==='building')w=1-Math.max(0,f.prodT)/(UTYPES[f.next||FAC[f.type].prod.seq[0]].build*(f.level>1?G.BALANCE.upgradeSpeed:1));b.style.width=(w*100).toFixed(0)+'%';}
    return;
  }
  if(selSig!=='none'){selSig='none';
    selHead.innerHTML='<b>Command</b><span class="dim">Nothing selected</span>';
    selBody.innerHTML=`<p class="hint">Drag a box around your units, or click one of your bases to see its build pads.</p>
      <div class="tips"><kbd>Right-click</kbd><span>move / attack · right-drag to spread along a line</span><kbd>F</kbd><span>fight-move</span><kbd>H</kbd><span>halt</span>
      <kbd>Shift+1–9</kbd><span>save a control group, 1–9 to recall it</span><kbd>Space</kbd><span>jump home</span></div>`;}
}
function airPanelHTML(us,planes){const others=us.length-planes.length;
  return `<div><b style="font-family:var(--f-display)">${planes.length} aircraft</b>${others?` <span style="color:var(--dim)">+ ${others} ground</span>`:''}
    <span class="airall"><button data-air="auto">All auto</button><button data-air="manual">All manual</button></span></div>
    <div class="airlist">${planes.slice(0,10).map(u=>`<div class="airrow" data-id="${u.id}"><span class="an">${{intc:'Interceptor',cas:'CAS',bomb:'Bomber'}[u.type]}</span><span class="as" id="as${u.id}"></span>
      <span class="tg"><button data-mode="auto" data-id="${u.id}">Auto</button><button data-mode="manual" data-id="${u.id}">Manual</button></span><i class="hb" id="hb${u.id}"></i></div>`).join('')}
    ${planes.length>10?`<small class="dim">+${planes.length-10} more</small>`:''}</div>`;}
function updateAirPanel(planes){
  for(const u of planes.slice(0,10)){
    const st=document.getElementById('as'+u.id);if(st)st.textContent=G.planeStatus(u);
    const hb=document.getElementById('hb'+u.id);if(hb){hb.style.width=(u.hp/u.maxHp*100).toFixed(0)+'%';hb.style.background=u.pstate==='ground'&&u.rearmT>0?'var(--warn)':'var(--good)';}
    selBody.querySelectorAll(`button[data-id="${u.id}"]`).forEach(b=>b.setAttribute('aria-pressed',String((b.dataset.mode==='manual')===!!u.manual)));}}
selBody.addEventListener('click',e=>{
  const b=e.target.closest('button');if(!b)return;
  if(b.dataset.air){const ids=selUnits().filter(u=>u.def.plane).map(u=>u.id);A.order('airmode',ids,b.dataset.air==='manual');toast(b.dataset.air==='manual'?'Aircraft on Manual: right-click a target or area to send them.':'Aircraft on Auto: they pick their own targets.',true);}
  else if(b.dataset.mode){A.order('airmode',[+b.dataset.id],b.dataset.mode==='manual');}
  else if(b.dataset.uid){const id=+b.dataset.uid,u=G.units.find(o=>o.id===id);
    if(e.ctrlKey||e.metaKey){const t=u&&u.type;selected=new Set(selUnits().filter(o=>o.type===t).map(o=>o.id));}
    else if(e.shiftKey)selected.delete(id);else selected=new Set([id]);}
  else if(b.dataset.type){const t=b.dataset.type;
    if(e.shiftKey)selected=new Set(selUnits().filter(o=>o.type!==t).map(o=>o.id));else selected=new Set(selUnits().filter(o=>o.type===t).map(o=>o.id));}
  else if(b.dataset.plot!=null&&city){city.sel=+b.dataset.plot;cardTab='build';}
  selSig='';cardSig='';refreshSel();
});
selBody.addEventListener('dblclick',e=>{const b=e.target.closest('button[data-uid]');if(!b)return;const u=G.units.find(o=>o.id===+b.dataset.uid);if(u){cam.x=u.x;cam.z=u.z;}});

// one command-card button
function cb(o){return `<button class="cb" ${o.attrs||''} ${o.dis?'disabled':''} ${o.pressed!=null?`aria-pressed="${o.pressed}"`:''} data-hint="${(o.hint||'').replace(/"/g,'&quot;')}">${o.icon||''}<span class="n">${o.name}</span>${o.cost?`<span class="c">${o.cost}</span>`:''}${o.key?`<kbd>${o.key}</kbd>`:''}${o.bar?'<i class="pb" id="'+o.bar+'"></i>':''}</button>`;}
function renderCard(c,tabs){
  const tabSig=tabs.map(t=>t[0]).join(',')+'/'+cardTab;
  let top='',grid='',hint='',sig='';
  if(cardTab==='orders'){
    const us=c.us,planes=us.filter(u=>u.def.plane),ground=us.length-planes.length,st=stanceOf(us);
    sig='o'+ground+'|'+planes.length+'|'+st+'|'+fightArmed+'|'+planes.map(u=>u.manual?1:0).join('');
    if(sig!==cardSig){
      grid=cb({attrs:'data-cmd="fight"',icon:CI.fight,name:'Fight',key:'F',dis:!ground,pressed:fightArmed,hint:'<b>Fight-move</b>: click a spot. Units attack anything they meet on the way.'})+
        cb({attrs:'data-cmd="stop"',icon:CI.stop,name:'Halt',key:'H',hint:'<b>Halt</b>: stop and drop the current order.'});
      for(const [k,n,h] of STANCES)grid+=cb({attrs:`data-stance="${k}"`,icon:CI[k],name:n,dis:!ground,pressed:st===k,hint:`<b>${n}</b>: ${h}`});
      if(planes.length){const man=planes.every(u=>u.manual),auto=planes.every(u=>!u.manual);
        grid+=cb({attrs:'data-air="auto"',icon:CI.auto,name:'Air: Auto',pressed:auto,hint:'<b>Auto</b>: aircraft pick their own targets.'})+
          cb({attrs:'data-air="manual"',icon:CI.manual,name:'Air: Manual',pressed:man,hint:'<b>Manual</b>: aircraft wait for you. Right-click a target or area to send them.'});}
      hint=ground?`Stance applies to ${ground} ground unit${ground>1?'s':''}. Right-click to move or attack.`:'Right-click a target or area to send the aircraft.';
    }
  }else if(cardTab==='recruit'){
    const z=G.zones[c.k==='base'?c.z.id:deployZone],ok=z&&z.owner===ME&&ZTYPES[z.type].recruit;
    const ros=ok?G.rosterOf(z):[],dock=ok&&z.plots.some(p=>p.fac&&p.fac.type==='dockyard'&&p.fac.state==='ready'&&p.water);
    const avail=RECRUITABLE.filter(t=>ros.includes(t.key)&&!(t.req==='dockyard'&&!dock));
    const errs=avail.map(t=>G.canRecruit(ME,t.key,z.id)||'').join('|');
    sig='r'+(z?z.id:-1)+'|'+c.k+'|'+errs;
    if(sig!==cardSig){
      if(c.k!=='base')top=ok?`<span class="lbl">Deploy at</span><button data-cmd="dprev" aria-label="Previous base">‹</button><b>${z.name}</b><button data-cmd="dnext" aria-label="Next base">›</button>`:'<span class="lbl">No base to deploy from</span>';
      for(const t of avail){const err=G.canRecruit(ME,t.key,z.id);
        grid+=cb({attrs:`data-rec="${t.key}"`,icon:ICONS[t.key],name:t.name,cost:`$${t.cost}·${t.hr}`,key:t.hot,dis:!!err,hint:`<b>${t.name}</b> · $${t.cost}, ${t.hr} manpower${err?` · <span class="why">${err}</span>`:''}`});}
      // what this base can't field, and where to get it
      const notHere=RECRUITABLE.filter(t=>!avail.includes(t)),by={};
      for(const t of notHere){const why=ros.includes(t.key)?'build a Dockyard here':fieldedAt(t.key);(by[why]=by[why]||[]).push(t.name);}
      hint=ok?(notHere.length?'Not here: '+Object.entries(by).map(([w,l])=>`${l.join(', ')} <span class="why">(${w})</span>`).join(' · '):'This base fields every unit.'):'Capture a Fortress, Town, Port or your HQ to recruit.';
    }
  }else if(cardTab==='build'){
    const z=c.z,p=z.plots[city.sel];
    if(!p){sig='b-';grid='';}
    else if(!p.fac){
      const opts=FAC_KEYS.filter(k=>FAC[k].slot===p.kind);
      sig='be'+z.id+'|'+p.i+'|'+z.contested+'|'+opts.map(k=>G.canBuild(ME,z.id,p.i,k)||'').join('|');
      if(sig!==cardSig){
        top=`<span class="lbl">Pad ${p.i+1} · ${SLOT_LABEL[p.kind]}${p.water?' · waterside':''}</span>`;
        for(const k of opts){const D=FAC[k],err=G.canBuild(ME,z.id,p.i,k);
          grid+=cb({attrs:`data-build="${k}"`,icon:`<span class="ic">${FAC_ICON[k]}</span>`,name:D.name,cost:`$${D.cost}·${D.time}s`,dis:!!err,hint:`<b>${D.name}</b>: ${D.desc}${err?` <span class="why">${err}</span>`:''}`});}
        hint=`Pick a building for pad ${p.i+1}. Hover a button for details.`;
      }
    }else{
      const f=p.fac,D=FAC[f.type],uerr=G.canUpgrade(ME,z.id,p.i);
      sig='bf'+z.id+'|'+p.i+'|'+f.type+f.state+f.level+'|'+uerr+'|'+(f.mode||'cycle');
      if(sig!==cardSig){
        top=`<span class="lbl">Pad ${p.i+1}</span><b>${D.name}${f.level>1?' II':''}</b>`;
        if(f.level<2)grid+=cb({attrs:'data-cmd="upgrade"',icon:CI.up,name:'Upgrade',cost:`$${G.upgradeCost(p)}`,dis:!!uerr,hint:`<b>Upgrade</b>: faster output and a tougher building.${uerr?` <span class="why">${uerr}</span>`:''}`});
        grid+=cb({attrs:'data-cmd="demolish"',icon:CI.clear,name:'Demolish',hint:'<b>Demolish</b>: clear the pad for something else. Part of the cost is refunded.'});
        if(f.type==='hangar'&&f.state==='ready')for(const [k,l] of [['cycle','Cycle'],['intc','Interceptor'],['cas','CAS'],['bomb','Bomber']])
          grid+=cb({attrs:`data-afmode="${k}"`,icon:k==='cycle'?CI.auto:ICONS[k],name:l,pressed:(f.mode||'cycle')===k,hint:`<b>Hangar builds</b>: ${k==='cycle'?'each aircraft type in turn':l+'s only'}.`});
        hint=`${D.desc} <span id="cStatus" class="num"></span>`;
      }
    }
  }else if(cardTab==='base'){
    const z=c.z;sig='bs'+z.id+'|'+!!z.rally;
    if(sig!==cardSig){
      grid=cb({attrs:'data-cmd="zoom"',icon:CI.zoom,name:'Zoom in',key:'G',hint:'<b>Zoom in</b> on this base (or double-click it).'})+
        cb({attrs:'data-cmd="rallyclear"',icon:CI.clear,name:'Clear rally',dis:!z.rally,hint:'<b>Clear rally</b>: new troops muster at this base again.'})+
        cb({attrs:'data-cmd="rallyall"',icon:CI.rally,name:'All here',dis:!z.rally,hint:'<b>All zones here</b>: every base sends its new troops to this rally point.'});
      hint='Right-click the ground to set this base\'s rally point.';
    }
  }
  const full=tabSig+'#'+sig;
  if(full!==cardSig){cardSig=full;
    cardTabs.innerHTML=tabs.length>1?tabs.map(([k,l])=>`<button role="tab" data-tab="${k}" aria-selected="${k===cardTab}">${l}</button>`).join(''):`<button role="tab" aria-selected="true" disabled>${tabs[0][1]}</button>`;
    cardTop.innerHTML=top;cardGrid.innerHTML=grid;cardHint.innerHTML=hint;cardHint.dataset.base=hint;}
  // live status of the selected building
  if(cardTab==='build'&&city){const p=G.zones[city.zid].plots[city.sel],e=document.getElementById('cStatus');if(e&&p)e.textContent=' · '+facStatus(G.zones[city.zid],p);}
}
// card hints follow the pointer
cardGrid.addEventListener('pointerover',e=>{const b=e.target.closest('.cb');if(b&&b.dataset.hint)cardHint.innerHTML=b.dataset.hint;});
cardGrid.addEventListener('pointerleave',()=>{cardHint.innerHTML=cardHint.dataset.base||'';});
cardTabs.addEventListener('click',e=>{const b=e.target.closest('button[data-tab]');if(!b)return;cardTab=b.dataset.tab;cardSig='';refreshSel();});
cardTop.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;if(b.dataset.cmd==='dprev')cycleDeploy(-1);else if(b.dataset.cmd==='dnext')cycleDeploy(1);});
cardGrid.addEventListener('click',e=>{
  const b=e.target.closest('.cb');if(!b||b.disabled)return;const d=b.dataset,c=selCtx();
  if(d.rec)doRecruit(d.rec,c.k==='base'?c.z.id:deployZone);
  else if(d.stance){const ids=selUnits().filter(u=>!u.def.plane).map(u=>u.id);A.order('stance',ids,d.stance);
    const n=STANCES.find(s=>s[0]===d.stance);toast(`${n[1]}: ${n[2]}`,true);
    if(!NET)for(const u of selUnits())if(!u.def.plane)u.stance=d.stance==='aggr'?null:d.stance;}
  else if(d.air){const ids=selUnits().filter(u=>u.def.plane).map(u=>u.id);A.order('airmode',ids,d.air==='manual');}
  else if(d.build&&city){const r=A.build(city.zid,city.sel,d.build);if(!r.ok)toast(r.err);else toast(`${FAC[d.build].name} under construction`,true);}
  else if(d.afmode&&city){A.hangar(city.zid,city.sel,d.afmode);}
  else if(d.cmd==='fight')setFight(!fightArmed);
  else if(d.cmd==='stop'){A.order('stop',[...selected]);setFight(false);}
  else if(d.cmd==='upgrade'&&city){const r=A.upgrade(city.zid,city.sel);if(!r.ok)toast(r.err);}
  else if(d.cmd==='demolish'&&city){const r=A.demolish(city.zid,city.sel);if(r.ok)toast(r.pending?'Demolishing':`Demolished, refunded $${r.refund}`,true);}
  else if(d.cmd==='zoom'&&selZone!=null)zoomBase(selZone);
  else if(d.cmd==='rallyclear'&&selZone!=null)A.rally(selZone,null);
  else if(d.cmd==='rallyall'){const z=G.zones[selZone];if(z&&z.rally){A.grally(z.rally.x,z.rally.z);toast('Every zone now sends its new troops to this rally (zones you capture too)',true);}}
  cardSig='';selSig='';refreshSel();
});
"""
s=s[:i]+new+s[j:]

# zone view: no separate panel any more -- selecting your base shows its pads in the bar
i=s.index("// ---------- zone view mode ----------");j=s.index("let camGoal=null;")
s=s[:i]+"""// ---------- base pads (selecting one of your bases shows them in the command bar) ----------
let city=null;   // {zid,sel}: the selected base of yours and its selected pad
function zoomBase(zid){const z=G.zones[zid];if(!z)return;camGoal={x:z.x,z:z.z+6,d:62};}
function enterCity(zid){const z=G.zones[zid];if(!z||z.owner!==ME)return;
  selected.clear();setFight(false);selZone=zid;if(ZTYPES[z.type].recruit)deployZone=zid;cardTab='build';zoomBase(zid);selSig=cardSig='';refreshSel();}
function exitCity(){if(selZone!=null){selZone=null;city=null;selSig=cardSig='';refreshSel();}}
"""+s[j:]
i=s.index("let citySig='';\nfunction refreshCity(){");j=s.index("function drawCityOverlay(){")
s=s[:i]+"function refreshCity(){}\n"+s[j:]
open(p,'w').write(s)
