import sys,json;sys.path.insert(0,'/home/claude/anim')
from pose import *
BASE={'thigh.R':(0,0,.2),'thigh.L':(0,0,.2),'shin.R':(0,0,-.38),'shin.L':(0,0,-.38),'foot.R':(0,0,.18),'foot.L':(0,0,.18),'spine':(0,0,-.1),'head':(0,0,.08),'aim':(0,.3,-.5)}
BASEH=-.045
# peak poses of the idle bank (offsets on top of BASE); the clips ease in to these and out again
POSES=json.load(open('/home/claude/anim/poses.json'))
def comb(*Ds):
  O={}
  for D in Ds:
    for b,v in D.items():O[b]=tuple(a+c for a,c in zip(O.get(b,(0,0,0)),v))
  return O
if __name__=='__main__':
  clear();names=[];ks=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else list(POSES)
  for i,k in enumerate(ks):
    names.append(mesh(k,'rifle',comb(BASE,POSES[k]),BASEH,off=(0,0,(i-(len(ks)-1)/2)*1.1)).name)
  w=len(ks)*1.1
  render('/home/claude/anim/idle_a.png',names,view=(1,.25,.55),res=(180*len(ks),520),ortho=max(1.2,w*.5),target=(0,.75,0))
  render('/home/claude/anim/idle_b.png',names,view=(.2,.25,1),res=(180*len(ks),520),ortho=max(1.2,w*.5),target=(0,.75,0))
