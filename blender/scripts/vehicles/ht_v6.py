# HEAVY TANK v1 (Keegan 11-19): "low wide brute" with the split-track scheme fully realised: FOUR articulated track pods on
# armoured legs, twin cannons (alternating) in a wide slab turret of the medium's family, dozer/ram plate, reactive armour
# bricks, remote MG station, crew ladders, two-tone camo. Real metres, x forward, y left, z up, ground 0. ~7.9 m hull.
import os,sys
exec(open('/home/claude/veh/vlib.py').read())
for o in list(bpy.data.objects):bpy.data.objects.remove(o)
OLIVE=(.07,.078,.055);DARK=(.016,.018,.013)   # (v2) stronger bands
CAMO=(DARK,float(os.environ.get('CAMOS','.3')))
PAINT=vpaint('paint',OLIVE,mud=1.6,wear=1.5,dust=1.3,rust=1.0,hk=1.15,camo=CAMO);PAINTT=vpaint('paintT',tuple(c*.95 for c in OLIVE),mud=.7,wear=1.5,dust=1.3,rust=.8,hk=1.15,camo=CAMO)
WHEELP=vpaint('wheelPaint',(.05,.053,.044),mud=2.2,wear=1.0,dust=.3,hk=1.15);STEELD=M('gunsteel',(.04,.041,.043),.42,.7);TRK=M('trackSteel',(.05,.047,.043),.6,.6);RUBW=rubber('rubber',(.025,.025,.024))
TEAMB=M('stripeTeam',(.05,.24,.04),.65);STEN=M('stencil',(.75,.73,.62),.7);GLOWL=M('lensGlow',(.35,1,.5),.2,0,6);LAMPG=M('lampGlass',(1,.92,.7),.1,0,3)
ERA=vpaint('era',(.062,.066,.05),mud=1.2,wear=2.0,dust=1.4,rust=.6,hk=1.15,camo=CAMO)
CANV=cloth('canvas',(.12,.11,.075),260);STRAP=cloth('strapw',(.06,.06,.045),500);RED=M('redLens',(.6,.05,.03),.3,0,2);SOOT=M('soot',(.012,.011,.01),.95);WOOD=M('wood',(.16,.1,.05),.8)
P=[]
def add(name,bm,mat,grp='hull',bev=.008,smooth=False,segs=2):
  o=link(name,bm,mat,bev=bev,smooth=smooth,segs=segs);o['grp']=grp;P.append(o);return o
def arc(cx,cz,r,a0,a1,n):return [(cx+r*math.cos(a0+(a1-a0)*t/n),cz+r*math.sin(a0+(a1-a0)*t/n)) for t in range(n+1)]
def bx(c,s,mat,grp='hull',bev=.006,R=None):
  M4=Matrix.Translation(c)@(R or Matrix.Identity(4));return add('box',xf(box((0,0,0),s),M4),mat,grp,bev=bev)
def track_loop(pts,y,tw,grp):
  segs=[(Vector((a[0],0,a[1])),Vector((b[0],0,b[1]))) for a,b in zip(pts,pts[1:]+pts[:1])];L=sum((b-a).length for a,b in segs);n=int(L/.11);pitch=L/n
  acc=0;si=0
  for k in range(n):
    s=k*pitch
    while s>acc+(segs[si][1]-segs[si][0]).length:acc+=(segs[si][1]-segs[si][0]).length;si+=1
    a,b=segs[si];t=(s-acc)/(b-a).length;p=a+(b-a)*t;d=(b-a).normalized();ang=math.atan2(-d.z,d.x)
    Mt=Matrix.Translation((p.x,y,p.z))@Matrix.Rotation(ang,4,'Y')
    add('link',xf(box((0,0,0),(pitch*.92,tw,.055)),Mt),TRK,grp,bev=.004)
    add('grouser',xf(box((0,0,0),(.035,tw*.96,.04)),Mt@Matrix.Translation((0,0,-.045))),TRK,grp,bev=.003)
    if k%2==0:add('guide',xf(box((0,0,0),(.07,.05,.08)),Mt@Matrix.Translation((0,0,.06))),TRK,grp,bev=.003)
# ------------------------------------------------------------------ FOUR TRACK PODS (each its own group: they articulate)
PX,PY,PL,TW=2.02,1.8,3.0,.76;WR=.28;WZ=.09+WR;IR=.32;IZ=.49;TOPZ=.94   # (v3, Keegan) pods ~10% smaller   # (v2, Keegan) bigger pods
PODS=[];TRACKS_LP=[];PZ=.66
for sx,nx in ((1,'F'),(-1,'R')):
  for sy,ny in ((1,'L'),(-1,'R')):
    g='pod'+nx+ny;cx=sx*PX;cy=sy*PY;PODS.append((g,(cx,cy,PZ)))
    ex=[cx-PL/2+IR,cx+PL/2-IR]
    for x in [cx-.86,cx-.29,cx+.29,cx+.86]:
      for dy in (-.15,.15):
        add('wheel',cyl((x,cy+dy-.07,WZ),(x,cy+dy+.07,WZ),WR-.04,28),WHEELP,g,bev=.006);add('tyre',cyl((x,cy+dy-.065,WZ),(x,cy+dy+.065,WZ),WR,28),RUBW,g,bev=.01)
      add('hub',cyl((x,cy+sy*.2,WZ),(x,cy+sy*.25,WZ),.08,16),WHEELP,g,bev=.005)
    for i,x in enumerate(ex):
      teeth=(i==0)==(sx>0)   # drive sprocket at the inner end of each pod
      for dy in (-.15,.15):
        add('sprocket' if teeth else 'idler',cyl((x,cy+dy-.05,IZ),(x,cy+dy+.05,IZ),IR-(.03 if teeth else 0),26),STEELD,g,bev=.005)
        if teeth:
          for k in range(12):a=k*math.pi/6;add('tooth',xf(box((0,0,0),(.085,.08,.06)),Matrix.Translation((x+(IR-.01)*math.cos(a),cy+dy,IZ+(IR-.01)*math.sin(a)))@Matrix.Rotation(-a,4,'Y')),STEELD,g,bev=.004)
      add('axle',cyl((x,cy-.3,IZ),(x,cy+.3,IZ),.09,16),STEELD,g,bev=.005)
    for x in (cx-.58,cx+.58):add('roller',cyl((x,cy-.2,TOPZ-.11),(x,cy+.2,TOPZ-.11),.07,14),RUBW,g,bev=.005)
    # the pod frame (inner beam carrying the axles) and the track loop
    add('podBeam',hull([(x,cy+dy,z) for x in (ex[0],ex[1]) for dy in (-.07,.07) for z in (IZ-.12,TOPZ-.16)]),STEELD,g,bev=.008)
    pts=[(ex[0],.06)]+[(x,.06) for x in (cx-.86,cx-.29,cx+.29,cx+.86)]+[(ex[1]-.1,.08)]+arc(ex[1],IZ,IR+.04,-1.4,1.57,14)+[(cx+.58,TOPZ),(cx-.58,TOPZ)]+arc(ex[0],IZ,IR+.04,1.57,4.68,14)
    track_loop(pts,cy,TW,g);TRACKS_LP.append((pts,cy-TW/2,cy+TW/2,(cx,.45),g))
    # pod armour: top deck, sloped end fairings, outer side plate carrying ERA bricks, inner plate
    zt=TOPZ+.12;yi,yo=cy-sy*(TW/2+.1),cy+sy*(TW/2+.1)
    add('podTop',hull([(x,y,z) for x in (cx-PL/2+.2,cx+PL/2-.2) for y in (yi,yo) for z in (zt,zt+.07)]),PAINT,g,bev=.01)
    for e in (1,-1):add('podFair',hull([(cx+e*(PL/2-.2),y,zt+.07) for y in (yi,yo)]+[(cx+e*(PL/2-.2),y,zt) for y in (yi,yo)]+[(cx+e*(PL/2+.12),y,zt-.32) for y in (yi,yo)]+[(cx+e*(PL/2+.06),y,zt-.36) for y in (yi,yo)]),PAINT,g,bev=.01)
    add('podSide',hull([(x,cy+sy*(TW/2+dy),z) for x in (cx-PL/2+.05,cx+PL/2-.05) for dy in (.06,.12) for z in (.52,zt+.04)]),PAINT,g,bev=.008)
    add('podInner',hull([(x,cy-sy*(TW/2+dy),z) for x in (cx-PL/2+.3,cx+PL/2-.3) for dy in (.06,.11) for z in (.62,zt+.04)]),PAINT,g,bev=.008)
    for i in range(6):
      for j in range(2):
        x=cx-PL/2+.36+i*.455;z=.66+j*.2;add('eraBrick',hull([(x+dx,cy+sy*(TW/2+.12+do),z+dz) for dx in (-.19,.19) for dz in (-.085,.085) for do in (0,.07)]),ERA,g,bev=.006)
    # ladder rungs up the outer side of the front pods (crew access to the deck)
    if sx>0:
      for k in range(3):z=.6+k*.2;add('rung',cyl((cx-1.3,cy+sy*(TW/2+.2),z),(cx-1.0,cy+sy*(TW/2+.2),z),.016,8),STEELD,g,bev=0)
      for x in (cx-1.3,cx-1.0):add('rungPost',cyl((x,cy+sy*(TW/2+.12),.6),(x,cy+sy*(TW/2+.2),.6),.016,8),STEELD,g,bev=0);add('rungRail',cyl((x,cy+sy*(TW/2+.2),.55),(x,cy+sy*(TW/2+.2),1.06),.016,8),STEELD,g,bev=0)
    # pivot: a big armoured cylinder from the pod's inner plate into the leg
    add('podPivot',cyl((cx,cy-sy*(TW/2+.1),PZ),(cx,cy-sy*(TW/2+.5),PZ),.28,20),STEELD,g,bev=.01)
    add('pivotCap',cyl((cx,cy+sy*(TW/2+.12),PZ),(cx,cy+sy*(TW/2+.17),PZ),.17,8),PAINT,g,bev=.006)
# ------------------------------------------------------------------ hull: long, wide and low; long sloped nose
FZ=1.0;ZT=1.74;HW=1.2;YS=1.42;YT=1.18;GX=2.05;NX=3.95
add('hullLow',prism([(-3.6,.5),(3.2,.5),(NX,.85),(NX,FZ),(-3.82,FZ),(-3.82,.78)],-HW,HW),PAINT,bev=.012)
CH=.08   # (v3, Keegan: contour the hull) chamfered roof edge, nose tapering in plan, sponson waist, rear tapering in
up=[(x,sy*y,z) for sy in (1,-1) for x,y,z in ((NX,YS-.32,FZ),(2.7,YS,FZ),(-3.3,YS,FZ),(-3.75,YS-.2,FZ),(GX,YT-.1,ZT-CH),(GX+.15,YT-.28,ZT-.02),(-3.1,YT,ZT-.04-CH),(-3.3,YT-.14,ZT-.04),(NX+.06,HW*.8,FZ-.02),(-3.85,YS-.3,FZ-.02),(-3.6,YT-.12,ZT-.28),(.2,YT,ZT-CH),(.2,YT-.12,ZT))]
add('hull',hull(up),PAINT,bev=.014)
GN=Vector((ZT-FZ,0,NX-GX)).normalized()
def gp(u,y,o):return Vector((NX,y,FZ))+(Vector((GX,y,ZT))-Vector((NX,y,FZ)))*u+GN*o
SN0=lambda sy:Vector((0,sy*(ZT-FZ),YS-YT)).normalized()
def sp(x,sy,u,o=0):return Vector((x,sy*(YS+(YT-YS)*u),FZ+(ZT-FZ)*u))+SN0(sy)*o
# (v3) contour pieces: a raised engine-deck spine, angled armour wedges on the front shoulders, a rear deck step
add('deckSpine',hull([(x,y,z) for x in (-3.2,-.9) for y in (-.62,.62) for z in (ZT-.06,ZT+.08)]+[(x,y,ZT+.13) for x in (-3.1,-1.0) for y in (-.5,.5)]),PAINT,bev=.012)
for sy in (1,-1):
  add('shoulderWedge',hull([(x,sy*y,z) for x,y,z in ((2.55,YS-.05,FZ+.02),(1.2,YS+.04,FZ+.02),(1.2,YT+.05,ZT-CH-.02),(2.0,YT-.04,ZT-CH-.02),(1.25,YS+.1,FZ+.3),(2.4,YS+.02,FZ+.25))]),PAINT,bev=.01)
  add('rearWedge',hull([(x,sy*y,z) for x,y,z in ((-2.6,YS+.03,FZ+.02),(-3.55,YS-.18,FZ+.02),(-2.6,YT+.06,ZT-CH-.06),(-3.3,YT-.04,ZT-CH-.1),(-2.7,YS+.08,FZ+.28))]),PAINT,bev=.01)
# legs: armoured arms from the hull sides out to each pod's pivot
for g,(cx,cy,cz) in PODS:
  sy=1 if cy>0 else -1
  add('leg',hull([(cx+dx,sy*y,z) for dx in (-.42,.42) for y in (.8,cy-sy*(TW/2+.45)) for z in (PZ-.26,PZ+.3)]+[(cx+dx,sy*.8,z) for dx in (-.55,.55) for z in (PZ-.2,PZ+.34)]),PAINT,'hull',bev=.012)
  add('legBand',hull([(cx+dx,sy*y,z) for dx in (-.43,.43) for y in (1.2,1.28) for z in (PZ-.27,PZ+.31)]),STEELD,'hull',bev=.004)
  for k in range(4):add('legBolt',cyl((cx-.3+k*.2,sy*1.24,PZ+.3),(cx-.3+k*.2,sy*1.24,PZ+.33),.016,8),STEELD,'hull',bev=0)
# glacis: driver hatch, visor, reactive armour brick field, headlights, tow eyes
add('drvHatch',hull([tuple(gp(u,y,o)) for u in (.7,.9) for y in (-.62,-.12) for o in (-.01,.06)]),PAINT,bev=.008)
add('drvSlit',hull([tuple(gp(u,y,o)) for u in (.76,.82) for y in (-.56,-.18) for o in (.05,.075)]),GLOWL,bev=0)
for i in range(5):
  for j in range(3):
    y=-.9+i*.45;u=.12+j*.16
    if j==2 and -.7<y<0:continue
    add('eraBrick',hull([tuple(gp(uu,yy,o)) for uu in (u-.07,u+.07) for yy in (y-.22,y+.22) for o in (-.005,.075)]),ERA,bev=.006)
for sy in (1,-1):
  hp=gp(.08,sy*(YS-.45),.02);add('lampBody',cyl(hp,hp+Vector((.14,0,.03)),.08,16),STEELD,bev=.004);add('lampGlass',cyl(hp+Vector((.13,0,.028)),hp+Vector((.16,0,.034)),.066,16),LAMPG,bev=0)
  add('fender',hull([(x,sy*y,z) for y in (HW,YS) for x,z in ((-3.8,FZ-.03),(-3.8,FZ),(NX,FZ-.03),(NX,FZ))]),PAINT,bev=.006)
# engine deck: grilles, exhausts out the rear corners, rear plate jerrycans, tow cable, tools
for sy in (1,-1):
  bx((-2.55,sy*.55,ZT-.03),(1.0,.75,.04),PAINT)
  for k in range(13):add('louvre',xf(box((0,0,0),(.06,.68,.016)),Matrix.Translation((-2.98+k*.07,sy*.55,ZT-.005))@Matrix.Rotation(.6,4,'Y')),STEELD,'hull',bev=.002)
  pt=Vector((-3.7,sy*1.05,1.45));add('exhaust',cyl(pt,pt+Vector((-.25,0,.12)),.09,16),STEELD,bev=.004);add('exTip',cyl(pt+Vector((-.23,0,.11)),pt+Vector((-.27,0,.13)),.085,16),SOOT,bev=0)
  add('exGuard',hull([(x,sy*y,z) for x in (-3.9,-3.6) for y in (.88,1.22) for z in (1.32,1.62)]),PAINT,bev=.008)
  for k in range(3):bx((-3.86,sy*(.25+k*.2),1.15),(.14,.17,.34),PAINTT,bev=.015)
  bx((-3.8,sy*.45,.92),(.05,.7,.05),STEELD)
  add('tailLight',xf(box((0,0,0),(.03,.1,.06)),Matrix.Translation((-3.825,sy*1.0,.92))),RED,'hull',bev=.004)
  # grab rails along the deck edge (crew access from the ladders)
  for x in (1.2,2.1):
    a0=sp(x-.2,sy,.92,0);a1=sp(x+.2,sy,.92,0);sn=SN0(sy)
    add('grabPost',cyl(a0-sn*.01,a0+sn*.07,.015,8),STEELD,bev=0);add('grabPost',cyl(a1-sn*.01,a1+sn*.07,.015,8),STEELD,bev=0);add('grab',cyl(a0+sn*.07,a1+sn*.07,.015,8),STEELD,bev=0)
  # sponson stowage boxes along the sloped sides
  for x0,x1 in ((-3.0,-1.9),(-.4,.6)):
    add('sideBox',hull([tuple(sp(x,sy,u,o)) for x in (x0,x1) for u in (.15,.7) for o in (0,.14)]),PAINT,bev=.01)
    add('sideBoxLid',hull([tuple(sp(x,sy,u,o)) for x in (x0-.01,x1+.01) for u in (.68,.75) for o in (0,.155)]),PAINT,bev=.005)
def rz(x):return ZT-.04+.04*min(1,max(0,(x+3.35)/(GX+3.35)))
yc=YT-.15;pts=[Vector((x,yc,rz(x)+.016)) for x in (-1.6,-.9,-.2,.5,1.2)]
for a0,a1 in zip(pts,pts[1:]):add('cable',cyl(a0,a1,.022,8),STEELD,bev=0)
for x in (-1.3,0.1,1.0):add('cableClamp',hull([(x+dx,yc+dy,rz(x)+dz) for dx in (-.03,.03) for dy in (-.04,.04) for dz in (-.005,.05)]),STEELD,bev=.003)
def tool(x0,x1,y,z,r,mat,head=None):
  add('toolHaft',cyl((x0,y,z),(x1,y,z),r,10),mat,bev=0)
  for x in (x0+.14,x1-.14):add('toolClamp',xf(box((0,0,0),(.035,.06,.05)),Matrix.Translation((x,y,z-.01))),STEELD,'hull',bev=.003)
  if head:add('toolHead',xf(box((0,0,0),head[1]),Matrix.Translation(head[0])),STEELD,'hull',bev=.004)
tool(-1.7,-.6,-(YT-.12),rz(-1.)+.026,.024,WOOD,((-.52,-(YT-.12),rz(-.5)+.02),(.26,.14,.014)))
tool(-1.7,-.65,-(YT-.3),rz(-1.)+.028,.026,WOOD,((-.6,-(YT-.3),rz(-.6)+.03),(.06,.32,.05)))
for k,y in enumerate((-.5,-.25,0,.25,.5)):add('spareLink',xf(box((0,0,0),(.14,.22,.05)),Matrix.Translation(tuple(gp(.47,y*1.6,.03)))@Matrix((Vector((GN.z,0,-GN.x)),Vector((0,1,0)),GN)).to_4x4()),TRK,'hull',bev=.004)
# ------------------------------------------------------------------ slab turret (medium's family, bigger and flatter) + bustle
TX,ZR=-.55,ZT;tg='turret';H=.62;TW2=1.2   # (v4, Keegan) turret no wider than the hull
add('ring',cyl((TX,0,ZR-.02),(TX,0,ZR+.07),1.05,48),STEELD,tg,bev=.008)
def T(x,y,z):return (TX+x,y,ZR+z)
bd=[T(x,sy*y,z) for sy in (1,-1) for x,y,z in ((.75,TW2,.05),(.75,TW2-.07,H-.03),(-.6,TW2,.05),(-.6,TW2-.07,H),(-2.15,TW2-.07,.2),(-2.15,TW2-.13,H-.02),(-2.22,TW2-.18,.3),(-2.22,TW2-.2,H-.06))]
add('turretBody',hull(bd),PAINTT,tg,bev=.014)
for sy in (1,-1):
  ck=[T(x,sy*y,z) for x,y,z in ((1.4,.6,.05),(1.32,.6,H-.06),(.9,TW2,.05),(.85,TW2-.07,H-.04),(.4,.6,.05),(.4,.6,H-.02),(.4,TW2,.05),(.4,TW2-.07,H))]
  add('cheek',hull(ck),PAINTT,tg,bev=.014)
  # reactive armour bricks on the cheek face
  for k in range(3):
    for j in range(2):
      t=(k+.5)/3;p0=Vector(T(1.4-.5*t,sy*(.6+(TW2-.6)*t),.17+j*.24));nn=Vector((TW2-.6,sy*.5,0)).normalized();tt=Vector((-.5,sy*(TW2-.6),0)).normalized()
      add('eraBrick',hull([tuple(p0+tt*a+Vector((0,0,b))+nn*c) for a in (-.14,.14) for b in (-.1,.1) for c in (-.06,.05)]),ERA,tg,bev=.006)
  add('smokeMount',hull([T(x,sy*y,z) for x in (.5,.78) for y in (TW2-.08,TW2+.06) for z in (H-.14,H-.02)]),STEELD,tg,bev=.005)
  for k in range(8):
    o=Vector(T(.55+.05*(k%4),sy*(TW2-.04+.03*(k%4)),H-.09+.055*(k//4)));d=Vector((.75,sy*.45,.35)).normalized()
    add('smokeTube',cyl(o,o+d*.22,.032,12),STEELD,tg,bev=.003);add('smokeCap',cyl(o+d*.21,o+d*.23,.034,12),RUBW,tg,bev=0)
  sn=Vector((0,sy,.1)).normalized()
  def sd(x,z,o):return Vector(T(x,sy*(TW2-.07*(z-.05)/(H-.08)),z))+sn*o
  add('stripe',hull([tuple(sd(x,z,o)) for x in (-.5,.7) for z in (.38,.46) for o in (-.004,.006)]),TEAMB,tg,bev=0)
  add('bustleBox',hull([tuple(sd(x,z,o)) for x in (-2.0,-.75) for z in (.16,.5) for o in (-.01,.14)]),PAINTT,tg,bev=.01)
  add('bustleBoxLid',hull([tuple(sd(x,z,o)) for x in (-2.01,-.74) for z in (.5,.53) for o in (-.01,.15)]),PAINTT,tg,bev=.004)
CX,CY=TX-.3,-.55
add('cupola',cyl((CX,CY,ZR+H-.01),(CX,CY,ZR+H+.14),.3,8,.28),PAINTT,tg,bev=.01)
for k in range(8):a=k*2*math.pi/8;add('visionBlock',xf(box((0,0,0),(.05,.11,.06)),Matrix.Translation((CX+.285*math.cos(a),CY+.285*math.sin(a),ZR+H+.075))@Matrix.Rotation(a,4,'Z')),GLOWL,tg,bev=.003)
add('cupHatch',cyl((CX,CY,ZR+H+.14),(CX,CY,ZR+H+.19),.25,8,.23),PAINTT,tg,bev=.006)
add('ldrHatch',xf(box((0,0,0),(.46,.4,.04)),Matrix.Translation((TX-.3,.58,ZR+H+.01))),PAINTT,tg,bev=.008)
add('sightHood',hull([T(x,y,z) for x in (.4,.8) for y in (-.25,-.6) for z in (H-.03,H+.22)]+[T(.86,y,H-.03) for y in (-.25,-.6)]),PAINTT,tg,bev=.01)
add('sightGlass',hull([T(x,y,z) for x,z in ((.8,H+.05),(.8,H+.18),(.82,H+.05),(.82,H+.17)) for y in (-.29,-.56)]),GLOWL,tg,bev=0)
add('blowPanel',xf(box((0,0,0),(.9,1.6,.025)),Matrix.Translation(T(-1.5,0,H-.015))),PAINTT,tg,bev=.006)
add('mast',cyl(T(-1.1,.82,H-.03),T(-1.1,.82,H+.32),.03,10),STEELD,tg,bev=0)
add('sensorHead',hull([T(x,y,z) for x in (-1.19,-1.0) for y in (.74,.9) for z in (H+.3,H+.45)]),PAINTT,tg,bev=.008);add('sensorLens',cyl(T(-1.0,.82,H+.37),T(-.97,.82,H+.37),.035,14),GLOWL,tg,bev=0)
add('antBase',cyl(T(-1.95,-.85,H-.06),T(-1.95,-.85,H),.04,10),STEELD,tg,bev=.003);add('antenna',cyl(T(-1.95,-.85,H),T(-2.01,-.85,H+2.3),.007,6,.003),STEELD,tg,bev=0)
# (v4b, Keegan: a spaceship-style NODE turret) low armoured collar, a faceted armoured ball (icosphere-like hull) with a glowing
# sensor eye band, twin slim barrels out of a slot, cooling fins on the back, small vents. Original design. Same rig point
# (rws = muzzle) for the game.
RW=T(.1,.6,H)
add('rwsRing',cyl(RW,(RW[0],RW[1],RW[2]+.07),.24,12,.2),STEELD,tg,bev=.006)
NC=Vector((RW[0],RW[1],RW[2]+.27));NR=.22
pts=[]
for a in range(10):
  for b in range(-2,4):
    th=a*2*math.pi/10+(.31 if b%2 else 0);ph=b*math.pi/8
    pts.append(tuple(NC+Vector((math.cos(th)*math.cos(ph)*NR*1.08,math.sin(th)*math.cos(ph)*NR,math.sin(ph)*NR*.9))))
pts.append(tuple(NC+Vector((0,0,NR*.95))))
add('nodeBall',hull(pts),PAINTT,tg,bev=.006)
add('nodeNeck',cyl((NC.x,NC.y,RW[2]+.05),(NC.x,NC.y,NC.z-.1),.13,10),STEELD,tg,bev=.004)
add('nodeBand',hull([tuple(NC+Vector((x,y,z))) for x in (.06,.25) for y in (-.13,.13) for z in (.03,.075)]),STEELD,tg,bev=.003)
add('nodeEye',hull([tuple(NC+Vector((x,y,z))) for x in (.2,.245) for y in (-.11,.11) for z in (.04,.065)]),GLOWL,tg,bev=0)
add('nodeSlot',hull([tuple(NC+Vector((x,y,z))) for x in (.12,.26) for y in (-.09,.09) for z in (-.09,-.02)]),STEELD,tg,bev=.004)
for dy in (-.045,.045):
  add('nodeBarrel',cyl(NC+Vector((.2,dy,-.055)),NC+Vector((.72,dy,-.055)),.019,10),STEELD,tg,bev=0)
  add('nodeMuz',cyl(NC+Vector((.68,dy,-.055)),NC+Vector((.74,dy,-.055)),.026,8),STEELD,tg,bev=0)
for k in range(5):add('nodeFin',hull([tuple(NC+Vector((x,-.14+k*.07+dy,z))) for x in (-.3,-.17) for dy in (-.008,.008) for z in (-.08,.1)]),STEELD,tg,bev=.002)
for sy_ in (1,-1):add('nodeVent',hull([tuple(NC+Vector((x,sy_*.215,z))) for x in (-.06,.06) for z in (-.04,.04)]+[tuple(NC+Vector((x,sy_*.19,z))) for x in (-.06,.06) for z in (-.04,.04)]),SOOT,tg,bev=0)
# rear basket
add('basketFloor',xf(box((0,0,0),(.42,1.8,.03)),Matrix.Translation(T(-2.4,0,.3))),STEELD,tg,bev=.005)
for y in (-.88,-.3,.3,.88):add('basketPost',cyl(T(-2.6,y,.3),T(-2.6,y,H+.04),.014,8),STEELD,tg,bev=0)
add('basketRail',cyl(T(-2.6,-.9,H+.04),T(-2.6,.9,H+.04),.016,8),STEELD,tg,bev=0)
for y in (-.9,.9):add('basketSide',cyl(T(-2.6,y,H+.04),T(-2.2,y,H+.04),.016,8),STEELD,tg,bev=0);add('basketSideLo',cyl(T(-2.6,y,.3),T(-2.2,y,.3),.016,8),STEELD,tg,bev=0)
add('bag',xf(box((0,0,0),(.32,.55,.3)),Matrix.Translation(T(-2.4,.48,.465))),CANV,tg,bev=.05,smooth=True,segs=3)
add('bag',xf(box((0,0,0),(.3,.45,.26)),Matrix.Translation(T(-2.4,.0,.445))),CANV,tg,bev=.045,smooth=True,segs=3)
add('ammoCan',xf(box((0,0,0),(.3,.18,.22)),Matrix.Translation(T(-2.4,-.52,.425))),PAINTT,tg,bev=.008)
add('tarp',cyl(T(-2.4,-.8,.68),T(-2.4,.8,.68),.085,16),CANV,tg,bev=0,smooth=True)
# ------------------------------------------------------------------ twin cannons: wide recessed mantlet, two sleeved barrels
MX=TX+1.35;MZ=ZR+.3
add('mantlet',hull([(x,sy*.62,z) for x in (TX+.75,TX+1.3) for sy in (1,-1) for z in (ZR+.08,ZR+.52)]),PAINTT,tg,bev=.012)
add('mantletFace',hull([(x,sy*.56,z) for x in (TX+1.29,TX+1.34) for sy in (1,-1) for z in (ZR+.13,ZR+.47)]),PAINTT,tg,bev=.008)
GS=.34
for sy,gn in ((1,'gunL'),(-1,'gunR')):
  y=sy*GS
  add('collar',cyl((MX-.02,y,MZ),(MX+.25,y,MZ),.15,24,.13),PAINTT,gn,bev=.01)
  add('sleeve',cyl((MX+.25,y,MZ),(MX+1.6,y,MZ),.1,24),PAINTT,gn,bev=.006)
  for k in range(4):add('sleeveBand',cyl((MX+.45+k*.3,y,MZ),(MX+.48+k*.3,y,MZ),.107,24),STEELD,gn,bev=0)
  add('fumeExt',cyl((MX+1.6,y,MZ),(MX+1.95,y,MZ),.13,24),PAINTT,gn,bev=.012)
  add('barrel',cyl((MX+1.95,y,MZ),(MX+3.5,y,MZ),.075,20),STEELD,gn,bev=.004)
  add('brake',cyl((MX+3.5,y,MZ),(MX+3.78,y,MZ),.11,8),STEELD,gn,bev=.008)
  for k in range(2):add('brakePort',xf(box((0,0,0),(.06,.24,.1)),Matrix.Translation((MX+3.58+k*.1,y,MZ))),SOOT,gn,bev=0)
# (v3, Keegan) X crossbrace between the cannons near mid-length: a clamp collar on each barrel, two diagonal bars crossing
# at the centre with a boss. It ties the barrels, so in game they recoil together (rig linkRecoil)
XB0,XB1=MX+.8,MX+1.35   # (v4, Keegan) on the green sleeves
for sy in (1,-1):
  for x in (XB0,XB1):add('braceCollar',cyl((x-.05,sy*GS,MZ),(x+.05,sy*GS,MZ),.12,16),STEELD,'gunL',bev=.004)
for a0,a1 in (((XB0,GS),(XB1,-GS)),((XB0,-GS),(XB1,GS))):
  p0=Vector((a0[0],a0[1]*.78,MZ));p1=Vector((a1[0],a1[1]*.78,MZ));add('braceBar',cyl(p0,p1,.032,10),STEELD,'gunL',bev=.003)
add('braceBoss',cyl(((XB0+XB1)/2,0,MZ-.05),((XB0+XB1)/2,0,MZ+.05),.06,12),STEELD,'gunL',bev=.004)
for sy in (1,-1):text(None,'H-07',sp(-1.2,sy,.4,.004),tuple(SN0(sy)),.24,TEAMB)
text(None,'K9 ARMOR',Vector((-3.84,-.3,.86)),(-1,0,0),.09,STEN)
# (v2, Keegan: more hull decor) deck hatches + periscopes, an armoured intake box with grille, spare road wheels on the rear
# deck, bolted armour strip and lower ERA row along the sponsons, jerrycan racks, extinguisher handles, tow hooks, antenna mount
for y in (.5,-.5):
  add('deckHatch',cyl((1.35,y,ZT-.02),(1.35,y,ZT+.04),.24,20),PAINT,bev=.008);add('hatchHinge',cyl((1.12,y-.12,ZT+.04),(1.12,y+.12,ZT+.04),.025,8),STEELD,bev=0)
  for k in range(3):a_=k*2.1-2.1;add('periscope',hull([(1.35+.3*math.cos(a_)+dx,y+.3*math.sin(a_)+dy,z) for dx in (-.05,.05) for dy in (-.04,.04) for z in (ZT-.02,ZT+.07)]),STEELD,bev=.004)
add('intake',hull([(x,y,z) for x in (-1.75,-1.05) for y in (-.8,.8) for z in (ZT-.03,ZT+.16)]),PAINT,bev=.012)
for k in range(8):add('intakeBar',xf(box((0,0,0),(.03,1.5,.02)),Matrix.Translation((-1.7+k*.085,0,ZT+.165))),STEELD,'hull',bev=0)
for y in (-.55,.55):
  add('spareWheel',cyl((-3.25,y,ZT-.03),(-3.25,y,ZT+.12),.3,24),WHEELP,bev=.008);add('spareHub',cyl((-3.25,y,ZT+.12),(-3.25,y,ZT+.16),.1,12),STEELD,bev=.004)
  add('wheelClamp',xf(box((0,0,0),(.06,.5,.04)),Matrix.Translation((-3.25,y,ZT+.17))),STEELD,'hull',bev=.004)
for sy in (1,-1):
  sn=SN0(sy)
  add('armourStrip',hull([tuple(sp(x,sy,u,o)) for x in (-3.4,2.9) for u in (.8,.9) for o in (-.01,.05)]),PAINT,bev=.006)
  for k in range(13):x=-3.2+k*.5;pt=sp(x,sy,.85,.05);add('bolt',cyl(pt-sn*.01,pt+sn*.018,.016,8),STEELD,bev=0)
  for i in range(11):
    x=-3.3+i*.6
    if x>-.5 or -3.1<x<-1.8:continue
    add('eraBrick',hull([tuple(sp(xx,sy,u,o)) for xx in (x-.25,x+.25) for u in (.1,.32) for o in (-.03,.07)]),ERA,bev=.006)
  add('jerryRack',hull([tuple(sp(x,sy,u,o)) for x in (.95,1.75) for u in (.12,.16) for o in (0,.2)]),STEELD,bev=.004)
  for k in range(3):x=1.05+k*.26;add('jerry',hull([tuple(sp(xx,sy,u,o)) for xx in (x,x+.2) for u in (.14,.62) for o in (.02,.17)]),PAINTT,bev=.015)
  for x in (-.7,-.2):pt=sp(x,sy,.55,0);add('extHandle',cyl(pt-sn*.05,pt+sn*.05,.02,8),RED,bev=0)
  pt=Vector((3.6,sy*.75,.68));LN=Vector((.7,0,-.7)).normalized();add('towEye',cyl(pt-LN*.06,pt+LN*.1,.085,16),STEELD,bev=.005)
add('antMount',cyl((-2.9,-.8,ZT-.04),(-2.9,-.8,ZT+.06),.05,10),STEELD,bev=.003);add('hullAntenna',cyl((-2.9,-.8,ZT+.06),(-2.95,-.8,ZT+1.6),.006,6,.003),STEELD,bev=0)
# (v2, Keegan: smaller, thinner hull; bigger pods) scale the hull (not the legs or pods) and carry the turret + guns with it
HSX,HSY,HSZ=float(os.environ.get('HSX','.88')),float(os.environ.get('HSY','.8')),float(os.environ.get('HSZ','.95'))
HM=Matrix.Diagonal((HSX,HSY,HSZ,1));TSc=float(os.environ.get('TSC','.88'))
TM=Matrix.Translation((TX*HSX,0,ZR*HSZ))@Matrix.Scale(TSc,4)@Matrix.Translation((-TX,0,-ZR))
for o in P:
  nm=o.name.split('.')[0]
  if o['grp']=='hull' and nm not in('leg','legBand','legBolt'):o.data.transform(HM)
  elif o['grp'] in('turret','gunL','gunR'):o.data.transform(TM)
for o in bpy.data.objects:
  if o.type=='FONT':o.matrix_world=HM@o.matrix_world
# (v6, Keegan) the shelf over the pods is removed again; the pods sit closer together with a gap between them
RIGV={'pivot':tuple(TM@Vector((TX,0,ZR))),'muz':[tuple(TM@Vector((MX+3.78,sy*GS,MZ))) for sy in (1,-1)],'exhaust':tuple(HM@Vector((-3.97,-1.05,1.57))),'tracks':[(sx*PX,sy*PY,0) for sy in (1,-1) for sx in (-1,1)],'recoil':.29,'guns':['gunL','gunR'],'linkRecoil':1,'podMax':.26,
  'pods':[[g,list(c)] for g,c in PODS],'rws':tuple(TM@(NC+Vector((.74,0,-.055))))}
# ------------------------------------------------------------------ QA:
from mathutils.bvhtree import BVHTree
dg=bpy.context.evaluated_depsgraph_get();T_={}
for o in P:
  me=o.evaluated_get(dg).to_mesh();vs=[o.matrix_world@v.co for v in me.vertices];T_[o]=(BVHTree.FromPolygons(vs,[tuple(p.vertices) for p in me.polygons]),min(v.z for v in vs));o.evaluated_get(dg).to_mesh_clear()
iss=[]
for o in P:
  if not any(T_[o][0].overlap(T_[n][0]) for n in P if n is not o and (n['grp']==o['grp'] or n['grp'] in('hull','turret'))):iss.append('floating '+o.name)
  if T_[o][1]<-.006:iss.append('below ground %s %.3f'%(o.name,T_[o][1]))
# each pod must touch the hull only through its pivot (articulation): any other pod part touching a hull part is reported
for g,_ in PODS:
  for o in P:
    if o['grp']!=g or o.name.startswith('podPivot'):continue
    if any(T_[o][0].overlap(T_[n][0]) for n in P if n['grp']=='hull'):iss.append('pod clash '+o.name)
print('\nHT parts',len(P),'QA',len(iss));[print('  ',x,[round(c,2) for c in bpy.data.objects[x.split(' ')[-1]].data.vertices[0].co]) for x in iss[:40]]
if os.environ.get('QAONLY'):raise SystemExit
flo=link('floor',box((0,0,-.01),(22,22,.02)),M('floor',(.09,.095,.08),.95))
shot=scene_setup(int(os.environ.get('SAMP','32')))
shot('/home/claude/veh/ht_34.png',(1,-1.05,.6),(0,0,1.2),11.0,(1500,1080))
shot('/home/claude/veh/ht_side.png',(0,-1,.07),(0,0,1.1),10.4,(1500,820))
shot('/home/claude/veh/ht_back.png',(-1,1,.55),(0,0,1.1),11.0,(1500,1080))
shot('/home/claude/veh/ht_guns.png',(.7,-1,.6),(0,0,1.9),4.6,(1400,900))
bpy.ops.wm.save_as_mainfile(filepath='/home/claude/veh/ht_v1.blend')
