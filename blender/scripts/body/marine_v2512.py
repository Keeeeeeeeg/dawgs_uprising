import sys,json,math;sys.path.insert(0,'/home/claude/mar')
import bpy
from mlib import *
for o in list(bpy.data.objects):bpy.data.objects.remove(o)
OUT={}
DEC={'lower':.42,'torso':.4,'arms':.6,'sup':.6,'mag':1}
LOD=False
HIP=.80;SH=1.27;LZ=.115   # torso pivot, shoulder height, leg spacing

def legs(P,kneel=False):
  if not kneel:
    for sd in (1,-1):
      z=LZ*sd
      P.cap('UNIFORM',(0,.70,z),(.015,.42,z*1.02),.092,.068,seg=10,rings=1)        # thigh
      P.ellip('UNIFORM',(-.03,.27,z),(.045,.075,.052),seg=8,rings=5)   # calf
      P.box('PLATE',(.06,.58,z*1.04),(.05,.18,.13),bev=.022,seg=2,rot=rotZ(-.06))     # thigh plate
      P.ellip('PLATEDK',(.058,.41,z*1.02),(.04,.05,.055),seg=8,rings=5)          # knee pad
      P.cap('UNIFORM',(.015,.40,z*1.02),(-.005,.11,z),.064,.05,seg=9,rings=1)    # shin
      P.box('PLATE',(.045,.26,z),(.035,.20,.095),bev=.015,rot=rotZ(.04))         # shin guard
      P.box('BOOT',(.035,.06,z),(.23,.12,.118),bev=.035,seg=2,taper=(.8,.9))    # boot
      P.box('BOOT',(.035,.012,z),(.235,.025,.118),bev=.008)                      # sole
  else:
    # (mgk) right knee down, left foot planted forward; hips at .45
    zL=-LZ;zR=LZ
    P.cap('UNIFORM',(0,.44,zL),(.30,.40,zL*1.05),.082,.066,seg=9,rings=1)
    P.ellip('PLATEDK',(.33,.42,zL*1.05),(.05,.05,.055),seg=8,rings=5)
    P.box('PLATE',(.16,.47,zL*1.05),(.17,.05,.12),bev=.02,rot=rotZ(.1))
    P.cap('UNIFORM',(.30,.40,zL*1.05),(.30,.11,zL),.064,.05,seg=9,rings=1)
    P.box('PLATE',(.345,.26,zL),(.035,.20,.095),bev=.015)
    P.box('BOOT',(.33,.055,zL),(.22,.11,.112),bev=.03,seg=2,taper=(.85,.9));P.box('BOOT',(.335,.012,zL),(.235,.025,.118),bev=.008)
    P.cap('UNIFORM',(0,.44,zR),(.04,.07,zR*1.05),.082,.066,seg=9,rings=1)
    P.ellip('PLATEDK',(.06,.055,zR*1.05),(.05,.05,.055),seg=8,rings=5)
    P.cap('UNIFORM',(.04,.07,zR*1.05),(-.26,.08,zR),.064,.05,seg=9,rings=1)
    P.box('BOOT',(-.33,.08,zR),(.11,.10,.11),bev=.03,seg=2,rot=rotZ(1.25))
  # pelvis + belt (static, above the leg box)
  hy=.80 if not kneel else .45
  P.ellip('UNIFORM',(0,hy-.02,0),(.125,.11,.19),seg=12,rings=7)
  P.box('STRAP',(0,hy+.04,0),(.25,.05,.36),bev=.02,seg=1)
  for zz in (-.11,.11):P.box('AMMO',(.11,hy+.02,zz),(.05,.07,.07),bev=.012)
  P.box('PLATEDK',(.10,hy-.06,0),(.04,.10,.16),bev=.015,rot=rotZ(.15))   # groin plate

def torso(P,y0=HIP,dx=0.0):
  Y=lambda v:y0+v
  P.box('UNIFORM',(dx-.01,Y(.11),0),(.18,.20,.29),bev=.06,seg=2,taper=(1.05,1.12))          # abdomen
  P.box('UNIFORM',(dx-.005,Y(.33),0),(.20,.25,.33),bev=.06,seg=2,taper=(1,1.12))    # ribcage
  P.box('VEST',(dx+.0,Y(.20),0),(.20,.07,.32),bev=.022)                       # cummerbund
  P.box('PLATE',(dx+.09,Y(.34),0),(.05,.22,.29),bev=.025,seg=2,rot=rotZ(-.06),taper=(1,1.08))  # chest plate (flat, slightly flared to the shoulders)
  for sd in (1,-1):P.box('PLATE',(dx+.03,Y(.34),sd*.16),(.13,.18,.04),bev=.02,rot=rotY(sd*-.15))   # side plates
  P.box('PLATEDK',(dx+.115,Y(.27),0),(.03,.05,.22),bev=.01)                     # lower chest rib
  for zz in (-.075,0,.075):P.box('AMMO',(dx+.13,Y(.22),zz),(.035,.065,.06),bev=.01)   # mag pouches
  P.box('PLATEDK',(dx-.10,Y(.33),0),(.05,.23,.28),bev=.025,rot=rotZ(.05))      # back plate
  P.box('PACK',(dx-.165,Y(.31),0),(.085,.18,.21),bev=.03,seg=2)                # pack
  P.box('STRAP',(dx-.165,Y(.415),.06),(.03,.03,.03),bev=.005);P.cyl('GUN',(dx-.17,Y(.40),.07),(dx-.18,Y(.56),.075),.006,seg=5)   # radio + whip
  P.box('VEST',(dx+.005,Y(.455),0),(.17,.05,.20),bev=.02)                       # collar
  P.cyl('SKIN',(dx,Y(.45),0),(dx+.01,Y(.53),0),.045,seg=8)                      # neck
  P.ellip('SKIN',(dx+.025,Y(.565),0),(.072,.08,.066),seg=10,rings=7)          # face
  # helmet: a compact rounded shell sitting down on the head, flared at the nape, ear cups and a crown stripe
  P.ellip('PLATE',(dx+.0,Y(.605),0),(.094,.072,.083),seg=12,rings=7)
  P.box('PLATE',(dx-.055,Y(.56),0),(.06,.05,.16),bev=.02,rot=rotZ(-.35))      # nape flare
  P.box('PLATEDK',(dx+.075,Y(.62),0),(.03,.022,.15),bev=.008,rot=rotZ(.25))   # brow ridge
  for zz in (-.082,.082):P.cyl('PLATEDK',(dx+.0,Y(.575),zz*.93),(dx,Y(.575),zz*1.12),.035,seg=8)   # ear cups
  P.box('ACCENT',(dx-.005,Y(.676),0),(.15,.012,.026),bev=.005)                 # crown stripe
  P.box('LENS',(dx+.06,Y(.585),-.045),(.012,.016,.02),bev=.003)               # comms eyepiece
  for sd in (1,-1):   # pauldrons (on the torso so they ride the body, not the gun)
    P.ellip('PLATE',(dx-.005,Y(.43),sd*.205),(.088,.042,.075),seg=10,rings=5,rot=rotX(sd*.45))
    P.box('ACCENT',(dx-.005,Y(.41),sd*.25),(.13,.022,.02),bev=.006,rot=rotX(sd*.45))

def arm(P,sh,el,ha,glove=True,plate=True):
  P.cap('UNIFORM',sh,el,.052,.044,seg=8,rings=1)
  P.cap('UNIFORM',el,ha,.045,.037,seg=8,rings=1)
  if plate:
    m=[(el[i]*.6+ha[i]*.4) for i in range(3)]
    import mathutils
    P.cap('PLATEDK',tuple(el[i]*.85+ha[i]*.15 for i in range(3)),tuple(el[i]*.35+ha[i]*.65 for i in range(3)),.05,.045,seg=8,rings=1,squash=.9)
  P.ellip('STRAP',ha,(.035,.03,.032),seg=8,rings=5)

def rifle(P,o,L=1.0,heavy=False):
  x,y,z=o   # stock butt point; gun along +x
  P.box('GUN',(x+.06,y-.005,z),(.12,.065,.04),bev=.012)                         # stock
  P.box('GUN',(x+.24,y+.0,z),(.26,.075,.048),bev=.014)                          # receiver
  P.box('GUNLT',(x+.27,y+.05,z),(.20,.02,.03),bev=.006)                         # top rail
  P.box('GUN',(x+.18,y-.065,z),(.035,.07,.032),bev=.008,rot=rotZ(.25))          # grip
  P.box('GUNLT',(x+.45,y+.005,z),(.17,.055,.042),bev=.012)                      # handguard
  P.cyl('GUN',(x+.52,y+.005,z),(x+.62*L,y+.005,z),.012 if not heavy else .02,seg=6)   # barrel
  P.box('GUNLT',(x+.27,y+.075,z),(.06,.035,.03),bev=.008)                       # optic
  if heavy:
    P.cyl('GUNLT',(x+.40,y+.005,z),(x+.62,y+.005,z),.032,seg=8)                 # cooling jacket
    P.box('GUN',(x+.06,y+.02,z),(.03,.04,.03))

def build(t):
  low=Part(t+'_lower');tor=Part(t+'_torso');arms=Part(t+'_arms');sup=Part(t+'_sup');mag=Part(t+'_mag')
  kneel=t=='mgk';hip=.45 if kneel else HIP;dx=.06 if kneel else 0
  legs(low,kneel);torso(tor,hip,dx)
  S=hip+.47;   # shoulder pivot (arms group origin)
  sx=dx
  if t in ('rifle','mg','mgk'):
    gy=S-.06;gz=.115;heavy=t!='rifle'
    rifle(arms,(sx+.0,gy,gz),L=1.25 if heavy else 1.0,heavy=heavy)
    arm(arms,(sx,S-.02,.20),(sx+.07,S-.20,.235),(sx+.19,S-.115,gz+.01))
    arm(sup,(sx,S-.02,-.20),(sx+.15,S-.19,-.15),(sx+.43,S-.09,gz-.03))
    if heavy:mag.box('AMMO',(0,0,0),(.09,.07,.06),bev=.012);mp=(sx+.22,gy-.07,gz+.05);muz=(sx+.62*1.25,gy+.005,gz)
    else:mag.box('GUN',(0,0,0),(.04,.10,.028),bev=.008,rot=rotZ(.2));mp=(sx+.31,gy-.085,gz);muz=(sx+.62,gy+.005,gz)
  elif t=='at':
    gy=S+.05;gz=.13
    arms.cyl('GUN',(sx-.30,gy,gz),(sx+.42,gy,gz),.05,seg=10)
    arms.cyl('GUNLT',(sx+.36,gy,gz),(sx+.46,gy,gz),.058,r2=.062,seg=10)
    arms.cyl('GUNLT',(sx-.36,gy,gz),(sx-.28,gy,gz),.062,r2=.056,seg=10)
    arms.box('GUN',(sx+.12,gy-.08,gz),(.035,.08,.03),bev=.008,rot=rotZ(.2))
    arms.box('GUN',(sx+.30,gy-.07,gz),(.03,.07,.03),bev=.008)
    arms.box('GUNLT',(sx+.10,gy+.065,gz-.04),(.08,.05,.03),bev=.01)    # sight
    arm(arms,(sx,S-.02,.20),(sx+.03,S-.21,.23),(sx+.12,gy-.11,gz))
    arm(sup,(sx,S-.02,-.20),(sx+.15,S-.17,-.12),(sx+.30,gy-.10,gz-.02))
    mag.cyl('PLATEDK',(-.04,0,0),(.04,0,0),.045,r2=.03,seg=10);mag.ellip('ACCENT',(.06,0,0),(.03,.03,.03),seg=8,rings=5)
    mp=(sx+.47,gy,gz);muz=(sx+.47,gy,gz)
  elif t=='flagb':
    gy=S-.08;gz=.05
    arms.box('GUN',(sx+.36,gy,gz),(.12,.045,.03),bev=.01);arms.box('GUN',(sx+.32,gy-.05,gz),(.03,.07,.028),bev=.008,rot=rotZ(.2))
    arm(arms,(sx,S-.02,.20),(sx+.12,S-.17,.20),(sx+.31,gy-.04,gz+.02))
    arm(sup,(sx,S-.02,-.20),(sx+.12,S-.17,-.18),(sx+.30,gy-.05,gz-.03))
    mag.box('GUN',(0,0,0),(.02,.05,.02));mp=(sx+.32,gy-.08,gz);muz=(sx+.43,gy,gz)
  obs={}
  for P in (low,tor,arms,sup,mag):
    if P.roles:
      ob=obs[P.name]=P.finish()
      for pl in ob.data.polygons:pl.use_smooth=True
      ob.data.set_sharp_from_angle(angle=.75)
      d=ob.modifiers.new('dec','DECIMATE');d.ratio=DEC.get(P.name.split('_',1)[1],.5)
  rig={'torso':[0,hip,0],'arms':[0,.47,0],'mag':[mp[0],mp[1]-S,mp[2]],'muz':[muz[0],muz[1]-S,muz[2]],'sup':[0,-.02,-.20]}
  OUT[t]={'rig':rig,'obs':obs,'S':S,'hip':hip}
  return obs

if __name__=='__main__':
  import os
  ts=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['rifle']
  for t in ts:build(t)
  # preview: place the mag at its spot for the render
  for t in ts:
    o=OUT[t]
    if t+'_mag' in o['obs']:
      r=o['rig'];o['obs'][t+'_mag'].location=G(r['mag'][0],r['mag'][1]+o['S'],r['mag'][2])
  names=[n for t in ts for n in OUT[t]['obs']]
  for i,(v,nm) in enumerate([((1,.12,0),'a'),((1,.35,.9),'b'),((0,.1,1),'c'),((-1,.3,-.7),'d')]):
    render('/home/claude/mar/prev_%s.png'%nm,names,view=v,res=(500,700),ortho=.85,target=(0.1,.78,0))
  # pack
  pk={}
  for t in ts:
    o=OUT[t];r=o['rig'];S=o['S']
    for n,ob in o['obs'].items():
      part=n.split('_',1)[1]
      if part=='mag':ob.location=(0,0,0);off=(0,0,0)
      elif part=='lower':off=(0,0,0)
      elif part=='torso':off=(0,o['hip'],0)
      elif part=='arms':off=(0,S,0)
      elif part=='sup':off=(0,S-.02,-.20)
      pk['inf_'+n]=pack(ob,off)
      if part!='mag':
        dm=ob.modifiers['dec'];r0=dm.ratio;dm.ratio=r0*.3;pk['inf_'+n+'L']=pack(ob,off);dm.ratio=r0
    pk['_rig_'+t]=r
  json.dump(pk,open('/home/claude/mar/marine_out.json','w'))
  print({k:v['n'] for k,v in pk.items() if not k.startswith('_')})
