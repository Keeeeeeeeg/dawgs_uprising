# Marine v2 BODY concept (Keegan, 2026-11-18): Halo CE marine reference for proportions/stance, OUR design.
# Chunkier RTS read (shoulders, hands, boots ~15% over life), HEAVIER armour (chest plate + collar, team pauldrons, forearm
# guards, thigh plates, groin plate, knee + shin guards), woodland-style camo fatigues. Real metres, z up, character faces -y,
# his RIGHT is -x. Built per pose from joint positions (2-bone IK for arms/legs), heads from heads/h15var.py.
import sys,os
exec(open('/home/claude/hm/h15var.py').read())
from mathutils import Euler
# ---------------------------------------------------------------- materials
def camo(name):
  m=M(name,(.1,.1,.06),.88);nt=m.node_tree;N=nt.nodes;Lk=nt.links;b=N['Principled BSDF'];tc=N.new('ShaderNodeTexCoord')
  def ramp(sc,cols,det=2.0,dist=0.0):
    n=N.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=sc;n.inputs['Detail'].default_value=det;n.inputs['Distortion'].default_value=dist;Lk.new(tc.outputs['Object'],n.inputs['Vector'])
    r=N.new('ShaderNodeValToRGB');r.color_ramp.interpolation='CONSTANT';E=r.color_ramp.elements
    E[0].position=0;E[0].color=cols[0][1]+(1,);E[1].position=cols[1][0];E[1].color=cols[1][1]+(1,)
    for p,c in cols[2:]:e=E.new(p);e.color=c+(1,)
    Lk.new(n.outputs['Fac'],r.inputs[0]);return r
  base=ramp(6.5,[(0,(.115,.085,.05)),(.44,(.15,.165,.085)),(.58,(.22,.2,.125))],2.5,.6)   # brown / olive / tan blotches
  blk=ramp(11,[(0,(0,0,0)),(.62,(1,1,1))],2,1.2)                                           # black branch streaks
  mx=N.new('ShaderNodeMix');mx.data_type='RGBA';mx.inputs['B'].default_value=(.025,.028,.02,1);Lk.new(base.outputs['Color'],mx.inputs['A']);Lk.new(blk.outputs['Color'],mx.inputs['Factor'])
  ao=N.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.04;g=N.new('ShaderNodeMix');g.data_type='RGBA';g.inputs['B'].default_value=(.02,.018,.014,1)
  inv=N.new('ShaderNodeMath');inv.operation='SUBTRACT';inv.inputs[0].default_value=1;Lk.new(ao.outputs['AO'],inv.inputs[1]);Lk.new(mx.outputs['Result'],g.inputs['A']);Lk.new(inv.outputs[0],g.inputs['Factor'])
  Lk.new(g.outputs['Result'],b.inputs['Base Color'])
  w=N.new('ShaderNodeTexWave');w.inputs['Scale'].default_value=600;w.inputs['Distortion'].default_value=3;Lk.new(tc.outputs['Object'],w.inputs['Vector'])
  wr=N.new('ShaderNodeTexNoise');wr.inputs['Scale'].default_value=40;wr.inputs['Detail'].default_value=3;Lk.new(tc.outputs['Object'],wr.inputs['Vector'])
  ad=N.new('ShaderNodeMath');ad.operation='MULTIPLY_ADD';ad.inputs[1].default_value=.3;Lk.new(w.outputs['Fac'],ad.inputs[0]);Lk.new(wr.outputs['Fac'],ad.inputs[2])
  bu=N.new('ShaderNodeBump');bu.inputs['Strength'].default_value=.45;bu.inputs['Distance'].default_value=.003;Lk.new(ad.outputs[0],bu.inputs['Height']);Lk.new(bu.outputs['Normal'],b.inputs['Normal'])
  return m
CAMO=camo('camo');ARM=steel('armour',(.085,.092,.075),0,.9);TEAMM=steel('team',(.07,.12,.05),0,.7)
GLOVE=rubber('glove',(.028,.028,.024));BOOT=rubber('boot',(.035,.03,.025));WEB=cloth('webbing',(.075,.078,.05),500);POUCH=cloth('pouch',(.095,.095,.06),380)
GUN=M('gun',(.022,.022,.022),.38,.55);GUNP=M('gunpoly',(.055,.06,.05),.6);SOLE=M('sole',(.015,.015,.015),.9)
FLOOR=M('floor',(.045,.048,.042),.95)
# ---------------------------------------------------------------- geometry helpers (world coords)
def put(name,bm,mat,bev=0,smooth=True,segs=2,coll=None):
  o=link(name,bm,mat,bev=bev,smooth=smooth,segs=segs);return o
def basis(ax,ref):
  ax=ax.normalized();u=ref-ax*ref.dot(ax)
  if u.length<1e-4:u=Vector((1,0,0))-ax*ax.x
  u.normalize();return ax,u,ax.cross(u)
def tube(a,b,r1,r2,ref=Vector((1,0,0)),flat=1.0,bul=0.0,NS=18,NR=10,caps=True):
  a,b=Vector(a),Vector(b);ax,u,v=basis(b-a,ref);L=(b-a).length;bm=bmesh.new();R=[]
  for j in range(NR+1):
    t=j/NR;r=r1+(r2-r1)*t+bul*math.sin(t*math.pi);c=a+ax*L*t
    R.append([bm.verts.new(c+u*r*math.cos(k/NS*2*math.pi)+v*r*flat*math.sin(k/NS*2*math.pi)) for k in range(NS)])
  for j in range(NR):
    for k in range(NS):bm.faces.new((R[j][k],R[j][(k+1)%NS],R[j+1][(k+1)%NS],R[j+1][k]))
  if caps:
    for ring,e,s in ((R[0],a-ax*r1*.6,-1),(R[-1],b+ax*r2*.6,1)):
      cv=bm.verts.new(e);[bm.faces.new((ring[k],ring[(k+1)%NS],cv)) for k in range(NS)]
  bmesh.ops.recalc_face_normals(bm,faces=bm.faces);return bm
def ell(c,r,R=None,seg=20,rings=12):
  bm=bmesh.new();bmesh.ops.create_uvsphere(bm,u_segments=seg,v_segments=rings,radius=1);Mx=Matrix.Diagonal((r[0],r[1],r[2],1))
  if R:Mx=R.to_4x4()@Mx
  bmesh.ops.transform(bm,matrix=Matrix.Translation(Vector(c))@Mx,verts=bm.verts);return bm
def hullT(pts,Fm):   # convex hull of frame-local points
  return hull([Fm[0]+Fm[1]@Vector(p) for p in pts])
def boxT(c,s,Fm,rot=None):
  bm=box((0,0,0),s,rot);bmesh.ops.transform(bm,matrix=Matrix.Translation(Fm[0]+Fm[1]@Vector(c))@Fm[1].to_4x4(),verts=bm.verts);return bm
def ik(a,t,l1,l2,pole):
  d=t-a;L=min(d.length,l1+l2-1e-4);dn=d.normalized();x=(l1*l1-l2*l2+L*L)/(2*L);h=math.sqrt(max(0,l1*l1-x*x))
  p=pole-dn*pole.dot(dn);p.normalize()
  print(' short %.3f'%(d.length-l1-l2) if d.length>l1+l2 else ' ok')
  return a+dn*x+p*h,a+dn*L
def Rz(a):return Matrix.Rotation(a,3,'Z')
def Rx(a):return Matrix.Rotation(a,3,'X')
def Ry(a):return Matrix.Rotation(a,3,'Y')
# ---------------------------------------------------------------- weapons (local: x forward, z up, grip at origin)
def weapon(kind,G):
  O,F=G;bms=[]
  def B(c,s,mat,rot=None,bev=.004):bms.append((boxT(c,s,(O,F),rot),mat,bev))
  def T(a,b,r,mat):bms.append((tube(O+F@Vector(a),O+F@Vector(b),r,r,F@Vector((0,0,1)),NS=12,NR=1),mat,0))
  if kind in('rifle','sniper'):
    L=1.0 if kind=='rifle' else 1.35
    B((.07,0,.06),(.3,.05,.07),GUN);B((-.19,0,.04),(.24,.045,.09),GUNP);B((-.31,0,.03),(.03,.05,.12),GUN)
    B((.0,0,-.03),(.035,.03,.08),GUNP,Matrix.Rotation(-.25,3,'Y'));B((.13,0,-.03),(.04,.026,.12),GUN,Matrix.Rotation(.18,3,'Y'))
    B((.32,0,.055),(.2*L,.055,.06),GUNP);T((.3,0,.06),(.3+.42*L,0,.06),.011,GUN);B((.1,0,.11),(.12,.03,.035),GUN)
    if kind=='sniper':T((.02,0,.13),(.26,0,.13),.022,GUN);B((.14,0,.105),(.03,.025,.03),GUN)
    else:B((.1,0,.135),(.07,.035,.035),GUN)
  elif kind=='mg':
    B((.07,0,.06),(.36,.08,.1),GUN);B((-.22,0,.04),(.22,.05,.1),GUNP);B((.0,0,-.03),(.035,.03,.08),GUNP,Matrix.Rotation(-.25,3,'Y'))
    B((.12,.07,-.0),(.14,.09,.14),GUNP);T((.25,0,.07),(.85,0,.07),.017,GUN);B((.42,0,.07),(.22,.07,.07),GUNP);B((.12,0,.13),(.2,.06,.025),GUN)
  elif kind=='rocket':
    T((-.45,0,.12),(.65,0,.12),.055,GUNP);T((.6,0,.12),(.68,0,.12),.062,GUN);T((-.48,0,.12),(-.43,0,.12),.062,GUN)
    B((.0,0,.0),(.035,.03,.09),GUNP,Matrix.Rotation(-.2,3,'Y'));B((.2,0,.03),(.035,.03,.07),GUNP);B((.1,-.07,.15),(.1,.04,.05),GUN)
  for bm,mat,bev in bms:put('gun',bm,mat,bev=bev)
# ---------------------------------------------------------------- the marine
def marine(P,head='rifle',seed=0,gear='std',weap='rifle',lens=None):
  """P: pose dict. pelvis (pos, Rotation), chest Rotation (relative), head Rotation (relative), feet [(ankle,yaw,toe pitch)] x2,
  gun = (grip pos, Rotation) in world, hands = 'gun' targets computed from the weapon."""
  r=random.Random(seed);Pp,Rp=Vector(P['pelvis'][0]),P['pelvis'][1];FP=(Pp,Rp)
  Rc=Rp@P.get('chest',Matrix.Identity(3));Cc=Pp+Rp@Vector((0,0,.3));FC=(Cc,Rc)
  def W(Fm,p):return Fm[0]+Fm[1]@Vector(p)
  # torso: lofted superellipse rings from the pelvis frame to the chest frame (chunky shoulders)
  rings=[(FP,-.1,.165,.11),(FP,-.02,.16,.105),(FP,.06,.15,.1),(FC,-.16,.15,.1),(FC,-.08,.18,.12),(FC,0,.205,.13),(FC,.09,.23,.135),(FC,.15,.2,.125),(FC,.2,.1,.085),(FC,.24,.065,.065)]
  bm=bmesh.new();RR=[];NS=28
  for Fm,z,w,d in rings:
    RR.append([bm.verts.new(W(Fm,(w*math.copysign(abs(math.cos(a))**.8,math.cos(a)),d*math.copysign(abs(math.sin(a))**.8,math.sin(a)),z))) for a in [k/NS*2*math.pi for k in range(NS)]])
  for j in range(len(RR)-1):
    for k in range(NS):bm.faces.new((RR[j][k],RR[j][(k+1)%NS],RR[j+1][(k+1)%NS],RR[j+1][k]))
  for ring,e in ((RR[0],W(FP,(0,0,-.13))),(RR[-1],W(FC,(0,0,.25)))):cv=bm.verts.new(e);[bm.faces.new((ring[k],ring[(k+1)%NS],cv)) for k in range(NS)]
  bmesh.ops.recalc_face_normals(bm,faces=bm.faces);put('torso',bm,CAMO)
  # chest plate (front + back), raised angular collar, side straps
  for sx in (1,-1):
    put('pec',hullT([(sx*.005,-.172,.0),(sx*.01,-.165,.14),(sx*.04,-.14,.19),(sx*.15,-.13,.16),(sx*.215,-.08,.12),(sx*.21,-.1,-.01),(sx*.12,-.15,-.05),(sx*.02,-.17,-.05),(sx*.2,-.02,.13),(sx*.18,-.02,-.02),(sx*.02,-.08,.14)],FC),ARM,bev=.006,smooth=False)
  for k,(z0,z1,w) in enumerate(((-.075,-.125,.165),(-.13,-.18,.15))):
    put('lame',hullT([(sx*w,-.12+abs(sx)*.0,z0) for sx in (1,-1)]+[(sx*w*.95,-.12,z1) for sx in (1,-1)]+[(sx*w*.55,-.155,z0) for sx in (1,-1)]+[(sx*w*.5,-.15,z1) for sx in (1,-1)]+[(sx*w,-.03,z0) for sx in (1,-1)]+[(sx*w*.95,-.03,z1) for sx in (1,-1)],FC),ARM,bev=.005,smooth=False)
  bk=[(sx*x,y,z) for sx in (1,-1) for x,y,z in [(.2,.1,.13),(.18,.12,.0),(.14,.12,-.13),(.06,.14,-.12),(.07,.145,.12),(.03,.11,.19)]]+[(0,.03,.1)]
  put('chestB',hullT(bk,FC),ARM,bev=.006,smooth=False)
  for sx in (1,-1):
    put('collar',hullT([(sx*.03,-.1,.17),(sx*.1,-.07,.17),(sx*.12,-.02,.2),(sx*.1,-.06,.26),(sx*.04,-.095,.25),(sx*.11,.0,.25),(sx*.06,.05,.18),(sx*.06,.06,.26)],FC),ARM,bev=.005,smooth=False)
    put('strap',boxT((sx*.2,0,-.03),(.02,.2,.05),FC),WEB,bev=.006)
  # belt with pouches, groin plate
  bm=tube(W(FP,(0,0,-.05)),W(FP,(0,0,.02)),.17,.165,Rp@Vector((1,0,0)),flat=.7,NS=28,NR=2);put('belt',bm,WEB)
  for k,x in enumerate((-.13,-.06,.06,.13)):
    if gear=='light' and k in(1,2):continue
    put('pouch',boxT((x,-.125+abs(x)*.25,-.03),(.055,.05,.08),FP,Rz(x*1.6)),POUCH,bev=.008)
  for sx in (1,-1):put('pouchS',boxT((sx*.175,.03,-.04),(.05,.08,.09),FP),POUCH,bev=.008)
  put('canteen',boxT((-.1,.13,-.04),(.08,.05,.1),FP),POUCH,bev=.015)
  put('groin',hullT([(-.07,-.13,-.06),(.07,-.13,-.06),(-.05,-.14,-.2),(.05,-.14,-.2),(0,-.15,-.24),(-.06,-.1,-.08),(.06,-.1,-.08),(0,-.1,-.24)],FP),ARM,bev=.005,smooth=False)
  # legs
  pole=Rp@Vector((0,-1,0))
  for i,sx in enumerate((-1,1)):
    hipJ=W(FP,(sx*.1,0,-.06));ank,yaw,toe=P['feet'][i];ank=Vector(ank)
    print('  leg',i,end='');kn,ank=ik(hipJ,ank,.45,.44,pole+Vector((sx*.15,0,0)))
    lr=Rp@Vector((1,0,0))
    put('thigh',tube(hipJ+(hipJ-kn).normalized()*-.0,kn,.095,.072,lr,flat=1.08,bul=.012),CAMO)
    put('shin',tube(kn,ank,.07,.055,lr,bul=.008),CAMO)
    tdir=(kn-hipJ).normalized();tb=basis(tdir,lr)
    Ft=(hipJ,Matrix((tb[1],tb[2],tb[0])).transposed())   # thigh frame: x=out, y=?, z=along the thigh (down)
    put('cargo',boxT((sx*.09,0,.2),(.035,.11,.12),Ft),POUCH,bev=.01)
    put('thighP',hullT([(sx*.02,-.09,.05),(sx*.08,-.07,.05),(sx*.1,-.0,.08),(sx*.02,-.11,.27),(sx*.09,-.08,.27),(sx*.11,-.01,.24),(sx*.06,-.1,.17)],Ft),ARM,bev=.005,smooth=False)
    sdir=(ank-kn).normalized();sb=basis(sdir,lr);Fs=(kn,Matrix((sb[1],sb[2],sb[0])).transposed())
    put('knee',hullT([(-.06,-.06,-.06),(.06,-.06,-.06),(-.055,-.1,.0),(.055,-.1,.0),(0,-.115,-.02),(-.05,-.07,.07),(.05,-.07,.07),(0,-.1,.06),(-.07,-.02,0),(.07,-.02,0)],Fs),TEAMM if 0 else ARM,bev=.006,smooth=False)
    put('shinG',hullT([(-.05,-.07,.09),(.05,-.07,.09),(0,-.09,.1),(-.055,-.06,.3),(.055,-.06,.3),(0,-.08,.3),(-.06,-.02,.2),(.06,-.02,.2)],Fs),ARM,bev=.005,smooth=False)
    put('knee_pad',ell(kn+sb[2]*0,(.072,.072,.072)),WEB)
    # boot: chunky, toe along the foot yaw
    fw=Rz(yaw)@Vector((0,-1,0));Fb=(ank,Rz(yaw)@Rx(toe))
    put('boot',hullT([(sx2*w,y,z) for sx2 in (1,-1) for w,y,z in [(.058,.07,-.075),(.06,-.17,-.075),(.05,-.205,-.05),(.045,-.19,-.015),(.055,-.08,.03),(.055,-.04,.08),(.058,.065,.1),(.055,.075,.02)]],Fb),BOOT,bev=.012,smooth=False)
    put('sole',boxT((0,-.065,-.083),(.125,.29,.02),Fb),SOLE,bev=.005)
  # weapon + arms
  gO,gR=Vector(P['gun'][0]),P['gun'][1];weapon(weap,(gO,gR))
  grip={'rifle':(0,0,0),'sniper':(0,0,0),'mg':(0,0,0),'rocket':(0,0,0)}[weap];fore={'rifle':(.21,0,-.0),'sniper':(.22,0,.0),'mg':(.22,0,.0),'rocket':(.18,0,.03)}[weap]
  tgts={'R':gO+gR@Vector(grip),'L':gO+gR@Vector(fore)}
  if P.get('free'):tgts['L']=Vector(P['free'])
  for side,sx in (('R',-1),('L',1)):
    sh=W(FC,(sx*.215,0,.13));hand=tgts[side];wr=hand+(gR@Vector((0,0,.0)))
    print('  arm',side,end='');el,wr=ik(sh,wr+Vector((0,0,.03)),.32,.3,Rc@Vector((sx*.9,.5,-1)))
    lr=(el-sh).cross(wr-el);lr=lr if lr.length>1e-4 else Rc@Vector((1,0,0))
    put('uarm',tube(sh,el,.08,.064,lr,bul=.01),CAMO);put('farm',tube(el,wr,.06,.048,lr,bul=.006),CAMO)
    put('elbow',ell(el,(.062,.062,.062)),WEB)
    fd=(wr-el).normalized();fb=basis(fd,Rc@Vector((sx,0,0)));Ff=(el,Matrix((fb[1],fb[2],fb[0])).transposed())
    put('vamb',hullT([(.03,-.045,.05),(.065,-.0,.05),(.03,.045,.05),(.06,-.03,.24),(.075,0,.24),(.06,.03,.24),(.045,-.04,.15),(.045,.04,.15)],Ff),ARM,bev=.004,smooth=False)
    # glove: chunky block from the wrist toward the grip
    hd=(hand-wr);hd=hd.normalized() if hd.length>.01 else fd;hb=basis(hd,gR@Vector((0,1,0)));Fh=(wr,Matrix((hb[1],hb[2],hb[0])).transposed())
    put('glove',hullT([(-.045,-.03,.0),(.045,-.03,.0),(-.045,.03,.0),(.045,.03,.0),(-.05,-.035,.09),(.05,-.035,.09),(-.045,.04,.1),(.045,.04,.1),(-.04,0,.13),(.04,0,.13)],Fh),GLOVE,bev=.012,smooth=False)
    # pauldron (army colour): two-lame angular shell over the deltoid, off the shoulder
    Fu=(sh,Rc@Matrix(((sx,0,0),(0,-1,0),(0,0,1))))
    pp=[(-.03,y,.085) for y in (-.085,.085)]+[(.04,y,.09) for y in (-.1,.1)]+[(.09,y,.04) for y in (-.105,.105)]+[(.11,y,-.05) for y in (-.1,.1)]+[(.1,y,-.11) for y in (-.085,.085)]+[(.05,0,.115),(.12,0,-.0),(.11,0,-.12)]+[(.0,y,-.03) for y in (-.09,.09)]
    put('paul',hullT(pp,Fu),TEAMM,bev=.008,smooth=False)
    put('paul2',hullT([(.085,y,-.11) for y in (-.08,.08)]+[(.12,y,-.12) for y in (-.075,.075)]+[(.105,y,-.19) for y in (-.065,.065)]+[(.075,y,-.18) for y in (-.065,.065)]+[(.125,0,-.165)],Fu),TEAMM,bev=.005,smooth=False)
    put('paulS',boxT((.06,0,.1),(.03,.16,.012),Fu,Matrix.Rotation(.5,3,'Y')),WEB,bev=.003)
  # gear on the back
  if gear in('std','radio','ammo','rocket'):
    put('pack',boxT((0,.2,-.02),(.26,.13,.3),FC),POUCH,bev=.02)
    if gear=='radio':put('radio',boxT((.07,.27,.05),(.1,.06,.22),FC),GUN,bev=.008);put('ant',tube(W(FC,(.1,.29,.15)),W(FC,(.13,.33,.75)),.004,.003,NS=6,NR=1),GUN)
    if gear=='ammo':put('can',boxT((-.06,.29,-.05),(.14,.09,.18),FC),GUNP,bev=.008)
    if gear=='rocket':put('spare',tube(W(FC,(.08,.28,-.25)),W(FC,(.08,.28,.45)),.05,.05,NS=12,NR=1),GUNP)
  # head (built at the origin, then carried by an empty to the neck)
  if os.environ.get('NOHEAD'):return None
  before=set(bpy.data.objects);L0=lens or lensmat(seed,(.25,.75,.3))
  if head=='sniper':sniper_head((0,0,0),L0)
  elif head=='spotter':spotter_head((0,0,0),L0)
  else:variant(seed,(0,0,0),L0)
  emp=bpy.data.objects.new('head',None);bpy.context.scene.collection.objects.link(emp)
  for o in set(bpy.data.objects)-before:
    if o is not emp:o.parent=emp
  Rh=Rc@P.get('head',Matrix.Identity(3));emp.matrix_world=Matrix.Translation(W(FC,(0,-.01,.37)))@Rh.to_4x4()
  return emp
# ---------------------------------------------------------------- poses (world, facing -y, right = -x)
def pose(name,x=0.0,yaw=0.0):
  Y=Rz(yaw);o=Vector((x,0,0))
  def p(v):return o+Y@Vector(v)
  if name=='neutral':
    return {'pelvis':(p((0,-.01,1.0)),Y),'feet':[(p((-.13,0,.09)),yaw+.12,0),(p((.13,.0,.09)),yaw-.12,0)],
            'gun':(p((-.12,-.19,1.05)),Y@Rz(-1.57+.45)@Ry(.5)),'head':Rx(-.05),'chest':Rx(.05)}
  if name=='relaxed':   # low ready, weight on the right leg, hip out, slight twist
    return {'pelvis':(p((-.03,0,.975)),Y@Ry(.05)@Rz(.1)),'chest':Ry(-.06)@Rz(-.12)@Rx(.03),'feet':[(p((-.12,.02,.09)),yaw+.2,0),(p((.17,-.08,.09)),yaw-.25,0)],
            'gun':(p((-.1,-.2,1.03)),Y@Rz(-1.57+.55)@Ry(.6)),'head':Rz(.2)@Rx(-.08)}
  if name=='aim':       # braced aim: bladed, knees bent, leaning in, butt in the shoulder pocket
    Rb=Y@Rz(-.65);Rc=Rz(.22)@Rx(.12)
    C=o+Y@Vector((0,0,.92))+Rb@Rc@Vector((0,0,.3));pocket=C+Rb@Rc@Vector((-.13,-.14,.12))
    Rg=Y@Rz(-1.57)@Ry(.02);gp=pocket-Rg@Vector((-.3,0,.03))
    return {'pelvis':(p((0,0,.92)),Rb),'chest':Rc,'feet':[(p((-.17,.18,.09)),yaw-.6,0),(p((.14,-.22,.09)),yaw-.1,0)],'gun':(gp,Rg),'head':Rz(.12)@Rx(.12)@Ry(-.15)}
  if name=='jog':       # Halo-Wars style low-ready jog: leaning in, rifle across the body, left leg striding
    return {'pelvis':(p((0,0,.95)),Y@Rx(.12)@Rz(.08)),'chest':Rx(.1)@Rz(-.12),'feet':[(p((-.1,.3,.25)),yaw,-.9),(p((.11,-.3,.12)),yaw,.25)],
            'gun':(p((-.08,-.27,1.07)),Y@Rz(-1.57+.6)@Ry(.3)),'head':Rx(-.15)}
  if name=='shoulder':  # launcher on the right shoulder
    Rb=Y@Rz(-.3);Rc=Rz(.2)@Rx(.05);C=o+Y@Vector((0,0,.95))+Rb@Rc@Vector((0,0,.3));Rg=Y@Rz(-1.57);gp=C+Rb@Rc@Vector((-.12,-.12,.13))+Rg@Vector((0,-.0,-.14))
    return {'pelvis':(p((0,0,.95)),Rb),'chest':Rc,'feet':[(p((-.16,.14,.09)),yaw-.4,0),(p((.14,-.18,.09)),yaw,0)],'gun':(gp,Rg),'head':Rz(.1)@Rx(.05)}
