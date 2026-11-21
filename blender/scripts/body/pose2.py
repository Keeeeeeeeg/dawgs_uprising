# (phase B) pose previewer for the textured marines (window.SKINT format): three.js Euler 'YZX' bones + LBS, per part
import sys,json,math,base64,struct,os
import numpy as np,bpy
from mathutils import Vector
SKT={}
def load(t):
  if t not in SKT:SKT[t]=json.load(open('/home/claude/lp/%s/skin_%s.json'%(t,t)))
  return SKT[t]
def eul(x,y,z):
  cx,sx,cy,sy,cz,sz=math.cos(x),math.sin(x),math.cos(y),math.sin(y),math.cos(z),math.sin(z)
  Rx=np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]]);Ry=np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]]);Rz=np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
  return Ry@Rz@Rx
def decode(d):
  b=base64.b64decode(d['p']);P=np.array(struct.unpack('<%dh'%(len(b)//2),b),dtype=float).reshape(-1,3)/1000
  si=np.frombuffer(base64.b64decode(d['si']),dtype=np.uint8).reshape(-1,2);sw=np.frombuffer(base64.b64decode(d['sw']),dtype=np.uint8)/255
  return P,si,sw
def posed(t,part,O,hipY=0):
  S0=load(t);d=S0['parts'][part]
  if isinstance(d,str):d=load(d)['parts'][part]
  P,si,sw=decode(d);B=S0['bones'];n=len(B);W=[None]*n
  for i,(nm,p,h) in enumerate(B):
    M=np.eye(4);hp=np.array(h)-(np.array(B[p][2]) if p>=0 else 0)
    if nm=='hips':hp=hp+np.array([0,hipY,0])
    M[:3,3]=hp;M[:3,:3]=eul(*O.get(nm,(0,0,0)));W[i]=(W[p]@M) if p>=0 else M
  S=np.array([W[i]@np.block([[np.eye(3),-np.array(h)[:,None]],[np.zeros((1,3)),np.ones((1,1))]]) for i,(nm,p,h) in enumerate(B)])
  V=np.c_[P,np.ones(len(P))];A=np.einsum('vij,vj->vi',S[si[:,0]],V);Bv=np.einsum('vij,vj->vi',S[si[:,1]],V)
  return (A*sw[:,None]+Bv*(1-sw[:,None]))[:,:3]
MATS={}
def gm(part):
  if part not in MATS:
    m=bpy.data.materials.new(part);m.use_nodes=True;b=m.node_tree.nodes['Principled BSDF'];b.inputs['Base Color'].default_value={'body':(.35,.36,.28,1),'helmet':(.25,.25,.27,1),'weapon':(.05,.05,.05,1),'allL':(.4,.3,.3,1)}[part];MATS[part]=m
  return MATS[part]
def mesh(name,t,O,hipY=0,off=(0,0,0),parts=('body','helmet','weapon')):
  obs=[]
  for part in parts:
    V=posed(t,part,O,hipY);me=bpy.data.meshes.new(name+part)
    vs=[(-v[2]+off[0],v[0]+off[1],v[1]+off[2]) for v in V]   # game (x fwd,y up,z right) -> Blender (x right?) : x=-z... keep: X=-z (left), Y=x (fwd), Z=y
    me.from_pydata(vs,[],[(k*3,k*3+1,k*3+2) for k in range(len(V)//3)]);me.materials.append(gm(part))
    o=bpy.data.objects.new(name+part,me);bpy.context.scene.collection.objects.link(o);obs.append(o)
  return obs
def game_idle(lowready=True,cr=.75,st=1.0):
  O={};hipY=0
  def add(b,x,y,z):o=O.setdefault(b,[0,0,0]);o[0]+=x;o[1]+=y;o[2]+=z
  for sd in 'RL':add('thigh.'+sd,0,0,.2*cr);add('shin.'+sd,0,0,-.38*cr);add('foot.'+sd,0,0,.18*cr)
  hipY-=.045*cr;add('spine',0,0,-.1*cr);add('head',0,0,.08*cr)
  if st>.01:add('thigh.L',0,0,.22*st);add('shin.L',0,0,-.12*st);add('foot.L',0,0,-.1*st);add('thigh.R',0,0,-.14*st);add('shin.R',0,0,-.1*st);add('foot.R',0,0,.24*st);add('hips',0,-.22*st,0);add('spine',0,.14*st,0)
  if lowready:add('aim',0,.3,-.5)
  return O,hipY
