p='/home/claude/vu/v23.html';s=open(p).read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(s.count(a),a[:80]);s=s.replace(a,b)
rep("    ST.squad.forEach((t,i)=>spawnUnit(t,f,hq.x+3+(i%3)*2.2,hq.z+5+Math.floor(i/3)*2.2));",
    "    ST.squad.forEach((t,i)=>{const u=spawnUnit(t,f,hq.x+3+(i%3)*2.2,hq.z+5+Math.floor(i/3)*2.2);if(u.def.builder)u.roverHome=hq.id;});")
rep("{fac.money-=UTYPES.rover.cost;const a=rnd()*TAU;spawnUnit('rover',fac.id,hq.x+Math.cos(a)*(hq.r+3),hq.z+Math.sin(a)*(hq.r+3));}}",
    """{const home=[hq,...G.zones.filter(z=>z.owner===fac.id&&z!==hq&&!z.contested)].find(z=>{const r=roverSlots(z);return r.n<r.cap;});
        if(home){fac.money-=UTYPES.rover.cost;const a=rnd()*TAU;const u=spawnUnit('rover',fac.id,home.x+Math.cos(a)*(home.r+3),home.z+Math.sin(a)*(home.r+3));u.roverHome=home.id;}}}""")
# --- garrison tiers
rep("  drill:{slow:1.6, costs:[150,260], time:[30,40], speed:[1,1.45,2]},","""  // Each base keeps a garrison of its own troops. What it can turn out is riflemen and machine gunners (its militia) plus
  // whatever its finished military buildings produce (a Motor Pool adds Technicals, tanks, AA vehicles...), within the
  // base's roster. Garrison Drill raises both the size (capK x the base type's garrison) and the quality (maxCost: the
  // dearest unit it may garrison), and speeds replacements. Level I is a thin, cheap militia.
  drill:{slow:1.6, costs:[200,380], time:[30,45], speed:[1,1.35,1.8], capK:[.5,.75,1], maxCost:[50,135,1e9], militia:['rifle','mg']},""")
rep("  function garrisonType(z,i){const seq=ZTYPES[z.type].garrisonSeq;return seq[i%seq.length];}","""  function garrisonCap(z){return Math.max(2,Math.round(ZTYPES[z.type].garrison*BALANCE.drill.capK[(z.drill||1)-1]));}
  // the ground units this base can garrison right now, cheapest first
  function garrisonPool(z){const DRL=BALANCE.drill,L=(z.drill||1)-1,set=new Set(DRL.militia);
    for(const p of z.plots){const f=p.fac;if(!f||f.state==='building'||!FACILITIES[f.type].prod)continue;for(const t of FACILITIES[f.type].prod.seq)set.add(t);}
    return [...set].filter(t=>{const d=UTYPES[t];return d&&!d.air&&!d.naval&&!d.plane&&!d.builder&&!d.noRecruit&&rosterOf(z).includes(t)&&d.cost<=DRL.maxCost[L];}).sort((a,b)=>UTYPES[a].cost-UTYPES[b].cost);}
  // pick the next garrison unit: a mix that leans toward the best the base can field, topping up whatever it has least of
  function garrisonType(z){const pool=garrisonPool(z);if(!pool.length)return 'rifle';const have={};
    for(const u of G.units)if(u.alive&&u.zoneMade===z.id)have[u.type]=(have[u.type]||0)+1;
    let best=pool[0],bs=-1e9;pool.forEach((t,i)=>{const w=1+i*.6,sc=w/(1+(have[t]||0))+rnd()*.3;if(sc>bs){bs=sc;best=t;}});return best;}""")
rep("""    const n=ZTYPES[z.type].garrison;
    for(let i=0;i<n;i++)addGarrison(z,garrisonType(z,i));""","""    const n=garrisonCap(z);
    for(let i=0;i<n;i++){const u=addGarrison(z,garrisonType(z));u.home=z.id;}""")
rep("  const GAR_FULL={};for(const [k,ZT] of Object.entries(ZTYPES)){let s=0;for(let i=0;i<ZT.garrison;i++)s+=UTYPES[ZT.garrisonSeq[i%ZT.garrisonSeq.length]].hp;GAR_FULL[k]=s*ZT.garrisonHp;}",
    "  // full garrison HP for the health bar: this base's current cap, at the average toughness of what it can garrison\n  const garFullOf=z=>{const pool=garrisonPool(z);let h=0;for(const t of pool)h+=UTYPES[t].hp;return garrisonCap(z)*(pool.length?h/pool.length:UTYPES.rifle.hp)*ZTYPES[z.type].garrisonHp;};")
rep("z.defHp=0;z.garFull=GAR_FULL[z.type];}","z.defHp=0;z.garFull=garFullOf(z);}")
rep("      let room=ZTYPES[z.type].garrison;\n","      let room=garrisonCap(z);\n")
rep("        let room=Math.min(AIB.pressGarrison,ZTYPES[z.type].garrison-garrisonCount(z));","        let room=Math.min(AIB.pressGarrison,garrisonCap(z)-garrisonCount(z));")
rep("        let room=ZTYPES[z.type].garrison-garrisonCount(z);","        let room=garrisonCap(z)-garrisonCount(z);")
rep("return k?k.gar+k.def:ZTYPES[z.type].garrison;}","return k?k.gar+k.def:garrisonCap(z);}")
# production: garrison only, from the pool
rep("      const GC=ZTYPES[z.type].garrison;let made=0;","      const GC=garrisonCap(z);let made=0;")
rep("""      let type=P.seq[z.prodI%P.seq.length];z.prodI++;
      if(gNeed&&(UTYPES[type].armor!=='inf'))type=garrisonType(z,garrisonCount(z));""","""      const type=garrisonType(z);z.prodI++;z.nextType=null;""")
rep("      const ev=P.every*BALANCE.drill.slow/BALANCE.drill.speed[(z.drill||1)-1];z.prodT=ev*","      // dearer troops take longer to raise (a tank about twice as long as a rifleman)\n      const nx=garrisonType(z);z.nextType=nx;const ev=P.every*BALANCE.drill.slow/BALANCE.drill.speed[(z.drill||1)-1]*Math.min(2.4,Math.max(1,Math.sqrt(UTYPES[nx].cost/30)));z.prodT=ev*")
rep("Object.assign(G,{","Object.assign(G,{garrisonCap,garrisonPool,roverSlots,")
open(p,'w').write(s)
