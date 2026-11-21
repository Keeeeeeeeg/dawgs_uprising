# (v25.32) the idle flavour bank, built from the Blender-checked peak poses (poses.json): each clip eases in, holds with a little
# life in it, and eases out. tags: idle (anyone, alone), sig (starts an exchange: the buddy answers with an 'ack' clip), ack
import json
P=json.load(open('/home/claude/anim/poses.json'))
def sc(D,k):return {b:[round(v*k,3) for v in x] for b,x in D.items()}
def clip(T,tags,w,keys):   # keys: [(t, pose dict)] -> per-bone tracks
  bones=sorted({b for _,D in keys for b in D});k={}
  for b in bones:k[b]=[[t,D.get(b,[0,0,0])] for t,D in keys]
  return {'T':T,'tags':tags,'w':w,'k':k}
Z={}
C={
 'ammoCheck':clip(4.2,['idle'],3,[(0,Z),(.2,P['ammo']),(.5,sc(P['ammo'],.9)),(.75,P['ammo']),(1,Z)]),
 'shadeEyes':clip(4.5,['idle'],2,[(0,Z),(.22,P['helmet']),(.45,dict(P['helmet'],head=[0,.35,-.05])),(.7,dict(P['helmet'],head=[0,-.3,-.05])),(.85,P['helmet']),(1,Z)]),
 'scanRifle':clip(5,['idle'],3,[(0,Z),(.18,P['scan']),(.5,dict(P['scan'],aim=[0,.35,.35],head=[0,.3,.05],spine=[0,.1,0])),(.82,P['scan']),(1,Z)]),
 'gesture':clip(3.2,['idle'],2,[(0,Z),(.25,P['talk']),(.5,sc(P['talk'],.8)),(.75,P['talk']),(1,Z)]),
 'sigHalt':clip(2.4,['sig'],2,[(0,Z),(.2,P['fist']),(.8,P['fist']),(1,Z)]),
 'sigPoint':clip(2.6,['sig'],2,[(0,Z),(.25,P['point']),(.75,P['point']),(1,Z)]),
 'sigMoveUp':clip(2.8,['sig'],2,[(0,Z),(.2,P['wave']),(.4,P['point']),(.6,P['wave']),(.8,P['point']),(1,Z)]),
 'sigTalk':clip(3.6,['sig'],2,[(0,Z),(.2,P['talk']),(.45,sc(P['talk'],.7)),(.7,P['talk']),(1,Z)]),
 'ackNod':clip(1.6,['ack'],3,[(0,Z),(.3,P['nod']),(.5,dict(P['nod'],head=[0,-.1,-.1])),(.7,P['nod']),(1,Z)]),
 'ackThumb':clip(1.8,['ack'],2,[(0,Z),(.3,P['fist']),(.7,P['fist']),(1,Z)]),
}
json.dump(C,open('/home/claude/anim/clips.json','w'),separators=(',',':'))
print(list(C))
