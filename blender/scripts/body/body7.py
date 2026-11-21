# Marine v2 BODY pass 2 (Keegan's notes): slimmer waist/hips, legs 5% shorter but thicker thighs/calves, slimmer pauldrons
# (nothing floating), detailed CE-style armour plates (layered thigh plates, ridged shin guards, capped knee guards, pec plates
# with a spine), sculpted fabric limbs (folds, calf, bloused trousers), full sleeves, muted pauldrons + bright army stripe,
# gear + bake details (straps, buckles, mag pouches, grenades, knife, stencils, rivets), chunkier weapons, a retro-futurist
# comms backpack, polished poses (side-on carry, head follows the aim, launcher on the shoulder).
import sys,os
src=open('/home/claude/body/body.py').read();exec(src.split('# ---------------------------------------------------------------- weapons')[0])
from mathutils.bvhtree import BVHTree
from mathutils import Quaternion
OLIVEP=M('olivepoly',(.08,.09,.05),.62);TUBE=steel('tube',(.2,.21,.2),0,.6);BRASS=M('brass2',(.45,.32,.12),.35,.9);LASER=M('laser',(1,.05,.03),.3,0,12);REDM=M('rocketred',(.55,.035,.025),.4,.1);RUB=rubber('pad',(.025,.025,.022));STRIPE=M('stripe',(.16,.62,.12),.55,.2);PACKM=steel('packsteel',(.075,.085,.055),0,.8);DIAL=M('dial',(.5,.45,.3),.3,.8);LAMP=M('lamp',(1,.55,.15),.4,0,6)
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
def weapon(kind,G,bip=('hang',0),laser=0.0):
  """pass 5 weapons, from Keegan's references (our own designs in those silhouettes; no copied markings or colour schemes).
  Local frame: x forward, z up, +y = the weapon's LEFT side, pistol grip at the origin."""
  O,F=G
  def B(c,s,mat,rot=None,bev=.004):put('gun',boxT(c,s,(O,F),rot),mat,bev=bev)
  def T(a,b,r,mat,NS=14,r2=None):put('gun',tube(O+F@Vector(a),O+F@Vector(b),r,r if r2 is None else r2,F@Vector((0,0,1)),NS=NS,NR=1 if r2 is None else 3),mat)
  def TW(a,b,r,mat,NS=10):put('gun',tube(a,b,r,r,F@Vector((0,0,1)),NS=NS,NR=1),mat)
  def H(pts,mat,bev=.004):put('gun',hullT(pts,(O,F)),mat,bev=bev,smooth=False)
  def sym(pts):return [(x,s*y,z) for x,y,z in pts for s in (1,-1)]
  def slots(x0,x1,n,z,h,y,w=.03,ang=0.0,mat=None):
    for k in range(n):
      x=x0+(x1-x0)*(k+.5)/n
      for s in (1,-1):B((x,s*y,z),(w,.004,h),mat or DARK,Matrix.Rotation(ang,3,'Y'),bev=.0015)
  def bipod(hx,hz,L=.42):
    for sy in (-1,1):
      top=O+F@Vector((hx,sy*.016,hz))
      if bip[0]=='ground':end=top.copy();end+=F@Vector((.1,sy*.14,0));end.z=bip[1]+.014
      elif bip[0]=='fold':end=O+F@Vector((hx-.32,sy*.04,hz-.05))
      else:end=top+Vector((0,0,-L))+F@Vector((-.06,sy*.06,0))
      TW(top,end,.012,GUN);TW(end-(end-top).normalized()*.13,end,.017,OLIVEP);put('gun',ell(end,(.024,.024,.013)),GUN)
    T((hx-.03,0,hz),(hx+.03,0,hz),.026,GUN)
  if kind=='rifle':
    # long slotted handguard, flat-top with flip-up sights, V-shaped lower with a forward-raked magwell, angled mag,
    # closed THUMBHOLE stock with a cheek riser. Gunmetal metal + olive polymer furniture.
    H(sym([(-.08,.03,.04),(.2,.03,.04),(-.08,.03,.105),(.2,.03,.105)]),GUN)                                      # upper receiver
    B((.25,0,.113),(.66,.026,.012),GUN,bev=.002)                                                                  # top rail
    H(sym([(.2,.036,.035),(.52,.036,.035),(.2,.036,.105),(.52,.036,.105)])+[(.2,0,.03),(.52,0,.03),(.2,0,.11),(.52,0,.11)],GUN)  # handguard
    slots(.23,.5,6,.07,.022,.0375,ang=.55)
    H(sym([(-.06,.028,.042),(.06,.028,.042),(.0,.028,.0),(-.05,.028,.0)]),GUN)                                   # lower / grip seat
    H(sym([(.06,.03,.042),(.19,.03,.042),(.175,.031,-.065),(.085,.031,-.065)]),GUN)                               # magwell (raked forward)
    H(sym([(.17,.024,-.05),(.21,.024,-.04),(.24,.024,.036),(.19,.024,.04)]),GUN)                                  # V brace up to the handguard
    B((.135,0,-.15),(.055,.03,.17),OLIVEP,Matrix.Rotation(-.22,3,'Y'),bev=.006);B((.155,0,-.24),(.065,.036,.02),OLIVEP,Matrix.Rotation(-.22,3,'Y'))
    B((.0,0,-.04),(.04,.034,.1),OLIVEP,Matrix.Rotation(-.28,3,'Y'),bev=.006);B((.05,0,-.025),(.06,.012,.008),GUN)  # grip + guard
    H(sym([(-.42,.024,.06),(-.06,.024,.06),(-.42,.024,.105),(-.06,.024,.105)]),OLIVEP)                            # stock top bar
    H(sym([(-.42,.022,-.08),(-.05,.022,-.08),(-.42,.022,-.05),(-.05,.022,-.06)]),OLIVEP)                          # stock bottom bar
    B((-.06,0,-.035),(.03,.04,.1),OLIVEP);B((-.43,0,.013),(.03,.05,.2),RUB,bev=.007)                               # front post (thumbhole), butt pad
    B((-.25,0,.113),(.2,.032,.02),DARK,bev=.005)   # cheek riser
    T((.52,0,.07),(.68,0,.07),.011,GUN);T((.66,0,.07),(.74,0,.07),.017,GUN)                                       # barrel + comp
    for x,h in ((.5,.035),(.0,.03)):H(sym([(x-.012,.012,.115),(x+.012,.012,.115)])+[(x,0,.119+h),(x-.004,0,.119+h)],DARK,bev=.002)   # flip-up sights
    B((.27,.04,.07),(.02,.006,.02),OLIVEP)                                                                        # sling loop
  elif kind=='sniper':
    # BULLPUP anti-materiel: slab body with windowed sides and a thumbhole, mag behind the grip, long slotted handguard,
    # fluted barrel + brake, big scope on rings, folding carry handle, LARGE hanging bipod
    H(sym([(-.46,.035,-.06),(-.1,.035,-.06),(-.46,.035,.12),(.3,.035,.12),(.3,.035,.02),(.04,.035,.02)]),GUN)       # body
    slots(-.38,.22,5,.085,.022,.036,w=.075)                                                                       # windows
    B((-.03,0,-.07),(.13,.04,.03),GUN);B((.0,0,-.035),(.04,.036,.09),OLIVEP,Matrix.Rotation(-.15,3,'Y'))         # thumbhole rim + grip
    H(sym([(.02,.006,-.065),(.1,.006,-.065),(.1,.006,.03),(.09,.006,.03),(.02,.006,-.05)]),GUN,bev=.002)
    B((-.2,0,-.13),(.1,.034,.15),OLIVEP,bev=.006)                                                                 # mag (behind the grip)
    B((-.47,0,.03),(.03,.06,.19),RUB,bev=.007);B((-.3,0,.13),(.22,.034,.02),DARK,bev=.005)                        # pad, cheek
    B((.4,0,.133),(1.0,.026,.012),GUN,bev=.002)                                                                   # long top rail
    H(sym([(.3,.034,.035),(.78,.034,.035),(.3,.034,.115),(.78,.034,.115)]),GUN);slots(.34,.74,7,.075,.03,.0355,w=.04)
    T((.78,0,.075),(1.24,0,.075),.017,GUN,16)
    for k in range(6):a2=k/6*6.283;put('gun',boxT((1.0,.017*math.cos(a2),.075+.017*math.sin(a2)),(.4,.006,.006),(O,F),Matrix.Rotation(a2,3,'X')),GUNP,bev=.002)
    H(sym([(1.22,.034,.04),(1.33,.034,.04),(1.22,.034,.11),(1.33,.034,.11)]),GUN)
    for x in (1.255,1.29):B((x,0,.075),(.014,.072,.042),DARK,bev=.002)
    T((-.1,0,.215),(.32,0,.215),.03,GUN,18);T((.3,0,.215),(.42,0,.215),.046,GUN,18,.046);T((.42,0,.215),(.5,0,.215),.044,GUNP,18);T((-.17,0,.215),(-.08,0,.215),.038,GUN,18)
    T((.1,0,.24),(.1,0,.27),.019,DIAL,12);T((.1,-.025,.215),(.1,-.055,.215),.019,DIAL,12)
    for x in (-.02,.22):B((x,0,.165),(.03,.05,.06),GUN)                                                           # rings
    H(sym([(.56,.012,.14),(.68,.012,.14),(.56,.012,.155),(.68,.012,.155)]),GUN);B((.56,0,.146),(.012,.02,.025),GUN);B((.68,0,.146),(.012,.02,.025),GUN)   # carry handle
    bipod(.72,.04,.44)
  elif kind=='mg':
    # MG42-inspired: boxy receiver, long top cover, perforated barrel shroud with the barrel-change opening, conical muzzle
    # booster, straight-line thumbhole stock, big angular SIDE BOX MAGAZINE on the left with a short belt, LARGE hanging bipod
    H(sym([(-.08,.045,-.005),(.33,.045,-.005),(-.08,.045,.13),(.33,.045,.13)]),GUN)
    H(sym([(.0,.04,.13),(.31,.04,.13),(.02,.03,.165),(.29,.03,.165)]),OLIVEP);B((-.03,0,.145),(.06,.04,.04),GUN)     # top cover + rear sight block
    H(sym([(-.44,.03,.03),(-.08,.03,.03),(-.44,.03,.12),(-.08,.03,.12)]),OLIVEP)                                  # straight-line stock
    H(sym([(-.44,.026,-.09),(-.05,.026,-.09),(-.44,.026,-.06),(-.05,.026,-.065)]),OLIVEP);B((-.45,0,.015),(.03,.06,.22),RUB,bev=.007)
    B((.0,0,-.04),(.045,.036,.1),OLIVEP,Matrix.Rotation(-.22,3,'Y'),bev=.006);H(sym([(.02,.006,-.06),(.1,.006,-.06),(.1,.006,.0),(.09,.006,.0)]),GUN,bev=.002)
    H([(x,y,z) for x in (.33,.86) for y in (-.034,.034) for z in (.02,.12)]+[(x,0,z) for x in (.33,.86) for z in (.015,.125)],GUN)   # shroud
    for k in range(8):
      x=.37+k*.058
      for s in (1,-1):B((x,s*.0345,.07),(.034,.004,.022),DARK,bev=.0015)
      B((x,0,.1225),(.034,.016,.004),DARK,bev=.0015)
    B((.45,-.0352,.04),(.2,.004,.02),DARK)                                                                         # barrel-change opening
    B((.32,-.048,.07),(.03,.012,.05),GUN,bev=.003)                                                                 # change latch (right)
    T((.86,0,.07),(.97,0,.07),.03,GUN,16,.02);B((.82,0,.14),(.012,.012,.04),DARK);T((.9,0,.07),(.99,0,.07),.012,DARK)
    H([(x,y,z) for x in (.04,.24) for y in (.038,.17) for z in (-.17,.05)]+[(.04,.17,-.12),(.24,.17,-.12)],OLIVEP,bev=.008)   # side box mag
    B((.14,.172,-.06),(.14,.004,.12),DARK);B((.14,.175,-.06),(.06,.003,.02),STEN)
    for k in range(5):T((.07+k*.035,.045,.075),(.07+k*.035,.06,.075),.009,BRASS,8)                                # short belt into the feed
    bipod(.8,.03,.44)
  elif kind=='rocket':
    # long tube with a slim parallel upper tube, chunky centre module with a ribbed bronze band, front grip, pistol grip with
    # a guard and a bent stock arm, flared rear venturi, RED warhead tip, red laser-guide emitter (+ beam when aiming)
    T((-.55,0,.14),(.66,0,.14),.052,TUBE,18);T((-.5,0,.215),(.6,0,.215),.02,TUBE,12)
    for x in (-.45,.55):B((x,0,.18),(.03,.03,.05),GUN)
    T((.62,0,.14),(.71,0,.14),.06,GUN,18);T((-.56,0,.14),(-.7,0,.14),.058,GUN,18,.09)                             # front cap, flared venturi
    T((-.06,0,.14),(.24,0,.14),.082,GUN,20)
    for k in range(6):T((.0+k*.035,0,.14),(.018+k*.035,0,.14),.087,BRASS,20)                                       # ribbed band
    T((.71,0,.14),(.84,0,.14),.045,REDM,18,.005)                                                                   # red tip
    B((.34,0,.04),(.04,.034,.11),GUNP,Matrix.Rotation(.12,3,'Y'),bev=.006)                                        # front grip
    B((.0,0,.03),(.04,.034,.11),GUNP,Matrix.Rotation(-.2,3,'Y'),bev=.006);B((.06,0,.0),(.07,.012,.008),GUN)        # pistol grip + guard
    H(sym([(.015,.014,-.02),(.0,.014,.01),(-.06,.014,-.04),(-.3,.014,.0),(-.3,.014,.03)]),GUN);H(sym([(-.3,.014,.0),(-.33,.014,.0),(-.36,.014,.09),(-.32,.014,.09)]),GUN)   # stock arm
    B((.2,-.07,.14),(.05,.03,.035),GUN);put('gun',ell(O+F@Vector((.226,-.07,.14)),(.006,.008,.008)),LASER)          # laser emitter
    if laser>0:TW(O+F@Vector((.23,-.07,.14)),O+F@Vector((.23+laser,-.07,.14)),.0022,LASER,6)
# ---------------------------------------------------------------- the marine
LEG=(.43,.42);ARML=(.345,.325)
def marine(P,head='rifle',seed=0,gear='std',weap='rifle',lens=None,team=(.16,.62,.12)):
  print('\nMARINE',seed,weap,end='')
  r=random.Random(seed);Pp,Rp=Vector(P['pelvis'][0]),P['pelvis'][1];FP=(Pp,Rp)
  Rc=Rp@P.get('chest',Matrix.Identity(3));Cc=Pp+Rp@Vector((0,0,.3));FC=(Cc,Rc);made=[];bodyobs=[]
  def W(Fm,p):return Fm[0]+Fm[1]@Vector(p)
  SIDE=[-1]
  def pb(name,bm,mat,**k):o=put(name,bm,mat,**k);o['side']=SIDE[0];made.append(o);bodyobs.append(o);return o
  def pg(name,bm,mat,**k):o=put(name,bm,mat,**k);o['side']=SIDE[0];made.append(o);return o
  # torso: slimmer waist and hips, the same broad chest
  rings=[(FP,-.1,.148,.105),(FP,-.02,.142,.1),(FP,.06,.13,.094),(FC,-.16,.128,.092),(FC,-.08,.16,.112),(FC,0,.178,.13),(FC,.09,.192,.135),(FC,.15,.19,.125),(FC,.2,.1,.085),(FC,.24,.065,.065)]
  bm=bmesh.new();RR=[];NS=28
  for Fm,z,w,d in rings:RR.append([bm.verts.new(W(Fm,(w*math.copysign(abs(math.cos(a))**.8,math.cos(a)),d*math.copysign(abs(math.sin(a))**.8,math.sin(a)),z))) for a in [k/NS*2*math.pi for k in range(NS)]])
  for j in range(len(RR)-1):
    for k in range(NS):bm.faces.new((RR[j][k],RR[j][(k+1)%NS],RR[j+1][(k+1)%NS],RR[j+1][k]))
  for ring,e in ((RR[0],W(FP,(0,0,-.13))),(RR[-1],W(FC,(0,0,.25)))):cv=bm.verts.new(e);[bm.faces.new((ring[k],ring[(k+1)%NS],cv)) for k in range(NS)]
  bmesh.ops.recalc_face_normals(bm,faces=bm.faces);pb('torso',bm,CAMO)
  # chest: pec plates either side of a raised spine plate, two abdominal lames, back plate, collar, side straps
  for sx in (1,-1):
    pb('pec',hullT([(sx*.018,-.172,.0),(sx*.02,-.165,.14),(sx*.045,-.145,.195),(sx*.095,-.15,.17),(sx*.115,-.142,.12),(sx*.15,-.136,.01),(sx*.11,-.158,-.05),(sx*.025,-.17,-.05),(sx*.12,-.1,.13),(sx*.135,-.1,-.02),(sx*.03,-.08,.15)],FC),ARM,bev=.006,smooth=False)
    pb('pecEdge',hullT([(sx*.122,-.145,.115),(sx*.14,-.136,.1),(sx*.155,-.138,.012),(sx*.142,-.145,.012),(sx*.135,-.11,.11),(sx*.142,-.115,.01)],FC),TEAMM,bev=.003,smooth=False)
  pb('spine',hullT([(sx*.025,y,z) for sx in (1,-1) for y,z in ((-.183,-.04),(-.178,.12),(-.16,.17),(-.16,-.05))]+[(0,-.19,.05)],FC),ARM,bev=.004,smooth=False)
  for k,(z0,z1,w) in enumerate(((-.075,-.125,.162),(-.13,-.18,.148))):
    pb('lame',hullT([(sx*w,-.122,z0) for sx in (1,-1)]+[(sx*w*.95,-.118,z1) for sx in (1,-1)]+[(sx*w*.55,-.16,z0) for sx in (1,-1)]+[(sx*w*.5,-.154,z1) for sx in (1,-1)]+[(sx*w,-.03,z0) for sx in (1,-1)]+[(sx*w*.95,-.03,z1) for sx in (1,-1)],FC),ARM,bev=.005,smooth=False)
  bk=[(sx*x,y,z) for sx in (1,-1) for x,y,z in [(.165,.12,.13),(.16,.13,.0),(.14,.12,-.13),(.06,.145,-.12),(.07,.15,.12),(.03,.115,.19),(.15,.08,.14)]]+[(0,.03,.1)]
  pb('chestB',hullT(bk,FC),ARM,bev=.006,smooth=False)
  for sx in (1,-1):pb('cumm',hullT([(sx*.13,y,z) for y in (-.09,.1) for z in (-.17,-.03)]+[(sx*.15,y,z) for y in (-.06,.07) for z in (-.15,-.05)],FC),WEB,bev=.008,smooth=False)
  for sx in (1,-1):
    pb('collar',hullT([(sx*.03,-.1,.17),(sx*.1,-.07,.17),(sx*.12,-.02,.2),(sx*.1,-.06,.26),(sx*.04,-.095,.25),(sx*.11,.0,.25),(sx*.06,.05,.18),(sx*.06,.06,.26)],FC),ARM,bev=.005,smooth=False)
    pg('strap',boxT((sx*.152,0,-.06),(.02,.2,.045),FC),WEB,bev=.006)
    pg('shStrap',hullT([(sx*.08,-.135,.17),(sx*.13,-.13,.17),(sx*.1,.0,.235),(sx*.15,.0,.225),(sx*.08,.125,.15),(sx*.13,.12,.15)],FC),WEB,bev=.004,smooth=False)
  pg('buckle',boxT((0,-.112,.0),(.04,.012,.028),FP),METL,bev=.003)
  # belt + pouches (double mags front, grenades and a dump pouch on the sides), groin plate with a centre ridge
  pb('belt',tube(W(FP,(0,0,-.05)),W(FP,(0,0,.02)),.152,.148,Rp@Vector((1,0,0)),flat=.72,NS=28,NR=2),WEB)
  for x in (-.11,-.05,.05,.11):
    if gear=='light' and abs(x)<.08:continue
    pg('mags',boxT((x,-.172+abs(x)*.2,-.16),(.05,.036,.07),FC,Rz(x*1.6)),POUCH,bev=.008)
    pg('flap',boxT((x,-.175+abs(x)*.2,-.123),(.052,.042,.012),FC,Rz(x*1.6)),POUCH,bev=.004)
  for sx in (1,-1):pg('pouchS',boxT((sx*.152,.035,-.01),(.05,.08,.075),FP),POUCH,bev=.008)
  for k in range(2):
    c=W(FP,(.13+k*.03,.085+k*.02,-.01));pg('nade',ell(c,(.026,.026,.032)),GUNP);pg('fuze',boxT((.13+k*.03,.085+k*.02,.02),(.014,.014,.022),FP),METL,bev=.003)
  pg('canteen',boxT((-.08,.125,-.04),(.08,.05,.1),FP),POUCH,bev=.015)
  gk=P.get('groinK',0)   # the groin flap swings forward when a thigh is raised (jog, carry)
  pb('groin',hullT([(-.045,-.118,-.05),(.045,-.118,-.05),(-.024,-.135-gk*.05,-.11+gk*.02),(.024,-.135-gk*.05,-.11+gk*.02),(0,-.145-gk*.06,-.125+gk*.025),(-.05,-.1,-.06),(.05,-.1,-.06),(0,-.12-gk*.06,-.125+gk*.025),(0,-.14,-.06)],FP),ARM,bev=.005,smooth=False)
  # knife on the left chest strap
  pg('sheath',boxT((-.02,.112,.0),(.16,.016,.034),FP,Matrix.Rotation(.12,3,'Y')),GUNP,bev=.004);pg('knife',boxT((-.13,.114,.008),(.07,.02,.022),FP,Matrix.Rotation(.12,3,'Y')),GUN,bev=.004)
  # legs: shorter, thicker thighs + calves, layered thigh plates, capped knee guards, ridged shin guards, bloused trousers
  pole=Rp@Vector((0,-1,0))
  for i,sx in enumerate((-1,1)):
    SIDE[0]=i;hipJ=W(FP,(sx*.098,0,-.06));FT=P['feet'][i];ank,yaw,toe=FT[:3];ank=Vector(ank)
    print('  L%d'%i,end='');kn,ank=ik(hipJ,ank,LEG[0],LEG[1],Vector(P['kpole'][i]) if P.get('kpole') else pole+Rp@Vector((sx*.12,0,0)))
    lr=Rp@Vector((1,0,0));fwd=(Rp@Vector((0,-1,0)))
    pb('thigh',tubeP(hipJ+(kn-hipJ).normalized()*.05,kn,lambda t:.085+.028*math.sin(min(1,t*2.2)*math.pi*.5)-.035*t+.008*math.sin(t*math.pi),lr,1.04,fold=.035,seed=seed*7+i),CAMO)
    pb('shin',tubeP(kn,ank+(kn-ank).normalized()*.075,lambda t:.074+.016*math.sin(min(1,t*1.5)*math.pi)-.012*t+.016*max(0,(t-.8)/.2)**2,lr,fold=.04,seed=seed*7+i+3,back=-fwd),CAMO)
    tdir=(kn-hipJ).normalized();tb=basis(tdir,lr);Ft=(hipJ,Matrix((tb[1],-tb[2],tb[0])).transposed())   # local -y = FRONT of the thigh
    pg('cargo',boxT((sx*.118,0,.22),(.032,.1,.12),Ft),POUCH,bev=.01)
    for k,(z0,z1) in enumerate(((.05,.2),(.17,.3))):
      pb('thighP',hullT([(sx*.015,-.124-k*.006,z0),(sx*.085,-.104,z0),(sx*.124,-.02,z0+.02),(sx*.015,-.13-k*.006,z1),(sx*.088,-.11,z1),(sx*.12,-.02,z1-.02),(sx*.065,-.13-k*.006,(z0+z1)/2),(sx*.01,-.08,z0),(sx*.01,-.08,z1)],Ft),ARM,bev=.005,smooth=False)
    sdir=(ank-kn).normalized();sb=basis(sdir,lr);Fs=(kn,Matrix((sb[1],-sb[2],sb[0])).transposed())   # local -y = FRONT of the shin
    pb('knee',hullT([(-.06,-.06,-.06),(.06,-.06,-.06),(-.055,-.1,.0),(.055,-.1,.0),(0,-.115,-.02),(-.05,-.07,.07),(.05,-.07,.07),(0,-.1,.06),(-.07,-.02,0),(.07,-.02,0)],Fs),ARM,bev=.006,smooth=False)
    pg('kneeCap',hullT([(-.03,-.11,-.035),(.03,-.11,-.035),(-.025,-.122,.0),(.025,-.122,.0),(0,-.128,-.015),(-.03,-.1,.04),(.03,-.1,.04)],Fs),TEAMM,bev=.004,smooth=False)
    pb('kneeStrap',tube(W(Fs,(0,0,-.03)),W(Fs,(0,0,-.005)),.092,.092,Fs[1]@Vector((1,0,0)),NS=20,NR=1),WEB)
    pb('kneePad',ell(kn,(.075,.075,.075)),WEB)
    pb('shinG',hullT([(-.055,-.1,.09),(.055,-.1,.09),(0,-.118,.1),(-.058,-.094,.31),(.058,-.094,.31),(0,-.11,.31),(-.098,-.025,.2),(.098,-.025,.2),(-.092,-.03,.1),(.092,-.03,.1)],Fs),ARM,bev=.005,smooth=False)
    pg('shinR',hullT([(-.008,-.116,.11),(.008,-.116,.11),(-.008,-.108,.3),(.008,-.108,.3),(0,-.126,.2)],Fs),ARM,bev=.003,smooth=False)
    pb('shinStrap',tube(W(Fs,(0,0,.26)),W(Fs,(0,0,.282)),.1,.1,Fs[1]@Vector((1,0,0)),NS=20,NR=1),WEB)
    Fb=(ank,FT[3] if len(FT)>3 else Rz(yaw)@Rx(toe));up=Fb[1]@Vector((0,0,1))
    pb('boot',hullT([(s2*w,y,z) for s2 in (1,-1) for w,y,z in [(.055,.075,-.07),(.056,.082,.0),(.054,-.17,-.07),(.05,-.215,-.055),(.042,-.225,-.035),(.04,-.2,-.012),(.052,-.1,.015),(.054,-.04,.065),(.058,.05,.09),(.057,-.0,.1)]],Fb),BOOT,bev=.014,smooth=False)
    pb('shaft',tubeP(ank-up*.01,ank+up*.2,lambda t:.064+.006*t,Fb[1]@Vector((1,0,0)),fold=.02,seed=seed+i,NR=6),BOOT)
    pb('gaiter',tube(ank+up*.06,ank+up*.13,.07,.075,Fb[1]@Vector((1,0,0)),NS=20,NR=2),WEB)
    pb('toecap',hullT([(s2*w,y,z) for s2 in (1,-1) for w,y,z in [(.058,-.115,-.073),(.054,-.218,-.056),(.046,-.228,-.034),(.043,-.205,-.008),(.054,-.12,.004)]],Fb),ARM,bev=.006,smooth=False)
    pb('anklePl',hullT([(sx*.062,y,z) for y,z in ((-.03,.0),(.05,.0),(-.02,.11),(.045,.11))]+[(sx*.074,.01,.055)],Fb),ARM,bev=.004,smooth=False)
    pb('heel',hullT([(s2*w,y,z) for s2 in (1,-1) for w,y,z in [(.05,.08,-.072),(.054,.088,-.0),(.046,.06,-.072),(.04,.064,.03)]],Fb),ARM,bev=.005,smooth=False)
    pb('sole',boxT((0,-.06,-.083),(.124,.3,.022),Fb),SOLE,bev=.005)
    for k in range(6):pg('lug',boxT((0,.06-k*.048,-.097),(.11,.018,.008),Fb),SOLE,bev=.002)
    for k in range(5):o=bake_obj('lace',boxT((0,-.075+k*.022,.06+k*.012),(.06,.006,.004),Fb,Matrix.Rotation(.6,3,'X')),WEB,(0,0,0));made.append(o)
  # weapon + arms (full sleeves, bicep, elbow folds), vambraces, gloves
  gO,gR=Vector(P['gun'][0]),P['gun'][1];_b=set(bpy.data.objects);weapon(weap,(gO,gR),P.get('bipod',('hang',0)),P.get('laser',0.0));made.extend(o for o in set(bpy.data.objects)-_b)
  CT={'pistol':((-.035,0,-.03),(-.03,0,-.05)),'flag':((0,0,0),(.4,0,0)),'rifle':((-.03,0,-.035),(.455,0,-.02)),'sniper':((-.004,0,-.035),(.3,0,.02)),'mg':((-.02,0,-.04),(.42,0,.03)),'rocket':((-.005,0,.05),(.32,0,.06))}[weap]
  WO={'R':Vector((-.075,-.018,.025)),'L':Vector((-.07,.03,-.045))}
  if weap=='pistol':WO={'R':Vector((-.06,-.01,.0)),'L':Vector((-.04,.045,-.03))}
  if weap=='flag':WO={'R':Vector((-.07,.02,-.04)),'L':Vector((-.07,.02,-.04))}
  tg={'R':(gO+gR@Vector(CT[0]),gO+gR@(Vector(CT[0])+WO['R'])),'L':(gO+gR@Vector(CT[1]),gO+gR@(Vector(CT[1])+WO['L']))}
  if P.get('lhand'):tg['L']=(Vector(P['lhand'][0]),Vector(P['lhand'][1]))
  elif P.get('lstock')==2:tg['L']=(gO+gR@Vector((-.24,0,-.02)),gO+gR@Vector((-.2,.06,-.08)))   # support hand under the butt
  elif P.get('lstock'):tg['L']=(gO+gR@Vector((-.06,.055,.12)),gO+gR@Vector((-.11,.1,.13)))   # support hand clamps the left side of the receiver   # MG support hand on top of the stock
  for side,sx in (('R',-1),('L',1)):
    hand,wt=tg[side];SIDE[0]=10 if side=='R' else 11;lt=Rc.transposed()@(wt-FC[0]);pro=max(0,min(1,(-lt.y-.15)/.25))   # shoulder protracts as the hand reaches forward
    sh=W(FC,(sx*(.215-.035*pro),-.15*pro,.13+.015*pro))
    print('  A'+side,end='');el,wr=ik(sh,wt,ARML[0],ARML[1],Rc@Vector((sx*1.3,-.05,-1)))
    lr=(el-sh).cross(wr-el);lr=lr if lr.length>1e-4 else Rc@Vector((1,0,0))
    pb('uarm',tubeP(sh+(el-sh).normalized()*.045,el,lambda t:.07-.008*t+.012*math.sin(t*math.pi),lr,fold=.03,seed=seed*5+sx),CAMO)
    pb('farm',tubeP(el,wr,lambda t:.064-.016*t+.006*math.sin(t*math.pi)+.01*max(0,1-t*4),lr,fold=.035,seed=seed*5+sx+9),CAMO)
    pb('elbow',ell(el,(.064,.064,.064)),WEB)
    fd=(wr-el).normalized();fb=basis(fd,Rc@Vector((sx,0,0)));Ff=(el,Matrix((fb[1],fb[2],fb[0])).transposed())
    pb('vamb',hullT([(.04,-.06,.06),(.084,-.0,.06),(.04,.06,.06),(.058,-.045,.24),(.076,0,.24),(.058,.045,.24),(.055,-.06,.15),(.055,.06,.15),(.0,-.072,.08),(.0,.072,.08)],Ff),ARM,bev=.004,smooth=False)
    hd=(hand-wr);hd=hd.normalized() if hd.length>.01 else fd;hb=basis(hd,gR@Vector((0,sx,0)));Fh=(wr,Matrix((hb[1],hb[2],hb[0])).transposed())
    pb('glove',hullT([(-.045,-.03,.0),(.045,-.03,.0),(-.045,.03,.0),(.045,.03,.0),(-.05,-.035,.09),(.05,-.035,.09),(-.045,.04,.1),(.045,.04,.1),(-.04,0,.13),(.04,0,.13)],Fh),GLOVE,bev=.012,smooth=False)
    pb('knuckle',hullT([(-.04,-.04,.06),(.04,-.04,.06),(-.035,-.048,.1),(.035,-.048,.1),(-.035,-.03,.1),(.035,-.03,.1)],Fh),ARM,bev=.004,smooth=False)
    # pauldron: slimmer, hugging the shoulder (inner edge sunk into the torso/arm so it never floats) + bright army stripe
    ud=(el-sh).normalized();qd=(Rc@Vector((0,0,-1))).rotation_difference(ud);qh=Quaternion().slerp(qd,.55)
    Fu=(sh,qh.to_matrix()@Rc@Matrix(((sx,0,0),(0,-1,0),(0,0,1))))
    pp=[(-.05,y,.075) for y in (-.075,.075)]+[(.03,y,.085) for y in (-.09,.09)]+[(.08,y,.035) for y in (-.095,.095)]+[(.1,y,-.05) for y in (-.09,.09)]+[(.09,y,-.105) for y in (-.075,.075)]+[(.04,0,.105),(.11,0,-.0),(.1,0,-.115)]+[(-.02,y,-.04) for y in (-.08,.08)]
    pb('paul',hullT(pp,Fu),TEAMM,bev=.008,smooth=False)
    pb('paul2',hullT([(.07,y,-.1) for y in (-.072,.072)]+[(.105,y,-.11) for y in (-.068,.068)]+[(.09,y,-.17) for y in (-.06,.06)]+[(.06,y,-.16) for y in (-.06,.06)]+[(.11,0,-.15)],Fu),TEAMM,bev=.005,smooth=False)
    stM=M('stripe%d'%seed,team,.5,.15)
    pg('stripe',hullT([(.096,y,-.035) for y in (-.092,.092)]+[(.104,y,-.06) for y in (-.09,.09)]+[(.1,y,-.05) for y in (-.091,.091)]+[(.093,y,-.04) for y in (-.09,.09)],Fu),stM,bev=.002,smooth=False)
    pg('paulS',boxT((.02,0,.09),(.03,.15,.012),Fu,Matrix.Rotation(.4,3,'Y')),WEB,bev=.003)
  SIDE[0]=-1
  # back gear
  if gear in('std','ammo','rocket','radio'):
    pg('pack',boxT((0,.2,-.02),(.26,.13,.3),FC),POUCH,bev=.02);pg('packFlap',boxT((0,.27,.1),(.24,.012,.1),FC),POUCH,bev=.006)
    if gear=='ammo':pg('can',boxT((-.06,.29,-.05),(.14,.09,.18),FC),GUNP,bev=.008)
    if gear=='rocket':
      for x in (-.06,.08):pg('spare',tube(W(FC,(x,.29,-.25)),W(FC,(x,.29,.42)),.055,.055,NS=14,NR=1),GUNP);pg('spareCap',tube(W(FC,(x,.29,.42)),W(FC,(x,.29,.53)),.05,.006,NS=14,NR=4),REDM)
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
  elif head=='officer':officer_head((0,0,0),L0)
  elif head=='leader':variant(seed,(0,0,0),L0,{'scanner':True,'scancol':team})
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
  for k in range(4):pg('toggle',boxT((.153,.19+k*.03,-.15),(.012,.006,.02),FC,Matrix.Rotation(.4,3,'Y')),METL,bev=.002)
  for k in range(3):pg('lamp',ell(W((.142,.2+k*.04,.12)),(.006,.006,.006)),LAMP)
  for sx in (1,-1):
    pg('batt',tube(W((sx*.165,.2,-.2)),W((sx*.165,.2,.05)),.04,.04,FC[1]@Vector((0,1,0)),NS=14,NR=1),PACKM);pg('battCap',tube(W((sx*.165,.2,.05)),W((sx*.165,.2,.075)),.03,.03,FC[1]@Vector((0,1,0)),NS=12,NR=1),METL)
  pg('dish',tube(W((-.09,.3,.2)),W((-.09,.36,.26)),.07,.07,FC[1]@Vector((1,0,0)),NS=20,NR=1),PACKM);pg('dishHub',ell(W((-.09,.381,.281)),(.02,.02,.02)),GUN)
  pg('whip',tube(W((.1,.3,.2)),W((.16,.38,.95)),.0045,.003,NS=6,NR=1),GUN);pg('whipBase',tube(W((.1,.29,.18)),W((.1,.3,.24)),.014,.012,NS=10,NR=1),GUN)
  pg('blade',boxT((.0,.3,.22),(.01,.04,.12),FC),GUN,bev=.003)
  bm=bmesh.new();pr=None
  for k in range(40):
    t=k/39;c=W((-.14+.02*t,.16-.3*t,-.0+.15*t))+FC[1]@Vector((.012*math.cos(t*60),0,.012*math.sin(t*60)))
    ring=[bm.verts.new(c+FC[1]@Vector((.004*math.cos(a),.004*math.sin(a),0))) for a in [i/6*2*math.pi for i in range(6)]]
    if pr:[bm.faces.new((pr[i],pr[(i+1)%6],ring[(i+1)%6],ring[i])) for i in range(6)]
    pr=ring
  pg('cord',bm,GUN);pg('handset',boxT((-.12,-.15,.17),(.035,.03,.12),FC,Matrix.Rotation(.3,3,'Y')),PACKM,bev=.008)
# ---------------------------------------------------------------- poses (pass 3)
def footR(toe,up):
  yv=-toe.normalized();zv=(up-yv*up.dot(yv)).normalized();xv=yv.cross(zv);return Matrix((xv,yv,zv)).transposed()
BUTT={'rifle':Vector((-.44,0,.03)),'sniper':Vector((-.48,0,.04)),'mg':Vector((-.465,0,.04)),'rocket':Vector((-.34,0,.14))}
def pose(name,x=0.0,yaw=0.0,kind='rifle'):
  Y=Rz(yaw);o=Vector((x,0,0))
  def p(v):return o+Y@Vector(v)
  def frames(pp,Rb,Rc):C=pp+Rb@Vector((0,0,.3));return C,Rb@Rc
  def shoulder_gun(pp,Rb,Rc,Rg,px=-.12):     # butt in the right shoulder pocket
    C,Rt=frames(pp,Rb,Rc);pocket=C+Rt@Vector((px,-.215-(.025 if kind=='sniper' else 0),.12));return pocket-Rg@BUTT[kind]
  def lowready(pp,Rb,Rc,pitch,yo):
    C,Rt=frames(pp,Rb,Rc);Rg=Rt@Rz(-1.57+yo)@Ry(pitch);return (shoulder_gun(pp,Rb,Rc,Rg),Rg)
  if name=='neutral':      # LOW READY: stock in the shoulder pocket, muzzle ~40 deg down in front, elbows in
    pp=p((0,-.01,.985));Rb=Y@Rz(.1);Rc=Rz(-.32)@Rx(.05)
    return {'pelvis':(pp,Rb),'chest':Rc,'feet':[(p((-.135,.01,.1)),yaw+.22,0),(p((.135,-.03,.1)),yaw-.22,0)],'gun':lowready(pp,Rb,Rc,.42 if kind=='sniper' else .56,.45),'look':p((0,-3,.9))}
  if name=='split':        # staggered firing stance: left foot forward, knees bent, weight forward, torso squared, level aim
    pp=p((.02,.0,.87));Rb=Y@Rz(-.4);Rc=Rz(-.14)@Rx(.17)
    C,Rt=frames(pp,Rb,Rc);Rg=Y@Rz(-1.57+.02)@Ry(.03);gp=shoulder_gun(pp,Rb,Rc,Rg)
    return {'pelvis':(pp,Rb),'chest':Rc,'feet':[(p((-.16,.22,.1)),yaw-.45,0),(p((.13,-.24,.1)),yaw-.08,0)],'gun':(gp,Rg),'look':gp+Rg@Vector((4,0,.15))}
  if name=='wide':         # wide at-ease idle: feet apart, weight on one hip, rifle low, head turned
    pp=p((-.05,.0,.93));Rb=Y@Ry(.06)@Rz(.14);Rc=Ry(-.08)@Rz(-.42)@Rx(.02)
    return {'pelvis':(pp,Rb),'chest':Rc,'feet':[(p((-.25,.03,.1)),yaw+.3,0),(p((.25,-.04,.1)),yaw-.3,0)],'gun':lowready(pp,Rb,Rc,.85,.5),'look':p((2.5,-2.5,1.3))}
  if name=='jog':          # low-ready jog
    pp=p((0,0,.91));Rb=Y@Rx(.14)@Rz(.08);Rc=Rx(.06)@Rz(-.34)
    return {'pelvis':(pp,Rb),'chest':Rc,'groinK':1,'feet':[(p((-.1,.28,.23)),yaw,.75),(p((.13,-.24,.15)),yaw,-.2)],'gun':lowready(pp,Rb,Rc,.6,.45),'look':p((0,-4,1.0))}
  if name=='shoulder':     # launcher resting ON the right pauldron, eye beside the tube at the sight
    pp=p((0,0,.91));Rb=Y@Rz(-.2);Rc=Rz(.12)@Rx(.06);C,Rt=frames(pp,Rb,Rc);sh=C+Rt@Vector((-.205,0,.13))
    top=sh+Rt@Vector((-.04,0,.105))+Rt@Vector((0,0,.15));Rg=Y@Rz(-1.57)@Ry(.04);gp=top-Rg@BUTT['rocket']
    return {'pelvis':(pp,Rb),'chest':Rc,'feet':[(p((-.16,.18,.1)),yaw-.45,0),(p((.13,-.2,.1)),yaw-.05,0)],'gun':(gp,Rg),'laser':4.0,'look':gp+Rg@Vector((4,.0,.2))}
  if name=='prone':        # MG prone on the deployed bipod, propped on the elbows, legs splayed, toes dug in
    pp=p((0,.32,.295));Rb=Y@Rx(1.42);Rc=Rx(-.45);Rg=Y@Rz(-1.57)@Ry(.0);gp=shoulder_gun(pp,Rb,Rc,Rg,-.075)
    return {'pelvis':(pp,Rb),'chest':Rc,'feet':[(p((-.3,1.22,.16)),0,0,footR(Y@Vector((-.8,.2,-.5)),Y@Vector((0,-1,.2)))),(p((.3,1.22,.16)),0,0,footR(Y@Vector((.8,.2,-.5)),Y@Vector((0,-1,.2))))],'kpole':[Y@Vector((-.3,0,-1)),Y@Vector((.3,0,-1))],
            'gun':(gp,Rg),'bipod':('ground',0.0),'lstock':1,'look':gp+Rg@Vector((4,0,.1))}
  if name=='cover':        # MG kneeling behind sandbags, bipod planted on top of the cover
    pp=p((0,.12,.615));Rb=Y@Rz(-.12);Rc=Rx(.32)@Rz(.08);Rg=Y@Rz(-1.57)@Ry(.02);gp=shoulder_gun(pp,Rb,Rc,Rg,-.095)
    return {'pelvis':(pp,Rb),'chest':Rc,'feet':[(p((-.125,.52,.22)),yaw+.1,1.75),(p((.17,-.2,.1)),yaw-.1,0)],'kpole':[Y@Vector((0,-.05,-1)),Y@Vector((.3,-1,.2))],
            'gun':(gp,Rg),'bipod':('ground',COVER_H),'lstock':2,'look':gp+Rg@Vector((4,0,.1))}
  if name=='carry':        # MG carried on the move: heavy, two-handed across the chest, bipod legs hanging
    pp=p((0,0,.92));Rb=Y@Rx(.1)@Rz(.06);Rc=Rx(.04)@Rz(-.08);C,Rt=frames(pp,Rb,Rc);Rg=Rt@Rz(-1.57+.9)@Ry(.2)
    gp=C+Rt@Vector((-.1,-.32,-.17))
    return {'pelvis':(pp,Rb),'chest':Rc,'feet':[(p((-.11,.22,.21)),yaw,.7),(p((.12,-.22,.12)),yaw,-.15)],'gun':(gp,Rg),'look':p((0,-4,1.0))}
COVER_H=.8

# ---------------------------------------------------------------- pass 6: detailed weapons for the pistol and the colours
exec(open('/home/claude/wpn/weapons6.py').read())
_weapon_old=weapon
def weapon(kind,G,bip=('hang',0),laser=0.0):
  return build_weapon(kind,G,bip,laser)   # (pass 7) every role carries the detailed weapons
  return _weapon_old(kind,G,bip,laser)
BUTT['pistol']=Vector((-.07,0,0));BUTT['flag']=Vector((0,0,0))
BUTT.update({'rifle':Vector((-.356,0,.0)),'sniper':Vector((-.49,0,.02)),'mg':Vector((-.47,0,.034))})
_pose_old=pose
def pose(name,x=0.0,yaw=0.0,kind='rifle'):
  Y=Rz(yaw);o=Vector((x,0,0))
  def p(v):return o+Y@Vector(v)
  if name=='officer':   # a dignified late-1800s officer: upright, chest out, chin up, heels near together with toes turned
    # out, pistol held one-handed low at his side pointing ahead and down, left hand resting in the small of his back
    pp=p((0,0,.995));Rb=Y@Rz(-.12);Rc=Rx(-.07)@Rz(.04);C=pp+Rb@Vector((0,0,.3));Rt=Rb@Rc
    Rg=Rt@Rz(-1.57+.05)@Ry(.85);gp=C+Rt@Vector((-.3,-.12,-.4))
    lh=C+Rt@Vector((.02,.17,-.27));lw=C+Rt@Vector((.12,.19,-.24))
    return {'pelvis':(pp,Rb),'chest':Rc,'feet':[(p((-.115,.05,.1)),yaw+.42,0),(p((.13,-.08,.1)),yaw-.45,0)],'gun':(gp,Rg),'lhand':(lh,lw),'look':p((1.2,-4,1.9))}
  if name=='colours':   # the bearer: staff upright in front of the right shoulder, left hand low, right hand high
    pp=p((0,0,.985));Rb=Y;Rc=Rx(.03);C=pp+Rb@Vector((0,0,.3));Rt=Rb@Rc
    Rg=Y@Rx(.12)@Ry(-math.pi/2);gp=C+Rt@Vector((-.15,-.38,-.18))
    return {'pelvis':(pp,Rb),'chest':Rc,'feet':[(p((-.135,.01,.1)),yaw+.22,0),(p((.135,-.03,.1)),yaw-.22,0)],'gun':(gp,Rg),'look':p((0,-4,1.5))}
  return _pose_old(name,x,yaw,kind)
