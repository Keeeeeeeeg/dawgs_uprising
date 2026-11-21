p='/home/claude/vu/v22.html';s=open(p).read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(s.count(a),a[:80]);s=s.replace(a,b)
# unit type for a building's body
rep("    pillbox:{name:'Pillbox',","    bld:    {name:'Building',      hot:'', cost:0,  mp:0,hp:400, speed:0,   range:0, minR:0, dmg:0,  rof:9,   acc:0,  splash:0,  weapon:'bullet',    armor:'struct',build:0, static:true, noRecruit:true, struct:true},\n    pillbox:{name:'Pillbox',")
rep("  build:{radius:24,","  // every non-defence building has a body enemies can shoot: HP = base + cost x perCost (x lvl2 when upgraded)\n  buildingHp:{base:260, perCost:2.2, lvl2:1.4},\n  build:{radius:24,")
# attach/detach bodies
rep("  function removePlot(z,p){const k=z.plots.indexOf(p);if(k<0)return;","""  function attachBody(z,p){if(!p.fac||isDefence(p.fac.type)||(p.body&&p.body.alive))return;const BH=BALANCE.buildingHp;
    const u=spawnUnit('bld',z.owner,p.x,p.z);u.x=p.x;u.z=p.z;u.ang=p.ang;u.plot=p;u.zone=z;u.maxHp=u.hp=Math.round((BH.base+FACILITIES[p.fac.type].cost*BH.perCost)*(p.fac.level>1?BH.lvl2:1));p.body=u;}
  function removePlot(z,p){const k=z.plots.indexOf(p);if(k<0)return;
    if(p.body&&p.body.alive){p.body.plot=null;p.body.alive=false;emit('death',p.body);}""")
rep("    emit('facility',p,z);assignBuilders(f,ids||[],z,p);return {ok:true,pi:p.i};}","    attachBody(z,p);emit('facility',p,z);assignBuilders(f,ids||[],z,p);return {ok:true,pi:p.i};}")
# start buildings and hangars
rep("      p.fac={type,level:1,state:'ready',t:0,T:1,prodT:ST.facilityFirst+k*ST.facilityStagger,prodI:0,pstate:'idle',unit:null};blockArea(p.x,p.z,2.6,true);});",
    "      p.fac={type,level:1,state:'ready',t:0,T:1,prodT:ST.facilityFirst+k*ST.facilityStagger,prodI:0,pstate:'idle',unit:null};blockArea(p.x,p.z,2.6,true);attachBody(hq,p);});")
rep("    p.fac={type:'hangar',level:1,state:'ready',t:0,T:1,prodT:FACILITIES.hangar.time,prodI:0,pstate:'idle',unit:null};blockArea(p.x,p.z,2.6,true);}",
    "    p.fac={type:'hangar',level:1,state:'ready',t:0,T:1,prodT:FACILITIES.hangar.time,prodI:0,pstate:'idle',unit:null};blockArea(p.x,p.z,2.6,true);attachBody(z,p);}")
# upgrades toughen the body; capture hands it over
rep("          if(isDefence(f.type)&&f.unit&&f.unit.alive){f.unit.maxHp=f.unit.hp=f.unit.def.hp*(f.level>1?BALANCE.upgradedDefenceHp:1);}",
    "          if(isDefence(f.type)&&f.unit&&f.unit.alive){f.unit.maxHp=f.unit.hp=f.unit.def.hp*(f.level>1?BALANCE.upgradedDefenceHp:1);}\n          if(p.body&&p.body.alive&&f.level>1&&was==='upgrading'){const k=p.body.hp/p.body.maxHp;p.body.maxHp=Math.round(p.body.maxHp*BALANCE.buildingHp.lvl2);p.body.hp=p.body.maxHp*k;}")
rep("      p.fac.state='ready';p.fac.prodT=FACILITIES[p.fac.type].prod?UTYPES[FACILITIES[p.fac.type].prod.seq[0]].build*PR.afterCapture:0;\n      emit('facility',p,z);",
    "      p.fac.state='ready';p.fac.prodT=FACILITIES[p.fac.type].prod?UTYPES[FACILITIES[p.fac.type].prod.seq[0]].build*PR.afterCapture:0;\n      if(p.body&&p.body.alive)p.body.f=f;else attachBody(z,p);\n      emit('facility',p,z);")
# a destroyed building (or defence) is gone: rubble, not an empty plot
rep("      if(t.plot){const p=t.plot;if(p.fac&&p.fac.unit===t){blockArea(p.x,p.z,2.6,false);p.fac=null;emit('facility',p,t.zone);}}",
    """      if(t.plot){const p=t.plot;if(p.fac&&(p.fac.unit===t||p.body===t)){p.destroyed=true;p.body=null;if(p.fac.unit===t)p.fac.unit=null;
        if(F[t.zone.owner]&&F[t.zone.owner].player||f===0)log(`${FACILITIES[p.fac.type].name} destroyed at ${t.zone.name}`,f);removePlot(t.zone,p);}}""")
# bodies don't count as army units, don't fight, and are a low-priority target
rep("  function unitCount(f){let n=0;for(const u of G.units)if(u.alive&&u.f===f)n++;return n;}","  function unitCount(f){let n=0;for(const u of G.units)if(u.alive&&u.f===f&&!u.def.struct)n++;return n;}")
rep("    if(d.builder){updateRover(u,dt);return;}","    if(d.builder){updateRover(u,dt);return;}\n    if(d.struct)return;")
rep("      if(o===u.target)s*=TG.stickiness;","      if(o===u.target)s*=TG.stickiness;\n      if(o.def.struct)s*=6;   // buildings only when nothing that fights back is near")
open(p,'w').write(s)
