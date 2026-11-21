import sys,json,math;sys.path.insert(0,'/home/claude/anim')
import numpy as np
from pose import SK,eul
from idles import BASE,BASEH,comb
def joints(t,O,hipY=0):
  B=SK[t]['bones'];W=[None]*len(B);J={}
  for i,(nm,p,h) in enumerate(B):
    M=np.eye(4);hp=np.array(h)-(np.array(B[p][2]) if p>=0 else 0)
    if nm=='hips':hp=hp+np.array([0,hipY,0])
    M[:3,3]=hp;M[:3,:3]=eul(*O.get(nm,(0,0,0)));W[i]=(W[p]@M) if p>=0 else M;J[nm]=W[i][:3,3].copy()
  return J
def solve(t,O0,bones,targets,iters=4000,seed=1):
  """targets: {joint name: world pos}; tweak the euler of `bones` (added to O0) to reach them"""
  rng=np.random.default_rng(seed);x=np.zeros(3*len(bones))
  def err(x):
    O=dict(O0)
    for i,b in enumerate(bones):O[b]=tuple(np.array(O.get(b,(0,0,0)))+x[i*3:i*3+3])
    J=joints(t,O,BASEH);return sum(np.sum((J[k]-np.array(v))**2) for k,v in targets.items())+.002*np.sum(x**2)
  e=err(x);step=.6
  for it in range(iters):
    c=x+rng.normal(0,step,len(x));ec=err(c)
    if ec<e:x,e=c,ec
    if it%400==399:step*=.6
  return {b:[round(float(v),3) for v in x[i*3:i*3+3]] for i,b in enumerate(bones)},e
if __name__=='__main__':
  t='rifle';O0=comb(BASE);J=joints(t,O0,BASEH);sh=J['arm.L'];hd=J['head']
  print('shoulder',sh.round(3),'head',hd.round(3),'elbow',J['fore.L'].round(3),'hand',J['hand.L'].round(3))
  S=lambda *v:(sh+np.array(v)).tolist()
  def A(e,h,up=.23,lo=.38):
    e=np.array(e,float);h=np.array(h,float);E=sh+e/np.linalg.norm(e)*up;return {'fore.L':E.tolist(),'hand.L':(E+h/np.linalg.norm(h)*lo).tolist()}
  T={'fist':A((.1,.05,-1),(.1,1,0)),'point':A((1,.2,-.35),(1,.25,-.25)),'wave':A((.7,.8,-.5),(.5,1,.05)),
     'helmet':{'fore.L':(sh+np.array([.12,.08,-.18])).tolist(),'hand.L':(hd+np.array([.07,.14,-.09])).tolist()},'nod':A((.3,-1,-.2),(1,.5,.1)),'talk':A((.25,-1,-.25),(1,.55,.3))}
  T0={'fist':{'fore.L':S(.04,.0,-.26),'hand.L':S(.06,.27,-.27)},
     'point':{'fore.L':S(.21,.03,-.12),'hand.L':S(.44,.08,-.16)},
     'wave':{'fore.L':S(.14,.17,-.14),'hand.L':S(.24,.38,-.12)},
     'helmet':{'fore.L':S(.12,.02,-.22),'hand.L':(hd+np.array([.05,.2,-.09])).tolist()},
     'nod':{'fore.L':S(.1,-.2,-.08),'hand.L':S(.3,-.1,-.02)},
     'talk':{'fore.L':S(.06,-.21,-.12),'hand.L':S(.24,-.15,-.2)}}
  P=json.load(open('poses.json'))
  for k,tg in T.items():
    extra={b:v for b,v in P[k].items() if b not in('arm.L','fore.L')}
    sol,e=solve(t,comb(BASE,extra),['arm.L','fore.L'],tg)
    print(k,round(e,5),sol);P[k]=dict(extra,**sol)
  P['scan']={'aim':[0,-0.35,0.35],'head':[0,-0.3,0.05],'spine':[0,-0.1,0]}
  json.dump(P,open('poses.json','w'),indent=1)
