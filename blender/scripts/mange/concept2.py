import sys,math,random;sys.path.insert(0,'/home/claude/mar');sys.path.insert(0,'/home/claude/mg')
import marine as MR
import bpy,bmesh
from mathutils import Vector
from mlib import Part,G,rotX,rotY,rotZ,COL
from skel import Tree
for o in list(bpy.data.objects):bpy.data.objects.remove(o)
exec(open('/home/claude/mg/concept.py').read().split("def husk():")[0].split("for o in list(bpy.data.objects):bpy.data.objects.remove(o)")[1])   # colours, tendril/growth/veins helpers
COL.update({'FLESH':(.42,.33,.3),'FLESHDK':(.22,.16,.15),'SINEW':(.3,.06,.07),'RAGO':(.2,.22,.13),'RAGR':(.36,.06,.05),'UNIFORM':(.18,.19,.18)})
exec("def cyc_mats():"+open('/home/claude/mg/concept.py').read().split("def cyc_mats():")[1].split("if __name__")[0])
V=Vector
def husk2():
  T=Tree('husk2');S=1.0
  # pelvis -> spine bending forward -> neck -> head hanging low and to the side
  pel=T.node((0,.8,0),.13,'RAGO',.17)
  sp=T.chain(pel,[((.06,.95,.01),.15,'UNIFORM'),((.15,1.1,.02),.19,'UNIFORM'),((.24,1.2,.03),.21,'FLESH'),((.33,1.26,.04),.17,'FLESH')])
  nk=T.chain(sp,[((.42,1.27,.06),.07,'FLESHDK'),((.5,1.22,.08),.09,'FLESH'),((.56,1.16,.09),.08,'FLESH')])   # head (last two)
  # legs: right uniform-clad, left swollen with growth, knees bent, turned in
  for sd,sw in ((1,0),(-1,1)):
    h=T.node((0,.76,.12*sd),.09+.02*sw,'UNIFORM' if not sw else 'FLESH')
    T.e.append((pel,h))
    T.chain(h,[((.1,.45,.13*sd),.07+.03*sw,'UNIFORM' if not sw else 'FLESHDK'),((.02,.12,.12*sd),.055,'UNIFORM'),((.03,.05,.12*sd),.06,'BOOT'),((.16,.04,.12*sd),.05,'BOOT')])
  # arms: right human (sleeve, bare forearm, claws), left a sinew stalk ending in a bone blade
  shR=T.node((.27,1.3,.22),.07,'UNIFORM');T.e.append((sp-1,shR))
  T.chain(shR,[((.36,1.08,.27),.055,'FLESH'),((.5,.9,.26),.045,'FLESH'),((.56,.86,.25),.04,'FLESHDK')])
  shL=T.node((.27,1.3,-.22),.075,'RAGO');T.e.append((sp-1,shL))
  T.chain(shL,[((.33,1.08,-.29),.065,'SINEW'),((.42,.92,-.3),.06,'SINEW')])
  ob=T.build(disp=.03,dscale=.05,seed=3)
  P=Part('husk2_hard')
  # armour scraps still strapped on
  P.box('PLATE',(.06,.58,.135),(.05,.16,.11),bev=.02,rot=rotZ(-.25))
  P.box('PLATE',(.25,1.24,.11),(.05,.17,.13),bev=.02,rot=rotZ(-1.0)*rotY(.25))
  P.box('PLATEDK',(.1,1.12,-.16),(.12,.16,.04),bev=.015,rot=rotZ(-.5)*rotX(-.3))
  P.ellip('PLATE',(.53,1.24,.12),(.085,.05,.075),seg=10,rings=6,rot=rotZ(-.6))   # helmet shell split off the skull
  # the chest maw, teeth round it, eyes
  P.ellip('GORE',(.36,1.13,0),(.06,.09,.08),seg=10,rings=6);P.ellip('GLOW',(.38,1.13,0),(.03,.06,.05),seg=8,rings=5)
  for i in range(6):a=i/6*6.283;P.cap('TOOTH',(.37,1.13+math.sin(a)*.08,math.cos(a)*.07),(.41,1.13+math.sin(a)*.05,math.cos(a)*.045),.008,.002,seg=4,rings=1)
  for z in (.04,-.03):P.ellip('GLOW',(.62,1.17,.09+z),(.01,.008,.01),seg=6,rings=4)
  P.box('FLESHDK',(.6,1.08,.09),(.07,.035,.07),bev=.012,rot=rotZ(.7))   # hanging jaw
  # the bone blade, claws
  P.cap('BONE',(.4,.95,-.3),(.75,.62,-.28),.035,.004,seg=6,rings=1,squash=.4)
  for k in range(4):P.cap('BONE',(.57,.85,.25+(k-1.5)*.015),(.63,.78,.25+(k-1.5)*.02),.009,.002,seg=4,rings=1)
  growth(P,(.2,1.32,.17),.11,n=8,seed=5,glow=.35);growth(P,(.06,.6,-.15),.07,n=5,seed=11,glow=.3);growth(P,(.52,1.28,.05),.05,n=4,seed=9,glow=.5)
  for i,(z,a) in enumerate(((.06,.4),(-.05,-.3),(0,.05))):tendril(P,(.12,1.22,z),(-.5,1,a),n=7,L=.5+i*.08,r0=.028,seed=20+i)
  veins(P,(.12,.95,.15),(.2,1.15,.2),n=3,seed=7);veins(P,(.1,.95,-.15),(.2,1.15,-.2),n=3,seed=8)
  for i in range(5):tendril(P,(.27,1.25,-.26),(random.uniform(-.2,.2),-1,random.uniform(-.3,.3)),n=3,L=.2,r0=.012,role='RAGO',curl=.3,seed=40+i)
  return [ob,P.finish()]
def runner2():
  T=Tree('runner2')
  pel=T.node((0,.66,0),.11,'RAGR',.15)
  sp=T.chain(pel,[((.14,.76,0),.12,'FLESH'),((.3,.84,0),.14,'FLESH'),((.46,.88,0),.13,'FLESHDK')])
  T.chain(sp,[((.56,.88,0),.05,'SINEW'),((.64,.84,0),.065,'FLESH'),((.74,.8,0),.06,'FLESH'),((.82,.76,0),.035,'FLESHDK')])   # long skull
  for sd in (1,-1):
    h=T.node((0,.62,.11*sd),.075,'RAGR');T.e.append((pel,h))
    T.chain(h,[((.17,.46,.13*sd),.06,'SINEW'),((-.08,.2,.12*sd),.04,'SINEW'),((.0,.03,.12*sd),.03,'FLESHDK'),((.12,.02,.12*sd),.028,'FLESHDK')])
    s=T.node((.42,.84,.15*sd),.06,'FLESH');T.e.append((sp-1,s))
    T.chain(s,[((.56,.6,.2*sd),.045,'SINEW'),((.7,.32,.22*sd),.038,'SINEW'),((.76,.05,.22*sd),.03,'FLESHDK')])
  T.chain(pel,[((-.15,.7,0),.04,'SINEW'),((-.32,.75,.04),.03,'SINEW'),((-.48,.74,.1),.02,'SINEW'),((-.6,.7,.15),.012,'SINEW')])   # tail
  ob=T.build(disp=.022,dscale=.04,seed=4)
  P=Part('runner2_hard')
  for i in range(7):P.cap('BONE',(.08+i*.06,.88+i*.006,0),(.06+i*.06,.95+i*.006,0),.014,.003,seg=5,rings=1)   # spine ridge
  for i in range(4):
    for sd in (1,-1):P.cap('BONE',(.2+i*.06,.8,.13*sd),(.22+i*.06,.72,.1*sd),.01,.008,seg=4,rings=1)   # ribs
  P.box('RAGR',(.25,.86,0),(.3,.08,.3),bev=.03,rot=rotZ(.2))   # torn tunic over the back
  P.ellip('PLATEDK',(.66,.9,0),(.07,.025,.06),seg=8,rings=5)   # a scrap of helmet fused to the crown
  for sd in (1,-1):
    P.cap('FLESHDK',(.74,.76,.03*sd),(.86,.68,.05*sd),.022,.008,seg=6,rings=1)   # split jaw
    for i in range(4):P.cap('TOOTH',(.75+i*.025,.74,.04*sd),(.75+i*.025,.7,.035*sd),.006,.001,seg=4,rings=1)
    P.ellip('GLOW',(.75,.82,.04*sd),(.012,.009,.01),seg=6,rings=4)
    for k in range(3):P.cap('BONE',(.76,.05,.22*sd),(.86,.02,.22*sd+(k-1)*.03),.012,.002,seg=4,rings=1)   # talons
    for t in range(3):P.cap('BONE',(.12,.02,.12*sd+(t-1)*.02),(.18,.0,.12*sd+(t-1)*.025),.008,.002,seg=4,rings=1)   # toes
  veins(P,(.1,.75,.1),(.4,.85,.12),n=3,seed=31);veins(P,(.1,.75,-.1),(.4,.85,-.12),n=3,seed=32)
  return [ob,P.finish()]
if __name__=='__main__':
  hk=husk2();rn=runner2();hum=list(MR.build('rifle').values())
  for o in hk:o.location=o.location+G(0,0,-.8)
  for o in rn:o.location=o.location+G(-.3,0,.75)
  for o in hum:o.location=o.location+G(0,0,-2.1)
  cyc_mats()
  allh=[o.name for o in hk+rn]
  shot('/home/claude/mg/d_front.png',allh+[o.name for o in hum],(1,.35,.55),(0,.75,-.55),3.5,res=(1300,900))
  shot('/home/claude/mg/d_side.png',allh,(.05,.2,-1),(.1,.7,0),2.7,res=(1300,800))
  shot('/home/claude/mg/d_back.png',allh,(-1,.5,-.35),(.1,.75,0),2.7,res=(1300,800))
