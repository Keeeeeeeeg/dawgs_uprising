import os
os.environ['NOHEAD']='1'
exec(open('/home/claude/body/body5.py').read());exec(open('/home/claude/wpn/weapons6.py').read())
from mathutils.bvhtree import BVHTree
R={}
for k,(kind,z) in enumerate((('rifle',2.45),('sniper',1.75),('mg',1.05),('rocket',-.05))):
  R[kind]=build_weapon(kind,(Vector((0,0,z)),Matrix.Identity(3)),('hang',0),.5 if kind=='rocket' else 0)
dg=bpy.context.evaluated_depsgraph_get()
for kind,obs in R.items():
  T={o:BVHTree.FromObject(o,dg) for o in obs};n=0
  for o in obs:
    if not any(T[o].overlap(T[q]) for q in obs if q is not o):
      vs=[v.co for v in o.evaluated_get(dg).data.vertices];print('FLOAT',kind,o.data.name,[round(c,3) for c in sum(vs,Vector())/max(1,len(vs))]);n+=1
  print('QA',kind,len(obs),'parts, floating',n,' tris',sum(len(o.evaluated_get(dg).data.polygons) for o in obs))
if os.environ.get('QAONLY'):raise SystemExit
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=int(os.environ.get('SAMP','48'));sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
w=bpy.data.worlds.new('W');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(.13,.135,.13,1)
for nm,loc,en,sz in (('k',(2,-4,4),700,4),('r',(-3,3,2),300,4),('f',(1,-5,0),200,6)):
  l=bpy.data.objects.new(nm,bpy.data.lights.new(nm,'AREA'));sc.collection.objects.link(l);l.data.energy=en;l.data.size=sz;l.location=loc;l.rotation_euler=(Vector((.3,0,1.2))-Vector(loc)).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
def shot(nm,d,tgt,osc,res):
  tgt=Vector(tgt);cam.data.ortho_scale=osc;sc.render.resolution_x,sc.render.resolution_y=res;pos=tgt+Vector(d).normalized()*8;cam.location=pos;cam.rotation_euler=(tgt-pos).to_track_quat('-Z','Y').to_euler();sc.render.filepath='/home/claude/wpn/'+nm+'.png';bpy.ops.render.render(write_still=True)
which=os.environ.get('SHOTS','side,q,closeR,closeM,rifleside').split(',')
if 'rifleside' in which:shot('w11_rifle_side',(0,1,0),(.25,0,2.4),1.35,(1600,800))
if 'side' in which:shot('w11_side_left',(0,1,0),(.35,0,1.2),2.9,(1600,1600))
if 'q' in which:shot('w11_34',(.55,.8,.35),(.35,0,1.2),3.0,(1600,1600))
if 'closeR' in which:shot('w11_rifle_close',(.35,.85,.25),(.15,0,2.42),1.05,(1600,900))
if 'grip' in which:shot('w11_rifle_grip',(.25,.9,-.1),(.0,0,2.4),.42,(1400,900))
if 'afg' in which:shot('w11_rifle_afg',(.3,.88,-.15),(.55,0,2.43),.38,(1400,900))
if 'closeM' in which:shot('w11_mg_close',(.3,-.9,.3),(.3,0,1.05),1.25,(1600,900))
bpy.ops.wm.save_as_mainfile(filepath='/home/claude/wpn/weapons11.blend')
