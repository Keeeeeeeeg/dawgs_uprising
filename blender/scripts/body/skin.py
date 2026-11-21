# (v25.14) skinned marine: one body mesh + weapon, weights from a skeleton of segments. Exports mar/skin_<t>.json
import sys,json,math,base64,struct;sys.path.insert(0,'/home/claude/mar')
import bpy
from mathutils import Vector
import marine as MR
from mlib import *

# skeleton: name, parent, head, tail (raw game coords)
SK0=SK=[('hips',None,(0,.80,0),(0,.95,0)),('spine','hips',(0,.95,0),(0,1.12,0)),('chest','spine',(0,1.12,0),(0,1.27,0)),('head','chest',(0,1.27,0),(.02,1.48,0)),('aim','chest',(0,1.22,0),(.1,1.22,0)),
 ('thigh.R','hips',(0,.76,.115),(.015,.40,.117)),('shin.R','thigh.R',(.015,.40,.117),(-.005,.085,.115)),('foot.R','shin.R',(-.005,.085,.115),(.13,.03,.115)),
 ('thigh.L','hips',(0,.76,-.115),(.015,.40,-.117)),('shin.L','thigh.L',(.015,.40,-.117),(-.005,.085,-.115)),('foot.L','shin.L',(-.005,.085,-.115),(.13,.03,-.115)),
 ('arm.R','aim',(0,1.25,.20),(.07,1.07,.235)),('fore.R','arm.R',(.07,1.07,.235),(.19,1.155,.125)),('hand.R','fore.R',(.19,1.155,.125),(.24,1.15,.125)),
 ('arm.L','aim',(0,1.25,-.20),(.15,1.08,-.15)),('fore.L','arm.L',(.15,1.08,-.15),(.43,1.18,.085)),('hand.L','fore.L',(.43,1.18,.085),(.47,1.18,.09)),
 ('gun','hand.R',(.19,1.155,.125),(.4,1.155,.125)),('mag','gun',(.31,1.065,.115),(.31,1.0,.115))]
NAMES=[b[0] for b in SK];IDX={n:i for i,n in enumerate(NAMES)}
CLOTH={'UNIFORM','SKIN','STRAP','VEST','GHILLIE','GHILLIE2','CANVAS'}
def segd(p,a,b):
  a=Vector(a);b=Vector(b);ab=b-a;t=max(0,min(1,(p-a).dot(ab)/max(1e-9,ab.length_squared)));return (p-(a+ab*t)).length
FAM=lambda i:[i]+[IDX[SK[i][1]]] if SK[i][1] else [i]

ARMS=[]
_arm=MR.arm
def _rec(P,sh,el,ha,**k):ARMS.append((P.name,sh,el,ha));return _arm(P,sh,el,ha,**k)
MR.arm=_rec
def skel(t):
  # per type: arm joints from the builder's arm() calls; kneeling gunner gets its own hips
  sk=[list(b) for b in SK]
  for nm,sh,el,ha in ARMS:
    sd='R' if nm.endswith('_arms') else 'L'
    for b in sk:
      if b[0]=='arm.'+sd:b[2],b[3]=sh,el
      if b[0]=='fore.'+sd:b[2],b[3]=el,ha
      if b[0]=='hand.'+sd:b[2]=ha;b[3]=(ha[0]+.05,ha[1],ha[2])
      if sd=='R' and b[0]=='gun':b[2]=ha;b[3]=(ha[0]+.2,ha[1],ha[2])
  return sk
def build(t,variant=0,ratio=.45):
  global SK
  SK=SK0
  for o in list(bpy.data.objects):bpy.data.objects.remove(o)
  MR.OUT.clear();ARMS.clear();obs=MR.build(t);SK=skel(t)
  tris=[]   # (role, [p0,p1,p2] game coords, part)
  dg=bpy.context.evaluated_depsgraph_get()
  for n,ob in obs.items():
    part=n.split('_',1)[1]
    if part.endswith('L'):continue
    o=MR.OUT[t];r=o['rig'];S=o['S']
    if part=='mag':ob.location=G(r['mag'][0],r['mag'][1]+S,r['mag'][2])
    d=ob.modifiers.get('dec')
    if d:d.ratio=ratio if part in('lower','torso') else (.7 if ratio>.3 else .3)
    dg.update();ev=ob.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();M=ob.matrix_world
    for tr in me.loop_triangles:
      role=ob.data.materials[tr.material_index].name.split('.')[0]
      ps=[Vector(ungame(M@me.vertices[v].co)) for v in tr.vertices]
      tris.append((role,ps,part))
  return tris

def weights(tris,t):
  out=[]
  gunroles={'GUN','GUNLT'}
  for role,ps,part in tris:
    c=(ps[0]+ps[1]+ps[2])/3
    if part=='mag':out.append((role,ps,[(IDX['mag'],1)]*3));continue
    if part in('arms','sup') and role in gunroles and t!='at' or (t=='at' and part=='arms' and role in gunroles):
      out.append((role,ps,[(IDX['gun'],1)]*3));continue
    cand=[i for i in range(len(SK)-2) if NAMES[i]!='aim']
    if part=='sup':cand=[IDX['arm.L'],IDX['fore.L'],IDX['hand.L']]
    elif part=='arms':cand=[IDX['arm.R'],IDX['fore.R'],IDX['hand.R']]
    elif part=='lower':cand=[IDX[n] for n in ('hips','thigh.R','shin.R','foot.R','thigh.L','shin.L','foot.L')]
    elif part=='torso':cand=[IDX[n] for n in ('hips','spine','chest','head')]
    if role in CLOTH:
      ws=[]
      for p in ps:
        ds=sorted((segd(p,SK[i][2],SK[i][3]),i) for i in cand)
        (d0,i0),(d1,i1)=ds[0],ds[1]
        # blend only between bones that are connected (parent/child), within a short band
        if (SK[i1][1]==NAMES[i0] or SK[i0][1]==NAMES[i1]) and d1-d0<.05:
          w0=.5+.5*min(1,(d1-d0)/.05);ws.append((i0,w0,i1))
        else:ws.append((i0,1,i0))
      out.append((role,ps,[(a,w,b) for a,w,b in ws]))
    else:
      i0=min(cand,key=lambda i:segd(c,SK[i][2],SK[i][3]));out.append((role,ps,[(i0,1)]*3))
  return out

def export(t,path,ratio=.45):
  tris=build(t,ratio=ratio);W=weights(tris,t)
  P=[];R=[];SI=[];SW=[];roles=[]
  for role,ps,ws in W:
    if role not in roles:roles.append(role)
    R.append(roles.index(role))
    for p,w in zip(ps,ws):
      P+=[int(round(p.x*1000)),int(round(p.y*1000)),int(round(p.z*1000))]
      if len(w)==2:SI+=[w[0],w[0]];SW.append(255)
      else:SI+=[w[0],w[2]];SW.append(int(round(w[1]*255)))
  b64=lambda fmt,a:base64.b64encode(struct.pack(fmt%len(a),*a)).decode()
  return {'roles':roles,'p':b64('<%dh',P),'r':base64.b64encode(bytes(R)).decode(),'si':base64.b64encode(bytes(SI)).decode(),'sw':base64.b64encode(bytes(SW)).decode(),'n':len(R)}

if __name__=='__main__':
  ts=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['rifle']
  res={}
  for t in ts:
    res[t]=export(t,None,.45);res[t]['rig']=MR.OUT[t]['rig'];res[t]['bones']=[[n,(IDX[p] if p else -1),list(h)] for n,p,h,tl in SK];res[t+'L']=export(t,None,.13)
    print(t,res[t]['n'],res[t+'L']['n'])
  json.dump(res,open('/home/claude/mar/skin_out.json','w'))
