# Marine v2 BODY pass 2 (Keegan's notes): slimmer waist/hips, legs 5% shorter but thicker thighs/calves, slimmer pauldrons
# (nothing floating), detailed CE-style armour plates (layered thigh plates, ridged shin guards, capped knee guards, pec plates
# with a spine), sculpted fabric limbs (folds, calf, bloused trousers), full sleeves, muted pauldrons + bright army stripe,
# gear + bake details (straps, buckles, mag pouches, grenades, knife, stencils, rivets), chunkier weapons, a retro-futurist
# comms backpack, polished poses (side-on carry, head follows the aim, launcher on the shoulder).
import sys,os
src=open('/home/claude/body/body.py').read();exec(src.split('# ---------------------------------------------------------------- weapons')[0])
from mathutils.bvhtree import BVHTree
STRIPE=M('stripe',(.16,.62,.12),.55,.2);PACKM=steel('packsteel',(.075,.085,.055),0,.8);DIAL=M('dial',(.5,.45,.3),.3,.8);LAMP=M('lamp',(1,.55,.15),.4,0,6)
TEAMC={'Dawgs':(.16,.62,.12)}
def tubeP(a,b,prof,ref=Vector((1,0,0)),flat=1.0,NS=20,NR=18,fold=0.0,seed=0,back=None):
  """fabric tube: radius prof(t) along a->b, + fold bands and a little angular noise; back (vector) pushes the calf/bicep side"""
  a,b=Vector(a),Vector(b);ax,u,v=basis(b-a,ref);L=(b-a).length;bm=bmesh.new();R=[];rr=random.Random(seed);ph=[rr.uniform(0,6.3) for _ in range(4)]
  for j in range(NR+1):
    t=j/NR;c=a+ax*L*t;ring=[]
    for k in range(NS):
      ang=k/NS*2*math.pi;d=u*math.cos(ang)+v*flat*math.sin(ang);r=prof(t)
      r*=1+fold*(.6*math.sin(t*22+ph[0]+.8*math.sin(ang*2+ph[1]))*math.exp(-((t-.5)/.42)**4)+.35*math.sin(ang*3+t*9+ph[2]))
      if back is not None:r*=1+.12*max(0,d.normalized().dot(back))*math.sin(min(1,t*1.6)*math.pi)
      ring.append(bm.verts.new(c+d*r))
    R.append(ring)
  for j in range(NR):
    for k in range(NS):bm.faces.new((R[j][k],R[j][(k+1)%NS],R[j+1][(k+1)%NS],R[j+1][k]))
  for ring,e in ((R[0],a-ax*prof(0)*.5),(R[-1],b+ax*prof(1)*.5)):cv=bm.verts.new(e);[bm.faces.new((ring[k],ring[(k+1)%NS],cv)) for k in range(NS)]
  bmesh.ops.recalc_face_normals(bm,faces=bm.faces);return bm
def Fr(o,x,y,z):return (o,Matrix((x,y,z)).transposed())
# ---------------------------------------------------------------- weapons (local: x forward, z up, grip at origin) -- chunkier
def weapon(kind,G):
  O,F=G
  def B(c,s,mat,rot=None,bev=.005):put('gun',boxT(c,s,(O,F),rot),mat,bev=bev)
  def T(a,b,r,mat,NS=14):put('gun',tube(O+F@Vector(a),O+F@Vector(b),r,r,F@Vector((0,0,1)),NS=NS,NR=1),mat)
  def H(pts,mat,bev=.005):put('gun',hullT(pts,(O,F)),mat,bev=bev,smooth=False)
  if kind in('rifle','sniper'):
    S=1.0 if kind=='rifle' else 1.25
    H([(x,y,z) for x in (-.04,.2) for y in (-.032,.032) for z in (.02,.105)]+[(.24,y,.09) for y in (-.03,.03)],GUN)                     # receiver
    H([(x,y,z) for x in (-.36,-.05) for y in (-.028,.028) for z in (.03,.1)]+[(-.36,y,-.03) for y in (-.026,.026)]+[(-.15,y,.0) for y in (-.024,.024)],GUNP)  # stock
    B((.0,0,-.04),(.04,.034,.09),GUNP,Matrix.Rotation(-.28,3,'Y'));B((.135,0,-.045),(.05,.03,.13),GUN,Matrix.Rotation(.2,3,'Y'))    # grip, mag
    H([(x,y,z) for x in (.2,.2+.24*S) for y in (-.034,.034) for z in (.03,.1)]+[(.2+.26*S,y,.065) for y in (-.025,.025)],GUNP)    # handguard
    T((.2,0,.07),(.2+.5*S,0,.07),.012,GUN);T((.2+.44*S,0,.07),(.2+.52*S,0,.07),.018,GUN)                                           # barrel + brake
    if kind=='sniper':T((-.02,0,.15),(.27,0,.15),.026,GUN);B((.12,0,.12),(.04,.03,.04),GUN);B((.4,0,.0),(.015,.12,.015),GUN,Matrix.Rotation(.0,3,'Y'))
    else:B((.08,0,.13),(.11,.045,.05),GUN,bev=.008);B((.1,0,.155),(.04,.03,.02),DARK)                                              # optic
  elif kind=='mg':
    H([(x,y,z) for x in (-.06,.3) for y in (-.045,.045) for z in (.0,.13)],GUN);B((-.22,0,.05),(.26,.06,.12),GUNP);B((.0,0,-.04),(.04,.034,.09),GUNP,Matrix.Rotation(-.28,3,'Y'))
    B((.1,.09,.0),(.17,.11,.16),GUNP,bev=.01);B((.1,.15,.06),(.13,.01,.03),DIAL)                                                    # belt box + tab
    T((.3,0,.07),(.95,0,.07),.02,GUN);H([(x,y,z) for x in (.3,.62) for y in (-.045,.045) for z in (.03,.11)],GUNP);T((.85,0,.07),(.98,0,.07),.03,GUN)
    B((.12,0,.17),(.24,.05,.03),GUN);T((.0,0,.19),(.06,0,.25),.008,GUN)                                                            # top cover + handle
    for sy in (-1,1):T((.78,sy*.02,.05),(.5,sy*.05,-.06),.009,GUN,8)                                                               # bipod folded
  elif kind=='rocket':
    T((-.5,0,.14),(.7,0,.14),.068,GUNP,18);T((.66,0,.14),(.74,0,.14),.078,GUN,18);T((-.55,0,.14),(-.46,0,.14),.08,GUN,18)
    for x in (-.25,.25):T((x,0,.14),(x+.06,0,.14),.074,PACKM,18)
    B((.0,0,.03),(.04,.034,.1),GUNP,Matrix.Rotation(-.2,3,'Y'));B((.22,0,.05),(.04,.034,.08),GUNP)
    B((.08,-.085,.17),(.12,.045,.07),GUN,bev=.01);B((.08,-.11,.17),(.004,.02,.035),STRIPE)                                        # sight box with lit window
# ---------------------------------------------------------------- the marine
LEG=(.43,.42);ARML=(.32,.3)
def marine(P,head='rifle',seed=0,gear='std',weap='rifle',lens=None,team=(.16,.62,.12)):
  r=random.Random(seed);Pp,Rp=Vector(P['pelvis'][0]),P['pelvis'][1];FP=(Pp,Rp)
  Rc=Rp@P.get('chest',Matrix.Identity(3));Cc=Pp+Rp@Vector((0,0,.3));FC=(Cc,Rc);made=[];bodyobs=[]
  def W(Fm,p):return Fm[0]+Fm[1]@Vector(p)
  def pb(name,bm,mat,**k):o=put(name,bm,mat,**k);made.append(o);bodyobs.append(o);return o
  def pg(name,bm,mat,**k):o=put(name,bm,mat,**k);made.append(o);return o
  # torso: slimmer waist and hips, the same broad chest
  rings=[(FP,-.1,.148,.105),(FP,-.02,.142,.1),(FP,.06,.13,.094),(FC,-.16,.128,.092),(FC,-.08,.16,.112),(FC,0,.2,.13),(FC,.09,.225,.135),(FC,.15,.2,.125),(FC,.2,.1,.085),(FC,.24,.065,.065)]
  bm=bmesh.new();RR=[];NS=28
  for Fm,z,w,d in rings:RR.append([bm.verts.new(W(Fm,(w*math.copysign(abs(math.cos(a))**.8,math.cos(a)),d*math.copysign(abs(math.sin(a))**.8,math.sin(a)),z))) for a in [k/NS*2*math.pi for k in range(NS)]])
  for j in range(len(RR)-1):
    for k in range(NS):bm.faces.new((RR[j][k],RR[j][(k+1)%NS],RR[j+1][(k+1)%NS],RR[j+1][k]))
  for ring,e in ((RR[0],W(FP,(0,0,-.13))),(RR[-1],W(FC,(0,0,.25)))):cv=bm.verts.new(e);[bm.faces.new((ring[k],ring[(k+1)%NS],cv)) for k in range(NS)]
  bmesh.ops.recalc_face_normals(bm,faces=bm.faces);pb('torso',bm,CAMO)
  # chest: pec plates either side of a raised spine plate, two abdominal lames, back plate, collar, side straps
  for sx in (1,-1):
    pb('pec',hullT([(sx*.018,-.17,.0),(sx*.02,-.162,.14),(sx*.045,-.14,.19),(sx*.15,-.13,.16),(sx*.21,-.08,.12),(sx*.205,-.1,-.01),(sx*.12,-.15,-.05),(sx*.025,-.168,-.05),(sx*.19,-.02,.13),(sx*.17,-.02,-.02),(sx*.03,-.08,.14)],FC),ARM,bev=.006,smooth=False)
    pb('pecEdge',hullT([(sx*.2,-.085,.125),(sx*.215,-.07,.11),(sx*.205,-.1,-.0),(sx*.19,-.11,.0),(sx*.2,-.06,.11),(sx*.19,-.06,-.01)],FC),TEAMM,bev=.003,smooth=False)
  pb('spine',hullT([(sx*.025,y,z) for sx in (1,-1) for y,z in ((-.183,-.04),(-.178,.12),(-.16,.17),(-.16,-.05))]+[(0,-.19,.05)],FC),ARM,bev=.004,smooth=False)
  for k,(z0,z1,w) in enumerate(((-.075,-.125,.158),(-.13,-.18,.142))):
    pb('lame',hullT([(sx*w,-.115,z0) for sx in (1,-1)]+[(sx*w*.95,-.11,z1) for sx in (1,-1)]+[(sx*w*.55,-.152,z0) for sx in (1,-1)]+[(sx*w*.5,-.146,z1) for sx in (1,-1)]+[(sx*w,-.03,z0) for sx in (1,-1)]+[(sx*w*.95,-.03,z1) for sx in (1,-1)],FC),ARM,bev=.005,smooth=False)
  bk=[(sx*x,y,z) for sx in (1,-1) for x,y,z in [(.2,.1,.13),(.18,.12,.0),(.14,.12,-.13),(.06,.14,-.12),(.07,.145,.12),(.03,.11,.19)]]+[(0,.03,.1)]
  pb('chestB',hullT(bk,FC),ARM,bev=.006,smooth=False)
  for sx in (1,-1):
    pb('collar',hullT([(sx*.03,-.1,.17),(sx*.1,-.07,.17),(sx*.12,-.02,.2),(sx*.1,-.06,.26),(sx*.04,-.095,.25),(sx*.11,.0,.25),(sx*.06,.05,.18),(sx*.06,.06,.26)],FC),ARM,bev=.005,smooth=False)
    pg('strap',boxT((sx*.19,0,-.03),(.03,.21,.05),FC),WEB,bev=.006)
    pg('shStrap',hullT([(sx*.08,-.135,.17),(sx*.13,-.13,.17),(sx*.1,.0,.235),(sx*.15,.0,.225),(sx*.08,.125,.15),(sx*.13,.12,.15)],FC),WEB,bev=.004,smooth=False)
  pg('buckle',boxT((0,-.148,.0),(.04,.012,.028),FP),METL,bev=.003)
  # belt + pouches (double mags front, grenades and a dump pouch on the sides), groin plate with a centre ridge
  pb('belt',tube(W(FP,(0,0,-.05)),W(FP,(0,0,.02)),.152,.148,Rp@Vector((1,0,0)),flat=.72,NS=28,NR=2),WEB)
  for x in (-.11,-.05,.05,.11):
    if gear=='light' and abs(x)<.08:continue
    pg('mags',boxT((x,-.122+abs(x)*.2,-.03),(.05,.04,.085),FP,Rz(x*1.6)),POUCH,bev=.008)
    pg('flap',boxT((x,-.126+abs(x)*.2,.012),(.052,.046,.012),FP,Rz(x*1.6)),POUCH,bev=.004)
  for sx in (1,-1):pg('pouchS',boxT((sx*.15,.02,-.04),(.05,.08,.09),FP),POUCH,bev=.008)
  for k in range(2):
    c=W(FP,(.158,-.07+k*.045,-.06));pg('nade',ell(c,(.026,.026,.032)),GUNP);pg('fuze',boxT((.158,-.07+k*.045,-.02),(.014,.014,.022),FP),METL,bev=.003)
  pg('canteen',boxT((-.08,.125,-.04),(.08,.05,.1),FP),POUCH,bev=.015)
  pb('groin',hullT([(-.065,-.115,-.06),(.065,-.115,-.06),(-.05,-.125,-.2),(.05,-.125,-.2),(0,-.135,-.24),(-.06,-.09,-.08),(.06,-.09,-.08),(0,-.09,-.24),(0,-.135,-.07)],FP),ARM,bev=.005,smooth=False)
  # knife on the left chest strap
  pg('sheath',boxT((.11,-.145,.06),(.032,.016,.15),FC,Matrix.Rotation(.5,3,'Y')),GUNP,bev=.004);pg('knife',boxT((.075,-.15,.13),(.02,.018,.06),FC,Matrix.Rotation(.5,3,'Y')),GUN,bev=.004)
  # legs: shorter, thicker thighs + calves, layered thigh plates, capped knee guards, ridged shin guards, bloused trousers
  pole=Rp@Vector((0,-1,0))
  for i,sx in enumerate((-1,1)):
    hipJ=W(FP,(sx*.095,0,-.06));ank,yaw,toe=P['feet'][i];ank=Vector(ank)
    kn,ank=ik(hipJ,ank,LEG[0],LEG[1],pole+Vector((sx*.15,0,0)))
    lr=Rp@Vector((1,0,0));fwd=(Rp@Vector((0,-1,0)))
    pb('thigh',tubeP(hipJ,kn,lambda t:.108-.03*t+.012*math.sin(t*math.pi),lr,1.06,fold=.035,seed=seed*7+i),CAMO)
    pb('shin',tubeP(kn,ank+(kn-ank).normalized()*.02,lambda t:.074+.016*math.sin(min(1,t*1.5)*math.pi)-.012*t+.016*max(0,(t-.8)/.2)**2,lr,fold=.04,seed=seed*7+i+3,back=-fwd),CAMO)
    tdir=(kn-hipJ).normalized();tb=basis(tdir,lr);Ft=(hipJ,Matrix((tb[1],tb[2],tb[0])).transposed())
    pg('cargo',boxT((sx*.1,0,.22),(.03,.1,.12),Ft),POUCH,bev=.01)
    for k,(z0,z1) in enumerate(((.05,.2),(.17,.3))):
      pb('thighP',hullT([(sx*.015,-.1,z0),(sx*.075,-.085,z0),(sx*.105,-.02,z0+.02),(sx*.015,-.112,z1),(sx*.08,-.095,z1),(sx*.105,-.02,z1-.02),(sx*.06,-.112,(z0+z1)/2),(sx*.01,-.06,z0),(sx*.01,-.06,z1)],Ft),ARM,bev=.005,smooth=False)
    sdir=(ank-kn).normalized();sb=basis(sdir,lr);Fs=(kn,Matrix((sb[1],sb[2],sb[0])).transposed())
    pb('knee',hullT([(-.06,-.06,-.06),(.06,-.06,-.06),(-.055,-.1,.0),(.055,-.1,.0),(0,-.115,-.02),(-.05,-.07,.07),(.05,-.07,.07),(0,-.1,.06),(-.07,-.02,0),(.07,-.02,0)],Fs),ARM,bev=.006,smooth=False)
    pg('kneeCap',hullT([(-.03,-.11,-.035),(.03,-.11,-.035),(-.025,-.122,.0),(.025,-.122,.0),(0,-.128,-.015),(-.03,-.1,.04),(.03,-.1,.04)],Fs),TEAMM,bev=.004,smooth=False)
    pb('kneeStrap',tube(W(Fs,(0,0,-.03)),W(Fs,(0,0,-.005)),.085,.085,Fs[1]@Vector((1,0,0)),NS=20,NR=1),WEB)
    pb('kneePad',ell(kn,(.075,.075,.075)),WEB)
    pb('shinG',hullT([(-.05,-.075,.09),(.05,-.075,.09),(0,-.095,.1),(-.055,-.065,.31),(.055,-.065,.31),(0,-.085,.31),(-.062,-.02,.2),(.062,-.02,.2)],Fs),ARM,bev=.005,smooth=False)
    pg('shinR',hullT([(-.008,-.095,.11),(.008,-.095,.11),(-.008,-.087,.3),(.008,-.087,.3),(0,-.103,.2)],Fs),ARM,bev=.003,smooth=False)
    pb('shinStrap',tube(W(Fs,(0,0,.24)),W(Fs,(0,0,.262)),.082,.082,Fs[1]@Vector((1,0,0)),NS=20,NR=1),WEB)
    Fb=(ank,Rz(yaw)@Rx(toe))
    pb('boot',hullT([(sx2*w,y,z) for sx2 in (1,-1) for w,y,z in [(.058,.07,-.075),(.06,-.17,-.075),(.05,-.205,-.05),(.045,-.19,-.015),(.055,-.08,.03),(.055,-.04,.08),(.06,.065,.11),(.058,.075,.02)]],Fb),BOOT,bev=.012,smooth=False)
    pb('sole',boxT((0,-.065,-.083),(.125,.29,.02),Fb),SOLE,bev=.005)
    pg('bootStrap',boxT((0,-.03,.05),(.125,.03,.02),Fb,Matrix.Rotation(.5,3,'X')),WEB,bev=.004)
  # weapon + arms (full sleeves, bicep, elbow folds), vambraces, gloves
  gO,gR=Vector(P['gun'][0]),P['gun'][1];weapon(weap,(gO,gR))
  fore={'rifle':(.22,0,.03),'sniper':(.27,0,.03),'mg':(.28,0,.0),'rocket':(.22,0,.05)}[weap]
  tg={'R':gO,'L':gO+gR@Vector(fore)}
  for side,sx in (('R',-1),('L',1)):
    sh=W(FC,(sx*.205,0,.13));hand=tg[side]
    el,wr=ik(sh,hand+Vector((0,0,.03)),ARML[0],ARML[1],Rc@Vector((sx*.9,.5,-1)))
    lr=(el-sh).cross(wr-el);lr=lr if lr.length>1e-4 else Rc@Vector((1,0,0))
    pb('uarm',tubeP(sh,el,lambda t:.078-.014*t+.012*math.sin(t*math.pi),lr,fold=.03,seed=seed*5+sx),CAMO)
    pb('farm',tubeP(el,wr,lambda t:.064-.016*t+.006*math.sin(t*math.pi)+.01*max(0,1-t*4),lr,fold=.035,seed=seed*5+sx+9),CAMO)
    pb('elbow',ell(el,(.064,.064,.064)),WEB)
    fd=(wr-el).normalized();fb=basis(fd,Rc@Vector((sx,0,0)));Ff=(el,Matrix((fb[1],fb[2],fb[0])).transposed())
    pb('vamb',hullT([(.035,-.045,.06),(.068,-.0,.06),(.035,.045,.06),(.055,-.03,.24),(.07,0,.24),(.055,.03,.24),(.05,-.042,.15),(.05,.042,.15)],Ff),ARM,bev=.004,smooth=False)
    hd=(hand-wr);hd=hd.normalized() if hd.length>.01 else fd;hb=basis(hd,gR@Vector((0,1,0)));Fh=(wr,Matrix((hb[1],hb[2],hb[0])).transposed())
    pb('glove',hullT([(-.045,-.03,.0),(.045,-.03,.0),(-.045,.03,.0),(.045,.03,.0),(-.05,-.035,.09),(.05,-.035,.09),(-.045,.04,.1),(.045,.04,.1),(-.04,0,.13),(.04,0,.13)],Fh),GLOVE,bev=.012,smooth=False)
    pb('knuckle',hullT([(-.04,-.04,.06),(.04,-.04,.06),(-.035,-.048,.1),(.035,-.048,.1),(-.035,-.03,.1),(.035,-.03,.1)],Fh),ARM,bev=.004,smooth=False)
    # pauldron: slimmer, hugging the shoulder (inner edge sunk into the torso/arm so it never floats) + bright army stripe
    Fu=(sh,Rc@Matrix(((sx,0,0),(0,-1,0),(0,0,1))))
    pp=[(-.05,y,.075) for y in (-.075,.075)]+[(.03,y,.085) for y in (-.09,.09)]+[(.08,y,.035) for y in (-.095,.095)]+[(.1,y,-.05) for y in (-.09,.09)]+[(.09,y,-.105) for y in (-.075,.075)]+[(.04,0,.105),(.11,0,-.0),(.1,0,-.115)]+[(-.02,y,-.04) for y in (-.08,.08)]
    pb('paul',hullT(pp,Fu),TEAMM,bev=.008,smooth=False)
    pb('paul2',hullT([(.07,y,-.1) for y in (-.072,.072)]+[(.105,y,-.11) for y in (-.068,.068)]+[(.09,y,-.17) for y in (-.06,.06)]+[(.06,y,-.16) for y in (-.06,.06)]+[(.11,0,-.15)],Fu),TEAMM,bev=.005,smooth=False)
    stM=M('stripe%d'%seed,team,.5,.15)
    pg('stripe',hullT([(.096,y,-.035) for y in (-.092,.092)]+[(.104,y,-.06) for y in (-.09,.09)]+[(.1,y,-.05) for y in (-.091,.091)]+[(.093,y,-.04) for y in (-.09,.09)],Fu),stM,bev=.002,smooth=False)
    pg('paulS',boxT((.02,0,.09),(.03,.15,.012),Fu,Matrix.Rotation(.4,3,'Y')),WEB,bev=.003)
  # back gear
  if gear in('std','ammo','rocket','radio'):
    pg('pack',boxT((0,.2,-.02),(.26,.13,.3),FC),POUCH,bev=.02);pg('packFlap',boxT((0,.27,.1),(.24,.012,.1),FC),POUCH,bev=.006)
    if gear=='ammo':pg('can',boxT((-.06,.29,-.05),(.14,.09,.18),FC),GUNP,bev=.008)
    if gear=='rocket':
      for x in (-.06,.08):pg('spare',tube(W(FC,(x,.29,-.25)),W(FC,(x,.29,.42)),.055,.055,NS=14,NR=1),GUNP);pg('spareCap',tube(W(FC,(x,.29,.42)),W(FC,(x,.29,.46)),.06,.06,NS=14,NR=1),GUN)
  if gear=='comms':comms_pack(FC,pg)
  # BAKE DETAILS on the body: rivets on plates and stencils, ray-cast onto the plates so they sit exactly on the surface
  dg=bpy.context.evaluated_depsgraph_get();trees=[(o,BVHTree.FromObject(o,dg)) for o in bodyobs if o.data.materials[0] in (ARM,TEAMM)]
  def hit(p,d):
    best=None
    for o,t in trees:
      h=t.ray_cast(Vector(p),Vector(d).normalized(),1.0)
      if h[0] is not None and (best is None or h[3]<best[2]):best=(o.matrix_world@h[0],(o.matrix_world.to_3x3()@h[1]).normalized(),h[3])
    return best
  def rivet(p,d,rad=.0045):
    b=hit(p,d)
    if not b:return
    bm2=bmesh.new();bmesh.ops.create_cone(bm2,cap_ends=True,segments=10,radius1=rad,radius2=rad*.75,depth=.003)
    bmesh.ops.transform(bm2,matrix=Matrix.Translation(b[0]+b[1]*.001)@b[1].to_track_quat('Z','Y').to_matrix().to_4x4(),verts=bm2.verts);o=bake_obj('rivet',bm2,METL,(0,0,0));made.append(o)
  def sten(s,p,d,size):
    b=hit(p,d)
    if not b:return
    cu=bpy.data.curves.new('t','FONT');cu.body=s;cu.size=size;cu.extrude=.0004;cu.align_x='CENTER';cu.align_y='CENTER'
    o=bpy.data.objects.new('sten',cu);BAKE.objects.link(o);o['bake']=1;o.data.materials.append(STEN);o.matrix_world=Matrix.Translation(b[0]+b[1]*.0008)@b[1].to_track_quat('Z','Y').to_matrix().to_4x4();made.append(o)
  out=Rc@Vector((0,-1,0))
  for sx in (1,-1):
    for z in (.15,.0):rivet(W(FC,(sx*.17,-.5,z)),out)
    rivet(W(FC,(sx*.42,-.02,.1)),Rc@Vector((-sx,0,0)));rivet(W(FC,(sx*.42,.03,.05)),Rc@Vector((-sx,0,0)))
  sten('%s-%02d'%(r.choice(['DG','K9']),r.randrange(1,99)),W(FC,(-.11,-.5,.08)),out,.026)
  sten(str(r.randrange(1,9)),W(FC,(.42,0,.06)),Rc@Vector((-1,0,0)),.05)
  # head on an empty at the neck; the head follows the aim when the pose gives a look target
  if os.environ.get('NOHEAD'):return made,bodyobs
  before=set(bpy.data.objects);L0=lens or lensmat(seed,(.25,.75,.3))
  if head=='sniper':sniper_head((0,0,0),L0)
  elif head=='spotter':spotter_head((0,0,0),L0)
  else:variant(seed,(0,0,0),L0)
  emp=bpy.data.objects.new('head',None);bpy.context.scene.collection.objects.link(emp)
  for o in set(bpy.data.objects)-before:
    if o is not emp:o.parent=emp
  hc=W(FC,(0,-.01,.37))
  if P.get('look') is not None:
    d=(Vector(P['look'])-hc).normalized();Rh=(-d).to_track_quat('Y','Z').to_matrix()   # head local -y = forward
  else:Rh=Rc@P.get('head',Matrix.Identity(3))
  emp.matrix_world=Matrix.Translation(hc)@Rh.to_4x4()
  return made,bodyobs
def comms_pack(FC,pg):
  """retro-futurist field comms set (original): chunky steel case on a frame, ribbed heat-sink block, rotary dials, toggle row,
  amber status lamps, side battery canisters, folding dish stub, whip + blade antennas, coiled handset cable to the chest"""
  def W(p):return FC[0]+FC[1]@Vector(p)
  pg('frame',boxT((0,.15,-.02),(.24,.02,.36),FC),GUN,bev=.006)
  pg('case',hullT([(sx*.14,y,z) for sx in (1,-1) for y,z in ((.16,-.2),(.31,-.18),(.32,.12),(.16,.16),(.28,.17))],FC),PACKM,bev=.012,smooth=False)
  for k in range(7):pg('fin',boxT((0,.235,.19+k*.0),(.24,.012+0,.04),FC,None) if False else boxT((-.11+k*.037,.24,.19),(.012,.13,.045),FC),PACKM,bev=.003)
  pg('panel',boxT((.145,.24,-.03),(.012,.13,.24),FC),GUN,bev=.004)
  for k,(y,z) in enumerate(((.2,.04),(.28,.04),(.24,-.07))):
    pg('dial',tube(W((.15,y,z)),W((.172,y,z)),.022,.02,FC[1]@Vector((0,1,0)),NS=16,NR=1),DIAL);pg('knob',tube(W((.172,y,z)),W((.185,y,z)),.008,.008,FC[1]@Vector((0,1,0)),NS=8,NR=1),GUN)
  for k in range(4):pg('toggle',boxT((.158,.19+k*.03,-.15),(.012,.006,.02),FC,Matrix.Rotation(.4,3,'Y')),METL,bev=.002)
  for k in range(3):pg('lamp',ell(W((.155,.2+k*.04,.12)),(.006,.006,.006)),LAMP)
  for sx in (1,-1):
    pg('batt',tube(W((sx*.165,.2,-.2)),W((sx*.165,.2,.05)),.04,.04,FC[1]@Vector((0,1,0)),NS=14,NR=1),PACKM);pg('battCap',tube(W((sx*.165,.2,.05)),W((sx*.165,.2,.075)),.03,.03,FC[1]@Vector((0,1,0)),NS=12,NR=1),METL)
  pg('dish',tube(W((-.09,.3,.2)),W((-.09,.36,.26)),.07,.07,FC[1]@Vector((1,0,0)),NS=20,NR=1),PACKM);pg('dishHub',ell(W((-.09,.37,.27)),(.015,.015,.015)),GUN)
  pg('whip',tube(W((.1,.3,.2)),W((.16,.38,.95)),.0045,.003,NS=6,NR=1),GUN);pg('whipBase',tube(W((.1,.29,.18)),W((.1,.3,.24)),.014,.012,NS=10,NR=1),GUN)
  pg('blade',boxT((.0,.33,.26),(.01,.04,.12),FC),GUN,bev=.003)
  bm=bmesh.new();pr=None
  for k in range(40):
    t=k/39;c=W((-.14+.02*t,.16-.3*t,-.0+.15*t))+FC[1]@Vector((.012*math.cos(t*60),0,.012*math.sin(t*60)))
    ring=[bm.verts.new(c+FC[1]@Vector((.004*math.cos(a),.004*math.sin(a),0))) for a in [i/6*2*math.pi for i in range(6)]]
    if pr:[bm.faces.new((pr[i],pr[(i+1)%6],ring[(i+1)%6],ring[i])) for i in range(6)]
    pr=ring
  pg('cord',bm,GUN);pg('handset',boxT((-.12,-.15,.17),(.035,.03,.12),FC,Matrix.Rotation(.3,3,'Y')),PACKM,bev=.008)
# ---------------------------------------------------------------- poses: legs 5% shorter -> pelvis 4 cm lower
def pose(name,x=0.0,yaw=0.0):
  Y=Rz(yaw);o=Vector((x,0,0))
  def p(v):return o+Y@Vector(v)
  if name=='neutral':   # side-on low-ready carry: rifle across the body, muzzle forward-left and down
    return {'pelvis':(p((0,-.01,.96)),Y),'chest':Rx(.05),'feet':[(p((-.13,0,.09)),yaw+.12,0),(p((.13,.0,.09)),yaw-.12,0)],
            'gun':(p((-.12,-.2,1.02)),Y@Rz(-1.57+.95)@Ry(.42)),'head':Rx(-.05)}
  if name=='relaxed':
    return {'pelvis':(p((-.03,0,.935)),Y@Ry(.05)@Rz(.1)),'chest':Ry(-.06)@Rz(-.12)@Rx(.03),'feet':[(p((-.12,.02,.09)),yaw+.2,0),(p((.17,-.08,.09)),yaw-.25,0)],
            'gun':(p((-.1,-.21,1.0)),Y@Rz(-1.57+1.0)@Ry(.5)),'look':p((1.5,-3,1.2))}
  if name=='aim':
    Rb=Y@Rz(-.72);Rc=Rz(.24)@Rx(.12)
    C=o+Y@Vector((0,0,.88))+Rb@Rc@Vector((0,0,.3));pocket=C+Rb@Rc@Vector((-.13,-.14,.12))
    Rg=Y@Rz(-1.57)@Ry(.02);gp=pocket-Rg@Vector((-.32,0,.06))
    return {'pelvis':(p((0,0,.88)),Rb),'chest':Rc,'feet':[(p((-.17,.18,.09)),yaw-.6,0),(p((.14,-.22,.09)),yaw-.1,0)],'gun':(gp,Rg),'look':gp+Rg@Vector((3,0,.12))}
  if name=='jog':
    return {'pelvis':(p((0,0,.91)),Y@Rx(.12)@Rz(.08)),'chest':Rx(.1)@Rz(-.12),'feet':[(p((-.1,.28,.24)),yaw,-.9),(p((.11,-.28,.11)),yaw,.25)],
            'gun':(p((-.08,-.26,1.05)),Y@Rz(-1.57+.9)@Ry(.3)),'look':p((0,-4,1.0))}
  if name=='shoulder':  # launcher ON the right shoulder: tube resting on the pauldron, eye at the sight
    Rb=Y@Rz(-.3);Rc=Rz(.2)@Rx(.05);C=o+Y@Vector((0,0,.91))+Rb@Rc@Vector((0,0,.3));sh=C+Rb@Rc@Vector((-.205,0,.13))
    Rg=Y@Rz(-1.57)@Ry(.03);gp=sh+Vector((0,0,.12))-Rg@Vector((0,0,.14))+Rg@Vector((.18,0,0))
    return {'pelvis':(p((0,0,.91)),Rb),'chest':Rc,'feet':[(p((-.16,.14,.09)),yaw-.4,0),(p((.14,-.18,.09)),yaw,0)],'gun':(gp,Rg),'look':gp+Rg@Vector((3,0,.14))}
