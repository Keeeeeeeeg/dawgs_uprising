import sys;sys.path.insert(0,'/home/claude/anim')
from pose import *
clear()
def prone(pr,variant):
  O={};add=lambda b,x,y,z:O.__setitem__(b,tuple(a+bb for a,bb in zip(O.get(b,(0,0,0)),(x,y,z))))
  add('hips',0,0,-1.42*pr);add('aim',0,0,1.25*pr);add('head',0,0,1.05*pr);add('spine',0,0,.12*pr)
  if variant==0:add('thigh.L',-.14*pr,0,0);add('thigh.R',.14*pr,0,0);add('foot.L',0,0,.7*pr);add('foot.R',0,0,.7*pr);add('shin.R',0,0,-.2*pr)
  else:   # supported prone: legs spread wide, heels down and toes turned out flat
    add('thigh.L',.42*pr,0,0);add('thigh.R',-.42*pr,0,0);add('shin.L',0,0,-.05*pr);add('shin.R',0,0,-.05*pr)
    add('foot.L',.2*pr,1.25*pr,.15*pr);add('foot.R',-.2*pr,-1.25*pr,.15*pr)
  return O,-.63*pr
names=[]
for i,v in enumerate((0,1)):
  O,h=prone(1,v);names.append(mesh('p%d'%i,'sniper',O,h,off=(0,0,i*1.6-.8)).name)
render('/home/claude/anim/prone_top.png',names,view=(0,1,.001),res=(700,700),ortho=1.6,target=(-.6,.2,0))
render('/home/claude/anim/prone_side.png',names,view=(-.5,.6,1),res=(700,500),ortho=1.4,target=(-.6,.2,0))
