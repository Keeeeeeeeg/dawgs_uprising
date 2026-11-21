p='/home/claude/vu/v24.html';s=open(p).read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(s.count(a),a[:80]);s=s.replace(a,b)
rep("  missile:{every:120, max:3, dmg:650,","  // ICBMs: only an HQ with a Missile Silo (a Base Upgrade: siloCost, siloTime s) builds them, one every `every` s up to max.\n  // A launch takes launchDelay s (doors open, steam, the missile rises) before the flight starts.\n  missile:{siloCost:1800, siloTime:90, launchDelay:4.5, aiSiloAfter:480, every:180, max:2, dmg:650,")
rep("  function missileStock(f){let n=0;for(const z of G.zones)if(z.owner===f&&z.type==='hq')n+=z.msl;return n;}","""  function missileStock(f){let n=0;for(const z of G.zones)if(z.owner===f&&z.type==='hq'&&z.silo)n+=z.msl;return n;}
  function hasSilo(f){return G.zones.some(z=>z.owner===f&&z.type==='hq'&&z.silo);}
  function canSilo(f,zid){const z=G.zones[zid];if(!z||z.owner!==f)return 'Not your base.';if(z.type!=='hq')return 'Only an HQ can hold a Missile Silo.';
    if(z.silo)return 'Silo already built.';if(z.siloUp)return 'Already under construction.';if(z.contested)return 'Cannot build while the base is under attack.';
    if(F[f].money<MSL.siloCost)return `Need $${MSL.siloCost}.`;return null;}
  function silo(f,zid){const e=canSilo(f,zid);if(e)return {ok:false,err:e};const z=G.zones[zid];F[f].money-=MSL.siloCost;z.siloUp={t:0,T:MSL.siloTime};emit('zoneup',z);return {ok:true};}""")
rep("  function missileNext(f){let t=null;for(const z of G.zones)if(z.owner===f&&z.type==='hq'&&z.msl<MSL.max){","  function missileNext(f){let t=null;for(const z of G.zones)if(z.owner===f&&z.type==='hq'&&z.silo&&z.msl<MSL.max){")
rep("""    for(const z of G.zones){
      if(z.type!=='hq'||z.owner===null)continue;
      if(z.msl>=MSL.max){z.mslT=0;continue;}""","""    for(const z of G.zones){
      if(z.type!=='hq'||z.owner===null)continue;
      if(z.siloUp&&!z.contested){z.siloUp.t+=dt;if(z.siloUp.t>=z.siloUp.T){z.silo=true;z.siloUp=null;z.mslT=0;emit('zoneup',z);if(F[z.owner].player)log(`${z.name}: Missile Silo complete. First missile in ${Math.round(MSL.every/60)} min.`,z.owner);}}
      if(!z.silo)continue;
      if(z.msl>=MSL.max){z.mslT=0;continue;}""")
rep("    let hq=null,bd=1e9;for(const q of G.zones)if(q.owner===f&&q.type==='hq'&&q.msl>0){","    let hq=null,bd=1e9;for(const q of G.zones)if(q.owner===f&&q.type==='hq'&&q.silo&&q.msl>0){")
rep("    if(!hq)return {ok:false,err:'No missile ready. Each HQ you hold builds one every '+Math.round(MSL.every/60)+' minutes.'};",
    "    if(!hq)return {ok:false,err:hasSilo(f)?'No missile ready yet.':'No Missile Silo. Build one at your HQ (Base Upgrades).'};")
rep("    const p={sx:hq.x,sz:hq.z,sy:hq.y+2,ex:x,ez:z,ey:Math.max(0,heightAt(x,z)),t:0,T,wpn:'missile',","    const sp=siloSpot(hq),p={sx:sp.x,sz:sp.z,sy:hq.y+2,ex:x,ez:z,ey:Math.max(0,heightAt(x,z)),t:-MSL.launchDelay,T,wpn:'missile',")
rep("  function launchMissile(f,x,z){","  // where the silo sits inside an HQ (renderer uses the same spot)\n  function siloSpot(z){const a=(z.gate||0)+Math.PI*.75;return {x:z.x+Math.cos(a)*z.r*.52,z:z.z+Math.sin(a)*z.r*.52};}\n  function launchMissile(f,x,z){")
rep("z.rally=null;z.msl=0;z.mslT=0;","z.rally=null;z.msl=0;z.mslT=0;z.siloUp=null;")
rep("      case 'hosp':return hospital(f,c.zid);","      case 'hosp':return hospital(f,c.zid);\n      case 'silo':return silo(f,c.zid);")
rep("Object.assign(G,{","Object.assign(G,{canSilo,hasSilo,siloSpot,")
# AI builds a silo late in the game when it is rich
rep("    if(fac.money>AIB.buildMoney*1.5&&rnd()<.04){","    if(G.time>MSL.aiSiloAfter&&fac.money>MSL.siloCost+400&&rnd()<.05){const hq=G.zones.find(q=>q.owner===fac.id&&q.type==='hq'&&!canSilo(fac.id,q.id));if(hq)silo(fac.id,hq.id);}\n    if(fac.money>AIB.buildMoney*1.5&&rnd()<.04){")
open(p,'w').write(s)
