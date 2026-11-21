p='/home/claude/vu/v21.html';s=open(p).read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(s.count(a),a[:80]);s=s.replace(a,b)
rep("  production:{fieldPerFacility:2,","""  // a base's own troops: it only ever keeps `garrison` of them alive (wherever they are), replacing losses. The trickle is
  // slow (base `every` x slow) until bought Garrison Drill levels speed it up; each level takes `time` s to put in.
  drill:{slow:1.6, costs:[150,260], time:[30,40], speed:[1,1.45,2]},
  production:{fieldPerFacility:2,""")
rep("""    const u=spawnUnit(type,z.owner,z.x+Math.cos(a)*r,z.z+Math.sin(a)*r);
    u.garrison=z.id;return toughen(u,z);""","""    const u=spawnUnit(type,z.owner,z.x+Math.cos(a)*r,z.z+Math.sin(a)*r);
    u.garrison=z.id;u.zoneMade=z.id;return toughen(u,z);""")
rep("    for(const u of G.units)if(u.home===z.id)u.home=null;","    for(const u of G.units){if(u.home===z.id)u.home=null;if(u.zoneMade===z.id)u.zoneMade=null;}\n    z.drill=1;z.drillUp=null;")
rep("""      const gNeed=garrisonCount(z)<ZTYPES[z.type].garrison&&!(fac.player&&(!fac.autoGarrison||(fac.rally&&!z.rally)));
      if(!gNeed&&fieldCount(z)>=fieldCap(z)){z.prodState='full';continue;}""","""      // hard cap: the base keeps at most `garrison` of its own troops alive, wherever they have been sent
      const GC=ZTYPES[z.type].garrison;let made=0;for(const u of G.units)if(u.alive&&u.zoneMade===z.id)made++;
      if(made>=GC){z.prodState='full';continue;}
      const gNeed=garrisonCount(z)<GC&&!(fac.player&&(!fac.autoGarrison||(fac.rally&&!z.rally)));""")
rep("""      u.home=z.id;
      if(gNeed){u.garrison=z.id;toughen(u,z);""","""      u.home=z.id;u.zoneMade=z.id;
      if(gNeed){u.garrison=z.id;toughen(u,z);""")
rep("      z.prodT=P.every*(PR.jitterMin+rnd()*PR.jitterSpread);z.prodEvery=P.every;","      const ev=P.every*BALANCE.drill.slow/BALANCE.drill.speed[(z.drill||1)-1];z.prodT=ev*(PR.jitterMin+rnd()*PR.jitterSpread);z.prodEvery=ev;")
# drill upgrades
rep("  function produce(dt){","""  const DR=BALANCE.drill;
  function drillCost(z){return DR.costs[(z.drill||1)-1];}
  function canDrill(f,zid){const z=G.zones[zid];if(!z||z.owner!==f)return 'Not your base.';if((z.drill||1)>=3)return 'Fully drilled.';
    if(z.drillUp)return 'Already upgrading.';if(z.contested)return 'Cannot upgrade while the base is under attack.';if(F[f].money<drillCost(z))return `Need $${drillCost(z)}.`;return null;}
  function drill(f,zid){const e=canDrill(f,zid);if(e)return {ok:false,err:e};const z=G.zones[zid];F[f].money-=drillCost(z);
    z.drillUp={t:0,T:DR.time[(z.drill||1)-1]};emit('zoneup',z);return {ok:true};}
  function drillTick(dt){for(const z of G.zones){const d=z.drillUp;if(!d)continue;if(z.owner===null){z.drillUp=null;continue;}if(z.contested)continue;
    d.t+=dt;if(d.t>=d.T){z.drill=(z.drill||1)+1;z.drillUp=null;emit('zoneup',z);if(F[z.owner].player)log(`${z.name}: Garrison Drill ${z.drill===2?'II':'III'} complete`,z.owner);}}}
  function produce(dt){
    drillTick(dt);""")
rep("      case 'hangar':","      case 'drill':return drill(f,c.zid);\n      case 'hangar':")
rep("Object.assign(G,{onRadar,","Object.assign(G,{canDrill,drillCost,onRadar,")
# AI buys drill now and then for its HQ and fortresses
rep("    // construction: Construction Rovers build everything","""    if(fac.money>AIB.buildMoney*1.5&&rnd()<.04){const z=G.zones.find(q=>q.owner===fac.id&&(q.type==='hq'||q.type==='fortress')&&!canDrill(fac.id,q.id));if(z)drill(fac.id,z.id);}
    // construction: Construction Rovers build everything""")
open(p,'w').write(s)
