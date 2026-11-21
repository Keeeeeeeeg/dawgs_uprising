# (v25.34 concept) the Mange as infected soldiers: Husk (a fallen Dawgs rifleman) and Runner (a Crimson Legion trooper).
# Built from the same primitives as the marines (mlib Part), posed in game coords (x forward, y up, z right), rendered in Cycles.
import sys,math,random;sys.path.insert(0,'/home/claude/mar')
import bpy,bmesh
from mathutils import Vector,Matrix
from mlib import Part,G,rotX,rotY,rotZ,COL
import marine as MR
for o in list(bpy.data.objects):bpy.data.objects.remove(o)
COL.update({'FLESH':(.55,.47,.44),'FLESHDK':(.32,.24,.24),'SINEW':(.35,.08,.09),'BONE':(.78,.74,.64),'GLOW':(.3,1,.9),'RAGO':(.24,.27,.17),'RAGR':(.45,.08,.07),'GORE':(.22,.03,.04),'TOOTH':(.85,.82,.72)})
R=random.Random(4)
def tendril(P,a,d,n=5,L=.5,r0=.035,role='SINEW',curl=.6,seed=1):
  rr=random.Random(seed);p=Vector(a);d=Vector(d).normalized()
  for i in range(n):
    q=p+d*(L/n);P.cap(role,tuple(p),tuple(q),r0*(1-i/n*.7),r0*(1-(i+1)/n*.7),seg=7,rings=1)
    d=(d+Vector((rr.uniform(-1,1),rr.uniform(-.5,1),rr.uniform(-1,1)))*curl*.35).normalized();p=q
def growth(P,c,r,n=6,seed=2,glow=.3):
  rr=random.Random(seed)
  for i in range(n):
    o=Vector((rr.uniform(-1,1),rr.uniform(-1,1),rr.uniform(-1,1)))*r*.7;s=r*rr.uniform(.35,.7)
    P.ellip('FLESH' if rr.random()>.3 else 'FLESHDK',tuple(Vector(c)+o),(s,s*rr.uniform(.7,1.2),s),seg=8,rings=5)
    if rr.random()<glow:P.ellip('GLOW',tuple(Vector(c)+o*1.15),(s*.35,s*.35,s*.35),seg=6,rings=4)
def veins(P,a,b,n=3,seed=3):
  rr=random.Random(seed)
  for i in range(n):
    o=Vector((0,rr.uniform(-.03,.03),rr.uniform(-.03,.03)));P.cap('GLOW',tuple(Vector(a)+o),tuple(Vector(b)+o*1.5),.007,.004,seg=4,rings=1)
def husk():
  P=Part('husk')
  # legs: one still in its plated trouser, the other swollen and split by growths, both bent and turned in (a dragging stance)
  for sd,swell in ((1,0),(-1,1)):
    z=.12*sd
    P.cap('UNIFORM' if not swell else 'FLESH',(0,.74,z),(.08,.42,z*1.1),.095+.03*swell,.075+.02*swell,seg=10,rings=1)
    P.cap('UNIFORM',(.08,.42,z*1.1),(-.02,.1,z*1.05),.068,.05,seg=9,rings=1)
    P.box('BOOT',(.04,.06,z*1.05),(.23,.12,.12),bev=.03,seg=2)
    if not swell:P.box('PLATE',(.09,.6,z*1.05),(.05,.17,.12),bev=.02,rot=rotZ(-.2))
    else:growth(P,(.06,.58,z*1.15),.08,n=5,seed=11)
  P.ellip('RAGO',(0,.78,0),(.13,.11,.2),seg=10,rings=6)
  # hunched torso: the spine bent forward, ribcage swollen on one side, chest plate cracked open over a glowing maw
  T=lambda x,y,z:(x+(y-.8)*.55,y-(y-.8)*.12,z)   # lean forward with height
  P.cap('UNIFORM',T(0,.85,0),T(.02,1.25,0),.16,.19,seg=12,rings=2)
  P.box('PLATE',T(.15,1.18,.08),(.05,.2,.14),bev=.02,rot=rotZ(-.75)*rotY(.2))   # half of the chest plate
  P.box('PLATE',T(.13,1.12,-.13),(.04,.13,.08),bev=.015,rot=rotZ(-.9)*rotY(-.5))   # the other half, torn back
  P.ellip('GORE',T(.15,1.1,-.02),(.06,.1,.08),seg=10,rings=6);P.ellip('GLOW',T(.17,1.1,-.02),(.035,.07,.05),seg=8,rings=5)   # the maw
  for i in range(5):P.cap('TOOTH',T(.16,1.04+i*.03,-.06),T(.2,1.05+i*.03,-.03),.008,.002,seg=4,rings=1)
  growth(P,T(-.05,1.2,.16),.12,n=7,seed=5,glow=.4)   # swollen right shoulder
  P.box('PACK',T(-.17,1.12,0),(.09,.18,.2),bev=.03,seg=2,rot=rotZ(.5))
  for i,(z,a) in enumerate(((.05,.4),(-.06,-.3),(0,.1))):tendril(P,T(-.15,1.25,z),(-.4,1,a),n=6,L=.45+i*.08,r0=.03,seed=20+i)   # tendrils out of the spine
  veins(P,T(.05,.9,.12),T(.05,1.2,.17),seed=7);veins(P,T(-.05,.9,-.1),T(-.08,1.2,-.14),seed=8)
  # head hanging forward and to one side: helmet split open, flesh bulging out, the jaw unhinged
  H=Vector(T(.06,1.37,0))+Vector((.12,-.05,.04))
  P.ellip('FLESH',tuple(H),(.08,.085,.07),seg=10,rings=7)
  P.ellip('PLATE',tuple(H+Vector((-.02,.04,.03))),(.09,.06,.07),seg=10,rings=6)   # what is left of the helmet
  growth(P,tuple(H+Vector((-.02,.08,-.04))),.06,n=5,seed=9,glow=.6)
  P.ellip('GLOW',tuple(H+Vector((.07,.01,-.03))),(.012,.01,.012),seg=6,rings=4);P.ellip('GLOW',tuple(H+Vector((.07,.015,.03))),(.008,.007,.008),seg=6,rings=4)   # eyes
  P.box('FLESHDK',tuple(H+Vector((.05,-.08,0))),(.06,.04,.08),bev=.015,rot=rotZ(.5))   # hanging jaw
  # arms: the right still human, fingers become claws; the left a long bone blade grown through the sleeve
  sh=Vector(T(.02,1.3,.21));el=sh+Vector((.12,-.22,.05));ha=el+Vector((.16,-.2,.0))
  P.cap('UNIFORM',tuple(sh),tuple(el),.055,.047,seg=8,rings=1);P.cap('FLESH',tuple(el),tuple(ha),.045,.035,seg=8,rings=1)
  for k in range(4):P.cap('BONE',tuple(ha),tuple(ha+Vector((.06,-.06,(k-1.5)*.02))),.01,.003,seg=4,rings=1)
  sh2=Vector(T(.02,1.3,-.21));el2=sh2+Vector((.06,-.2,-.08));bl=el2+Vector((.3,-.32,-.02))
  P.cap('RAGO',tuple(sh2),tuple(el2),.06,.05,seg=8,rings=1)
  P.cap('SINEW',tuple(el2),tuple(el2+(bl-el2)*.35),.05,.04,seg=8,rings=1)
  P.cap('BONE',tuple(el2+(bl-el2)*.3),tuple(bl),.035,.006,seg=6,rings=1,squash=.45)   # the blade
  veins(P,tuple(el2),tuple(el2+(bl-el2)*.5),n=2,seed=12)
  for i in range(4):tendril(P,tuple(sh2+Vector((0,-.05,-.02))),(R.uniform(-.2,.2),-1,R.uniform(-.3,.3)),n=3,L=.22,r0=.012,role='RAGO',curl=.3,seed=40+i)   # torn sleeve strips
  return P
def runner():
  P=Part('runner')
  # crouched sprinter: legs bent like a dog's (the shin swept back, the heel lifted), long arms reaching to the ground
  for sd in (1,-1):
    z=.11*sd;k=Vector((.16,.5,z*1.2));a=Vector((-.12,.2,z*1.1))
    P.cap('UNIFORM',(0,.66,z),tuple(k),.075,.06,seg=9,rings=1);P.cap('SINEW',tuple(k),tuple(a),.05,.035,seg=8,rings=1)
    P.cap('FLESHDK',tuple(a),(.02,.02,z*1.1),.035,.025,seg=7,rings=1);P.box('BOOT',(.07,.025,z*1.1),(.16,.05,.09),bev=.015)
    for t in range(3):P.cap('BONE',(.15,.02,z*1.1+(t-1)*.025),(.21,.0,z*1.1+(t-1)*.03),.008,.002,seg=4,rings=1)   # toes burst through the boot
    P.box('RAGR',(.12,.55,z*1.1),(.12,.14,.1),bev=.01,rot=rotZ(-.6))
  P.ellip('RAGR',(0,.68,0),(.11,.09,.17),seg=10,rings=6)
  T=lambda x,y,z:(x+(y-.68)*1.1,.68+(y-.68)*.55,z)   # torso pitched far forward
  P.cap('FLESH',T(0,.7,0),T(.02,1.15,0),.12,.14,seg=12,rings=2)
  for i in range(5):P.cap('BONE',T(.1,.82+i*.06,-.1),T(.12,.84+i*.06,.1),.012,.012,seg=5,rings=1)   # ribs showing through
  P.box('RAGR',T(-.06,1.0,0),(.09,.3,.26),bev=.03,rot=rotZ(-.9))   # torn tunic over the back
  for i in range(7):P.cap('BONE',T(-.12,.78+i*.055,0),T(-.16,.8+i*.055,0),.016,.004,seg=5,rings=1)   # spine ridge
  veins(P,T(0,.8,.1),T(.02,1.1,.12),seed=31);veins(P,T(0,.8,-.1),T(.02,1.1,-.12),seed=32)
  H=Vector(T(.06,1.25,0))+Vector((.1,-.02,0))
  P.ellip('FLESH',tuple(H),(.1,.07,.065),seg=10,rings=7)   # an elongated skull
  for s in (1,-1):P.cap('FLESHDK',tuple(H+Vector((.05,-.03,.03*s))),tuple(H+Vector((.17,-.07,.05*s))),.025,.01,seg=6,rings=1)   # split jaw
  for s in (1,-1):
    for i in range(4):P.cap('TOOTH',tuple(H+Vector((.07+i*.025,-.045,.035*s))),tuple(H+Vector((.07+i*.025,-.07,.03*s))),.006,.001,seg=4,rings=1)
  P.ellip('GLOW',tuple(H+Vector((.07,.02,.035))),(.012,.009,.01),seg=6,rings=4);P.ellip('GLOW',tuple(H+Vector((.07,.02,-.035))),(.012,.009,.01),seg=6,rings=4)
  P.ellip('PLATEDK',tuple(H+Vector((-.03,.05,0))),(.06,.025,.06),seg=8,rings=5)   # a scrap of helmet fused to the crown
  for sd in (1,-1):
    sh=Vector(T(.02,1.1,.17*sd));el=sh+Vector((.18,-.2,.06*sd));ha=Vector((.42,.04,.2*sd))
    P.cap('FLESH',tuple(sh),tuple(el),.05,.04,seg=8,rings=1);P.cap('SINEW',tuple(el),tuple(ha),.04,.03,seg=8,rings=1)
    for k in range(3):P.cap('BONE',tuple(ha),tuple(ha+Vector((.1,-.03,(k-1)*.03))),.012,.002,seg=4,rings=1)   # long talons
    P.cap('RAGR',tuple(sh),tuple(sh+(el-sh)*.6),.056,.05,seg=8,rings=1)
  tendril(P,T(-.1,1.0,0),(-1,.3,.2),n=6,L=.4,r0=.022,seed=50)   # a whipping tail from the spine
  return P
def human():   # a marine for scale, from the marine builder
  obs=MR.build('rifle');return list(obs.values())
# materials for Cycles
def cyc_mats():
  for m in bpy.data.materials:
    if m.get('keep'):continue
    r=m.name.split('.')[0];c=COL.get(r,(.5,.5,.5));m.use_nodes=True;nt=m.node_tree;b=nt.nodes.get('Principled BSDF')
    if not b:continue
    b.inputs['Base Color'].default_value=c+(1,);b.inputs['Roughness'].default_value=.45 if r in('FLESH','FLESHDK','SINEW','GORE') else .6
    if r in('FLESH','FLESHDK','SINEW','GORE'):
      try:b.inputs['Subsurface Weight'].default_value=.25;b.inputs['Subsurface Radius'].default_value=(.02,.008,.006)
      except Exception:pass
      if r in('SINEW','GORE'):b.inputs['Roughness'].default_value=.25
    if r=='GLOW':b.inputs['Emission Color'].default_value=c+(1,);b.inputs['Emission Strength'].default_value=6
    if r in('PLATE','PLATEDK','GUN'):b.inputs['Metallic'].default_value=.6;b.inputs['Roughness'].default_value=.4
def shot(path,obs,view,target,ortho,res=(900,1100)):
  sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=48;sc.cycles.device='CPU'
  try:sc.cycles.use_denoising=True
  except Exception:pass
  sc.render.resolution_x,sc.render.resolution_y=res;sc.view_settings.view_transform='AgX'
  for o in sc.objects:
    if o.type=='MESH':o.hide_render=o.name not in obs
  w=bpy.data.worlds.get('W') or bpy.data.worlds.new('W');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(.05,.055,.05,1);w.node_tree.nodes['Background'].inputs[1].default_value=.6
  for nm,loc,en in (('KEY',(2.5,3,-2),900),('RIM',(-3,2.2,2.5),600),('FILL',(1,1,3),180)):
    l=bpy.data.objects.get(nm)
    if not l:l=bpy.data.objects.new(nm,bpy.data.lights.new(nm,'AREA'));sc.collection.objects.link(l)
    l.data.energy=en*.12;l.data.size=1.5;l.location=G(*loc);l.rotation_euler=(G(0,.8,0)-l.location).to_track_quat('-Z','Y').to_euler()
  l=bpy.data.objects['RIM'];l.data.color=(.55,1,.95)
  cam=sc.objects.get('CAM') or bpy.data.objects.new('CAM',bpy.data.cameras.new('CAM'))
  if cam.name not in sc.collection.objects:sc.collection.objects.link(cam)
  cam.data.type='ORTHO';cam.data.ortho_scale=ortho;T=G(*target);d=G(*view).normalized();cam.location=T+d*6;cam.rotation_euler=(T-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam
  # ground
  g=bpy.data.objects.get('GROUND')
  if not g:
    me=bpy.data.meshes.new('GROUND');bm=bmesh.new();bmesh.ops.create_grid(bm,x_segments=1,y_segments=1,size=8);bm.to_mesh(me);g=bpy.data.objects.new('GROUND',me);sc.collection.objects.link(g)
    gm=bpy.data.materials.new('GROUNDM');gm.use_nodes=True;gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.16,.15,.12,1);me.materials.append(gm)
  g.hide_render=False
  sc.render.filepath=path;bpy.ops.render.render(write_still=True)
if __name__=='__main__':
  hk=husk().finish();rn=runner().finish()
  for o in (hk,rn):
    for p in o.data.polygons:p.use_smooth=True
  hk.location=G(0,0,-.75);rn.location=G(0,0,.75)
  hum=human()
  for o in hum:o.location=o.location+G(0,0,-2.1)
  cyc_mats()
  names=[hk.name,rn.name]+[o.name for o in hum]
  shot('/home/claude/mg/c_front.png',names,(1,.35,.55),(0,.75,-.5),3.4,res=(1300,900))
  shot('/home/claude/mg/c_side.png',[hk.name,rn.name],(0,.25,-1),(0,.7,0),2.6,res=(1300,800))
  shot('/home/claude/mg/c_back.png',[hk.name,rn.name],(-1,.45,-.4),(0,.75,0),2.6,res=(1300,800))
