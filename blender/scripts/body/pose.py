# (v25.32) pose previewer: poses the game's skinned marines exactly as three.js does (bones = translation + Euler 'YZX',
# linear blend skinning) and renders them in Blender, so idle clips and stances can be authored and checked here.
import sys,json,math,base64,struct;sys.path.insert(0,'/home/claude/mar')
import numpy as np,bpy
from mlib import G,mat,render
SK=json.load(open('/home/claude/mar/skin_out.json'))
def decode(t):
  d=SK[t];b=base64.b64decode(d['p']);P=np.array(struct.unpack('<%dh'%(len(b)//2),b),dtype=float).reshape(-1,3)/1000
  r=base64.b64decode(d['r']);si=np.frombuffer(base64.b64decode(d['si']),dtype=np.uint8).reshape(-1,2);sw=np.frombuffer(base64.b64decode(d['sw']),dtype=np.uint8)/255
  return d,P,list(r),si,sw
def eul(x,y,z):   # three.js Euler order YZX: R = Ry * Rz * Rx
  cx,sx,cy,sy,cz,sz=math.cos(x),math.sin(x),math.cos(y),math.sin(y),math.cos(z),math.sin(z)
  Rx=np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]]);Ry=np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]]);Rz=np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
  return Ry@Rz@Rx
def posed(t,O,hipY=0):
  d,P,r,si,sw=decode(t);B=d['bones'];n=len(B);W=[None]*n
  for i,(nm,p,h) in enumerate(B):
    M=np.eye(4);hp=np.array(h)-(np.array(B[p][2]) if p>=0 else 0);
    if nm=='hips':hp=hp+np.array([0,hipY,0])
    M[:3,3]=hp;M[:3,:3]=eul(*O.get(nm,(0,0,0)));W[i]=(W[p]@M) if p>=0 else M
  S=[]
  for i,(nm,p,h) in enumerate(B):Bi=np.eye(4);Bi[:3,3]=-np.array(h);S.append(W[i]@Bi)
  S=np.array(S);V=np.c_[P,np.ones(len(P))]
  A=np.einsum('vij,vj->vi',S[si[:,0]],V);Bv=np.einsum('vij,vj->vi',S[si[:,1]],V)
  return (A*sw[:,None]+Bv*(1-sw[:,None]))[:,:3],d,r
def mesh(name,t,O,hipY=0,off=(0,0,0),yaw=0):
  V,d,r=posed(t,O,hipY);c,s=math.cos(yaw),math.sin(yaw)
  me=bpy.data.meshes.new(name);vs=[];fs=[]
  for i,v in enumerate(V):x,y,z=v;x,z=x*c-z*s,x*s+z*c;vs.append(G(x+off[0],y+off[1],z+off[2]))
  for k in range(len(V)//3):fs.append((k*3,k*3+1,k*3+2))
  me.from_pydata(vs,[],fs);roles=d['roles']
  for ro in roles:me.materials.append(mat(ro))
  for k,pl in enumerate(me.polygons):pl.material_index=r[k]
  ob=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(ob);return ob
def clear():
  for o in list(bpy.data.objects):bpy.data.objects.remove(o)
