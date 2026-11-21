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
  o=link(name,bm,mat,bev=bev,smooth=smooth,segs=segs);o['grp']=grp;o['rg']=RG[0];P.append(o);return o
RG=[True]   # (v3) running gear is built at its final spacing; the rest is shortened afterwards
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
TY=1.3;TW=.5;WR=.27;WZ=.09+WR   # (v3, Keegan: more nimble) smaller wheels on a shorter run
BOG=[  # (name, road wheel xs, sprocket/idler: (x,z,r,teeth?) at each end, return roller xs)
  ('F',[.8,1.31,1.82],(.4,.46,.2,False),(2.23,.54,.25,False),[1.05,1.57]),
  ('R',[-.8,-1.31,-1.82],(-.4,.46,.2,False),(-2.23,.56,.27,True),[-1.05,-1.57])]
TOPZ=.96;TRACKS_LP=[]   # (bake) each bogie's track centre line -> a low-poly ribbon
for sy in (1,-1):
  for bn,wx,inner,outer,rol in BOG:
    for x in wx:
      for dy in (-.12,.12):
        yc=sy*TY+dy;add('wheel',cyl((x,yc-.07,WZ),(x,yc+.07,WZ),WR-.04,30),WHEELP,'hull',bev=.006);add('tyre',cyl((x,yc-.065,WZ),(x,yc+.065,WZ),WR,30),RUBW,'hull',bev=.01)
      add('hub',cyl((x,sy*(TY+.16),WZ),(x,sy*(TY+.22),WZ),.085,16),WHEELP,'hull',bev=.006)
      for k in range(6):a=k*math.pi/3;add('bolt',cyl((x+.055*math.cos(a),sy*(TY+.21),WZ+.055*math.sin(a)),(x+.055*math.cos(a),sy*(TY+.235),WZ+.055*math.sin(a)),.012,8),STEELD,'hull',bev=0)
      add('arm',xf(box((0,0,0),(.36,.24,.08)),Matrix.Translation((x+.15*(1 if bn=='F' else -1),sy*(TY-.36),WZ+.12))@Matrix.Rotation(-.45*(1 if bn=='F' else -1),4,'Y')),STEELD,'hull',bev=.006)
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
    track_loop(pts,sy,TY,TW,None);TRACKS_LP.append((pts,sy*TY-TW/2,sy*TY+TW/2,((lo[0]+hi[0])/2,.45)))
  # armoured final-drive hub between the bogies (the split)
  add('splitHub',cyl((0,sy*(TY-.3),.52),(0,sy*(TY+.12),.52),.22,8),STEELD,'hull',bev=.012)
  add('splitCap',cyl((0,sy*(TY+.12),.52),(0,sy*(TY+.2),.52),.14,8),PAINT,'hull',bev=.008)
  for k in range(8):a=k*math.pi/4+.2;add('bolt',cyl((.1*math.cos(a),sy*(TY+.19),.52+.1*math.sin(a)),(.1*math.cos(a),sy*(TY+.225),.52+.1*math.sin(a)),.014,8),STEELD,'hull',bev=0)
RG[0]=False
# ------------------------------------------------------------------ hull (T-34 style): lower tub, sloped sponson sides, long glacis
FZ=1.0;ZT=float(os.environ.get('ZT','1.32'));HW=.86;GX=1.72   # (v5, Keegan: squat it down) roof 8 cm lower, glacis top moved back so it stays as steep   # (v2, Keegan: lower, meaner) roof 12 cm lower, glacis top moved back to keep it steep
add('hullLow',prism([(-2.53,.46),(2.04,.46),(2.62,.78),(2.62,FZ),(-2.62,FZ),(-2.62,.72)],-HW,HW),PAINT,bev=.01)
# upper hull: glacis from the nose (x 2.62, z 1.0) up to x 1.25 at roof height (~60 deg), sloped sides out over the tracks,
# rear plate sloping in; the roof is a little narrower than the sponsons (side slope ~40 deg)
YB,YT=1.64,1.08   # sponson width at the fender line, roof edge
up=[(x,sy*y,z) for sy in (1,-1) for x,y,z in ((2.64,YB-.08,FZ),(-2.6,YB,FZ),(GX,YT,ZT),(-2.3,YT,ZT-.04),(2.7,HW*.9,FZ-.02),(-2.72,YB-.12,FZ-.02))]
add('hull',hull(up),PAINT,bev=.012)
GN=Vector((ZT-FZ,0,2.64-GX)).normalized()   # glacis normal
def gp(u,y,o):return Vector((2.64,y,FZ))+(Vector((GX,y,ZT))-Vector((2.64,y,FZ)))*u+GN*o
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
    add('sideBox',hull([tuple(sp(x,sy,u,o)) for x in (x0,x1) for u in (.15,.75) for o in (0,.14)]),PAINT,bev=.01)
    add('sideBoxLid',hull([tuple(sp(x,sy,u,o)) for x in (x0-.01,x1+.01) for u in (.73,.8) for o in (0,.155)]),PAINT,bev=.005)
    for xx in (x0+.15,x1-.15):add('latch',hull([tuple(sp(xx+dx,sy,u,.145)) for dx in (-.03,.03) for u in (.5,.65)]+[tuple(sp(xx+dx,sy,u,.125)) for dx in (-.03,.03) for u in (.52,.63)]),STEELD,bev=.002)
  for k in range(8):x=-1.55+k*.35;pt=sp(x,sy,.86,0);add('bolt',cyl(pt-SN0(sy)*.025,pt+SN0(sy)*.016,.014,8),STEELD,bev=0)
# engine deck: louvres, two exhausts out of the sloped rear plate (T-34 cue), access hatch, rear fuel drums
for sy in (1,-1):
  add('grilleFrame',xf(box((0,0,0),(.75,.62,.035)),Matrix.Translation((-1.75,sy*.5,ZT-.025))),PAINT,bev=.006)
  for k in range(10):add('louvre',xf(box((0,0,0),(.06,.56,.014)),Matrix.Translation((-2.07+k*.07,sy*.5,ZT-.005))@Matrix.Rotation(.6,4,'Y')),STEELD,bev=.002)
add('engHatch',xf(box((0,0,0),(.5,.6,.03)),Matrix.Translation((-.98,0,ZT-.02))),PAINT,bev=.008)
for k in range(6):add('bolt',cyl((-1.18+k*.08,-.27,ZT-.01),(-1.18+k*.08,-.27,ZT+.01),.013,8),STEELD,bev=0)
RN=Vector((-.6,0,.8)).normalized()
for sy in (1,-1):
  pt=Vector((-2.66,sy*.55,1.16));add('exhaust',cyl(pt-RN*.03,pt+Vector((-.18,0,-.04)),.07,16),STEELD,bev=.004);add('exTip',cyl(pt+Vector((-.16,0,-.035)),pt+Vector((-.2,0,-.045)),.065,16),SOOT,bev=0)
  add('exGuard',xf(box((0,0,0),(.06,.26,.2)),Matrix.Translation((-2.75,sy*.55,1.16))),PAINT,bev=.006)
  add('drum',cyl((-2.62,sy*1.15,1.0),(-2.62,sy*1.15,ZT-.02),.17,20),PAINTT,bev=.01)
  for z in (1.08,ZT-.12):add('drumBand',cyl((-2.62,sy*1.15,z),(-2.62,sy*1.15,z+.025),.178,20),STEELD,bev=0)
  add('drumBracket',xf(box((0,0,0),(.1,.36,.04)),Matrix.Translation((-2.55,sy*1.15,1.08))),STEELD,bev=.004)
  add('tailLight',xf(box((0,0,0),(.03,.1,.06)),Matrix.Translation((-2.68,sy*1.3,.95))),RED,bev=.004)
# ------------------------------------------------------------------ skirts with the SPLIT NOTCH over the track break
for sy in (1,-1):
  SN=Vector((0,sy,.12)).normalized();zt,zb=FZ-.03,.62   # (v3) skirts stop above the wheel hubs: more running gear on show
  def kp(x,z,o=0):return Vector((x,sy*(YB+.04+(FZ-z)*.12),z))+SN*o
  for i,(x0,x1) in enumerate(((-2.5,-1.66),(-1.62,-1.0),(-.96,-.56),(.56,.96),(1.0,1.62),(1.66,2.5))):
    g='skirt%s%d'%('L' if sy>0 else 'R',i);inner=(i in (2,3))
    zb2=zb+.08 if inner else zb   # panels beside the split are shorter
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
# ------------------------------------------------------------------ (v4, Keegan) Cold War slab turret: low, wide, flat-sided, a
# wedge of angled cheek armour either side of a recessed flat mantlet, long bustle (autoloader) with an undercut and a rear
# stowage basket. Original design in the modern-MBT family (no copied details). ~15% larger than v3.
TX,ZR=.55,ZT;tg='turret';H=.58;TW2=.95
add('ring',cyl((TX,0,ZR-.02),(TX,0,ZR+.07),.8,48),STEELD,tg,bev=.008)
def T(x,y,z):return (TX+x,y,ZR+z)
# main body + bustle: flat sides leaning in 6 deg, roof dipping slightly toward the front, bustle undercut over the deck
bd=[T(x,sy*y,z) for sy in (1,-1) for x,y,z in ((.62,TW2,.05),(.62,TW2-.06,H-.03),(-.45,TW2,.05),(-.45,TW2-.06,H),(-1.72,TW2-.05,.2),(-1.72,TW2-.11,H-.02),(-1.78,TW2-.15,.3),(-1.78,TW2-.17,H-.06))]
add('turretBody',hull(bd),PAINTT,tg,bev=.012)
# cheeks: a wedge seen from above, from beside the mantlet back to the side corners, face leaning back as it rises
for sy in (1,-1):
  ck=[T(x,sy*y,z) for x,y,z in ((1.06,.33,.05),(1.0,.33,H-.06),(.7,TW2,.05),(.66,TW2-.06,H-.04),(.3,.33,.05),(.3,.33,H-.02),(.3,TW2,.05),(.3,TW2-.06,H))]
  add('cheek',hull(ck),PAINTT,tg,bev=.012)
  # bolted cheek seam + lifting eye
  for k in range(3):
    t=(k+.5)/3;pt=Vector(T(1.03-.34*t,sy*(.33+.62*t),H*.5));nn=Vector((.62,sy*.34,0)).normalized();add('bolt',cyl(pt-nn*.03,pt+nn*.006,.014,8),STEELD,tg,bev=0)
  pt=Vector(T(.5,sy*(TW2-.2),H-.05));add('liftEye',cyl(pt,pt+Vector((0,0,.1)),.035,10),STEELD,tg,bev=.003)
  # 6-tube smoke cluster on the cheek's outer corner, pointing forward and out
  add('smokeMount',hull([T(x,sy*y,z) for x in (.44,.66) for y in (TW2-.06,TW2+.06) for z in (H-.12,H-.02)]),STEELD,tg,bev=.005)
  for k in range(6):
    o=Vector(T(.5+.04*(k%3),sy*(TW2-.03+.04*(k%3)),H-.07+.05*(k//3)));d=Vector((.75,sy*.45,.35)).normalized()
    add('smokeTube',cyl(o,o+d*.2,.03,12),STEELD,tg,bev=.003);add('smokeCap',cyl(o+d*.19,o+d*.21,.032,12),RUBW,tg,bev=0)
  # army-colour band along the flat side, slim stowage boxes on the bustle sides
  sn=Vector((0,sy,.1)).normalized()
  def sd(x,z,o):return Vector(T(x,sy*(TW2-.06*(z-.05)/(H-.08)),z))+sn*o
  add('stripe',hull([tuple(sd(x,z,o)) for x in (-.4,.55) for z in (.36,.43) for o in (-.004,.006)]),TEAMB,tg,bev=0)
  add('bustleBox',hull([tuple(sd(x,z,o)) for x in (-1.6,-.62) for z in (.16,.5) for o in (-.01,.13)]),PAINTT,tg,bev=.01)
  add('bustleBoxLid',hull([tuple(sd(x,z,o)) for x in (-1.61,-.61) for z in (.5,.53) for o in (-.01,.14)]),PAINTT,tg,bev=.004)
  for x in (-1.4,-.82):add('latch',hull([tuple(sd(x+dx,z,o)) for dx in (-.03,.03) for z in (.34,.46) for o in (.12,.145)]),STEELD,tg,bev=.002)
# roof: commander's cupola (right), loader's hatch (left), gunner's sight doghouse (right front), independent sight (left),
# blow-out panels on the bustle, sensor mast + antenna
CX,CY=TX-.2,-.46
add('cupola',cyl((CX,CY,ZR+H-.01),(CX,CY,ZR+H+.13),.26,8,.24),PAINTT,tg,bev=.01)
for k in range(7):a=k*2*math.pi/7;add('visionBlock',xf(box((0,0,0),(.05,.1,.055)),Matrix.Translation((CX+.245*math.cos(a),CY+.245*math.sin(a),ZR+H+.07))@Matrix.Rotation(a,4,'Z')),GLOWL,tg,bev=.003)
add('cupHatch',cyl((CX,CY,ZR+H+.13),(CX,CY,ZR+H+.18),.21,8,.19),PAINTT,tg,bev=.006)
add('cupMG',cyl((CX+.12,CY+.1,ZR+H+.21),(CX+.6,CY+.1,ZR+H+.23),.018,8),STEELD,tg,bev=0);add('cupMGbody',xf(box((0,0,0),(.3,.07,.1)),Matrix.Translation((CX+.1,CY+.1,ZR+H+.21))),STEELD,tg,bev=.004)
add('cupMGpost',cyl((CX+.05,CY+.1,ZR+H+.17),(CX+.05,CY+.1,ZR+H+.21),.025,8),STEELD,tg,bev=0)
add('ldrHatch',xf(box((0,0,0),(.44,.4,.04)),Matrix.Translation((TX-.2,.44,ZR+H+.01))),PAINTT,tg,bev=.008)
add('sightHood',hull([T(x,y,z) for x in (.32,.68) for y in (-.2,-.5) for z in (H-.03,H+.2)]+[T(.74,y,H-.03) for y in (-.2,-.5)]),PAINTT,tg,bev=.01)
add('sightGlass',hull([T(x,y,z) for x,z in ((.68,H+.04),(.68,H+.16),(.7,H+.04),(.7,H+.15)) for y in (-.24,-.46)]),GLOWL,tg,bev=0)
add('indSight',cyl(T(.0,.5,H-.01),T(.0,.5,H+.12),.1,12),PAINTT,tg,bev=.006);add('indHead',hull([T(x,y,z) for x in (-.1,.12) for y in (.4,.6) for z in (H+.12,H+.27)]),PAINTT,tg,bev=.008)
add('indGlass',xf(box((0,0,0),(.012,.14,.08)),Matrix.Translation(T(.125,.5,H+.195))),GLOWL,tg,bev=0)
add('blowPanel',xf(box((0,0,0),(.72,1.2,.025)),Matrix.Translation(T(-1.2,0,H-.015))),PAINTT,tg,bev=.006)
for x in (-1.5,-.9):
  for y in (-.5,0,.5):add('bolt',cyl(T(x,y,H-.005),T(x,y,H+.015),.013,8),STEELD,tg,bev=0)
add('mast',cyl(T(-.8,.62,H-.03),T(-.8,.62,H+.3),.03,10),STEELD,tg,bev=0)
add('sensorHead',hull([T(x,y,z) for x in (-.88,-.7) for y in (.54,.7) for z in (H+.28,H+.42)]),PAINTT,tg,bev=.008);add('sensorLens',cyl(T(-.7,.62,H+.35),T(-.67,.62,H+.35),.035,14),GLOWL,tg,bev=0)
add('antBase',cyl(T(-1.55,-.62,H-.06),T(-1.55,-.62,H),.04,10),STEELD,tg,bev=.003);add('antenna',cyl(T(-1.55,-.62,H),T(-1.61,-.62,H+2.1),.007,6,.003),STEELD,tg,bev=0)
# rear stowage basket hung off the bustle: floor, posts, rails, bags, a rolled tarp
add('basketFloor',xf(box((0,0,0),(.4,1.5,.03)),Matrix.Translation(T(-1.96,0,.3))),STEELD,tg,bev=.005)
for y in (-.74,-.25,.25,.74):add('basketPost',cyl(T(-2.14,y,.3),T(-2.14,y,H+.04),.013,8),STEELD,tg,bev=0)
add('basketRail',cyl(T(-2.14,-.76,H+.04),T(-2.14,.76,H+.04),.015,8),STEELD,tg,bev=0)
for y in (-.76,.76):add('basketSide',cyl(T(-2.14,y,H+.04),T(-1.76,y,H+.04),.015,8),STEELD,tg,bev=0);add('basketSideLo',cyl(T(-2.14,y,.3),T(-1.76,y,.3),.015,8),STEELD,tg,bev=0)
add('bag',xf(box((0,0,0),(.3,.5,.28)),Matrix.Translation(T(-1.95,.38,.46))),CANV,tg,bev=.05,smooth=True,segs=3)
add('bag',xf(box((0,0,0),(.28,.4,.24)),Matrix.Translation(T(-1.95,-.1,.435))),CANV,tg,bev=.045,smooth=True,segs=3)
add('ammoCan',xf(box((0,0,0),(.28,.16,.2)),Matrix.Translation(T(-1.95,-.55,.414))),PAINTT,tg,bev=.008)
add('tarp',cyl(T(-1.95,-.6,.66),T(-1.95,.6,.66),.08,16),CANV,tg,bev=0,smooth=True)
for y in (-.3,.3):add('tarpStrap',cyl(T(-1.95,y-.02,.66),T(-1.95,y+.02,.66),.084,16),STRAP,tg,bev=0)
# ------------------------------------------------------------------ 75 mm gun: flat recessed mantlet, thermal sleeve, fume extractor, brake
MX=TX+.82;MZ=ZR+.3;gn='gun'
add('mantlet',hull([(x,sy*.33,z) for x in (TX+.6,TX+1.0) for sy in (1,-1) for z in (ZR+.1,ZR+.5)]),PAINTT,tg,bev=.01)
add('mantletFace',hull([(x,sy*.26,z) for x in (TX+.99,TX+1.03) for sy in (1,-1) for z in (ZR+.16,ZR+.44)]),PAINTT,tg,bev=.008)
add('coaxPort',cyl((TX+1.02,.18,MZ+.08),(TX+1.07,.18,MZ+.08),.03,10),STEELD,tg,bev=0)
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
TSC=(1,1,1)   # (v4) turret built at its final size, no rescale   # was (.95*.85,.88*.85,.9*.85)   # (v3, Keegan) turret 15% smaller again   # (v2, Keegan) a less meaty turret: slimmer and lower
Mts=Matrix.Translation((TX,0,ZR))@Matrix.Diagonal((*TSC,1))@Matrix.Translation((-TX,0,-ZR));Mgs=Matrix.Translation(((MX-TX)*(TSC[0]-1),0,(MZ-ZR)*(TSC[2]-1)))
for o in P:
  if o['grp']=='turret' and o.name.split('.')[0]!='ring':o.data.transform(Mts)
  elif o['grp']=='turret':pass
  elif o['grp']=='gun':o.data.transform(Mgs)
# (v2, Keegan: more hull detail) tow cable along the left roof edge, tools on the right, spare track on the lower nose, grab
# handles on the sponsons, track jack + tow hooks on the rear
def rz(x):return ZT-.04+.04*min(1,(x+2.3)/(GX+2.3))
yc=YT-.13;pts=[Vector((x,yc,rz(x)+.014)) for x in (-2.2,-1.5,-.8,-.1,.6,1.3)]
for a0,a1 in zip(pts,pts[1:]):add('cable',cyl(a0,a1,.02,8),STEELD,bev=0)
for x in (-1.8,-.45,.95):add('cableClamp',hull([(x+dx,yc+dy,rz(x)+dz) for dx in (-.03,.03) for dy in (-.04,.04) for dz in (-.005,.045)]),STEELD,bev=.003)
for p0,d in ((pts[0],-1),(pts[-1],1)):add('cableEye',cyl(p0,p0+Vector((.12*d,0,0)),.034,10),STEELD,bev=0)
WOOD=M('wood',(.16,.1,.05),.8)
def tool(x0,x1,y,z,r,mat,head=None):
  add('toolHaft',cyl((x0,y,z),(x1,y,z),r,10),mat,bev=0)
  for x in (x0+.14,x1-.14):add('toolClamp',xf(box((0,0,0),(.035,.06,.05)),Matrix.Translation((x,y,z-.01))),STEELD,bev=.003)
  if head:add('toolHead',xf(box((0,0,0),head[1]),Matrix.Translation(head[0])),STEELD,bev=.004)
tool(-2.1,-1.05,-(YT-.1),ZT+.024,.022,WOOD,((-.98,-(YT-.1),ZT+.02),(.24,.13,.014)))   # shovel
tool(-2.1,-1.1,-(YT-.27),ZT+.026,.024,WOOD,((-1.06,-(YT-.27),ZT+.03),(.06,.3,.05)))   # pick
tool(-.2,1.0,-(YT-.12),ZT+.016,.014,STEELD)                                            # crowbar
ND=Vector((.4,0,-.72)).normalized();NT=Vector((.72,0,.4)).normalized()
for y in (-.62,-.31,0,.31,.62):
  c=Vector((1.9,y,.38))+NT*.42+ND*.028;add('spareLink',xf(box((0,0,0),(.12,.28,.05)),Matrix.Translation(c)@Matrix((NT,Vector((0,1,0)),ND)).transposed().to_4x4()),TRK,bev=.004)
c=Vector((1.9,0,.38))+NT*.42+ND*.06;add('spareBar',cyl(c+Vector((0,-.8,0)),c+Vector((0,.8,0)),.014,8),STEELD,bev=0)
for sy in (1,-1):
  sn=SN0(sy)
  for x in (-.95,-.35):
    a0=sp(x-.12,sy,.82,0);a1=sp(x+.12,sy,.82,0)
    add('grabPost',cyl(a0-sn*.01,a0+sn*.07,.014,8),STEELD,bev=0);add('grabPost',cyl(a1-sn*.01,a1+sn*.07,.014,8),STEELD,bev=0);add('grab',cyl(a0+sn*.07,a1+sn*.07,.014,8),STEELD,bev=0)
  add('towHook',xf(box((0,0,0),(.1,.12,.14)),Matrix.Translation((-2.62,sy*.62,.62))),STEELD,bev=.008)
add('trackJack',cyl((-2.7,-.3,.82),(-2.7,.3,.82),.07,14),PAINTT,bev=.006)
for y in (-.22,.22):add('jackStrap',cyl((-2.7,y-.02,.82),(-2.7,y+.02,.82),.075,14),STRAP,bev=0)
# markings: army-colour number on the sponsons, unit stencil on the rear
for sy in (1,-1):text(None,'M-41',sp(-.55,sy,.4,.004),tuple(SN0(sy)),.2,TEAMB)
text(None,'K9 ARMOR',Vector((-2.72,-.2,.86)),(-1,0,0),.08,STEN)
HX=float(os.environ.get('HX','.92'))   # (v3, Keegan: shorter, tighter hull) ~4.9 m; turret keeps its shape, just moves with the hull
for o in P:
  if o['rg']:continue
  o.data.transform(Matrix.Translation((TX*(HX-1),0,0)) if o['grp'] in('turret','gun') else Matrix.Diagonal((HX,1,1,1)))
for o in bpy.data.objects:
  if o.type=='FONT':o.matrix_world=Matrix.Diagonal((HX,1,1,1))@o.matrix_world
# rig points for the game (final Blender coords): turret pivot, muzzle, exhaust, tread-mark points, barrel recoil
RIGV={'pivot':(TX*HX,0,ZR),'muz':[(MX+3.17*GL+TX*(HX-1),0,MZ)],'exhaust':(-2.84*HX,-.55,1.12),'tracks':[(x*HX,sy*TY,0) for sy in (1,-1) for x in (-2.0,2.0)],'recoil':.26,'guns':['gun']}
# ------------------------------------------------------------------ QA:
from mathutils.bvhtree import BVHTree
dg=bpy.context.evaluated_depsgraph_get();T={}
for o in P:
  me=o.evaluated_get(dg).to_mesh();vs=[o.matrix_world@v.co for v in me.vertices];T[o]=(BVHTree.FromPolygons(vs,[tuple(p.vertices) for p in me.polygons]),min(v.z for v in vs));o.evaluated_get(dg).to_mesh_clear()
iss=[]
for o in P:
  if not any(T[o][0].overlap(T[n][0]) for n in P if n is not o and (n['grp']==o['grp'] or o['grp'] in('track',) or n['grp'] in('hull','turret','track'))):iss.append('floating '+o.name)
  if T[o][1]<-.006:iss.append('below ground %s %.3f'%(o.name,T[o][1]))
print('\nMT parts',len(P),'QA',len(iss));[print('  ',x,[round(c,2) for c in bpy.data.objects[x.split(' ')[-1]].data.vertices[0].co]) for x in iss[:40]]
if os.environ.get('QAONLY'):raise SystemExit
flo=link('floor',box((0,0,-.01),(16,16,.02)),M('floor',(.09,.095,.08),.95))
shot=scene_setup(int(os.environ.get('SAMP','48')))
shot('/home/claude/veh/mt_34.png',(1,-1.05,.62),(0,0,1.1),8.2,(1500,1080))
shot('/home/claude/veh/mt_side.png',(0,-1,.08),(0,0,1.1),7.0,(1500,920))
0 and shot('/home/claude/veh/mt_back.png',(-1,1,.55),(0,0,1.1),8.2,(1500,1080))
0 and shot('/home/claude/veh/mt_turret.png',(1,-.9,.5),(.5,0,1.7),3.6,(1400,960))
bpy.ops.wm.save_as_mainfile(filepath='/home/claude/veh/mt_v1.blend')
