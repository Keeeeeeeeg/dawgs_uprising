p='/home/claude/vu/v23.html';s=open(p).read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(s.count(a),a[:80]);s=s.replace(a,b)
# rover at every base (1 per forward base, 2 at an HQ)
rep("      roster:['rifle','mg','at','tech','ltank','mtank','htank','spg','how','lheli','heli','flak','sam','airship'],naval:['boat','monitor'],",
    "      roster:['rifle','mg','at','tech','ltank','mtank','htank','spg','how','lheli','heli','flak','sam','airship','rover'],naval:['boat','monitor'],")
rep("      roster:['rifle','mg','at','tech','ltank','flak'],naval:['boat'],","      roster:['rifle','mg','at','tech','ltank','flak','rover'],naval:['boat'],")
rep("      roster:['rifle','mg','flak','intc','cas','bomb'],naval:[],","      roster:['rifle','mg','flak','intc','cas','bomb','rover'],naval:[],")
rep("  build:{radius:24, minFromCentre:3.5, spacing:6.4, maxRovers:3, aiRovers:3,","  // rovers: each base can keep its own (roverPerBase, roverAtHQ at an HQ); recruit one there to fill the slot\n  build:{radius:24, minFromCentre:3.5, spacing:6.4, roverPerBase:1, roverAtHQ:2, aiRovers:3,")
rep("    if(def.builder&&roverCount(f)>=BLD.maxRovers)return `You already have ${BLD.maxRovers} Construction Rovers.`;",
    "    if(def.builder){const r=roverSlots(z);if(r.n>=r.cap)return `${z.name} already has its ${r.cap} Construction Rover${r.cap>1?'s':''} (${r.n}/${r.cap}).`;}")
rep("  function roverCount(f){","  function roverSlots(z){let n=0;for(const u of G.units)if(u.alive&&u.def.builder&&u.roverHome===z.id&&u.f===z.owner)n++;return {n,cap:z.type==='hq'?BLD.roverAtHQ:BLD.roverPerBase};}\n  function roverCount(f){")
# recruit records the rover's home base
rep("    const u=port?spawnUnit(type,f,port.water.x,port.water.z):spawnUnit(type,f,z.x+Math.cos(a)*r,z.z+Math.sin(a)*r);\n","    const u=port?spawnUnit(type,f,port.water.x,port.water.z):spawnUnit(type,f,z.x+Math.cos(a)*r,z.z+Math.sin(a)*r);\n    if(def.builder)u.roverHome=z.id;\n")
open(p,'w').write(s)
