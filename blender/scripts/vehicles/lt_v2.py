# Phase C, LIGHT TANK v1 ("bulldog brawler" + near-future): real metres, x forward, y left, z up, ground z 0, turret ring at
# (TX,0,ZR). Keegan's brief: tracks, twin 20 mm autocannons side by side in one mantlet with ammo chutes curling into the turret
# sides, ~3.6 m, faceted add-on armour with bolt rows, sensor mast + optics, segmented track skirts, APS pods, smoke launchers,
# stowage + tools, engine deck grilles/vents/exhaust, caged headlights, army-colour turret band + small tac markings.
import os,sys
exec(open('/home/claude/veh/vlib.py').read())
for o in list(bpy.data.objects):bpy.data.objects.remove(o)
OLIVE=(.075,.082,.058)
PAINT=vpaint('paint',OLIVE,mud=1.7,wear=1.8,dust=1.3,rust=1.0);PAINTT=vpaint('paintT',tuple(c*.92 for c in OLIVE),mud=.8,wear=1.8,dust=1.3,rust=.8)
WHEELP=vpaint('wheelPaint',(.055,.058,.048),mud=2.2,wear=1.0,dust=.3);STEELD=M('gunsteel',(.04,.041,.043),.42,.7);TRK=M('trackSteel',(.05,.047,.043),.6,.6);RUBW=rubber('rubber',(.025,.025,.024))
TEAMB=M('stripeTeam',(.05,.24,.04),.65);STEN=M('stencil',(.75,.73,.62),.7);GLOWL=M('lensGlow',(.35,1,.5),.2,0,6);LAMPG=M('lampGlass',(1,.92,.7),.1,0,3)
CANV=cloth('canvas',(.12,.11,.075),260);STRAP=cloth('strapw',(.06,.06,.045),500);BRASS=M('brassL',(.45,.32,.12),.35,.9);RED=M('redLens',(.6,.05,.03),.3,0,2)
P=[]   # every part: (object, group) ; groups: hull, turret, gunL, gunR, skirtL0.. (detachable), track
def add(name,bm,mat,grp='hull',bev=.008,smooth=False,segs=2):
  o=link(name,bm,mat,bev=bev,smooth=smooth,segs=segs);o['grp']=grp;P.append(o);return o
# ------------------------------------------------------------------ running gear
TY=1.17;TW=.42;WX=[-1.12,-.58,-.04,.5,1.04];WR=.25;WZ=.08+WR;SPX,SPZ,SPR=-1.53,.56,.25;IDX,IDZ,IDR=1.47,.5,.22
for sy in (1,-1):
  g='hull'
  for i,x in enumerate(WX):   # double road wheels: steel disc + rubber tyre + hub + bolts
    for dy in (-.1,.1):
      yc=sy*TY+dy
      add('wheel',cyl((x,yc-.065,WZ),(x,yc+.065,WZ),WR-.035,28),WHEELP,g,bev=.006)
      add('tyre',cyl((x,yc-.06,WZ),(x,yc+.06,WZ),WR,28),RUBW,g,bev=.01)
    add('hub',cyl((x,sy*(TY+.14),WZ),(x,sy*(TY+.2),WZ),.075,16),WHEELP,g,bev=.006)
    for k in range(6):a=k*math.pi/3;add('bolt',cyl((x+.05*math.cos(a),sy*(TY+.19),WZ+.05*math.sin(a)),(x+.05*math.cos(a),sy*(TY+.215),WZ+.05*math.sin(a)),.011,8),STEELD,g,bev=0)
    add('arm',xf(box((0,0,0),(.32,.06,.07)),Matrix.Translation((x+.13,sy*(TY-.25),WZ+.1))@Matrix.Rotation(-.45,4,'Y')),STEELD,g,bev=.006)   # suspension arm to the hull
  # drive sprocket (rear) with teeth, idler (front)
  for dy in (-.1,.1):
    add('sprocket',cyl((SPX,sy*TY+dy-.03,SPZ),(SPX,sy*TY+dy+.03,SPZ),SPR-.03,24),STEELD,g,bev=.004)
    for k in range(12):a=k*math.pi/6;add('tooth',xf(box((0,0,0),(.07,.06,.05)),Matrix.Translation((SPX+(SPR-.01)*math.cos(a),sy*TY+dy,SPZ+(SPR-.01)*math.sin(a)))@Matrix.Rotation(-a,4,'Y')),STEELD,g,bev=.004)
    add('idler',cyl((IDX,sy*TY+dy-.05,IDZ),(IDX,sy*TY+dy+.05,IDZ),IDR,24),STEELD,g,bev=.006)
  add('sprHub',cyl((SPX,sy*(TY-.15),SPZ),(SPX,sy*(TY+.17),SPZ),.09,16),STEELD,g,bev=.006);add('idHub',cyl((IDX,sy*(TY-.15),IDZ),(IDX,sy*(TY+.16),IDZ),.07,16),STEELD,g,bev=.006)
  for x in (-.85,.25):add('roller',cyl((x,sy*(TY-.12),.86),(x,sy*(TY+.12),.86),.07,16),RUBW,g,bev=.005)
  # TRACK: links along the loop (bottom run, front idler arc, top run over the return rollers, sprocket arc), grouser bars
  path=[];N0=60
  def arc(cx,cz,r,a0,a1,n):return [(cx+r*math.cos(a0+(a1-a0)*t/n),cz+r*math.sin(a0+(a1-a0)*t/n)) for t in range(n+1)]
  pts=[(SPX,.055)]+[(x,.055) for x in WX]+[(IDX-.12,.07)]+arc(IDX,IDZ,IDR+.03,-1.35,1.57,18)+[(.25,.96),(-.85,.96)]+arc(SPX,SPZ,SPR+.03,1.57,4.4,20)
  TRACK_PTS=pts
  # resample at link pitch
  segs=[(Vector((a[0],0,a[1])),Vector((b[0],0,b[1]))) for a,b in zip(pts,pts[1:]+pts[:1])];L=sum((b-a).length for a,b in segs);n=int(L/.085);pitch=L/n
  acc=0;si=0;pos=0.0;cen=Vector((0,0,.5))
  for k in range(n):
    s=k*pitch
    while s>acc+(segs[si][1]-segs[si][0]).length:acc+=(segs[si][1]-segs[si][0]).length;si+=1
    a,b=segs[si];t=(s-acc)/(b-a).length;p=a+(b-a)*t;d=(b-a).normalized();nrm=Vector((d.z,0,-d.x))   # outward (loop runs clockwise seen from +y)
    if nrm.dot(p-Vector(((SPX+IDX)/2,0,.45)))<0:nrm=-nrm
    ang=math.atan2(-d.z,d.x)
    Mt=Matrix.Translation((p.x,sy*TY,p.z))@Matrix.Rotation(ang,4,'Y')
    add('link',xf(box((0,0,0),(pitch*.92,TW,.045)),Mt),TRK,'track',bev=.004)
    add('grouser',xf(box((0,0,0),(.025,TW*.96,.03)),Mt@Matrix.Translation((0,0,-.035))),TRK,'track',bev=.003)
    if k%2==0:add('guide',xf(box((0,0,0),(.05,.035,.06)),Mt@Matrix.Translation((0,0,.045))),TRK,'track',bev=.003)
# ------------------------------------------------------------------ hull: central box between the tracks, sponsons over them
HW=.9;ZT=1.16
# (v2, Keegan: chunkier bulldog, more slope, aggressive stance) one long sloped glacis running up to the turret ring, deck
# dropping slightly to the rear, lower hull kept between the tracks
GL0=Vector((1.9,0,.64));GL1=Vector((.78,0,ZT));GD=(GL1-GL0).normalized();GN=Vector((-GD.z,0,GD.x))
if GN.z<0:GN=-GN
HP=[(-1.72,.42),(1.42,.36),(1.9,.64),(.78,ZT),(-1.42,ZT-.04),(-1.8,.98)]
add('hullLow',prism([(-1.72,.42),(1.42,.36),(1.9,.64),(1.8,.9),(-1.8,.9)],-HW,HW),PAINT,bev=.02)
add('hull',prism(HP,-.97,.97),PAINT,bev=.022)
SN=Vector((.26,0,1.08)).normalized()   # sponson brow slope normal
for sy in (1,-1):   # wide sponsons over the tracks: same slope at the front, outer top edge chamfered
  add('sponson',hull([(x,sy*y,z) for x,y,z in [(-1.74,.92,.92),(1.7,.92,.88),(-1.74,1.43,.92),(1.7,1.43,.88),(-1.74,.92,ZT-.04),(.78,.92,ZT),(-1.72,1.25,ZT-.04),(.78,1.25,ZT),(-1.74,1.43,1.06),(.6,1.43,1.07),(1.84,1.43,.9),(1.86,.92,.9)]]),PAINT,bev=.022)
  # HEAVY BROW: thick bolted armour block over each track front, following the slope
  def bp(t,y,o):return Vector((.78+1.08*t,sy*y,ZT-.26*t))+SN*o
  add('brow',hull([tuple(bp(t,y,o)) for t in (.12,1.0) for y in (.96,1.44) for o in (-.02,.08)]+[tuple(bp(t,y,.1)) for t in (.2,.9) for y in (1.02,1.36)]+[tuple(bp(t,1.45,-.13)) for t in (.12,1.0)]),PAINT,bev=.014)
  for t in (.3,.55,.8):
    for y in (1.05,1.34):pt=bp(t,y,.095);add('bolt',cyl(pt-SN*.015,pt+SN*.012,.013,8),STEELD,bev=0)
  # caged headlights tucked under the brow lip
  hx,hy,hz=1.86,sy*1.2,.93
  add('lampBody',cyl((hx-.08,hy,hz+.04),(hx+.04,hy,hz+.04),.06,16),STEELD,bev=.004);add('lampGlass',cyl((hx+.03,hy,hz+.04),(hx+.055,hy,hz+.04),.05,16),LAMPG,bev=0)
  for k in range(3):a=-.6+k*.6;add('cage',cyl((hx+.07,hy+.065*math.sin(a),hz+.04+.065*math.cos(a)),(hx-.03,hy+.065*math.sin(a),hz+.04+.065*math.cos(a)),.006,6),STEELD,bev=0)
  add('cageRing',cyl((hx+.07,hy,hz+.04),(hx+.08,hy,hz+.04),.07,16,None),STEELD,bev=0)
  add('fender',xf(box((0,0,0),(.36,.5,.025)),Matrix.Translation((1.8,sy*1.19,.885))@Matrix.Rotation(-.3,4,'Y')),PAINT,bev=.006)
  LN=Vector((.28,0,-.48)).normalized();LD=Vector((.48,0,.28)).normalized();pt=Vector((1.42,sy*.62,.36))+LD*.25;add('towEye',cyl(pt-LN*.03,pt+LN*.08,.05,14),STEELD,bev=.004)
# glacis add-on armour: one thick faceted plate on the lower half of the long glacis, bolt rows along its edges
def gp(t,y,o):return GL0+(GL1-GL0)*t+Vector((0,y,0))+GN*o
add('glacisPlate',hull([tuple(gp(t,y,o)) for t in (.04,.6) for y in (-.6,.6) for o in (-.01,.05)]+[tuple(gp(t,y,.065)) for t in (.1,.54) for y in (-.53,.53)]),PAINT,bev=.012)
for t in (.12,.52):
  for k in range(6):pt=gp(t,-.5+k*.2,.06);add('bolt',cyl(pt-GN*.015,pt+GN*.012,.013,8),STEELD,bev=0)
# driver: hatch on the glacis behind the plate, three periscopes looking forward, hinge
DP=gp(.8,.45,0)
add('drvHatch',cyl(DP-GN*.02,DP+GN*.035,.16,24),PAINT,bev=.008);add('drvHinge',xf(box((0,0,0),(.08,.24,.04)),Matrix.Translation(DP-GD*.2+GN*.02)),STEELD,bev=.005)
for k in range(3):
  c=DP+GD*-.2*0-GD*(-.0)+(-GD)*.19+Vector((0,-.12+k*.12,0))
  add('periscope',hull([tuple(c+GN*o+GD*d+Vector((0,w,0))) for o in (-.02,.06) for d in (-.03,.03) for w in (-.04,.04)]),STEELD,bev=.004)
# engine deck (rear): raised deck, louvred grilles, access hatches, exhaust with heat shield, fuel cans, tow cable
add('deck',prism([(-1.72,ZT-.02),(-.75,ZT-.02),(-.8,ZT+.06),(-1.66,ZT+.06)],-1.05,1.05),PAINT,bev=.012)
for sy in (1,-1):
  add('grilleFrame',xf(box((0,0,0),(.62,.62,.03)),Matrix.Translation((-1.22,sy*.46,ZT+.07))),PAINT,bev=.006)
  for k in range(9):add('louvre',xf(box((0,0,0),(.05,.56,.012)),Matrix.Translation((-1.48+k*.065,sy*.46,ZT+.085))@Matrix.Rotation(.6,4,'Y')),STEELD,bev=.002)
add('accessHatch',xf(box((0,0,0),(.34,.5,.03)),Matrix.Translation((-.62,0,ZT+.012))),PAINT,bev=.008)
for k in range(6):add('bolt',cyl((-.77+k*.06,-.22,ZT+.02),(-.77+k*.06,-.22,ZT+.04),.012,8),STEELD,bev=0)
# exhaust: small pipe out of the rear right with a muffler, perforated heat shield and soot
EX=Vector((-1.86,-.95,.9))
add('muffler',cyl((-1.79,-.95,.78),(-1.79,-.6,.78),.075,18),STEELD,bev=.006)
SOOT=M('soot',(.012,.011,.01),.95);add('exPipe',cyl((-1.82,-.98,.78),(-1.82,-.98,1.16),.035,14),STEELD,bev=.003);add('exTip',cyl((-1.82,-.98,1.16),(-1.9,-.98,1.21),.035,14),SOOT,bev=.003);add('exClamp',cyl((-1.82,-.98,1.0),(-1.82,-.98,1.03),.042,14),STEELD,bev=0);add('exBracket',xf(box((0,0,0),(.05,.05,.04)),Matrix.Translation((-1.8,-.98,1.0))),STEELD,bev=.003)
add('heatShield',xf(box((0,0,0),(.035,.4,.17)),Matrix.Translation((-1.87,-.78,.78))),PAINT,bev=.006)
for k in range(5):add('shieldSlot',xf(box((0,0,0),(.01,.04,.11)),Matrix.Translation((-1.889,-.94+k*.08,.78))),STEELD,bev=0)
add('rearPlate',hull([(-1.78,-1.2,.55),(-1.78,1.2,.55),(-1.8,-1.25,1.02),(-1.8,1.25,1.02),(-1.7,-1.2,.5),(-1.7,1.2,.5)]),PAINT,bev=.012)
for sy in (1,-1):add('tailLight',xf(box((0,0,0),(.025,.08,.05)),Matrix.Translation((-1.8,sy*1.12,.98))),RED,bev=.004)
for k,y in enumerate((.55,.25)):   # jerrycans in a rack on the rear plate
  add('jerry',xf(box((0,0,0),(.12,.26,.34)),Matrix.Translation((-1.88,y,.75))),PAINTT,bev=.015);add('jerryCap',cyl((-1.88,y+.08,.9),(-1.88,y+.08,.96),.025,10),STEELD,bev=.003)
  add('jerryStrap',xf(box((0,0,0),(.14,.28,.03)),Matrix.Translation((-1.88,y,.82))),STRAP,bev=.004)
add('canRack',xf(box((0,0,0),(.05,.7,.04)),Matrix.Translation((-1.82,.4,.6))),STEELD,bev=.005)
# tools + stowage on the sponson tops: shovel, pick, crowbar, tow cable coiled along the left side, spare track links on the glacis
def tool(x0,x1,y,z,r,mat,head=None):
  add('toolHaft',cyl((x0,y,z),(x1,y,z),r,10),mat,bev=0)
  for x in (x0+.12,x1-.12):add('toolClamp',xf(box((0,0,0),(.03,.05,.04)),Matrix.Translation((x,y,z-.005))),STEELD,bev=.003)
  if head:add('toolHead',xf(box((0,0,0),head[1]),Matrix.Translation(head[0])),STEELD,bev=.004)
WOOD=M('wood',(.16,.1,.05),.8)
tool(-.3,.55,1.2,ZT+.025,.018,WOOD,((.64,1.2,ZT+.025),(.2,.11,.012)))   # shovel
tool(-.45,.4,1.05,ZT+.025,.02,WOOD,((-.46,1.05,ZT+.03),(.05,.3,.04)))     # pick
tool(-.4,.5,-1.2,ZT+.022,.012,STEELD)                                     # crowbar
# tow cable: a flat coil on the right sponson, eye on top
for k in range(3):
  rr=.17-k*.035;cz=ZT+.025;c=(-.15,-1.12)
  ring=[];segN=24
  for q in range(segN+1):
    a=q/segN*2*math.pi;ring.append(Vector((c[0]+rr*math.cos(a),c[1]+rr*math.sin(a),cz)))
  for a0,a1 in zip(ring,ring[1:]):add('cable',cyl(a0,a1,.016,8),STEELD,bev=0)
add('cableEye',cyl((-.15+.17,-1.12,ZT+.025),(-.15+.25,-1.12,ZT+.03),.03,10),STEELD,bev=0)
LN=Vector((.28,0,-.48)).normalized();LD=Vector((.48,0,.28)).normalized()
for k,y in enumerate((-.33,-.11,.11,.33)):   # spare track links on the lower front plate
  c=Vector((1.42,y,.36))+LD*.33+LN*.02;add('spareLink',xf(box((0,0,0),(.085,.2,.04)),Matrix.Translation(c)@Matrix((LD,Vector((0,1,0)),LN)).transposed().to_4x4()),TRK,bev=.004)
c=Vector((1.42,0,.36))+LD*.33+LN*.045;add('spareBar',cyl(c+Vector((0,-.45,0)),c+Vector((0,.45,0)),.012,8),STEELD,bev=0)
# side skirts: five panels per side, mud-caked, hung on brackets (each panel its own group: can be knocked off when damaged)
for sy in (1,-1):
  for i in range(5):
    x0=-1.62+i*.64;g='skirt%s%d'%('L' if sy>0 else 'R',i)
    add('skirt',hull([(x0+.02,sy*1.43,.52),(x0+.6,sy*1.43,.52),(x0+.02,sy*1.43,.93),(x0+.6,sy*1.43,.93),(x0+.04,sy*1.47,.55),(x0+.58,sy*1.47,.55),(x0+.04,sy*1.47,.92),(x0+.58,sy*1.47,.92)]),PAINT,g,bev=.01)
    for zz in (.6,.86):add('skirtBolt',cyl((x0+.08,sy*1.47,zz),(x0+.08,sy*1.485,zz),.013,8),STEELD,g,bev=0);add('skirtBolt',cyl((x0+.54,sy*1.47,zz),(x0+.54,sy*1.485,zz),.013,8),STEELD,g,bev=0)
    add('skirtHanger',xf(box((0,0,0),(.06,.06,.06)),Matrix.Translation((x0+.31,sy*1.42,.93))),STEELD,g,bev=.004)
  add('skirtRail',xf(box((0,0,0),(3.25,.05,.05)),Matrix.Translation((-.02,sy*1.405,.935))),STEELD,bev=.005)
# ------------------------------------------------------------------ turret
TX,ZR=.0,ZT
tg='turret'
add('ring',cyl((TX,0,ZR-.02),(TX,0,ZR+.06),.6,48),STEELD,tg,bev=.008)
tb=[]
for z,s,fx in ((ZR+.05,1.0,0),(ZR+.42,.93,-.02),(ZR+.56,.78,-.06)):
  tb+=[(TX+.86*s+fx,-.42*s,z),(TX+.86*s+fx,.42*s,z),(TX+.55*s,-.76*s,z),(TX+.55*s,.76*s,z),(TX-.72*s,-.78*s,z),(TX-.72*s,.78*s,z),(TX-1.0*s,-.55*s,z),(TX-1.0*s,.55*s,z)]
add('turretBody',hull(tb),PAINTT,tg,bev=.025)
# faceted add-on cheek armour with bolt rows (sits proud of the turret front)
for sy in (1,-1):
  add('turretCheek',hull([(TX+.88,sy*.38,ZR+.08),(TX+.88,sy*.38,ZR+.45),(TX+.58,sy*.78,ZR+.08),(TX+.6,sy*.74,ZR+.45),(TX+.95,sy*.42,ZR+.12),(TX+.95,sy*.42,ZR+.41),(TX+.65,sy*.8,ZR+.12),(TX+.66,sy*.77,ZR+.41)]),PAINTT,tg,bev=.012)
  for k in range(3):
    t=(k+.5)/3;pt=Vector((TX+.95-.3*t,sy*(.42+.38*t),0));nn=Vector((.38,sy*.3,0)).normalized()
    for zz in (ZR+.17,ZR+.36):pt.z=zz;add('bolt',cyl(pt-nn*.01,pt+nn*.012,.012,8),STEELD,tg,bev=0)
# turret band in the army colour (a painted strip just above the cheeks, all round)
band=[]
for z in (ZR+.47,ZR+.53):
  s=.93-(z-ZR-.42)/.14*.15;band+=[(TX+.87*s,-.425*s,z),(TX+.87*s,.425*s,z),(TX+.555*s,-.765*s,z),(TX+.555*s,.765*s,z),(TX-.725*s,-.785*s,z),(TX-.725*s,.785*s,z),(TX-1.005*s,-.555*s,z),(TX-1.005*s,.555*s,z)]
add('stripe',hull(band),TEAMB,tg,bev=0)
# bustle stowage basket on the turret rear: rails, two bags, an ammo can, a rolled tarp
BX0=TX-1.0;add('basketFloor',xf(box((0,0,0),(.32,1.2,.03)),Matrix.Translation((BX0-.14,0,ZR+.16))),STEELD,tg,bev=.005)
for y in (-.6,-.2,.2,.6):add('basketPost',cyl((BX0-.3,y,ZR+.16),(BX0-.3,y,ZR+.42),.012,8),STEELD,tg,bev=0)
add('basketRail',cyl((BX0-.3,-.62,ZR+.42),(BX0-.3,.62,ZR+.42),.014,8),STEELD,tg,bev=0)
for y in (-.62,.62):add('basketSide',cyl((BX0-.3,y,ZR+.42),(BX0+.02,y,ZR+.42),.014,8),STEELD,tg,bev=0)
add('bag',xf(box((0,0,0),(.26,.42,.24)),Matrix.Translation((BX0-.15,.34,ZR+.29))),CANV,tg,bev=.05,smooth=True,segs=3)
add('bag',xf(box((0,0,0),(.24,.34,.2)),Matrix.Translation((BX0-.15,-.08,ZR+.27))),CANV,tg,bev=.045,smooth=True,segs=3)
add('ammoCan',xf(box((0,0,0),(.26,.13,.18)),Matrix.Translation((BX0-.15,-.42,ZR+.265))),PAINTT,tg,bev=.008)
add('tarp',cyl((BX0-.12,-.55,ZR+.48),(BX0-.12,.55,ZR+.48),.07,16),CANV,tg,bev=0,smooth=True)
for y in (-.3,.3):add('tarpStrap',cyl((BX0-.12,y-.02,ZR+.48),(BX0-.12,y+.02,ZR+.48),.074,16),STRAP,tg,bev=0)
# commander's cupola (closed) with periscope ring, hatch, grab handle
CX,CY=TX-.38,.36
add('cupola',cyl((CX,CY,ZR+.55),(CX,CY,ZR+.7),.24,24,.22),PAINTT,tg,bev=.01)
for k in range(6):a=k*math.pi/3+.3;add('cupScope',xf(box((0,0,0),(.06,.09,.05)),Matrix.Translation((CX+.225*math.cos(a),CY+.225*math.sin(a),ZR+.64))@Matrix.Rotation(a,4,'Z')),STEELD,tg,bev=.004)
add('cupHatch',cyl((CX,CY,ZR+.7),(CX,CY,ZR+.74),.2,24,.18),PAINTT,tg,bev=.006);add('grab',cyl((CX-.08,CY-.08,ZR+.748),(CX+.08,CY+.08,ZR+.748),.012,8),STEELD,tg,bev=0)
# loader hatch, gunner's sight box with glowing optic, sensor mast with sensor head (glowing lens), whip antenna base
add('ldrHatch',cyl((TX-.35,-.38,ZR+.555),(TX-.35,-.38,ZR+.59),.19,20),PAINTT,tg,bev=.006)
add('sightBox',hull([(TX+.42,-.5,ZR+.55),(TX+.72,-.5,ZR+.5),(TX+.42,-.28,ZR+.55),(TX+.72,-.28,ZR+.5),(TX+.42,-.5,ZR+.72),(TX+.64,-.5,ZR+.7),(TX+.42,-.28,ZR+.72),(TX+.64,-.28,ZR+.7)]),PAINTT,tg,bev=.01)
add('sightGlass',xf(box((0,0,0),(.01,.16,.08)),Matrix.Translation((TX+.665,-.39,ZR+.63))@Matrix.Rotation(-.25,4,'Y')),GLOWL,tg,bev=0)
add('mastBase',cyl((TX-.78,.45,ZR+.52),(TX-.78,.45,ZR+.58),.07,14),STEELD,tg,bev=.004)
add('mast',cyl((TX-.78,.45,ZR+.58),(TX-.78,.45,ZR+.98),.025,10),STEELD,tg,bev=0)
add('sensorHead',hull([(TX-.85,.38,ZR+.96),(TX-.68,.38,ZR+.96),(TX-.85,.52,ZR+.96),(TX-.68,.52,ZR+.96),(TX-.85,.4,ZR+1.1),(TX-.7,.4,ZR+1.1),(TX-.85,.5,ZR+1.1),(TX-.7,.5,ZR+1.1),(TX-.64,.45,ZR+1.03)]),PAINTT,tg,bev=.008)
add('sensorLens',cyl((TX-.66,.45,ZR+1.03),(TX-.63,.45,ZR+1.03),.032,14),GLOWL,tg,bev=0)
add('antBase',cyl((TX-.82,-.5,ZR+.5),(TX-.82,-.5,ZR+.6),.035,10),STEELD,tg,bev=.003);add('antenna',cyl((TX-.82,-.5,ZR+.6),(TX-.88,-.5,ZR+1.9),.006,6,.003),STEELD,tg,bev=0)
# smoke dischargers: 4 tubes each side on the turret cheeks (angled out and up)
for sy in (1,-1):
  add('smokeMount',xf(box((0,0,0),(.16,.14,.1)),Matrix.Translation((TX+.5,sy*.78,ZR+.47))),STEELD,tg,bev=.005)
  for k in range(4):
    d=Vector((math.cos(.35*sy*0)+.2,sy*(.55+.08*k),.55)).normalized();o=Vector((TX+.5,sy*(.74+.03*k),ZR+.5+.02*(k%2)))
    add('smokeTube',cyl(o,o+d*.16,.03,12),STEELD,tg,bev=.003);add('smokeCap',cyl(o+d*.15,o+d*.17,.032,12),RUBW,tg,bev=0)
# APS pods (active protection): small armoured launcher boxes on the four turret corners with a sensor window each
for (px,py) in ((TX+.62,.72),(TX+.62,-.72),(TX-.64,.6),(TX-.64,-.6)):
  sy=1 if py>0 else -1
  add('apsPod',hull([(px-.09,py-.07,ZR+.5),(px+.09,py-.07,ZR+.5),(px-.09,py+.07,ZR+.5),(px+.09,py+.07,ZR+.5),(px-.07,py-.06,ZR+.62),(px+.07,py-.06,ZR+.62),(px-.07,py+.06,ZR+.62),(px+.07,py+.06,ZR+.62)]),PAINTT,tg,bev=.008)
  add('apsEye',xf(box((0,0,0),(.06,.004 if True else 0,.03)),Matrix.Translation((px,py+sy*.064,ZR+.57))),GLOWL,tg,bev=0)
# ------------------------------------------------------------------ twin 20 mm autocannons in one mantlet
MX=TX+.88;MZ=ZR+.33
add('mantlet',hull([(MX-.08,-.36,MZ-.17),(MX-.08,.36,MZ-.17),(MX-.08,-.36,MZ+.17),(MX-.08,.36,MZ+.17),(MX+.14,-.3,MZ-.13),(MX+.14,.3,MZ-.13),(MX+.14,-.3,MZ+.13),(MX+.14,.3,MZ+.13)]),PAINTT,tg,bev=.015)
for sy,gn in ((1,'gunL'),(-1,'gunR')):
  y=sy*.14
  add('jacket',cyl((MX+.12,y,MZ),(MX+.48,y,MZ),.06,20),STEELD,gn,bev=.006)
  for k in range(4):add('jacketRib',cyl((MX+.18+k*.08,y,MZ),(MX+.2+k*.08,y,MZ),.066,20),STEELD,gn,bev=0)
  add('barrel',cyl((MX+.48,y,MZ),(MX+1.0,y,MZ),.032,16),STEELD,gn,bev=.003)
  add('brake',cyl((MX+1.0,y,MZ),(MX+1.13,y,MZ),.045,16),STEELD,gn,bev=.004)
  for k in range(3):add('brakeSlot',xf(box((0,0,0),(.022,.1,.018)),Matrix.Translation((MX+1.03+k*.035,y,MZ))),RUBW,gn,bev=0)
  # ammo feed chute: articulated links curling from a box on the turret flank into the side of the mantlet
  A=Vector((TX-.3,sy*.96,ZR+.42));B=Vector((TX+.42,sy*.69,ZR+.36));C1=A+Vector((.2,sy*.04,.13));C2=B+Vector((-.16,sy*.3,.1))
  add('ammoBox',hull([(A.x-.2,sy*.74,ZR+.14),(A.x+.2,sy*.74,ZR+.14),(A.x-.2,sy*1.0,ZR+.16),(A.x+.2,sy*1.0,ZR+.16),(A.x-.2,sy*.74,ZR+.44),(A.x+.2,sy*.74,ZR+.44),(A.x-.2,sy*1.0,ZR+.42),(A.x+.2,sy*1.0,ZR+.42)]),PAINTT,tg,bev=.008)
  add('ammoLid',xf(box((0,0,0),(.42,.28,.02)),Matrix.Translation((A.x,sy*.87,ZR+.44))),STEELD,tg,bev=.004)
  add('feedPort',hull([(B.x-.09,sy*.66,B.z-.06),(B.x+.09,sy*.66,B.z-.06),(B.x-.09,sy*.66,B.z+.06),(B.x+.09,sy*.66,B.z+.06),(B.x-.07,sy*.74,B.z-.05),(B.x+.07,sy*.74,B.z-.05),(B.x-.07,sy*.74,B.z+.05),(B.x+.07,sy*.74,B.z+.05)]),STEELD,tg,bev=.006)
  prev=None;NL=16
  for k in range(NL+1):
    t=k/NL;p=(1-t)**3*A+3*(1-t)**2*t*C1+3*(1-t)*t*t*C2+t**3*B
    if prev is not None:
      d=(p-prev);c=(p+prev)/2;q=Vector((1,0,0)).rotation_difference(d.normalized()).to_matrix().to_4x4()
      add('chute',xf(box((0,0,0),(d.length*1.05,.07,.045)),Matrix.Translation(c)@q),STEELD,tg,bev=.006)
      add('chuteRib',xf(box((0,0,0),(.012,.08,.055)),Matrix.Translation(prev)@q),STEELD,tg,bev=.002)
    prev=p
# tactical markings: army-colour number on both hull sides + a chevron on the turret rear (stencils = bake details)
for sy in (1,-1):text(None,'D-27',Vector((.2,sy*1.4905,.73)),(0,sy,0),.16,TEAMB)
text(None,'K9 ARMOR',Vector((-1.79,-.2,.6)),(-1,0,0),.06,STEN)
TS=float(os.environ.get('TSCALE','.85'))
Ms=Matrix.Translation((TX,0,ZR))@Matrix.Scale(TS,4)@Matrix.Translation((-TX,0,-ZR))
for o in P:
  if o['grp'] in('turret','gunL','gunR'):o.data.transform(Ms)
# ------------------------------------------------------------------ QA: nothing floats (every part touches another), nothing below the ground
from mathutils.bvhtree import BVHTree
dg=bpy.context.evaluated_depsgraph_get();T={}
for o in P:
  me=o.evaluated_get(dg).to_mesh();vs=[o.matrix_world@v.co for v in me.vertices];T[o]=(BVHTree.FromPolygons(vs,[tuple(p.vertices) for p in me.polygons]),min(v.z for v in vs));o.evaluated_get(dg).to_mesh_clear()
iss=[]
grid={}
for o in P:
  if not any(T[o][0].overlap(T[n][0]) for n in P if n is not o and (n['grp']==o['grp'] or o['grp'] in('track',) or n['grp'] in('hull','turret','track'))):iss.append('floating '+o.name)
  if T[o][1]<-.006:iss.append('below ground %s %.3f'%(o.name,T[o][1]))
print('\nLT parts',len(P),'QA',len(iss));[print('   @',x,[round(c,2) for c in (sum((v.co for v in bpy.data.objects[x.split(' ',1)[1]].data.vertices),Vector())/len(bpy.data.objects[x.split(' ',1)[1]].data.vertices))]) for x in iss if x.startswith('floating')];from collections import Counter;[print('  ',k,v) for k,v in Counter(x.split('.')[0] for x in iss).items()]
if os.environ.get('QAONLY'):raise SystemExit
put=None
sc=bpy.context.scene
flo=link('floor',box((0,0,-.01),(12,12,.02)),M('floor',(.09,.095,.08),.95));
shot=scene_setup(int(os.environ.get('SAMP','64')))
shot('/home/claude/veh/lt_34.png',(1,-1.05,.62),(0,0,.95),5.6,(1500,1080))
shot('/home/claude/veh/lt_back.png',(-1,1,.55),(0,0,.95),5.6,(1500,1080))
shot('/home/claude/veh/lt_side.png',(0,-1,.08),(0,0,.95),4.6,(1500,920))
shot('/home/claude/veh/lt_top.png',(.25,-.3,1),(0,0,1.2),4.4,(1200,1200))
shot('/home/claude/veh/lt_turret.png',(1,-.8,.45),(.35,0,1.45),2.2,(1400,960))
bpy.ops.wm.save_as_mainfile(filepath='/home/claude/veh/lt_v1.blend')
