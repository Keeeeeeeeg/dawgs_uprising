# MEDIUM TANK v1 concept (Keegan 11-19): the army's all-rounder MBT. Real metres, x forward, y left, z up, ground z 0.
# T-34 style sloped hull (long steep glacis, sloped sponson sides, sloped rear), boxy WELDED turret (Panzer IV flavour, flat
# angled plates) with the 75 mm autoloader in a rear bustle, Cold War touches (thermal-sleeved barrel with a fume extractor,
# laser rangefinder box, rubber-edged skirts). NO Sherman influence. SPLIT TRACKS: two short track units per side (front +
# rear bogie, each its own loop with sprocket/idler), an armoured final-drive hub between them, and a notch carved out of the
# skirts over the split. ~5.3 m hull (light ~3.35 m < medium < heavy ~7.6 m).
import os,sys
exec(open('/home/claude/veh/vlib.py').read())
for o in list(bpy.data.objects):bpy.data.objects.remove(o)
OLIVE=(.072,.08,.056);HK=1.0
PAINT=vpaint('paint',OLIVE,mud=1.6,wear=1.6,dust=1.3,rust=1.0,hk=HK);PAINTT=vpaint('paintT',tuple(c*.92 for c in OLIVE),mud=.7,wear=1.6,dust=1.3,rust=.8,hk=HK)
WHEELP=vpaint('wheelPaint',(.055,.058,.048),mud=2.2,wear=1.0,dust=.3,hk=HK);STEELD=M('gunsteel',(.04,.041,.043),.42,.7);TRK=M('trackSteel',(.05,.047,.043),.6,.6);RUBW=rubber('rubber',(.025,.025,.024))
TEAMB=M('stripeTeam',(.05,.24,.04),.65);STEN=M('stencil',(.75,.73,.62),.7);GLOWL=M('lensGlow',(.35,1,.5),.2,0,6);LAMPG=M('lampGlass',(1,.92,.7),.1,0,3)
CANV=cloth('canvas',(.12,.11,.075),260);STRAP=cloth('strapw',(.06,.06,.045),500);RED=M('redLens',(.6,.05,.03),.3,0,2);SOOT=M('soot',(.012,.011,.01),.95)
P=[]
def add(name,bm,mat,grp='hull',bev=.008,smooth=False,segs=2):
  o=link(name,bm,mat,bev=bev,smooth=smooth,segs=segs);o['grp']=grp;P.append(o);return o
def arc(cx,cz,r,a0,a1,n):return [(cx+r*math.cos(a0+(a1-a0)*t/n),cz+r*math.sin(a0+(a1-a0)*t/n)) for t in range(n+1)]
def track_loop(pts,sy,ty,tw,cen):
  segs=[(Vector((a[0],0,a[1])),Vector((b[0],0,b[1]))) for a,b in zip(pts,pts[1:]+pts[:1])];L=sum((b-a).length for a,b in segs);n=int(L/.1);pitch=L/n
  acc=0;si=0
  for k in range(n):
    s=k*pitch
    while s>acc+(segs[si][1]-segs[si][0]).length:acc+=(segs[si][1]-segs[si][0]).length;si+=1
    a,b=segs[si];t=(s-acc)/(b-a).length;p=a+(b-a)*t;d=(b-a).normalized();ang=math.atan2(-d.z,d.x)
    Mt=Matrix.Translation((p.x,sy*ty,p.z))@Matrix.Rotation(ang,4,'Y')
    add('link',xf(box((0,0,0),(pitch*.92,tw,.05)),Mt),TRK,'track',bev=.004)
    add('grouser',xf(box((0,0,0),(.03,tw*.96,.035)),Mt@Matrix.Translation((0,0,-.04))),TRK,'track',bev=.003)
    if k%2==0:add('guide',xf(box((0,0,0),(.06,.04,.07)),Mt@Matrix.Translation((0,0,.05))),TRK,'track',bev=.003)
# ------------------------------------------------------------------ SPLIT running gear: two bogies per side
TY=1.22;TW=.5;WR=.3;WZ=.09+WR
BOG=[  # (name, road wheel xs, sprocket/idler: (x,z,r,teeth?) at each end, return roller xs)
  ('F',[.86,1.39,1.92],(.4,.48,.2,False),(2.42,.56,.26,False),[1.12,1.66]),
  ('R',[-.86,-1.39,-1.92],(-.4,.48,.2,False),(-2.42,.58,.28,True),[-1.12,-1.66])]
TOPZ=.96
for sy in (1,-1):
  for bn,wx,inner,outer,rol in BOG:
    for x in wx:
      for dy in (-.12,.12):
        yc=sy*TY+dy;add('wheel',cyl((x,yc-.07,WZ),(x,yc+.07,WZ),WR-.04,30),WHEELP,'hull',bev=.006);add('tyre',cyl((x,yc-.065,WZ),(x,yc+.065,WZ),WR,30),RUBW,'hull',bev=.01)
      add('hub',cyl((x,sy*(TY+.16),WZ),(x,sy*(TY+.22),WZ),.085,16),WHEELP,'hull',bev=.006)
      for k in range(6):a=k*math.pi/3;add('bolt',cyl((x+.055*math.cos(a),sy*(TY+.21),WZ+.055*math.sin(a)),(x+.055*math.cos(a),sy*(TY+.235),WZ+.055*math.sin(a)),.012,8),STEELD,'hull',bev=0)
      add('arm',xf(box((0,0,0),(.36,.18,.08)),Matrix.Translation((x+.15*(1 if bn=='F' else -1),sy*(TY-.28),WZ+.12))@Matrix.Rotation(-.45*(1 if bn=='F' else -1),4,'Y')),STEELD,'hull',bev=.006)
    for (ex,ez,er,teeth) in (inner,outer):
      for dy in (-.12,.12):
        add('sprocket' if teeth else 'idler',cyl((ex,sy*TY+dy-.04,ez),(ex,sy*TY+dy+.04,ez),er-(.03 if teeth else 0),24),STEELD,'hull',bev=.005)
        if teeth:
          for k in range(12):a=k*math.pi/6;add('tooth',xf(box((0,0,0),(.08,.07,.055)),Matrix.Translation((ex+(er-.01)*math.cos(a),sy*TY+dy,ez+(er-.01)*math.sin(a)))@Matrix.Rotation(-a,4,'Y')),STEELD,'hull',bev=.004)
      add('sprHub',cyl((ex,sy*(TY-.18),ez),(ex,sy*(TY+.18),ez),.09,16),STEELD,'hull',bev=.006)
    for x in rol:add('roller',cyl((x,sy*(TY-.14),TOPZ-.11),(x,sy*(TY+.14),TOPZ-.11),.075,16),RUBW,'hull',bev=.005)
    # this bogie's own track loop
    lo,hi=(inner,outer) if bn=='F' else (outer,inner)   # lo = rear end, hi = front end
    pts=[(lo[0],.06)]+[(x,.06) for x in sorted(wx)]+[(hi[0]-.1,.07)]+arc(hi[0],hi[1],hi[2]+.035,-1.45,1.57,16)+[(x,TOPZ) for x in sorted(rol,reverse=True)]+arc(lo[0],lo[1],lo[2]+.035,1.57,4.6,16)
    track_loop(pts,sy,TY,TW,None)
  # armoured final-drive hub between the bogies (the split)
  add('splitHub',cyl((0,sy*(TY-.3),.52),(0,sy*(TY+.12),.52),.22,8),STEELD,'hull',bev=.012)
  add('splitCap',cyl((0,sy*(TY+.12),.52),(0,sy*(TY+.2),.52),.14,8),PAINT,'hull',bev=.008)
  for k in range(8):a=k*math.pi/4+.2;add('bolt',cyl((.1*math.cos(a),sy*(TY+.19),.52+.1*math.sin(a)),(.1*math.cos(a),sy*(TY+.225),.52+.1*math.sin(a)),.014,8),STEELD,'hull',bev=0)
# ------------------------------------------------------------------ hull (T-34 style): lower tub, sloped sponson sides, long glacis
FZ=1.0;ZT=1.52;HW=.86
add('hullLow',prism([(-2.5,.38),(1.9,.38),(2.62,.78),(2.62,FZ),(-2.62,FZ),(-2.62,.72)],-HW,HW),PAINT,bev=.01)
# upper hull: glacis from the nose (x 2.62, z 1.0) up to x 1.25 at roof height (~60 deg), sloped sides out over the tracks,
# rear plate sloping in; the roof is a little narrower than the sponsons (side slope ~40 deg)
YB,YT=1.56,1.06   # sponson width at the fender line, roof edge
up=[(x,sy*y,z) for sy in (1,-1) for x,y,z in ((2.64,YB-.08,FZ),(-2.6,YB,FZ),(1.24,YT,ZT),(-2.3,YT,ZT-.04),(2.7,HW*.9,FZ-.02),(-2.72,YB-.12,FZ-.02))]
add('hull',hull(up),PAINT,bev=.012)
GN=Vector((ZT-FZ,0,2.64-1.24)).normalized()   # glacis normal
def gp(u,y,o):return Vector((2.64,y,FZ))+(Vector((1.24,y,ZT))-Vector((2.64,y,FZ)))*u+GN*o
SN0=lambda sy:Vector((0,sy*(ZT-FZ),YB-YT)).normalized()
def sp(x,sy,u,o=0):return Vector((x,sy*(YB+(YT-YB)*u),FZ+(ZT-FZ)*u))+SN0(sy)*o
# driver hatch + visor on the glacis (offset left like a T-34, but a squared Cold War hatch), hull MG ball replaced by a sensor
add('drvHatch',hull([tuple(gp(u,y,o)) for u in (.5,.86) for y in (.18,.66) for o in (-.01,.06)]),PAINT,bev=.008)
add('drvSlit',hull([tuple(gp(u,y,o)) for u in (.66,.72) for y in (.26,.58) for o in (.055,.07)]),GLOWL,bev=0)
for y in (.24,.6):pt=gp(.8,y,.07);add('hinge',cyl(pt-Vector((0,.04,0)),pt+Vector((0,.04,0)),.025,10),STEELD,bev=0)
pt=gp(.62,-.42,0);add('sensorBall',cyl(pt-GN*.02,pt+GN*.1,.11,20),PAINT,bev=.01);add('sensorBallLens',cyl(pt+GN*.1,pt+GN*.115,.05,16),GLOWL,bev=0)
# appliqué armour slabs on the glacis (bolted), a towing bar at the nose
for yy in ((-1.0,-.56),(-.28,.12)):
  add('glacisArmour',hull([tuple(gp(u,y,o)) for u in (.05,.42) for y in yy for o in (-.01,.06)]),PAINT,bev=.006)
  for u in (.12,.35):
    for y in (yy[0]+.06,yy[1]-.06):pt=gp(u,y,.06);add('bolt',cyl(pt-GN*.01,pt+GN*.014,.015,8),STEELD,bev=0)
for sy in (1,-1):
  LN=Vector((.7,0,-.7)).normalized();pt=Vector((2.6,sy*.6,.72));add('towEye',cyl(pt-LN*.05,pt+LN*.09,.075,16),STEELD,bev=.005)
  # fenders over the track tops front and rear, headlights on the glacis corners
  add('fender',hull([(x,sy*y,z) for y in (HW,YB) for x,z in ((-2.66,FZ-.03),(-2.66,FZ),(2.66,FZ-.03),(2.66,FZ))]),PAINT,bev=.006)
  add('fenderFront',hull([(x,sy*y,z) for y in (HW+.1,YB+.02) for x,z in ((2.64,FZ-.03),(2.64,FZ),(2.92,FZ-.2),(2.92,FZ-.17))]),PAINT,bev=.006)
  add('mudFlap',hull([(x,sy*y,z) for y in (HW+.2,YB) for x,z in ((-2.64,FZ-.02),(-2.68,FZ-.02),(-2.64,.72),(-2.68,.72))]),RUBW,bev=.004)
  hp=gp(.2,sy*(YB-.22),.02);add('lampBody',cyl(hp,hp+Vector((.12,0,.03)),.07,16),STEELD,bev=.004);add('lampGlass',cyl(hp+Vector((.11,0,.028)),hp+Vector((.135,0,.034)),.058,16),LAMPG,bev=0)
  # sloped sponson side: bolted plate line, stowage boxes, fuel drums at the rear (T-34 cue, but square Cold War boxes)
  for x0,x1 in ((-1.9,-1.1),(.2,1.0)):
    add('sideBox',hull([tuple(sp(x,sy,u,o)) for x in (x0,x1) for u in (.15,.75) for o in (0,.22)]),PAINT,bev=.01)
    add('sideBoxLid',hull([tuple(sp(x,sy,u,o)) for x in (x0-.01,x1+.01) for u in (.73,.8) for o in (0,.235)]),PAINT,bev=.005)
    for xx in (x0+.15,x1-.15):add('latch',hull([tuple(sp(xx+dx,sy,u,.225)) for dx in (-.03,.03) for u in (.5,.65)]+[tuple(sp(xx+dx,sy,u,.205)) for dx in (-.03,.03) for u in (.52,.63)]),STEELD,bev=.002)
  for k in range(9):x=-1.9+k*.35;pt=sp(x,sy,.88,0);add('bolt',cyl(pt-SN0(sy)*.025,pt+SN0(sy)*.016,.014,8),STEELD,bev=0)
# engine deck: louvres, two exhausts out of the sloped rear plate (T-34 cue), access hatch, rear fuel drums
for sy in (1,-1):
  add('grilleFrame',xf(box((0,0,0),(.75,.62,.035)),Matrix.Translation((-1.75,sy*.5,ZT-.025))),PAINT,bev=.006)
  for k in range(10):add('louvre',xf(box((0,0,0),(.06,.56,.014)),Matrix.Translation((-2.07+k*.07,sy*.5,ZT-.005))@Matrix.Rotation(.6,4,'Y')),STEELD,bev=.002)
add('engHatch',xf(box((0,0,0),(.5,.6,.03)),Matrix.Translation((-.98,0,ZT-.02))),PAINT,bev=.008)
for k in range(6):add('bolt',cyl((-1.18+k*.08,-.27,ZT-.01),(-1.18+k*.08,-.27,ZT+.01),.013,8),STEELD,bev=0)
RN=Vector((-.6,0,.8)).normalized()
for sy in (1,-1):
  pt=Vector((-2.66,sy*.55,1.16));add('exhaust',cyl(pt-RN*.03,pt+Vector((-.18,0,-.04)),.07,16),STEELD,bev=.004);add('exTip',cyl(pt+Vector((-.16,0,-.035)),pt+Vector((-.2,0,-.045)),.065,16),SOOT,bev=0)
  add('exGuard',xf(box((0,0,0),(.06,.26,.2)),Matrix.Translation((-2.75,sy*.55,1.2))),PAINT,bev=.006)
  add('drum',cyl((-2.62,sy*1.15,1.05),(-2.62,sy*1.15,1.5),.17,20),PAINTT,bev=.01)
  for z in (1.15,1.4):add('drumBand',cyl((-2.62,sy*1.15,z),(-2.62,sy*1.15,z+.025),.178,20),STEELD,bev=0)
  add('drumBracket',xf(box((0,0,0),(.1,.36,.04)),Matrix.Translation((-2.55,sy*1.15,1.08))),STEELD,bev=.004)
  add('tailLight',xf(box((0,0,0),(.03,.1,.06)),Matrix.Translation((-2.68,sy*1.3,.95))),RED,bev=.004)
# ------------------------------------------------------------------ skirts with the SPLIT NOTCH over the track break
for sy in (1,-1):
  SN=Vector((0,sy,.12)).normalized();zt,zb=FZ-.03,.48
  def kp(x,z,o=0):return Vector((x,sy*(YB+.04+(FZ-z)*.12),z))+SN*o
  for i,(x0,x1) in enumerate(((-2.5,-1.66),(-1.62,-1.0),(-.96,-.56),(.56,.96),(1.0,1.62),(1.66,2.5))):
    g='skirt%s%d'%('L' if sy>0 else 'R',i);inner=(i in (2,3))
    zb2=zb+.12 if inner else zb   # panels beside the split are shorter
    xa,xb=(x0,x1)
    if i==2:shape=[(xa,zt),(xb,zt),(xa,zb2),(xb-.18,zb2),(xb,zb2+.2)]   # chamfered into the notch
    elif i==3:shape=[(xa,zt),(xb,zt),(xb,zb2),(xa+.18,zb2),(xa,zb2+.2)]
    else:shape=[(xa,zt),(xb,zt),(xa,zb2),(xb,zb2)]
    add('skirt',hull([tuple(kp(x,z,o)) for x,z in shape for o in (-.04,0)]),PAINT,g,bev=.006)
    add('skirtRubber',hull([tuple(kp(x,z,o)) for x,z in ((xa+.02,zb2+.0),(xb-.02,zb2+.0)) for o in (-.03,-.01)]+[tuple(kp(x,zb2-.09,o)) for x in (xa+.02,xb-.02) for o in (-.03,-.01)]) if not inner else hull([tuple(kp(x,z,o)) for x,z in ((xa+.02,zb2),(xa+.02,zb2-.07)) for o in (-.03,-.01)]+[tuple(kp(x,z,o)) for x,z in (((xb-.2 if i==2 else xb-.02),zb2),((xb-.2 if i==2 else xb-.02),zb2-.07)) for o in (-.03,-.01)]),RUBW,g,bev=.003)
    for xx in (xa+.1,xb-.1):
      for zz in (zt-.07,):pt=kp(xx,zz,0);add('skirtBolt',cyl(pt-SN*.005,pt+SN*.02,.015,8),STEELD,g,bev=0)
    pt=kp((xa+xb)/2,zt+.01,-.06);add('skirtHanger',xf(box((0,0,0),(.07,.08,.07)),Matrix.Translation(pt)),STEELD,g,bev=.004)
  # the notch itself: a heavy U-frame over the split hub, hazard stripe
  add('notchFrame',hull([tuple(kp(x,z,o)) for x in (-.6,.6) for z in (zt+.02,zt-.1) for o in (-.1,.01)]),STEELD,bev=.006)
  add('skirtRail',hull([(x,sy*(YB+.04+dy),zt+dz) for x in (-2.56,2.56) for dy in (-.1,-.05) for dz in (-.005,.04)]),STEELD,bev=.005)
# ------------------------------------------------------------------ welded boxy turret (Panzer IV flavour) + autoloader bustle
TX,ZR=.55,ZT;tg='turret'
add('ring',cyl((TX,0,ZR-.02),(TX,0,ZR+.07),.82,48),STEELD,tg,bev=.008)
H=.7
def tbox(pts,name,mat=PAINTT,bev=.012):return add(name,hull(pts),mat,tg,bev=bev)
# body: flat front plate, side plates angled in ~12 deg, flat roof, sides chamfered at the front corners
tb=[]
for z,s in ((ZR+.05,1.0),(ZR+H,.86)):
  tb+=[(TX+1.08*s+.0,-.62*s,z),(TX+1.08*s,.62*s,z),(TX+.8*s,-1.02*s,z),(TX+.8*s,1.02*s,z),(TX-.82,-1.02*s,z),(TX-.82,1.02*s,z)]
tbox(tb,'turretBody',bev=.014)
# rear bustle (autoloader): a long box overhanging the engine deck, lower roof, a blow-out panel on top
bu=[(x,sy*y,z) for sy in (1,-1) for x,y,z in ((TX-.8,.9,ZR+.12),(TX-1.78,.78,ZR+.14),(TX-.8,.84,ZR+H-.04),(TX-1.72,.72,ZR+H-.08),(TX-1.84,.7,ZR+.22))]
tbox(bu,'bustle')
add('blowPanel',xf(box((0,0,0),(.62,.9,.025)),Matrix.Translation((TX-1.3,0,ZR+H-.055))),PAINTT,tg,bev=.006)
for x in (TX-1.56,TX-1.04):
  for y in (-.4,.4):add('bolt',cyl((x,y,ZR+H-.045),(x,y,ZR+H-.025),.013,8),STEELD,tg,bev=0)
add('ammoDoor',hull([(TX+x,sy*y,ZR+z) for sy in (1,-1) for x,y,z in ((-1.80,.5,.3),(-1.73,.5,.55),(-1.835,.46,.32),(-1.765,.46,.53))]),PAINTT,tg,bev=.006)
# spaced armour panels (Schürzen-style, but bolted Cold War slabs) on the turret sides
for sy in (1,-1):
  sn=Vector((0,sy,.14)).normalized()
  def tp(x,z,o):return Vector((x,sy*(1.02-(z-ZR-.05)/(H-.05)*.14),z))+sn*o
  add('turretSkirt',hull([tuple(tp(x,z,o)) for x in (TX-.7,TX+.62) for z in (ZR+.14,ZR+.6) for o in (.05,.09)]),PAINTT,tg,bev=.008)
  for x in (TX-.6,TX,TX+.52):
    add('skirtStrut',hull([tuple(tp(x+dx,z,o)) for dx in (-.03,.03) for z in (ZR+.3,ZR+.36) for o in (0,.06)]),STEELD,tg,bev=.003)
    pt=tp(x,ZR+.5,.092);add('bolt',cyl(pt-sn*.01,pt+sn*.014,.014,8),STEELD,tg,bev=0)
  # army-colour band on the spaced panels
  add('stripe',hull([tuple(tp(x,z,o)) for x in (TX-.68,TX+.6) for z in (ZR+.4,ZR+.47) for o in (.089,.093)]),TEAMB,tg,bev=0)
  # smoke dischargers on the front corners
  for k in range(3):
    o=Vector((TX+.88,sy*(.88+.05*k),ZR+.55+.03*k));d=Vector((.5,sy*.45,.6)).normalized()
    add('smokeTube',cyl(o,o+d*.2,.035,12),STEELD,tg,bev=.003);add('smokeCap',cyl(o+d*.19,o+d*.21,.037,12),RUBW,tg,bev=0)
  add('smokeMount',xf(box((0,0,0),(.18,.16,.08)),Matrix.Translation((TX+.88,sy*.94,ZR+.52))),STEELD,tg,bev=.005)
# commander's cupola (rear right, low with vision blocks), loader hatch, laser rangefinder box + gunner sight, sensor mast, antenna
CX,CY=TX-.35,-.46
add('cupola',cyl((CX,CY,ZR+H-.01),(CX,CY,ZR+H+.14),.27,8,.25),PAINTT,tg,bev=.01)
for k in range(7):a=k*2*math.pi/7;add('visionBlock',xf(box((0,0,0),(.05,.11,.06)),Matrix.Translation((CX+.255*math.cos(a),CY+.255*math.sin(a),ZR+H+.08))@Matrix.Rotation(a,4,'Z')),GLOWL,tg,bev=.003)
add('cupHatch',cyl((CX,CY,ZR+H+.14),(CX,CY,ZR+H+.19),.22,8,.2),PAINTT,tg,bev=.006)
add('cupMG',cyl((CX+.12,CY+.1,ZR+H+.22),(CX+.62,CY+.1,ZR+H+.24),.018,8),STEELD,tg,bev=0);add('cupMGbody',xf(box((0,0,0),(.3,.07,.1)),Matrix.Translation((CX+.1,CY+.1,ZR+H+.22))),STEELD,tg,bev=.004)
add('cupMGpost',cyl((CX+.05,CY+.1,ZR+H+.18),(CX+.05,CY+.1,ZR+H+.22),.025,8),STEELD,tg,bev=0)
add('ldrHatch',xf(box((0,0,0),(.42,.38,.04)),Matrix.Translation((TX-.3,.42,ZR+H+.01))),PAINTT,tg,bev=.008)
add('lrfBox',hull([(x,y,z) for x in (TX+.36,TX+.7) for y in (.36,.62) for z in (ZR+H-.01,ZR+H+.17)]),PAINTT,tg,bev=.01)
add('lrfGlass',xf(box((0,0,0),(.012,.2,.1)),Matrix.Translation((TX+.705,.49,ZR+H+.085))),GLOWL,tg,bev=0)
add('sightHood',hull([(x,y,z) for x in (TX+.4,TX+.66) for y in (-.18,-.02) for z in (ZR+H-.01,ZR+H+.1)]),PAINTT,tg,bev=.008)
add('sightGlass',xf(box((0,0,0),(.012,.12,.06)),Matrix.Translation((TX+.665,-.1,ZR+H+.05))),GLOWL,tg,bev=0)
add('mast',cyl((TX-.95,.5,ZR+H-.04),(TX-.95,.5,ZR+H+.3),.03,10),STEELD,tg,bev=0)
add('sensorHead',hull([(x,y,z) for x in (TX-1.03,TX-.85) for y in (.42,.58) for z in (ZR+H+.28,ZR+H+.42)]),PAINTT,tg,bev=.008);add('sensorLens',cyl((TX-.85,.5,ZR+H+.35),(TX-.82,.5,ZR+H+.35),.035,14),GLOWL,tg,bev=0)
add('antBase',cyl((TX-1.5,-.5,ZR+H-.08),(TX-1.5,-.5,ZR+H),.04,10),STEELD,tg,bev=.003);add('antenna',cyl((TX-1.5,-.5,ZR+H),(TX-1.56,-.5,ZR+H+2.1),.007,6,.003),STEELD,tg,bev=0)
# stowage on the bustle sides: track links, a bedroll
for sy in (1,-1):
  for k in range(3):add('spareLink',xf(box((0,0,0),(.18,.03,.26)),Matrix.Translation((TX-1.0-k*.22,sy*(.9-.12*(.2+k*.22)/.98+.005),ZR+.42))),TRK,tg,bev=.004)
add('tarp',cyl((TX-1.6,-.6,ZR+H-.02),(TX-1.6,.6,ZR+H-.02),.08,16),CANV,tg,bev=0,smooth=True)
for y in (-.3,.3):add('tarpStrap',cyl((TX-1.6,y-.02,ZR+H-.02),(TX-1.6,y+.02,ZR+H-.02),.084,16),STRAP,tg,bev=0)
# ------------------------------------------------------------------ 75 mm gun: boxy mantlet, thermal sleeve, fume extractor, brake
MX=TX+1.08;MZ=ZR+.36;gn='gun'
add('mantlet',hull([(MX-.1,sy*.42,MZ+dz) for sy in (1,-1) for dz in (-.25,.25)]+[(MX+.2,sy*.3,MZ+dz) for sy in (1,-1) for dz in (-.19,.19)]),PAINTT,tg,bev=.018)
add('coaxPort',cyl((MX+.18,.22,MZ+.06),(MX+.24,.22,MZ+.06),.03,10),STEELD,tg,bev=0)
add('collar',cyl((MX+.18,0,MZ),(MX+.4,0,MZ),.13,24,.11),PAINTT,gn,bev=.01)
add('sleeve',cyl((MX+.4,0,MZ),(MX+1.6,0,MZ),.085,24),PAINTT,gn,bev=.006)
for k in range(4):add('sleeveBand',cyl((MX+.6+k*.3,0,MZ),(MX+.63+k*.3,0,MZ),.092,24),STEELD,gn,bev=0)
add('fumeExt',cyl((MX+1.6,0,MZ),(MX+1.95,0,MZ),.115,24),PAINTT,gn,bev=.012)
add('barrel',cyl((MX+1.95,0,MZ),(MX+2.95,0,MZ),.065,20),STEELD,gn,bev=.004)
add('brake',cyl((MX+2.95,0,MZ),(MX+3.17,0,MZ),.085,8),STEELD,gn,bev=.008)
for k in range(2):add('brakePort',xf(box((0,0,0),(.05,.2,.08)),Matrix.Translation((MX+3.02+k*.08,0,MZ))),SOOT,gn,bev=0)
GL=float(os.environ.get('GL','.85'))   # (Keegan) gun 15% shorter
for o in P:
  if o['grp']=='gun':o.data.transform(Matrix.Translation((MX,0,MZ))@Matrix.Diagonal((GL,1,1,1))@Matrix.Translation((-MX,0,-MZ)))
# markings: army-colour number on the sponsons, unit stencil on the rear
for sy in (1,-1):text(None,'M-41',sp(-.45,sy,.42,.004),tuple(SN0(sy)),.2,TEAMB)
text(None,'K9 ARMOR',Vector((-2.72,-.2,.86)),(-1,0,0),.08,STEN)
# ------------------------------------------------------------------ QA
from mathutils.bvhtree import BVHTree
dg=bpy.context.evaluated_depsgraph_get();T={}
for o in P:
  me=o.evaluated_get(dg).to_mesh();vs=[o.matrix_world@v.co for v in me.vertices];T[o]=(BVHTree.FromPolygons(vs,[tuple(p.vertices) for p in me.polygons]),min(v.z for v in vs));o.evaluated_get(dg).to_mesh_clear()
iss=[]
for o in P:
  if not any(T[o][0].overlap(T[n][0]) for n in P if n is not o and (n['grp']==o['grp'] or o['grp'] in('track',) or n['grp'] in('hull','turret','track'))):iss.append('floating '+o.name)
  if T[o][1]<-.006:iss.append('below ground %s %.3f'%(o.name,T[o][1]))
print('\nMT parts',len(P),'QA',len(iss));[print('  ',x) for x in iss[:40]]
if os.environ.get('QAONLY'):raise SystemExit
flo=link('floor',box((0,0,-.01),(16,16,.02)),M('floor',(.09,.095,.08),.95))
shot=scene_setup(int(os.environ.get('SAMP','48')))
shot('/home/claude/veh/mt_34.png',(1,-1.05,.62),(0,0,1.1),8.2,(1500,1080))
shot('/home/claude/veh/mt_side.png',(0,-1,.08),(0,0,1.1),7.0,(1500,920))
0 and shot('/home/claude/veh/mt_back.png',(-1,1,.55),(0,0,1.1),8.2,(1500,1080))
bpy.ops.wm.save_as_mainfile(filepath='/home/claude/veh/mt_v1.blend')
