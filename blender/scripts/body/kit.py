# (v25.17) base set-piece kit: one mesh per piece, built in real metres (scaled by S to the game's soldier scale), sitting on y=0.
# python3 /home/claude/mar/kit.py  -> mar/kit_out.json + mar/kit_sheet.png
import sys,json,math,random;sys.path.insert(0,'/home/claude/mar')
import bpy
from mlib import *
S=.47   # real metres -> game units (a 1.8 m soldier is .85)
COL.update({'OLIVE':(.33,.35,.25),'OLIVEDK':(.24,.25,.19),'GREY':(.42,.44,.45),'GREYDK':(.29,.31,.32),'DARK':(.13,.14,.14),'STEEL':(.54,.56,.57),
  'HAZARD':(.85,.68,.17),'CONC':(.6,.59,.55),'CONCDK':(.48,.46,.42),'LAMP':(1,.95,.77),'AMBER':(1,.6,.16),'TIRE':(.11,.11,.11),'YELLOW':(.85,.65,.14),
  'GLASS':(.16,.23,.27),'WOOD':(.54,.42,.27),'WHITE':(.85,.84,.8),'SAND':(.61,.55,.4),'SANDDK':(.52,.46,.33),'TARP':(.3,.34,.27),'TARPDK':(.22,.25,.2),
  'RUST':(.42,.25,.15),'CABLE':(.08,.08,.08),'RED':(.6,.16,.12),'GREEN':(.2,.5,.25),'MESH':(.36,.37,.34),'SOOT':(.09,.08,.07),'CANVAS':(.55,.52,.42)})
for o in list(bpy.data.objects):bpy.data.objects.remove(o)
OUT={};R=random.Random(7)
def done(P,name):
  ob=P.finish()
  for pl in ob.data.polygons:pl.use_smooth=True
  ob.data.set_sharp_from_angle(angle=.6)
  ob.scale=(S,S,S);bpy.context.view_layer.update()
  OUT[name]=ob;return ob
def legs4(P,role,cx,cz,w,d,h,r=.03):
  for sx in(-1,1):
    for sz in(-1,1):P.cyl(role,(cx+sx*w/2,0,cz+sz*d/2),(cx+sx*w/2,h,cz+sz*d/2),r,seg=6)

# ---------------- infrastructure ----------------
def cable(name,pts,y=.04,r=.035,clips=True):
  P=Part(name)
  for a,b in zip(pts,pts[1:]):P.cap('CABLE',(a[0],y,a[1]),(b[0],y,b[1]),r,r,seg=6,rings=1)
  for i,(x,z) in enumerate(pts[1:-1]):
    if clips and i%2==0:P.box('HAZARD',(x,.03,z),(.16,.06,.24),bev=.02)   # cable ramp / protector
  x,z=pts[0];P.box('GREYDK',(x,.25,z),(.3,.5,.22),bev=.03,seg=2);P.box('HAZARD',(x+.152,.38,z),(.01,.08,.14));P.box('LAMP',(x+.152,.26,z+.06),(.012,.03,.03))   # junction box
  x,z=pts[-1];P.box('GREY',(x,.15,z),(.26,.3,.2),bev=.03,seg=2)
  return done(P,name)
def floodRig(name,lamps=2,tall=3.4):
  P=Part(name)
  for a in range(3):   # tripod legs to a hub
    an=a*2.094;P.cap('GREYDK',(math.cos(an)*.9,0.02,math.sin(an)*.9),(0,1.1,0),.04,.035,seg=6,rings=1);P.box('DARK',(math.cos(an)*.9,.025,math.sin(an)*.9),(.16,.05,.16),bev=.02)
  P.cyl('GREY',(0,1.0,0),(0,tall,0),.06,seg=8);P.cyl('GREYDK',(0,1.0,0),(0,1.25,0),.09,seg=8)
  P.box('GREYDK',(0,tall,0),(.12,.08,.5*lamps),bev=.02)
  for i in range(lamps):
    z=(i-(lamps-1)/2)*.5;P.box('DARK',(.1,tall+.05,z),(.22,.3,.38),bev=.04,seg=2,rot=rotZ(-.35));P.box('LAMP',(.215,tall+.02,z),(.02,.24,.32),rot=rotZ(-.35))
  P.box('OLIVEDK',(-.45,.3,.3),(.6,.6,.4),bev=.05,seg=2);P.cyl('DARK',(-.45,.6,.4),(-.45,.66,.4),.05,seg=6)   # ballast/battery box
  P.cap('CABLE',(-.15,.3,.3),(0,1.0,0),.02,.02,seg=5,rings=1)
  return done(P,name)
def generator(name,big=False):
  P=Part(name);L=2.2 if big else 1.6
  P.box('OLIVEDK',(0,.12,0),(L+.2,.2,1.1),bev=.03)   # skid
  P.box('OLIVE',(0,.72,0),(L,1.0,1.0),bev=.08,seg=2)
  for i in range(5):P.box('DARK',(-L/2+.3+i*.12,.8,.505),(.06,.5,.01))   # louvres
  P.box('GREYDK',(L/2+.005,.75,0),(.01,.5,.5));P.box('LAMP',(L/2+.012,.95,.15),(.01,.05,.05));P.box('GREEN',(L/2+.012,.95,.05),(.01,.05,.05))
  P.cyl('DARK',(-L/3,1.22,-.2),(-L/3,1.9 if big else 1.7,-.2),.08,seg=8);P.cyl('SOOT',(-L/3,1.85 if big else 1.65,-.2),(-L/3,1.95 if big else 1.75,-.2),.1,seg=8)
  P.box('HAZARD',(0,1.225,.3),(.5,.01,.12))
  P.cyl('RED',(L/2-.2,.3,-.65),(L/2-.2,.75,-.65),.12,seg=8)   # extinguisher? fuel can
  return done(P,name)
def bladder(name):
  P=Part(name);P.ellip('DARK',(0,.32,0),(1.5,.34,.9),seg=16,rings=7)
  P.box('OLIVEDK',(0,.02,0),(3.2,.04,2.0),bev=.02)   # berm liner
  for sd in(-1,1):P.box('SANDDK',(0,.12,sd*1.05),(3.3,.24,.18),bev=.06,seg=2)
  P.cyl('GREYDK',(1.5,.3,0),(2.0,.3,0),.06,seg=6);P.box('GREY',(2.05,.3,0),(.15,.3,.2),bev=.02)
  return done(P,name)
def commsMast(name):
  P=Part(name);P.box('CONCDK',(0,.1,0),(.8,.2,.8),bev=.03)
  for i in range(3):
    an=i*2.094;P.cyl('STEEL',(math.cos(an)*.18,.2,math.sin(an)*.18),(math.cos(an)*.08,5.5,math.sin(an)*.08),.025,seg=5)
  for k in range(1,11):
    y=.2+k*.5;P.cyl('STEEL',(.18*(1-k/12),y,0),(-.09,y+.25,.15),.012,seg=4)
  P.cyl('WHITE',(0,5.0,0),(0,5.0,0.001),.0)if False else None
  P.box('WHITE',(.12,4.6,0),(.06,.5,.18),bev=.02);P.box('WHITE',(-.06,4.0,.1),(.06,.5,.18),bev=.02,rot=rotY(2.1))
  P.cyl('RED',(0,5.5,0),(0,5.62,0),.04,seg=6)
  for an in(0,2.094,4.19):P.cap('CABLE',(0,5.2,0),(math.cos(an)*2.2,.02,math.sin(an)*2.2),.008,.008,seg=4,rings=1)
  return done(P,name)

# ---------------- defensive clutter ----------------
def hesco(name,n=3,two=False):
  P=Part(name)
  for i in range(n):
    x=(i-(n-1)/2)*1.05
    P.box('SAND',(x,.5,0),(1.0,1.0,1.0),bev=.06,seg=2)
    for f in(-1,1):   # wire-mesh frames on the faces, as a lattice of thin bars
      for k in range(5):P.box('MESH',(x-.4+k*.2,.5,f*.505),(.015,1.0,.012))
      for k in range(5):P.box('MESH',(x,.1+k*.2,f*.505),(1.0,.015,.012))
    P.box('SANDDK',(x,1.0,0),(.92,.03,.92),bev=.01)
  if two:P.box('SAND',(0,1.5,0),(1.0,1.0,1.0),bev=.06,seg=2);P.box('SANDDK',(0,2.0,0),(.92,.03,.92))
  return done(P,name)
def tankTraps(name,n=3):
  P=Part(name)   # Czech hedgehogs: three welded beams, each resting on three beam ends
  base=Matrix.Rotation(math.atan(1/math.sqrt(2)),4,'X')@Matrix.Rotation(math.pi/4,4,'Y')   # blender frame: a cube diagonal stands vertical (blender z)
  for i in range(n):
    cx=(i-(n-1)/2)*1.7+R.uniform(-.2,.2);cz=R.uniform(-.4,.4);a=R.uniform(0,3)
    for k,size in enumerate([(1.5,.13,.13),(.13,1.5,.13),(.13,.13,1.5)]):
      P.box('RUST' if k==1 else 'DARK',(cx,.75/math.sqrt(3)+.07,cz),size,rot=rotY(a)@base)
  return done(P,name)
def coverBarricade(name):
  P=Part(name)   # spare deployable cover: a sloped plate on a frame with feet (the walls' cover language)
  P.box('GREY',(0,.55,0),(.18,1.1,1.6),bev=.04,seg=2,rot=rotZ(.18),taper=(.6,.9))
  P.box('GREYDK',(.02,1.05,0),(.2,.08,1.5),bev=.02,rot=rotZ(.18))
  for sd in(-1,1):P.box('DARK',(-.25,.18,sd*.6),(.6,.08,.12),bev=.02);P.box('HAZARD',(.1,.95,sd*.7),(.02,.1,.12),rot=rotZ(.18))
  P.box('LAMP',(.08,.75,0),(.02,.04,.3),rot=rotZ(.18))
  return done(P,name)
def sandNest(name,arc=2.2,rad=1.8):
  P=Part(name)   # pillow-shaped bags (rounded, slightly squashed boxes) laid like bricks round an arc, each course offset by half a bag
  for c in range(3):
    n=int(arc*rad/.5)
    for i in range(n+1):
      a=-arc/2+(i+(.5 if c%2 else 0))*arc/n
      if abs(a)>arc/2+.01:continue
      r=rad-c*.03;x=math.cos(a)*r-rad;z=math.sin(a)*r
      P.box('SAND' if (i*7+c*3)%4 else 'SANDDK',(x,.11+c*.2,z),(.36,.22,.56),bev=.09,seg=3,rot=rotY(-a+R.uniform(-.06,.06)))
  return done(P,name)

# ---------------- logistics ----------------
def crateTarp(name,w=3,d=2,h=2):
  P=Part(name);P.box('WOOD',(0,.07,0),(w*1.0+.2,.14,d*.8+.2),bev=.02)   # pallet
  P.box('TARP',(0,.14+h*.45/2,0),(w*1.0,h*.45,d*.8),bev=.12,seg=3)   # tarp over the stack
  P.box('TARPDK',(0,.14+h*.45,0),(w*1.0-.1,.06,d*.8-.1),bev=.05,seg=2)
  for k in(-1,0,1):P.box('STRAP' if 'STRAP' in COL else 'DARK',(k*w*.33,.14+h*.45/2,0),(.05,h*.45+.04,d*.8+.04))
  P.box('OLIVE',(w*.55,.39,-d*.2),(.6,.5,.45),bev=.03)   # a loose crate beside it
  return done(P,name)
def pallets(name):
  P=Part(name)
  for k in range(4):P.box('WOOD',(0,.07+k*.15,0),(1.2,.13,1.0),bev=.01)
  for k in range(4):
    for sl in range(5):P.box('WOOD' if sl%2 else 'SANDDK',(-.48+sl*.24,.14+k*.15,0),(.1,.012,1.0))
  return done(P,name)
def ammoCans(name):
  P=Part(name)
  for i in range(3):
    for j in range(2):
      P.box('OLIVE',(i*.32-.32,.15,j*.18-.09),(.28,.3,.15),bev=.02);P.box('DARK',(i*.32-.32,.31,j*.18-.09),(.12,.02,.04))
  P.box('OLIVE',(0,.45,0),(.28,.3,.15),bev=.02,rot=rotY(.3));P.box('HAZARD',(0,.6,0),(.06,.005,.1),rot=rotY(.3))
  return done(P,name)
def ramp(name):
  P=Part(name)
  P.box('GREY',(0,.35,0),(3.0,.7,2.4),bev=.04)   # loading dock block
  P.box('HAZARD',(1.5,.69,0),(.08,.02,2.3))
  P.box('GREYDK',(2.4,.18,0),(1.8,.06,1.6),bev=.01,rot=rotZ(-.38))   # steel ramp plate, sitting on the ground and the dock lip
  for sd in(-1,1):P.box('DARK',(2.4,.25,sd*.82),(1.9,.06,.05),rot=rotZ(-.38))
  for sd in(-1,1):P.cyl('DARK',(-1.3,.7,sd*1.1),(-1.3,1.6,sd*1.1),.03,seg=6)
  P.cyl('DARK',(-1.3,1.6,-1.1),(-1.3,1.6,1.1),.03,seg=6)
  return done(P,name)
def toolRack(name):
  P=Part(name);P.box('GREYDK',(0,.9,0),(.4,1.8,1.6),bev=.02)
  P.box('GREY',(.22,.9,0),(.04,1.6,1.5))
  for k in range(4):P.box('DARK',(.26,.4+k*.38,0),(.06,.02,1.4))
  for k,(y,z) in enumerate([(.6,-.4),(.98,.2),(1.36,-.1),(.6,.45)]):P.box(['RED','YELLOW','STEEL','OLIVE'][k],(.3,y+.08,z),(.12,.16,.22),bev=.02)
  P.box('OLIVE',(.6,.45,-.2),(.6,.9,.6),bev=.04,seg=2)   # tool chest
  for k in range(4):P.box('DARK',(.905,.15+k*.2,-.2),(.01,.02,.3))
  return done(P,name)

# ---------------- story pieces ----------------
def wreck(name):
  P=Part(name)   # a scrapped utility truck up on blocks, bonnet open, its engine hanging from a hoist beside it
  P.box('DARK',(0,.55,0),(3.6,.16,1.0),bev=.03)                                  # chassis rails
  P.box('RUST',(-.2,.95,0),(2.0,.12,1.8),bev=.03)                                # flatbed floor
  for sd in(-1,1):P.box('RUST',(-.2,1.15,sd*.88),(2.0,.35,.06),bev=.02)         # bed sides
  P.box('RUST',(-1.18,1.15,0),(.06,.35,1.8),bev=.02)
  P.box('SOOT',(1.25,1.35,0),(1.0,1.0,1.7),bev=.12,seg=2,taper=(.85,.95))       # burnt cab
  P.box('DARK',(1.3,1.55,0),(.9,.42,1.72));P.box('DARK',(1.77,1.55,0),(.04,.42,1.4))   # empty windows
  P.box('RUST',(2.2,.95,0),(.8,.45,1.6),bev=.06,seg=2)                           # engine bay
  P.box('RUST',(2.35,1.5,0),(.9,.06,1.5),bev=.02,rot=rotZ(1.1))                  # bonnet up
  for sx in(-1.3,1.9):
    for sz in(-1,1):P.box('CONCDK',(sx,.22,sz*.55),(.45,.44,.45),bev=.03)       # on blocks
    for sz in(-1,1):P.box('DARK',(sx,.62,sz*.86),(.95,.32,.08),bev=.04)        # empty wheel arches
  P.cyl('TIRE',(-.3,.4,1.3),(-.3,.62,1.3),.42,seg=14);P.cyl('GREY',(-.3,.4,1.3),(-.3,.64,1.3),.18,seg=10)   # a wheel lying flat
  P.box('DARK',(2.5,.7,1.7),(.6,.5,.55),bev=.06,seg=2)                           # the engine, hanging
  for sd in(-1,1):P.cyl('YELLOW',(2.5+sd*.7,0,1.7),(2.5,2.4,1.7),.05,seg=6)
  P.cyl('YELLOW',(2.5,2.4,1.7),(2.5,2.4,.9),.05,seg=6);P.cyl('DARK',(2.5,2.38,1.7),(2.5,.96,1.7),.012,seg=4)
  return done(P,name)
def fieldKitchen(name):
  P=Part(name)
  # tent: a ridge frame and canvas roof, open sides
  for sx in(-1,1):
    for sz in(-1,1):P.cyl('DARK',(sx*1.4,0,sz*1.1),(sx*1.4,1.9,sz*1.1),.035,seg=6)
  for sz in(-1,1):P.box('CANVAS',(0,2.25,sz*.6),(3.0,.04,1.35),rot=rotX(-sz*.55))
  P.box('CANVAS',(0,2.6,0),(3.0,.06,.12))
  P.box('GREYDK',(0,.45,-.5),(2.2,.9,.6),bev=.03)   # cooker
  for i in range(3):P.cyl('STEEL',(-.7+i*.7,.9,-.5),(-.7+i*.7,1.25,-.5),.2,seg=10)   # pots
  P.box('WOOD',(.2,.75,.6),(1.8,.06,.7));legs4(P,'DARK',.2,.6,1.6,.5,.72)
  P.box('OLIVE',(1.9,.3,-.8),(.6,.6,.5),bev=.03);P.cyl('RED',(1.9,.6,.4),(1.9,1.0,.4),.15,seg=8)
  return done(P,name)
def memorial(name):
  P=Part(name)
  P.box('CONCDK',(0,.08,0),(1.0,.16,.6),bev=.03)
  P.box('DARK',(0,.85,0),(.07,1.4,.06),bev=.01);P.box('DARK',(.0,.25,0),(.3,.08,.06))   # rifle, bayonet down
  P.ellip('GREY',(0,1.6,0),(.17,.11,.15),seg=12,rings=6);P.box('GREYDK',(0,1.55,0),(.36,.03,.32),bev=.01)   # helmet on the stock
  P.box('STEEL',(.05,1.25,.04),(.03,.06,.008));P.box('STEEL',(-.02,1.22,.045),(.03,.06,.008))   # tags
  for i in range(4):P.cyl('LAMP' if i%2 else 'AMBER',(-.35+i*.23,.16,.22),(-.35+i*.23,.24,.22),.03,seg=6)   # candles
  P.box('WOOD',(.3,.12,-.15),(.25,.08,.16))
  return done(P,name)
def repairStand(name):
  P=Part(name)   # a patched armour panel on a jig with a welder cart: sparks are thrown from 'tip'
  P.box('DARK',(0,.05,0),(1.6,.1,.6),bev=.02)
  for sd in(-1,1):P.cyl('GREYDK',(sd*.7,.1,0),(sd*.7,1.7,0),.04,seg=6)
  P.box('GREY',(0,1.0,0),(1.3,1.2,.12),bev=.03,seg=2)
  P.box('STEEL',(.2,1.15,.065),(.45,.35,.01));P.box('SOOT',(.2,1.15,.072),(.5,.04,.005))   # fresh patch and its bead
  P.box('YELLOW',(1.2,.4,.4),(.5,.6,.4),bev=.04,seg=2);P.cap('CABLE',(1.2,.5,.2),(.45,1.15,.2),.02,.02,seg=5,rings=1)
  return done(P,name)

def build_all():
  random.seed(7)
  cable('k_cableA',[(0,0),(1.2,.3),(2.4,.1),(3.6,.5),(4.6,.4)])
  cable('k_cableB',[(0,0),(.9,-.4),(1.6,-.2),(2.6,.3),(3.2,1.0)])
  floodRig('k_floodA',2,3.4);floodRig('k_floodB',3,4.2)
  generator('k_genA');generator('k_genB',True)
  bladder('k_bladder');commsMast('k_mast')
  hesco('k_hescoA',3);hesco('k_hescoB',2,True);tankTraps('k_traps',3);coverBarricade('k_cover');sandNest('k_sandA');sandNest('k_sandB',1.6,1.3)
  crateTarp('k_tarpA');crateTarp('k_tarpB',2,2,1.6);pallets('k_pallets');ammoCans('k_ammo');ramp('k_ramp');toolRack('k_tools')
  wreck('k_wreck');fieldKitchen('k_kitchen');memorial('k_memorial');repairStand('k_repair')

if __name__=='__main__':
  build_all()
  # contact sheet: each piece alone, same camera
  names=list(OUT)
  from PIL import Image
  ims=[]
  for n in names:
    ob=OUT[n];bb=[ob.matrix_world@Vector(c) for c in ob.bound_box];c=sum(bb,Vector())/8;sz=max((b-c).length for b in bb)
    g=ungame(c);render('/home/claude/mar/kp_%s.png'%n,[n],view=(1,.7,.8),res=(260,260),ortho=sz*1.05,target=g)
    ims.append(Image.open('/home/claude/mar/kp_%s.png'%n))
  cols=6;rows=(len(ims)+cols-1)//cols;sheet=Image.new('RGB',(260*cols,260*rows))
  for i,im in enumerate(ims):sheet.paste(im,((i%cols)*260,(i//cols)*260))
  sheet.save('/home/claude/mar/kit_sheet.png')
  pk={}
  for n,ob in OUT.items():
    d=pack(ob);bb=[ungame(ob.matrix_world@Vector(c)) for c in ob.bound_box]
    d['bb']=[round(min(b[i] for b in bb),3) for i in range(3)]+[round(max(b[i] for b in bb),3) for i in range(3)];pk[n]=d
  json.dump(pk,open('/home/claude/mar/kit_out.json','w'))
  print({k:(v['n'],v['bb']) for k,v in pk.items()})
