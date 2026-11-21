import sys;sys.path.insert(0,'/home/claude/mar')
import bpy
import marine as MR
from mlib import *
ts=sys.argv[sys.argv.index('--')+1:]
for o in list(bpy.data.objects):bpy.data.objects.remove(o)
names=[]
for i,t in enumerate(ts):
  obs=MR.build(t);o=MR.OUT[t]
  for n,ob in obs.items():
    if n.endswith('_mag'):r=o['rig'];ob.location=G(r['mag'][0],r['mag'][1]+o['S'],r['mag'][2])
    ob.location=ob.location+G(0,0,(i-(len(ts)-1)/2)*.75)
    names.append(n)
w=len(ts)*.75
render('/home/claude/mar/pv_front.png',names,view=(1,.15,0),res=(260*len(ts),700),ortho=max(1.4,w*.55),target=(0.1,1.1,0))
render('/home/claude/mar/pv_back.png',names,view=(-1,.3,.5),res=(260*len(ts),700),ortho=max(1.4,w*.55),target=(0.1,1.1,0))
