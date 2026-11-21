# (v25.25) set-piece kit v2: 12 richer pieces (1.5-3k tris), real metres x S, each one welded-looking mesh, on y=0.
# python3 /home/claude/mar/kit2.py -> mar/kit2_out.json + mar/kit2_sheet.png
import sys,math,random,json;sys.path.insert(0,'/home/claude/mar')
import bpy
from mathutils import Vector,Matrix
import kit as K   # reuses COL, done(), legs4 and the mlib Part
from mlib import *
for o in list(bpy.data.objects):bpy.data.objects.remove(o)
K.OUT.clear();OUT=K.OUT;done=K.done;legs4=K.legs4;R=random.Random(11)
COL.update({'BRASS':(.72,.56,.18),'NET':(.2,.22,.16),'ROPE':(.5,.45,.32),'CONCSL':(.5,.49,.46)})
def bx(P,role,c,s,b=.025,rot=None,seg=2):P.box(role,c,s,bev=min(b,min(s)*.45),seg=seg,rot=rot)
def wheel(P,x,y,z,r=.36,w=.22):
  P.cyl('TIRE',(x,y,z-w/2),(x,y,z+w/2),r,seg=14);P.cyl('GREY',(x,y,z-w/2-.005),(x,y,z+w/2+.005),r*.55,seg=10)
  for k in range(5):a=k*1.2566;P.box('DARK',(x+math.cos(a)*r*.3,y+math.sin(a)*r*.3,z+w/2+.008),(.04,.04,.01))
def stencil(P,c,s,role='WHITE'):P.box(role,c,s)
def lattice(P,role,x,z,h,w,step=.45):
  # three-legged lattice mast with zig-zag bracing
  legs=[(x+math.cos(a)*w,z+math.sin(a)*w) for a in (0,2.094,4.189)]
  for lx,lz in legs:P.cyl(role,(lx,0,lz),(x+(lx-x)*.4,h,z+(lz-z)*.4),.035,seg=6)
  y=.2;i=0
  while y<h-step:
    f0,f1=1-.6*y/h,1-.6*(y+step)/h
    for a in range(3):
      ax,az=legs[a];bx_,bz=legs[(a+1)%3]
      p0=(x+(ax-x)*f0,y,z+(az-z)*f0);p1=(x+(bx_-x)*f1,y+step,z+(bz-z)*f1)
      if i%2:p0,p1=(x+(bx_-x)*f0,y,z+(bz-z)*f0),(x+(ax-x)*f1,y+step,z+(az-z)*f1)
      P.cap(role,p0,p1,.014,.014,seg=4,rings=1)
    y+=step;i+=1

def floodTower():
  P=Part('k2_flood')
  bx(P,'OLIVEDK',(0,.55,0),(2.2,.3,1.3),.05)                     # trailer bed
  bx(P,'OLIVE',(-.35,.95,0),(1.2,.5,1.1),.06)                    # generator housing
  for k in range(6):P.box('DARK',(-.75+k*.15,.98,.556),(.06,.3,.01))
  P.cyl('DARK',(-.65,1.2,-.3),(-.65,1.55,-.3),.05,seg=8);P.cyl('SOOT',(-.65,1.5,-.3),(-.65,1.58,-.3),.07,seg=8)
  wheel(P,.2,.36,.72);wheel(P,.2,.36,-.72)
  P.cap('DARK',(1.1,.55,0),(1.9,.45,0),.04,.04,seg=6,rings=1);P.cyl('DARK',(1.9,.2,0),(1.9,.48,0),.05,seg=8)   # tow bar + jack
  for sx in(-1,1):
    for sz in(-1,1):P.cap('YELLOW',(sx*.95,.5,sz*.6),(sx*1.25,.05,sz*1.05),.035,.035,seg=6,rings=1);bx(P,'DARK',(sx*1.25,.03,sz*1.05),(.22,.06,.22),.02)   # outriggers
  P.cyl('GREY',(.55,.7,0),(.55,4.4,0),.09,seg=10);P.cyl('GREYDK',(.55,.7,0),(.55,2.2,0),.12,seg=10)   # telescopic mast
  P.cap('GREYDK',(.55,1.0,0),(.85,.7,0),.04,.04,seg=6,rings=1)
  bx(P,'GREYDK',(.55,4.45,0),(.12,.1,1.6),.02)
  for z in(-.6,-.2,.2,.6):
    bx(P,'DARK',(.68,4.62,z),(.22,.3,.34),.04,rot=rotZ(-.35));P.box('LAMP',(.8,4.58,z),(.02,.22,.28),rot=rotZ(-.35))
  P.cap('CABLE',(.0,1.1,.4),(.55,2.0,.12),.02,.02,seg=5,rings=1)
  stencil(P,(-.35,1.21,.2),(.4,.005,.14),'HAZARD')
  return done(P,'k2_flood')

def genset():
  P=Part('k2_gen');L=2.6
  bx(P,'DARK',(0,.09,0),(L+.3,.18,1.3),.03)                       # skid with fork pockets
  for z in(-.35,.35):P.box('SOOT',(0,.09,z),(L+.32,.1,.18))
  bx(P,'OLIVE',(0,.85,0),(L,1.3,1.2),.08,seg=3)                    # container
  for sd in(-1,1):
    for k in range(3):bx(P,'OLIVEDK',(-.8+k*.8,.85,sd*.605),(.7,1.1,.02),.01)   # doors
    for k in range(3):P.box('DARK',(-.5+k*.8,.85,sd*.62),(.03,.12,.02))       # handles
    for k in range(8):P.box('DARK',(1.0,.5+k*.09,sd*.61),(.4,.03,.02))       # louvres
  P.box('GREYDK',(L/2+.01,.85,0),(.02,.9,.9))
  for k in range(6):P.box('DARK',(L/2+.02,.5+k*.13,0),(.01,.04,.8))         # radiator grille
  P.cyl('DARK',(-.8,1.5,-.25),(-.8,2.25,-.25),.08,seg=10);P.cyl('SOOT',(-.8,2.2,-.25),(-.8,2.28,-.25),.11,seg=10);P.box('DARK',(-.8,2.33,-.25),(.24,.02,.24),rot=rotZ(.3))
  bx(P,'GREYDK',(-L/2-.2,.45,0),(.35,.7,.8),.04)                    # control panel box
  P.box('GREEN',(-L/2-.38,.62,.15),(.01,.06,.06));P.box('LAMP',(-L/2-.38,.62,-.05),(.01,.06,.06));P.box('RED',(-L/2-.38,.48,.05),(.01,.08,.08))
  P.cyl('YELLOW',(.9,.25,.85),(.9,.25,1.25),.32,seg=14);P.cyl('CABLE',(.9,.25,.84),(.9,.25,1.26),.2,seg=12)   # cable reel
  stencil(P,(0,1.505,0),(1.4,.005,.4),'HAZARD');stencil(P,(-.2,.9,.62),(.5,.12,.005))
  return done(P,'k2_gen')

def fuelPod():
  P=Part('k2_fuel')
  for x in(-1.1,1.1):bx(P,'DARK',(x,.35,0),(.25,.7,1.5),.03)          # cradles
  P.cyl('OLIVE',(-1.9,1.15,0),(1.9,1.15,0),.75,seg=24)
  for x in(-1.9,1.9):P.ellip('OLIVE',(x,1.15,0),(.25,.75,.75),seg=20,rings=8)
  for x in(-1.3,0,1.3):P.cyl('OLIVEDK',(x-.04,1.15,0),(x+.04,1.15,0),.77,seg=24)   # bands
  bx(P,'GREYDK',(0,1.92,0),(2.4,.04,.6),.01)                         # top walkway
  for x in(-1.1,1.1):
    for z in(-.3,.3):P.cyl('YELLOW',(x,1.93,z),(x,2.45,z),.018,seg=5)
  for z in(-.3,.3):P.cyl('YELLOW',(-1.1,2.45,z),(1.1,2.45,z),.018,seg=5)
  for k in range(7):P.box('GREYDK',(1.95+.05,.25+k*.25,-.5),(.04,.02,.32))   # ladder rungs
  for z in(-.66,-.34):P.cyl('GREYDK',(2.0,0,z),(2.0,1.95,z),.02,seg=5)
  P.cyl('GREYDK',(0,1.9,0),(0,2.05,0),.18,seg=12)                       # manhole
  bx(P,'RED',(-2.3,.55,.6),(.5,.8,.4),.04);P.cyl('CABLE',(-2.3,.55,.82),(-2.3,.55,1.0),.22,seg=12)   # hose reel cabinet
  P.cap('CABLE',(-2.1,.4,.9),(-1.6,.06,1.6),.035,.035,seg=6,rings=1)
  stencil(P,(0,1.15,.77),(1.2,.25,.005),'HAZARD');stencil(P,(0,1.15,-.77),(1.2,.25,.005),'HAZARD')
  return done(P,'k2_fuel')

def comms():
  P=Part('k2_comms')
  bx(P,'CONCDK',(0,.1,0),(1.0,.2,1.0),.03)
  lattice(P,'STEEL',0,0,7.0,.32)
  P.cyl('WHITE',(0,7.0,0),(0,7.6,0),.03,seg=6);P.cyl('RED',(0,7.6,0),(0,7.7,0),.05,seg=8)
  dish=(.25,5.6,0);P.ellip('WHITE',dish,(.08,.42,.42),seg=16,rings=6);P.cyl('GREYDK',(0,5.6,0),(.2,5.6,0),.04,seg=6)
  for y in(4.2,6.4):bx(P,'WHITE',(.12,y,.12),(.06,.6,.16),.02)          # panel antennas
  for an in(0,2.094,4.189):P.cap('CABLE',(0,6.2,0),(math.cos(an)*3.4,.04,math.sin(an)*3.4),.008,.008,seg=4,rings=1);bx(P,'CONCDK',(math.cos(an)*3.4,.08,math.sin(an)*3.4),(.3,.16,.3),.02)
  # equipment shelter with AC unit
  bx(P,'GREY',(1.9,.85,.0),(1.6,1.7,1.4),.06,seg=3);bx(P,'GREYDK',(2.71,.75,.25),(.02,1.3,.6),.01);P.box('DARK',(2.72,.8,.0),(.02,.06,.04))
  bx(P,'WHITE',(1.9,.95,-.78),(.8,.6,.18),.03);P.cyl('DARK',(1.9,.95,-.88),(1.9,.95,-.86),.22,seg=12)
  P.cap('CABLE',(1.1,1.4,0),(.1,1.6,0),.03,.03,seg=6,rings=1)
  for x in(1.25,2.55):P.box('LAMP',(x,1.72,.71),(.06,.04,.02))
  return done(P,'k2_comms')

def hesco():
  P=Part('k2_hesco')
  for i in range(4):
    x=(i-1.5)*1.04
    bx(P,'SAND',(x,.52,0),(1.0,1.04,1.0),.08,seg=3)
    for f in(-1,1):
      for k in range(6):P.box('MESH',(x-.42+k*.168,.52,f*.506),(.014,1.02,.012))
      for k in range(6):P.box('MESH',(x,.09+k*.17,f*.506),(1.0,.014,.012))
    for f in(-1,1):
      for k in range(6):P.box('MESH',(x+f*.506,.52,-.42+k*.168),(.012,1.02,.014))
    bx(P,'SANDDK',(x,1.04,0),(.9,.04,.9),.01)
  for i in range(7):   # sandbag cap
    P.box('SAND' if i%2 else 'SANDDK',(-1.7+i*.56,1.14,.0),(.52,.16,.34),bev=.06,seg=2,rot=rotY(R.uniform(-.08,.08)))
  bx(P,'WOOD',(0,.18,-.75),(3.6,.06,.4),.01)                            # firing step boards
  for x in(-1.5,0,1.5):P.box('WOOD',(x,.09,-.75),(.1,.18,.38))
  return done(P,'k2_hesco')

def nest():
  P=Part('k2_nest');rad=1.7;arc=3.4
  for c in range(4):
    n=int(arc*rad/.48)
    for i in range(n+1):
      a=-arc/2+(i+(.5 if c%2 else 0))*arc/n
      if abs(a)>arc/2+.01:continue
      r=rad-c*.035;x=math.cos(a)*r;z=math.sin(a)*r
      P.box('SAND' if (i*7+c*3)%4 else 'SANDDK',(x,.1+c*.19,z),(.34,.21,.54),bev=.085,seg=2,rot=rotY(-a+R.uniform(-.07,.07)))
  # a mounted MG on a tripod at the lip, an ammo can, a periscope stand
  P.cyl('DARK',(1.25,0,0),(1.3,.9,0),.03,seg=6)
  for an in(2.4,3.5,4.3):P.cap('DARK',(1.3,.85,0),(1.3+math.cos(an)*.4,.02,math.sin(an)*.4),.02,.02,seg=5,rings=1)
  bx(P,'GUN' if 'GUN' in COL else 'DARK',(1.55,.95,0),(.7,.12,.1),.02);P.cyl('DARK',(1.9,.97,0),(2.25,.97,0),.022,seg=6)
  bx(P,'OLIVE',(1.0,.12,.4),(.3,.24,.16),.02);bx(P,'OLIVE',(1.0,.12,-.4),(.3,.24,.16),.02)
  P.cyl('WOOD',(.2,0,.0),(.2,.5,0),.04,seg=6);bx(P,'WOOD',(.2,.52,0),(.8,.06,.5),.01)   # a crate seat
  return done(P,'k2_nest')

def hedgehogs():
  P=Part('k2_traps')
  base=Matrix.Rotation(math.atan(1/math.sqrt(2)),4,'X')@Matrix.Rotation(math.pi/4,4,'Y')
  for i in range(4):
    cx=(i-1.5)*1.9+R.uniform(-.2,.2);cz=R.uniform(-.5,.5);a=R.uniform(0,3)
    bx(P,'CONCSL',(cx,.04,cz),(1.4,.08,1.4),.03)
    for k,size in enumerate([(1.6,.16,.16),(.16,1.6,.16),(.16,.16,1.6)]):
      P.box('RUST' if (k+i)%3==0 else 'DARK',(cx,.8/math.sqrt(3)+.12,cz),size,rot=rotY(a)@base,bev=.02,seg=1)
    P.ellip('DARK',(cx,.8/math.sqrt(3)+.12,cz),(.14,.14,.14),seg=8,rings=5)   # welded node
  return done(P,'k2_traps')

def supplies():
  P=Part('k2_supply')
  for k,(x,z) in enumerate([(-1.0,0),(.35,0),(1.6,.1)]):bx(P,'WOOD',(x,.07,z),(1.2,.14,1.0),.01)
  bx(P,'OLIVE',(-1.0,.55,0),(1.1,.8,.9),.04);bx(P,'OLIVEDK',(-1.0,.96,0),(1.12,.04,.92),.01)
  for x in(-1.4,-.6):P.box('HAZARD',(x,.55,.456),(.08,.8,.01))
  bx(P,'GREY',(.35,.45,0),(1.1,.6,.9),.04);bx(P,'GREY',(.35,1.05,0),(1.0,.6,.8),.04)
  stencil(P,(.35,.45,.456),(.5,.15,.005));stencil(P,(.35,1.05,.406),(.4,.12,.005))
  for k in range(3):P.cyl('OLIVEDK',(1.4+k*.0,.14,-.25+k*.28),(1.4,.94,-.25+k*.28),.14,seg=12)   # drums
  for k in range(3):P.cyl('DARK',(1.4,.9,-.25+k*.28),(1.4,.95,-.25+k*.28),.15,seg=12)
  bx(P,'TARP',(-.33,1.42,0),(2.5,.06,1.2),.03,seg=2,rot=rotX(.0))   # tarp draped over the two stacks
  for sd in(-1,1):P.box('TARP',(-.33,1.12,sd*.62),(2.5,.6,.04),bev=.02,seg=1,rot=rotX(sd*-.15))
  for x in(-1.4,-.33,.75):
    for sd in(-1,1):P.cap('ROPE',(x,1.44,sd*.6),(x,.02,sd*1.1),.01,.01,seg=4,rings=1)
  return done(P,'k2_supply')

def ammo():
  P=Part('k2_ammo')
  bx(P,'WOOD',(0,.07,0),(1.3,.14,1.1),.01)
  for i in range(2):
    for j in range(2):
      for l in range(2 if (i+j)%2==0 else 1):
        c=(-.3+i*.6,.32+l*.36,-.25+j*.5);bx(P,'OLIVE',c,(.56,.34,.46),.03);P.box('HAZARD',(c[0],c[1],c[2]+.235),(.5,.05,.005));P.box('DARK',(c[0],c[1]+.18,c[2]),(.2,.02,.05))
  # an opened crate on top with rounds showing
  bx(P,'OLIVE',(.3,.88,.25),(.56,.2,.46),.02);P.box('OLIVEDK',(.3,1.12,.02),(.56,.03,.46),rot=rotX(1.1))
  for k in range(8):P.cyl('BRASS',(.1+k*.055,.95,.25-.15),(.1+k*.055,.95,.25+.15),.018,seg=6)
  return done(P,'k2_ammo')

def workshop():
  P=Part('k2_work')
  bx(P,'CONCSL',(0,.04,0),(3.2,.08,2.2),.03)
  for sd in(-1,1):P.cyl('GREYDK',(sd*.8,.08,-.6),(sd*.8,2.0,-.6),.05,seg=8)
  P.cyl('GREYDK',(-.85,1.95,-.6),(.85,1.95,-.6),.05,seg=8)
  bx(P,'GREY',(0,1.05,-.6),(1.4,1.3,.12),.04);bx(P,'STEEL',(.25,1.2,-.53),(.5,.4,.02),.01);P.box('SOOT',(.25,1.2,-.518),(.55,.04,.005))   # panel + fresh patch
  P.cap('DARK',(0,1.95,-.6),(0,1.7,-.6),.012,.012,seg=4,rings=1)
  # welding cart: frame, two gas bottles, the welder box, torch lead to the patch
  bx(P,'DARK',(1.2,.35,.4),(.6,.04,.4),.01)
  for sx in(-1,1):wheel(P,1.2+sx*.25,.1,.62,.1,.05)
  P.cyl('GREEN',(1.05,.37,.3),(1.05,1.25,.3),.1,seg=10);P.cyl('RED',(1.3,.37,.3),(1.3,1.15,.3),.1,seg=10)
  bx(P,'YELLOW',(1.25,.55,.5),(.4,.35,.2),.03)
  P.cap('CABLE',(1.1,.6,.5),(.3,1.1,-.45),.015,.015,seg=4,rings=1)
  # tool chest and a vice bench
  bx(P,'RED',(-1.2,.5,.5),(.7,.9,.5),.03)
  for k in range(4):P.box('DARK',(-1.2,.2+k*.2,.755),(.5,.02,.01))
  bx(P,'WOOD',(-.1,.85,.65),(1.4,.06,.5),.01);legs4(P,'DARK',-.1,.65,1.2,.4,.82,.025);bx(P,'GREYDK',(.4,.95,.65),(.15,.14,.12),.02)
  return done(P,'k2_work')

def wreck():
  P=Part('k2_wreck')
  bx(P,'DARK',(0,.55,0),(3.8,.16,1.0),.03)
  bx(P,'RUST',(-.3,.95,0),(2.0,.12,1.9),.03)
  for sd in(-1,1):bx(P,'RUST',(-.3,1.18,sd*.93),(2.0,.38,.06),.02)
  bx(P,'RUST',(-1.28,1.18,0),(.06,.38,1.9),.02)
  bx(P,'SOOT',(1.3,1.4,0),(1.1,1.05,1.8),.14,seg=3)
  for sd in(-1,1):P.box('DARK',(1.3,1.62,sd*.905),(.75,.4,.02))
  P.box('DARK',(1.86,1.6,0),(.02,.42,1.4))
  bx(P,'RUST',(2.3,.98,0),(.85,.5,1.7),.06,seg=2)
  P.box('RUST',(2.45,1.55,0),(.95,.06,1.6),bev=.02,seg=1,rot=rotZ(1.1))
  for sx in(-1.4,2.0):
    for sz in(-1,1):bx(P,'CONCDK',(sx,.22,sz*.6),(.45,.44,.45),.03);bx(P,'DARK',(sx,.66,sz*.92),(1.0,.34,.06),.04)
  wheel(P,-.3,.12,1.4,.42,.24) if False else None
  P.cyl('TIRE',(-.3,0,1.45),(-.3,.24,1.45),.42,seg=16);P.cyl('GREY',(-.3,0,1.45),(-.3,.26,1.45),.18,seg=10)
  bx(P,'DARK',(2.6,.75,1.75),(.6,.5,.55),.05)
  for sd in(-1,1):P.cap('YELLOW',(2.6+sd*.75,0,1.75),(2.6,2.5,1.75),.05,.05,seg=6,rings=1)
  P.cap('YELLOW',(2.6,2.5,1.75),(2.6,2.5,.9),.05,.05,seg=6,rings=1);P.cyl('DARK',(2.6,2.48,1.75),(2.6,1.0,1.75),.012,seg=4)
  return done(P,'k2_wreck')

def kitchen():
  P=Part('k2_kitchen')
  for sx in(-1,1):
    for sz in(-1,1):P.cyl('DARK',(sx*1.5,0,sz*1.2),(sx*1.5,1.95,sz*1.2),.04,seg=6)
    P.cyl('DARK',(sx*1.5,1.95,-1.2),(sx*1.5,2.6,0),.04,seg=6);P.cyl('DARK',(sx*1.5,1.95,1.2),(sx*1.5,2.6,0),.04,seg=6)
  for sz in(-1,1):P.box('CANVAS',(0,2.3,sz*.62),(3.2,.04,1.42),bev=.015,seg=1,rot=rotX(-sz*.5))
  P.box('CANVAS',(0,2.62,0),(3.2,.06,.14))
  P.box('CANVAS',(0,1.6,-1.25),(3.0,.75,.03),rot=rotX(.12))   # rolled side wall valance
  bx(P,'GREYDK',(0,.45,-.6),(2.2,.9,.6),.04)
  for i in range(3):P.cyl('STEEL',(-.7+i*.7,.9,-.6),(-.7+i*.7,1.25,-.6),.2,seg=14);P.cyl('GREY',(-.7+i*.7,1.25,-.6),(-.7+i*.7,1.28,-.6),.21,seg=14)
  P.cyl('DARK',(.9,.9,-.85),(.9,2.9,-.85),.06,seg=8);P.cyl('SOOT',(.9,2.85,-.85),(.9,2.95,-.85),.09,seg=8)   # stove pipe through the roof
  bx(P,'WOOD',(.2,.78,.6),(1.9,.06,.7),.01);legs4(P,'DARK',.2,.6,1.7,.5,.75,.025)
  for sd in(-1,1):bx(P,'WOOD',(.2,.45,.6+sd*.6),(1.9,.05,.25),.01);legs4(P,'DARK',.2,.6+sd*.6,1.7,.15,.42,.02)
  # water trailer beside the tent
  P.cyl('OLIVE',(2.4,.85,-1.0),(2.4,.85,1.0),.45,seg=16)
  for z in(-1.0,1.0):P.ellip('OLIVE',(2.4,.85,z),(.45,.45,.12),seg=14,rings=6)
  wheel(P,2.4,.3,-.0,.3,.2) if False else None
  for sd in(-1,1):P.cyl('TIRE',(2.4-.45*sd*0+0,.3,sd*.62),(2.4,.3,sd*.82),.3,seg=14)
  P.cyl('GREY',(2.4,.6,1.1),(2.4,.6,1.25),.04,seg=6)
  return done(P,'k2_kitchen')

ALL=[floodTower,genset,fuelPod,comms,hesco,nest,hedgehogs,supplies,ammo,workshop,wreck,kitchen]
if __name__=='__main__':
  for f in ALL:f()
  from PIL import Image
  ims=[]
  for n,ob in OUT.items():
    bb=[ob.matrix_world@Vector(c) for c in ob.bound_box];c=sum(bb,Vector())/8;sz=max((b-c).length for b in bb)
    render('/home/claude/mar/k2_%s.png'%n,[n],view=(1,.7,.8),res=(400,400),ortho=sz*1.05,target=ungame(c))
    ims.append(Image.open('/home/claude/mar/k2_%s.png'%n))
  cols=4;rows=(len(ims)+cols-1)//cols;sheet=Image.new('RGB',(400*cols,400*rows))
  for i,im in enumerate(ims):sheet.paste(im,((i%cols)*400,(i//cols)*400))
  sheet.save('/home/claude/mar/kit2_sheet.png')
  pk={}
  for n,ob in OUT.items():
    d=pack(ob);bb=[ungame(ob.matrix_world@Vector(c)) for c in ob.bound_box]
    d['bb']=[round(min(b[i] for b in bb),3) for i in range(3)]+[round(max(b[i] for b in bb),3) for i in range(3)];pk[n]=d
  json.dump(pk,open('/home/claude/mar/kit2_out.json','w'))
  print({k:v['n'] for k,v in pk.items()})
