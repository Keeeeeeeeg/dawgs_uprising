p='/home/claude/vu/v18.html';s=open(p).read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(s.count(a),a[:80]);s=s.replace(a,b)
# --- unit + balance
rep("    tech:   {name:'Technical',","    rover:  {name:'Construction Rover',hot:'E',cost:120,mp:1,hp:260,speed:7.5, range:0, minR:0, dmg:0,  rof:1,   acc:0,  splash:0,  weapon:'bullet',    armor:'veh', build:20, builder:true},\n    tech:   {name:'Technical',")
rep("      roster:['rifle','mg','at','tech','ltank','mtank','htank','spg','how','heli','flak','sam'],naval:['boat','monitor'],\n      garrisonSeq:['rifle','mg','at','rifle','mg','at'],prod:{every:28,",
    "      roster:['rifle','mg','at','tech','ltank','mtank','htank','spg','how','heli','flak','sam','rover'],naval:['boat','monitor'],\n      garrisonSeq:['rifle','mg','at','rifle','mg','at'],prod:{every:28,")
rep("  demolishRefund:{building:.9, built:.4},","""  demolishRefund:{building:.9, built:.4},
  // free construction: Construction Rovers (recruited at an HQ) put buildings anywhere within `radius` m of a base's ring.
  // Each base holds up to its slot total in buildings (any mix). Several rovers on one site work faster: speed = n^stack.
  build:{radius:24, minFromCentre:3.5, spacing:6.4, maxRovers:3, aiRovers:2, stack:.6, reach:6.5},""")
rep("    squad:['rifle','rifle','rifle','rifle','mg','at'],   // every army's opening squad at its fortress",
    "    squad:['rifle','rifle','rifle','rifle','mg','at','rover'],   // every army's opening squad at its fortress (with one Construction Rover)")
open(p,'w').write(s)
