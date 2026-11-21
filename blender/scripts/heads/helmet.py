# (concept) full-face marine helmet, our own design in the spirit of a future-soldier helmet: rounded ballistic shell with
# a rail, a wide wrap visor, a segmented jaw guard with breathing vents and a chin module. Real metres, head centre at origin.
import bpy,bmesh,math
from mathutils import Vector,Matrix
for o in list(bpy.data.objects):bpy.data.objects.remove(o)
def M(name,col,rough=.5,metal=0,emit=0,trans=0):
  m=bpy.data.materials.new(name);m.use_nodes=True;b=m.node_tree.nodes['Principled BSDF']
  b.inputs['Base Color'].default_value=col+(1,);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
  if emit:b.inputs['Emission Color'].default_value=col+(1,);b.inputs['Emission Strength'].default_value=emit
  if trans:b.inputs['Transmission Weight'].default_value=trans;b.inputs['IOR'].default_value=1.45
  return m
SHELL=M('shell',(.18,.19,.18),.55);DARK=M('dark',(.05,.05,.05),.5);VIS=M('visor',(.02,.025,.03),.05,.6);EYE=M('eye',(.2,1,.45),.3,0,8);RUB=M('rubber',(.03,.03,.03),.8);METL=M('metal',(.3,.3,.3),.35,.8)
def obj(name,bm,mat,smooth=True,bev=0,sol=0):
  me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free();o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o);me.materials.append(mat)
  for p in me.polygons:p.use_smooth=smooth
  if sol:s=o.modifiers.new('s','SOLIDIFY');s.thickness=sol;s.offset=-1
  if bev:b=o.modifiers.new('b','BEVEL');b.width=bev;b.segments=2;b.limit_method='ANGLE'
  o.modifiers.new('w','WEIGHTED_NORMAL');return o
def sphere_cut(r,sx,sy,sz,keep):   # keep(v) -> True to keep the vertex (faces with any dropped vertex are deleted)
  bm=bmesh.new();bmesh.ops.create_uvsphere(bm,u_segments=64,v_segments=40,radius=r)
  for v in bm.verts:v.co=Vector((v.co.x*sx,v.co.y*sy,v.co.z*sz))
  bmesh.ops.delete(bm,geom=[v for v in bm.verts if not keep(v.co)],context='VERTS');return bm
# shell: rounded dome, cut high at the front (brow), lower at the sides and the nape (blender: -y = front, z up)
def shell_keep(c):
  fr=max(0,-c.y)/0.13;return c.z>(.0+.035*fr*fr) - .02*(1-fr)
sh=obj('shell',sphere_cut(.13,1,1.08,1,shell_keep),SHELL,sol=.012,bev=.003)
# visor: a band of a slightly larger sphere across the front
def vis_keep(c):return c.y<-.02 and -.045<c.z<.04
vi=obj('visor',sphere_cut(.128,1.02,1.12,1,vis_keep),VIS,sol=.004)
# eyepiece glow on the left lens
bm=bmesh.new();bmesh.ops.create_uvsphere(bm,u_segments=12,v_segments=8,radius=.012);bmesh.ops.scale(bm,vec=(1.2,.3,.8),verts=bm.verts);bmesh.ops.translate(bm,vec=(-.045,-.142,.005),verts=bm.verts);obj('eye',bm,EYE)
# jaw guard: lower front of a sphere, segmented by two horizontal grooves (separate bands)
for k,(z0,z1) in enumerate(((-.06,-.048),(-.1,-.064),(-.15,-.104))):
  def jk(c,z0=z0,z1=z1):return c.y<-.0 and z0<c.z<z1 and abs(c.x)<.11-.15*(z1+.06)*-1
  obj('jaw%d'%k,sphere_cut(.125,1.0,1.18-k*.04,1.05,jk),SHELL,sol=.01,bev=.002)
# breathing vents: slotted ovals each side of the jaw
for s in (1,-1):
  for i in range(3):
    bm=bmesh.new();bmesh.ops.create_cube(bm,size=1);bmesh.ops.scale(bm,vec=(.006,.012,.03),verts=bm.verts)
    bmesh.ops.rotate(bm,cent=(0,0,0),matrix=Matrix.Rotation(s*.75,3,'Z'),verts=bm.verts)
    bmesh.ops.translate(bm,vec=(s*(.07+i*.012),-.105+i*.012,-.085),verts=bm.verts);obj('vent',bm,DARK,bev=.002)
# chin module
bm=bmesh.new();bmesh.ops.create_cube(bm,size=1);bmesh.ops.scale(bm,vec=(.05,.03,.035),verts=bm.verts);bmesh.ops.translate(bm,vec=(0,-.15,-.13),verts=bm.verts);obj('chin',bm,SHELL,bev=.006)
bm=bmesh.new();bmesh.ops.create_cube(bm,size=1);bmesh.ops.scale(bm,vec=(.026,.012,.02),verts=bm.verts);bmesh.ops.translate(bm,vec=(0,-.167,-.132),verts=bm.verts);obj('filt',bm,DARK,bev=.003)
# ear pods and side rails
for s in (1,-1):
  bm=bmesh.new();bmesh.ops.create_cone(bm,cap_ends=True,segments=24,radius1=.032,radius2=.03,depth=.025);bmesh.ops.rotate(bm,cent=(0,0,0),matrix=Matrix.Rotation(math.pi/2,3,'Y'),verts=bm.verts);bmesh.ops.translate(bm,vec=(s*.138,.0,-.02),verts=bm.verts);obj('ear',bm,SHELL,bev=.004)
  bm=bmesh.new();bmesh.ops.create_cube(bm,size=1);bmesh.ops.scale(bm,vec=(.006,.09,.012),verts=bm.verts);bmesh.ops.translate(bm,vec=(s*.133,.0,.035),verts=bm.verts);obj('rail',bm,METL,bev=.002)
# top: low rail mount at the brow and a raised ridge front-to-back
bm=bmesh.new();bmesh.ops.create_cube(bm,size=1);bmesh.ops.scale(bm,vec=(.045,.025,.012),verts=bm.verts);bmesh.ops.rotate(bm,cent=(0,0,0),matrix=Matrix.Rotation(-.55,3,'X'),verts=bm.verts);bmesh.ops.translate(bm,vec=(0,-.105,.085),verts=bm.verts);obj('mount',bm,DARK,bev=.003)
bm=bmesh.new();bmesh.ops.create_cube(bm,size=1);bmesh.ops.scale(bm,vec=(.022,.2,.012),verts=bm.verts);obj('ridge',bm,SHELL,bev=.005)
r=bpy.data.objects['ridge'];sd=r.modifiers.new('sd','SIMPLE_DEFORM');sd.deform_method='BEND';sd.deform_axis='X';sd.angle=2.3;r.location=(0,.0,.125)
# neck seal
bm=bmesh.new();bmesh.ops.create_cone(bm,cap_ends=False,segments=32,radius1=.085,radius2=.075,depth=.06);bmesh.ops.translate(bm,vec=(0,.01,-.15),verts=bm.verts);obj('neck',bm,RUB)
# render
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=64;sc.render.resolution_x,sc.render.resolution_y=(900,700);sc.view_settings.view_transform='AgX'
w=bpy.data.worlds.new('W');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(.04,.045,.04,1)
for nm,loc,en,col in (('k',(.6,-.8,.5),60,(1,1,1)),('r',(-.7,.6,.4),45,(.6,1,.9)),('f',(.0,-.6,-.4),12,(1,1,1))):
  l=bpy.data.objects.new(nm,bpy.data.lights.new(nm,'AREA'));sc.collection.objects.link(l);l.data.energy=en;l.data.size=.6;l.data.color=col;l.location=loc;l.rotation_euler=(Vector((0,0,0))-Vector(loc)).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.lens=85
for nm,pos in (('h34',(.42,-.62,.12)),('hside',(.75,0,.04)),('hfront',(0,-.75,.03)),('hback',(-.4,.6,.2))):
  cam.location=pos;cam.rotation_euler=(Vector((0,0,-.01))-Vector(pos)).to_track_quat('-Z','Y').to_euler();sc.render.filepath='/home/claude/hm/'+nm+'.png';bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath='/home/claude/hm/helmet_v1.blend')
