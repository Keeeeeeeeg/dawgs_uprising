# Phase C, LIGHT TANK v1 ("bulldog brawler" + near-future): real metres, x forward, y left, z up, ground z 0, turret ring at
# (TX,0,ZR). Keegan's brief: tracks, twin 20 mm autocannons side by side in one mantlet with ammo chutes curling into the turret
# sides, ~3.6 m, faceted add-on armour with bolt rows, sensor mast + optics, segmented track skirts, APS pods, smoke launchers,
# stowage + tools, engine deck grilles/vents/exhaust, caged headlights, army-colour turret band + small tac markings.
import os,sys
exec(open('/home/claude/veh/vlib.py').read())
for o in list(bpy.data.objects):bpy.data.objects.remove(o)
OLIVE=(.075,.082,.058)
HK=.86   # (v3g) mud line for the smaller tank
PAINT=vpaint('paint',OLIVE,mud=1.7,wear=1.8,dust=1.3,rust=1.0,hk=HK);PAINTT=vpaint('paintT',tuple(c*.92 for c in OLIVE),mud=.8,wear=1.8,dust=1.3,rust=.8,hk=HK)
WHEELP=vpaint('wheelPaint',(.055,.058,.048),mud=2.2,wear=1.0,dust=.3,hk=HK);STEELD=M('gunsteel',(.04,.041,.043),.42,.7);TRK=M('trackSteel',(.05,.047,.043),.6,.6);RUBW=rubber('rubber',(.025,.025,.024))
TEAMB=M('stripeTeam',(.05,.24,.04),.65);STEN=M('stencil',(.75,.73,.62),.7);GLOWL=M('lensGlow',(.35,1,.5),.2,0,6);LAMPG=M('lampGlass',(1,.92,.7),.1,0,3)
CANV=cloth('canvas',(.12,.11,.075),260);STRAP=cloth('strapw',(.06,.06,.045),500);BRASS=M('brassL',(.45,.32,.12),.35,.9);RED=M('redLens',(.6,.05,.03),.3,0,2)
P=[]   # every part: (object, group) ; groups: hull, turret, gunL, gunR, skirtL0.. (detachable), track
def add(name,bm,mat,grp='hull',bev=.008,smooth=False,segs=2):
  o=link(name,bm,mat,bev=bev,smooth=smooth,segs=segs);o['grp']=grp;P.append(o);return o
# ------------------------------------------------------------------ running gear
TY=1.25;TW=.42;WX=[-1.16,-.58,0,.58,1.16];WR=.275;WZ=.08+WR;SPX,SPZ,SPR=-1.6,.56,.25;IDX,IDZ,IDR=1.56,.5,.22   # (v3b) wider stance, bigger wheels
for sy in (1,-1):
  g='hull'
  for i,x in enumerate(WX):   # double road wheels: steel disc + rubber tyre + hub + bolts
    for dy in (-.1,.1):
      yc=sy*TY+dy
      add('wheel',cyl((x,yc-.065,WZ),(x,yc+.065,WZ),WR-.035,28),WHEELP,g,bev=.006)
      add('tyre',cyl((x,yc-.06,WZ),(x,yc+.06,WZ),WR,28),RUBW,g,bev=.01)
    add('hub',cyl((x,sy*(TY+.14),WZ),(x,sy*(TY+.2),WZ),.075,16),WHEELP,g,bev=.006)
    for k in range(6):a=k*math.pi/3;add('bolt',cyl((x+.05*math.cos(a),sy*(TY+.19),WZ+.05*math.sin(a)),(x+.05*math.cos(a),sy*(TY+.215),WZ+.05*math.sin(a)),.011,8),STEELD,g,bev=0)
    add('arm',xf(box((0,0,0),(.32,.16,.07)),Matrix.Translation((x+.13,sy*(TY-.25),WZ+.1))@Matrix.Rotation(-.45,4,'Y')),STEELD,g,bev=.006)   # suspension arm to the hull
  # drive sprocket (rear) with teeth, idler (front)
  for dy in (-.1,.1):
    add('sprocket',cyl((SPX,sy*TY+dy-.03,SPZ),(SPX,sy*TY+dy+.03,SPZ),SPR-.03,24),STEELD,g,bev=.004)
    for k in range(12):a=k*math.pi/6;add('tooth',xf(box((0,0,0),(.07,.06,.05)),Matrix.Translation((SPX+(SPR-.01)*math.cos(a),sy*TY+dy,SPZ+(SPR-.01)*math.sin(a)))@Matrix.Rotation(-a,4,'Y')),STEELD,g,bev=.004)
    add('idler',cyl((IDX,sy*TY+dy-.05,IDZ),(IDX,sy*TY+dy+.05,IDZ),IDR,24),STEELD,g,bev=.006)
  add('sprHub',cyl((SPX,sy*(TY-.15),SPZ),(SPX,sy*(TY+.17),SPZ),.09,16),STEELD,g,bev=.006);add('idHub',cyl((IDX,sy*(TY-.15),IDZ),(IDX,sy*(TY+.16),IDZ),.07,16),STEELD,g,bev=.006)
  for x in (-.87,.29):add('roller',cyl((x,sy*(TY-.12),.74),(x,sy*(TY+.12),.74),.07,16),RUBW,g,bev=.005)
  # TRACK: links along the loop (bottom run, front idler arc, top run over the return rollers, sprocket arc), grouser bars
  path=[];N0=60
  def arc(cx,cz,r,a0,a1,n):return [(cx+r*math.cos(a0+(a1-a0)*t/n),cz+r*math.sin(a0+(a1-a0)*t/n)) for t in range(n+1)]
  pts=[(SPX,.055)]+[(x,.055) for x in WX]+[(IDX-.12,.07)]+arc(IDX,IDZ,IDR+.03,-1.35,1.57,18)+[(.29,.84),(-.87,.84)]+arc(SPX,SPZ,SPR+.03,1.57,4.4,20)
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
HW=.98;FZ=.895;ZT=1.13   # (v3c) raised 10 cm back from v3b
# (v3b, Keegan: flatter and lower, the hull flaring out to the skirts, stouter bulldog: wider stance, chunkier nose, bigger
# wheels) lower hull with a rounded nose, superstructure whose sides FLARE OUT from the roof edge down to the fender line and
# carry on into the skirts as one slope, roof running in one line from the engine deck down to the front, turret on top
def roof(x):return ZT+.05-(min(x,.78)+1.84)/2.62*.05
SY1,SYF,KS,CH=1.08,1.5,.2,.07   # (v3g) narrower: shoulder to 1.5, skirts flare less   # (v3c) narrower shoulders: the roof stays narrow, the width comes from the sloped shoulder + flared skirts; CH = roof-edge chamfer
KF=(SYF-SY1)/(ZT-CH-FZ)
def ys(z):return SY1+(ZT-CH-z)*KF if z>=FZ else SYF+(FZ-z)*KS   # the flank: a broad sloped shoulder over the track, then the skirts flaring on down
NOSE=[(-1.76,.4),(1.38,.36),(1.78,.46),(1.9,.7),(1.66,FZ),(-1.8,FZ)]   # (v3e) chiselled nose: three flat plates
add('hullLow',prism(NOSE,-HW,HW),PAINT,bev=.008)
SY0=ys(FZ)
sup=[(x,sy*y,z) for sy in (1,-1) for x,y,z in ((-1.84,SY0,FZ),(1.5,SY0,FZ),(-1.84,SY1,roof(-1.84)-CH),(.78,SY1,ZT-CH),(-1.78,SY1-.1,roof(-1.78)),(.78,SY1-.1,ZT),(1.12,SY1-.14,ZT-.02),(1.17,SY1-.06,ZT-.06),(-1.86,SY1-.06,roof(-1.84)-CH-.04))]
add('hull',hull(sup),PAINT,bev=.009)   # (v3e) crisper creases
FN=Vector((.13-.04,0,.4)).normalized();FN=Vector((ZT-.04-FZ,0,1.5-1.15)).normalized()   # front plate normal (leaning back)
def fp(u,y,o):return Vector((1.5,y,FZ))+(Vector((1.15,y,ZT-.04))-Vector((1.5,y,FZ)))*u+FN*o   # (v3e) steeper, leaning further back
for yy in ((-1.12,-.62),(.1,1.12)):   # UNSC-style add-on armour on the front plate, bolt rows
  add('frontArmour',hull([tuple(fp(u,y,o)) for u in (.06,.9) for y in yy for o in (-.01,.05)]+[tuple(fp(u,y,.062)) for u in (.14,.82) for y in (yy[0]+.05,yy[1]-.05)]),PAINT,bev=.005)
  for u in (.22,.74):
    for k in range(4):y=yy[0]+.08+k*(yy[1]-yy[0]-.16)/3;pt=fp(u,y,.058);add('bolt',cyl(pt-FN*.015,pt+FN*.012,.013,8),STEELD,bev=0)
add('drvVisor',hull([tuple(fp(u,y,o)) for u in (.25,.75) for y in (-.52,-.04) for o in (-.01,.08)]),PAINT,bev=.006)
add('drvSlit',hull([tuple(fp(u,y,o)) for u in (.46,.54) for y in (-.46,-.1) for o in (.075,.088)]),GLOWL,bev=0)
for y in (-.4,-.14):add('periscope',hull([(1.03+dx,y+dy,ZT-.04+dz) for dx in (-.05,.05) for dy in (-.045,.045) for dz in (-.02,.05)]),STEELD,bev=.004)
add('drvHatch',cyl((.98,-.27,ZT-.05),(.98,-.27,ZT+.0),.16,24),PAINT,bev=.008)
# the bulldog jaw: a thick bolted bumper bar across the nose, big tow eyes under it
add('bumper',hull([(x,y,z) for y in (-1.0,1.0) for x,z in ((1.84,.54),(1.84,.68),(1.95,.56),(1.95,.66),(1.8,.6))]),PAINT,bev=.007)
for y in (-.8,-.4,0,.4,.8):pt=Vector((1.95,y,.61));add('bolt',cyl(pt-Vector((.01,0,0)),pt+Vector((.014,0,0)),.016,8),STEELD,bev=0)
for sy in (1,-1):
  add('fender',hull([(x,sy*y,z) for y in (HW,SY0) for x,z in ((-1.86,FZ-.03),(-1.86,FZ),(1.52,FZ-.03),(1.52,FZ))]),PAINT,bev=.006)
  add('fenderFront',hull([(x,sy*y,z) for y in (HW+.02,SY0+.04) for x,z in ((1.5,FZ-.03),(1.5,FZ),(2.04,FZ-.16),(2.04,FZ-.13))]),PAINT,bev=.006)
  add('mudFlap',hull([(x,sy*y,z) for y in (1.08,1.52) for x,z in ((-1.85,FZ-.02),(-1.88,FZ-.02),(-1.85,.66),(-1.88,.66))]),RUBW,bev=.004)
  hx,hy,hz=1.64,sy*1.32,FZ+.03   # caged headlight on the front fender
  add('lampBody',cyl((hx-.08,hy,hz+.02),(hx+.04,hy,hz+.02),.06,16),STEELD,bev=.004);add('lampGlass',cyl((hx+.03,hy,hz+.02),(hx+.055,hy,hz+.02),.05,16),LAMPG,bev=0)
  add('lampPost',cyl((hx-.02,hy,FZ-.06),(hx-.02,hy,hz-.03),.02,8),STEELD,bev=0)
  for k in range(3):a=-.6+k*.6;add('cage',cyl((hx+.07,hy+.065*math.sin(a),hz+.02+.065*math.cos(a)),(hx-.03,hy+.065*math.sin(a),hz+.02+.065*math.cos(a)),.006,6),STEELD,bev=0)
  add('cageRing',cyl((hx+.07,hy,hz+.02),(hx+.08,hy,hz+.02),.07,16,None),STEELD,bev=0)
  # bolted armour band on the flared flank, sensor eye on the front corner
  zA,zB=FZ+.02,FZ+.09;nO=Vector((0,sy*1,KF)).normalized()
  add('sideArmour',hull([(x,sy*ys(z),z) for x in (-1.5,1.3) for z in (zA,zB)]+[tuple(Vector((x,sy*ys(z),z))+nO*.035) for x in (-1.48,1.28) for z in (zA+.01,zB-.01)]),PAINT,bev=.004)
  for x in (-1.3,-.6,.1,.8):zz=(zA+zB)/2;pt=Vector((x,sy*ys(zz),zz))+nO*.025;add('bolt',cyl(pt-nO*.01,pt+nO*.022,.013,8),STEELD,bev=0)
  ce=fp(.55,sy*(SY1+.0),0);add('cornerEye',hull([tuple(ce+Vector((dx,dy*sy,dz))) for dx in (-.05,.05) for dy in (-.1,-.02) for dz in (-.025,.025)]),STEELD,bev=.004)
  add('cornerLens',hull([tuple(ce+Vector((.05+dx,dy*sy,dz))) for dx in (-.004,.004) for dy in (-.09,-.03) for dz in (-.015,.015)]),GLOWL,bev=0)
  LN=Vector((.7,0,-.7)).normalized();pt=Vector((1.82,sy*.6,.48));add('towEye',cyl(pt-LN*.05,pt+LN*.08,.065,16),STEELD,bev=.005)
for sy in (1,-1):
  add('grilleFrame',xf(box((0,0,0),(.62,.62,.03)),Matrix.Translation((-1.22,sy*.46,roof(-1.22)+.01))),PAINT,bev=.006)
  for k in range(9):add('louvre',xf(box((0,0,0),(.05,.56,.012)),Matrix.Translation((-1.48+k*.065,sy*.46,roof(-1.22)+.03))@Matrix.Rotation(.6,4,'Y')),STEELD,bev=.002)
add('accessHatch',xf(box((0,0,0),(.34,.5,.03)),Matrix.Translation((-.62,0,roof(-.62)+.008))),PAINT,bev=.008)
for k in range(6):add('bolt',cyl((-.77+k*.06,-.22,roof(-.62)+.01),(-.77+k*.06,-.22,roof(-.62)+.03),.012,8),STEELD,bev=0)
# exhaust: small pipe out of the rear right with a muffler, perforated heat shield and soot
EX=Vector((-1.86,-.95,.9))
add('muffler',cyl((-1.79,-.95,.78),(-1.79,-.6,.78),.075,18),STEELD,bev=.006)
SOOT=M('soot',(.012,.011,.01),.95);add('exPipe',cyl((-1.82,-.98,.78),(-1.82,-.98,1.06),.035,14),STEELD,bev=.003);add('exTip',cyl((-1.82,-.98,1.06),(-1.9,-.98,1.11),.035,14),SOOT,bev=.003);add('exClamp',cyl((-1.82,-.98,.92),(-1.82,-.98,.95),.042,14),STEELD,bev=0);add('exBracket',xf(box((0,0,0),(.05,.05,.04)),Matrix.Translation((-1.8,-.98,1.0))),STEELD,bev=.003)
add('heatShield',xf(box((0,0,0),(.035,.4,.17)),Matrix.Translation((-1.87,-.78,.78))),PAINT,bev=.006)
for k in range(5):add('shieldSlot',xf(box((0,0,0),(.01,.04,.11)),Matrix.Translation((-1.889,-.94+k*.08,.78))),STEELD,bev=0)
add('rearPlate',hull([(-1.78,-1.2,.55),(-1.78,1.2,.55),(-1.8,-1.3,.93),(-1.8,1.3,.93),(-1.7,-1.2,.5),(-1.7,1.2,.5)]),PAINT,bev=.012)
for sy in (1,-1):add('tailLight',xf(box((0,0,0),(.025,.08,.05)),Matrix.Translation((-1.8,sy*1.15,.88))),RED,bev=.004)
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
tool(-.5,.35,1.22,ZT-CH-(1.22-SY1)/KF+.012,.018,WOOD,((.44,1.22,ZT-CH-(1.22-SY1)/KF+.01),(.2,.1,.012)))   # shovel
tool(-.45,.4,1.4,ZT-CH-(1.4-SY1)/KF+.014,.02,WOOD,((.41,1.4,ZT-CH-(1.4-SY1)/KF+.016),(.05,.24,.04)))     # pick
tool(-.6,.3,-1.22,ZT-CH-(1.22-SY1)/KF+.008,.012,STEELD)                                     # crowbar
# tow cable: a flat coil on the right sponson, eye on top
for k in range(3):
  rr=.14-k*.035;cz=roof(-.62)+.012;c=(-.62,-.66)
  ring=[];segN=24
  for q in range(segN+1):
    a=q/segN*2*math.pi;ring.append(Vector((c[0]+rr*math.cos(a),c[1]+rr*math.sin(a),cz)))
  for a0,a1 in zip(ring,ring[1:]):add('cable',cyl(a0,a1,.016,8),STEELD,bev=0)
add('cableEye',cyl((-.62+.14,-.66,roof(-.62)+.012),(-.62+.21,-.66,roof(-.62)+.016),.03,10),STEELD,bev=0)
# (v3f, Keegan: detail the shoulders) armoured stowage bins with lids, hinges and latches on the rear shoulders, a bolted
# panel line along the roof-edge chamfer, and a tow cable clamped along the right shoulder
def shz(x,y):return roof(x)-CH-(abs(y)-SY1)/KF   # height of the sloped shoulder at (x, y)
for sy in (1,-1):
  SNn=Vector((0,sy,KF)).normalized()
  for x0,x1 in ((-1.7,-1.2),(-1.12,-.62)):
    yi,yo=SY1+.05,SY1+.33;zt=shz(x0,yi)+.17
    add('bin',hull([(x,sy*y,z) for x in (x0,x1) for y,z in ((yi,shz(x,yi)-.02),(yo,shz(x,yo)-.02),(yi,zt),(yo,zt-.025))]),PAINT,bev=.008)
    add('binLid',hull([(x,sy*y,z) for x in (x0-.015,x1+.015) for y,z in ((yi-.012,zt),(yo+.012,zt-.025),(yi-.012,zt+.022),(yo+.012,zt-.004))]),PAINT,bev=.005)
    add('binHinge',cyl((x0+.04,sy*(yi-.012),zt+.01),(x1-.04,sy*(yi-.012),zt+.01),.012,10),STEELD,bev=0)
    for xx in (x0+.12,x1-.12):add('binLatch',hull([(xx+dx,sy*(yo+dy),z) for dx in (-.025,.025) for dy in (.0,.022) for z in (zt-.09,zt-.03)]),STEELD,bev=.003)
    pt=Vector(((x0+x1)/2,sy*(yo+.0005),zt-.11));add('binStencil',xf(box((0,0,0),(.12,.004,.03)),Matrix.Translation(pt)),STEN,bev=0)
  for k in range(8):   # bolt row along the chamfer crease
    x=-1.6+k*.29;pt=Vector((x,sy*(SY1+.03),shz(x,SY1+.03)));add('bolt',cyl(pt-SNn*.01,pt+SNn*.014,.012,8),STEELD,bev=0)
  pl=[(x,sy*y,shz(x,y)+dz) for x in (-1.6,.66) for y in (SY1+.015,SY1+.045) for dz in (-.01,.008)]
  add('panelLine',hull(pl),STEELD,bev=.002)
# tow cable along the right shoulder in three clamps, eye at the front
yc=-(SY1+.2);pts=[Vector((x,yc,shz(x,yc)+.018)) for x in (-1.5,-1.0,-.5,0.0,.5,.8)]
for a0,a1 in zip(pts,pts[1:]):add('cable',cyl(a0,a1,.016,8),STEELD,bev=0)
for x in (-1.2,-.25,.55):pz=shz(x,yc);add('cableClamp',hull([(x+dx,yc+dy,pz+dz) for dx in (-.025,.025) for dy in (-.035,.035) for dz in (-.01,.042)]),STEELD,bev=.003)
add('cableEye',cyl(pts[-1],pts[-1]+Vector((.1,0,0)),.028,10),STEELD,bev=0)
LN=Vector((.63,0,.78)).normalized();LD=Vector((-.78,0,.63)).normalized()
for k,y in enumerate((-.33,-.11,.11,.33)):   # spare track links on the lower front plate
  c=Vector((1.804,y,.778))+LN*.02;add('spareLink',xf(box((0,0,0),(.085,.2,.04)),Matrix.Translation(c)@Matrix((LD,Vector((0,1,0)),LN)).transposed().to_4x4()),TRK,bev=.004)
c=Vector((1.804,0,.778))+LN*.045;add('spareBar',cyl(c+Vector((0,-.45,0)),c+Vector((0,.45,0)),.012,8),STEELD,bev=0)
# side skirts: five panels per side, mud-caked, hung on brackets (each panel its own group: can be knocked off when damaged)
for sy in (1,-1):
  SN=Vector((0,sy,KS)).normalized();zt,zb=FZ-.03,.47
  for i in range(5):
    x0=-1.62+i*.64;g='skirt%s%d'%('L' if sy>0 else 'R',i)
    def sp(x,z,o=0):return Vector((x,sy*ys(z),z))+SN*o
    add('skirt',hull([tuple(sp(x,z,o)) for x in (x0+.02,x0+.6) for z in (zt,zb) for o in (-.035,0)]+[tuple(sp(x,z,.006)) for x in (x0+.05,x0+.57) for z in (zt-.02,zb+.02)]),PAINT,g,bev=.005)
    for zz in (zb+.07,zt-.07):
      for xx in (x0+.08,x0+.54):pt=sp(xx,zz,.0);add('skirtBolt',cyl(pt-SN*.005,pt+SN*.018,.013,8),STEELD,g,bev=0)
    pt=sp(x0+.31,zt+.01,-.05);add('skirtHanger',xf(box((0,0,0),(.06,.07,.06)),Matrix.Translation(pt)),STEELD,g,bev=.004)
  add('skirtRail',hull([(x,sy*(ys(zt)+dy),zt+dz) for x in (-1.64,1.6) for dy in (-.09,-.04) for dz in (-.005,.035)]),STEELD,bev=.005)
# ------------------------------------------------------------------ turret
TX,ZR=.2,ZT   # (v3c) moved forward 20 cm
tg='turret'
add('ring',cyl((TX,0,ZR-.02),(TX,0,ZR+.06),.6,48),STEELD,tg,bev=.008)
tb=[]
for z,s,fx in ((ZR+.05,1.0,.02),(ZR+.56,.88,-.04)):   # (v3c) Panzer II: one sloped wall up to a flat roof
  top=z>ZR+.3;zf,zs=(ZR+.43,ZR+.5) if top else (z,z)   # (v3d) wider face, roof angled down toward the front
  tb+=[(TX+.86*s+fx,-.56*s,zf),(TX+.86*s+fx,.56*s,zf),(TX+.55*s,-.78*s,zs),(TX+.55*s,.78*s,zs),(TX-.72*s,-.78*s,z),(TX-.72*s,.78*s,z),(TX-1.0*s,-.55*s,z),(TX-1.0*s,.55*s,z)]
add('turretBody',hull(tb),PAINTT,tg,bev=.025)
# faceted add-on cheek armour with bolt rows (sits proud of the turret front)
for sy in (1,-1):
  add('turretCheek',hull([(TX+.88,sy*.38,ZR+.08),(TX+.88,sy*.38,ZR+.45),(TX+.58,sy*.78,ZR+.08),(TX+.6,sy*.74,ZR+.45),(TX+.95,sy*.42,ZR+.12),(TX+.95,sy*.42,ZR+.41),(TX+.65,sy*.8,ZR+.12),(TX+.66,sy*.77,ZR+.41)]),PAINTT,tg,bev=.012)
  for k in range(3):
    t=(k+.5)/3;pt=Vector((TX+.95-.3*t,sy*(.42+.38*t),0));nn=Vector((.38,sy*.3,0)).normalized()
    for zz in (ZR+.17,ZR+.36):pt.z=zz;add('bolt',cyl(pt-nn*.01,pt+nn*.012,.012,8),STEELD,tg,bev=0)
# turret band in the army colour (a painted strip just above the cheeks, all round)
band=[]
for z in (ZR+.3,ZR+.37):
  k=(z-ZR-.05)/.51;s=1-.12*k+.012;fx=.02-.06*k+.006;band+=[(TX+.86*s+fx,-.56*s,z),(TX+.86*s+fx,.56*s,z),(TX+.55*s,-.78*s,z),(TX+.55*s,.78*s,z),(TX-.72*s,-.78*s,z),(TX-.72*s,.78*s,z),(TX-1.0*s,-.55*s,z),(TX-1.0*s,.55*s,z)]
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
CX,CY=TX-.34,.25
add('cupola',cyl((CX,CY,ZR+.55),(CX,CY,ZR+.66),.2,24,.18),PAINTT,tg,bev=.01)
for k in range(6):a=k*math.pi/3+.3;add('cupScope',xf(box((0,0,0),(.06,.09,.05)),Matrix.Translation((CX+.185*math.cos(a),CY+.185*math.sin(a),ZR+.61))@Matrix.Rotation(a,4,'Z')),STEELD,tg,bev=.004)
add('cupHatch',cyl((CX,CY,ZR+.66),(CX,CY,ZR+.7),.17,24,.15),PAINTT,tg,bev=.006);add('grab',cyl((CX-.07,CY-.07,ZR+.708),(CX+.07,CY+.07,ZR+.708),.012,8),STEELD,tg,bev=0)
# loader hatch, gunner's sight box with glowing optic, sensor mast with sensor head (glowing lens), whip antenna base
add('ldrHatch',cyl((TX-.34,-.25,ZR+.555),(TX-.34,-.25,ZR+.59),.16,20),PAINTT,tg,bev=.006)
add('sightBox',hull([(TX+.2,-.42,ZR+.55),(TX+.44,-.42,ZR+.53),(TX+.2,-.22,ZR+.55),(TX+.44,-.22,ZR+.53),(TX+.2,-.42,ZR+.68),(TX+.4,-.42,ZR+.66),(TX+.2,-.22,ZR+.68),(TX+.4,-.22,ZR+.66)]),PAINTT,tg,bev=.01)
add('sightGlass',xf(box((0,0,0),(.01,.16,.08)),Matrix.Translation((TX+.425,-.32,ZR+.605))@Matrix.Rotation(-.25,4,'Y')),GLOWL,tg,bev=0)
add('mastBase',cyl((TX-.6,.36,ZR+.53),(TX-.6,.36,ZR+.58),.07,14),STEELD,tg,bev=.004)
add('mast',cyl((TX-.6,.36,ZR+.58),(TX-.6,.36,ZR+.86),.025,10),STEELD,tg,bev=0)
add('sensorHead',hull([(TX-.67,.29,ZR+.84),(TX-.5,.29,ZR+.84),(TX-.67,.43,ZR+.84),(TX-.5,.43,ZR+.84),(TX-.67,.31,ZR+.96),(TX-.52,.31,ZR+.96),(TX-.67,.41,ZR+.96),(TX-.52,.41,ZR+.96),(TX-.46,.36,ZR+.9)]),PAINTT,tg,bev=.008)
add('sensorLens',cyl((TX-.48,.36,ZR+.9),(TX-.45,.36,ZR+.9),.03,14),GLOWL,tg,bev=0)
add('antBase',cyl((TX-.62,-.36,ZR+.53),(TX-.62,-.36,ZR+.6),.035,10),STEELD,tg,bev=.003);add('antenna',cyl((TX-.62,-.36,ZR+.6),(TX-.68,-.36,ZR+1.9),.006,6,.003),STEELD,tg,bev=0)
# smoke dischargers: 4 tubes each side on the turret cheeks (angled out and up)
for sy in (1,-1):
  add('smokeMount',xf(box((0,0,0),(.16,.14,.1)),Matrix.Translation((TX+.5,sy*.72,ZR+.47))),STEELD,tg,bev=.005)
  for k in range(4):
    d=Vector((math.cos(.35*sy*0)+.2,sy*(.55+.08*k),.55)).normalized();o=Vector((TX+.5,sy*(.74+.03*k),ZR+.5+.02*(k%2)))
    add('smokeTube',cyl(o,o+d*.16,.03,12),STEELD,tg,bev=.003);add('smokeCap',cyl(o+d*.15,o+d*.17,.032,12),RUBW,tg,bev=0)
# APS pods (active protection): small armoured launcher boxes on the four turret corners with a sensor window each
for (px,py) in ((TX+.4,.46),(TX+.4,-.46),(TX-.5,.44),(TX-.5,-.44)):
  sy=1 if py>0 else -1
  add('apsPod',hull([(px-.09,py-.07,ZR+.5),(px+.09,py-.07,ZR+.5),(px-.09,py+.07,ZR+.5),(px+.09,py+.07,ZR+.5),(px-.07,py-.06,ZR+.62),(px+.07,py-.06,ZR+.62),(px-.07,py+.06,ZR+.62),(px+.07,py+.06,ZR+.62)]),PAINTT,tg,bev=.008)
  add('apsEye',xf(box((0,0,0),(.06,.006,.03)),Matrix.Translation((px,py+sy*.062,ZR+.57))),GLOWL,tg,bev=0)
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
for sy in (1,-1):zz=.7;text(None,'D-27',Vector((.2,sy*(ys(zz)+.004),zz))+Vector((0,sy,KS)).normalized()*.004,(0,sy,KS),.16,TEAMB)
text(None,'K9 ARMOR',Vector((-1.79,-.2,.6)),(-1,0,0),.06,STEN)
TS=float(os.environ.get('TSCALE','.85'))
TSX,TSY,TSZ=float(os.environ.get('TSX','.92')),float(os.environ.get('TSY','.95')),float(os.environ.get('TSZ','1.0'))   # (v3, Keegan: Panzer II reference: wider, lower, more sloped turret)
Ms=Matrix.Translation((TX,0,ZR))@Matrix.Diagonal((TSX,TSY,TSZ,1))@Matrix.Translation((-TX,0,-ZR))
Mg=Matrix.Translation((TX+(MX-TX)*TSX,0,ZR+(MZ-ZR)*TSZ))@Matrix.Scale(TS,4)@Matrix.Translation((-MX,0,-MZ))
for o in P:
  if o['grp']=='turret':o.data.transform(Ms)
  elif o['grp'] in('gunL','gunR'):o.data.transform(Mg)
LS=float(os.environ.get('LS','.85'))   # (v3g) overall scale: light < medium (~5.3 m) < heavy (~7.6 m)
LSM=Matrix.Scale(LS,4)
for o in P:o.data.transform(LSM)
for o in bpy.data.objects:
  if o.type=='FONT':o.matrix_world=LSM@o.matrix_world
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
0 and shot('/home/claude/veh/lt_top.png',(.25,-.3,1),(0,0,1.2),4.4,(1200,1200))
shot('/home/claude/veh/lt_turret.png',(1,-.8,.45),(.35,0,1.45),2.2,(1400,960))
bpy.ops.wm.save_as_mainfile(filepath='/home/claude/veh/lt_v3.blend')
