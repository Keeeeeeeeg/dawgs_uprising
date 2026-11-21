# (concept v2) full-face marine helmet: high-cut ballistic shell, goggle visor with a frame, faceted jaw guard of three plates
# (two cheek plates + a mouth piece) with vents and a chin filter. Real metres, head centre at origin, -y = front, z up.
import bpy,bmesh,math
from mathutils import Vector,Matrix
for o in list(bpy.data.objects):bpy.data.objects.remove(o)
def M(name,col,rough=.5,metal=0,emit=0,spec=.5):
  m=bpy.data.materials.new(name);m.use_nodes=True;b=m.node_tree.nodes['Principled BSDF']
  b.inputs['Base Color'].default_value=col+(1,);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
  if emit:b.inputs['Emission Color'].default_value=col+(1,);b.inputs['Emission Strength'].default_value=emit
  return m
SHELL=M('shell',(.085,.09,.085),.6);PLATE=M('plate',(.07,.072,.07),.5);DARK=M('dark',(.02,.02,.02),.6);VIS=M('visor',(.01,.012,.015),.04,.7);EYE=M('eye',(.2,1,.45),.3,0,10);RUB=M('rubber',(.015,.015,.015),.85);METL=M('metal',(.25,.25,.25),.3,.9)
def link(name,bm,mat,bev=0,sol=0,smooth=True,segs=2):
  me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free();o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o);me.materials.append(mat)
  for p in me.polygons:p.use_smooth=smooth
  if sol:s=o.modifiers.new('s','SOLIDIFY');s.thickness=sol;s.offset=-1
  if bev:b=o.modifiers.new('b','BEVEL');b.width=bev;b.segments=segs;b.limit_method='ANGLE';b.angle_limit=.6
  o.modifiers.new('w','WEIGHTED_NORMAL');return o
def sphere_cut(r,s,keep,u=72,v=48):
  bm=bmesh.new();bmesh.ops.create_uvsphere(bm,u_segments=u,v_segments=v,radius=r)
  for vv in bm.verts:vv.co=Vector((vv.co.x*s[0],vv.co.y*s[1],vv.co.z*s[2]))
  bmesh.ops.delete(bm,geom=[vv for vv in bm.verts if not keep(vv.co)],context='VERTS');return bm
def hull(pts):
  bm=bmesh.new();vs=[bm.verts.new(p) for p in pts];bmesh.ops.convex_hull(bm,input=vs);return bm
def box(c,s,rot=None):
  bm=bmesh.new();bmesh.ops.create_cube(bm,size=1);bmesh.ops.scale(bm,vec=s,verts=bm.verts)
  if rot:bmesh.ops.rotate(bm,cent=(0,0,0),matrix=rot,verts=bm.verts)
  bmesh.ops.translate(bm,vec=c,verts=bm.verts);return bm
# shell: rounded but low (s z .88), the rim rises over the brow and is cut high above the ears (high-cut), lower at the nape
def shell_keep(c):
  a=math.atan2(c.x,-c.y)   # 0 front, +-pi back
  rim=.03 if abs(a)<.55 else (-.005 if abs(a)<1.35 else (-.035 if abs(a)<2.2 else -.06))
  return c.z>rim
link('shell',sphere_cut(.128,(1,1.1,.9),shell_keep),SHELL,sol=.011,bev=.004)
# brim band (thin raised edge round the cut)
link('brim',sphere_cut(.1305,(1,1.1,.9),lambda c:(lambda a:(lambda rim:rim<c.z<rim+.008)(.03 if abs(a)<.55 else (-.005 if abs(a)<1.35 else (-.035 if abs(a)<2.2 else -.06))))(math.atan2(c.x,-c.y))),DARK,sol=.004)
# goggle visor: a lens wrapping the front, with a frame
def lens(c):return c.y<-.03 and -.035<c.z<.03 and abs(c.x)<.1
link('lens',sphere_cut(.124,(1.02,1.14,1),lens),VIS,sol=.003)
def frame(c):
  inn=c.y<-.03 and -.035<c.z<.03 and abs(c.x)<.1;out=c.y<-.02 and -.045<c.z<.04 and abs(c.x)<.112
  return out and not inn
link('frame',sphere_cut(.122,(1.03,1.14,1),frame),PLATE,sol=.008,bev=.002)
link('eye',sphere_cut(.1265,(1.02,1.14,1),lambda c:c.y<-.1 and -.012<c.z<.012 and -.072<c.x<-.04,u=96,v=64),EYE)
# jaw guard: three faceted plates. Points are hand-placed to wrap the lower face (cheek plates angle in to a pointed mouth piece)
for s in (1,-1):
  P=[(s*.112,-.02,-.035),(s*.105,-.075,-.045),(s*.085,-.11,-.05),(s*.04,-.135,-.05),
     (s*.11,-.02,-.11),(s*.095,-.07,-.13),(s*.07,-.1,-.135),(s*.04,-.12,-.13),
     (s*.1,-.01,-.04),(s*.093,-.06,-.05),(s*.07,-.09,-.055),(s*.035,-.115,-.055),(s*.095,-.01,-.105),(s*.08,-.06,-.12),(s*.06,-.085,-.125),(s*.035,-.105,-.12)]
  link('cheek',hull(P),PLATE,bev=.004)
  for i in range(3):link('vent',box((s*(.1-i*.008),-.045-i*.022,-.085),(.006,.014,.04),Matrix.Rotation(s*(.35+i*.25),3,'Z')),DARK,bev=.002)
M_P=[(-.032,-.14,-.055),(.032,-.14,-.055),(-.03,-.165,-.1),(.03,-.165,-.1),(-.022,-.15,-.14),(.022,-.15,-.14),(-.03,-.12,-.055),(.03,-.12,-.055),(-.025,-.135,-.135),(.025,-.135,-.135)]
link('mouth',hull(M_P),PLATE,bev=.004)
link('filter',box((0,-.168,-.112),(.034,.012,.03)),DARK,bev=.003)
for i in range(3):link('slot',box((0,-.1745,-.1+i*-.01),(.026,.003,.003)),METL)
# side: rail with a lamp module on one side, comms pod on the other, hinge bolt for the jaw guard
for s in (1,-1):
  link('rail',box((s*.13,-.005,.02),(.007,.085,.013)),METL,bev=.002)
  link('hinge',box((s*.115,-.012,-.05),(.016,.024,.024)),DARK,bev=.004)
link('lamp',box((.142,-.04,.02),(.016,.035,.02)),DARK,bev=.003);link('lampG',box((.142,-.059,.02),(.012,.004,.012)),M('lg',(.9,.9,.8),.2,0,3))
link('pod',box((-.14,.01,-.005),(.02,.05,.045)),PLATE,bev=.006)
link('mount',box((0,-.105,.07),(.05,.02,.016),Matrix.Rotation(-.7,3,'X')),DARK,bev=.003)
link('neck',(lambda bm:(bmesh.ops.create_cone(bm,cap_ends=False,segments=40,radius1=.08,radius2=.072,depth=.07),bmesh.ops.translate(bm,vec=(0,.01,-.15),verts=bm.verts),bm)[2])(bmesh.new()),RUB)
# render: neutral studio, a sage rim light, 3/4 hero + turnarounds
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=96;sc.render.resolution_x,sc.render.resolution_y=(800,800);sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
w=bpy.data.worlds.new('W');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(.03,.034,.03,1)
for nm,loc,en,col,sz in (('k',(.9,-1.1,.7),40,(1,.97,.92),.8),('r',(-1,.9,.5),35,(.65,1,.8),.6),('f',(-.6,-1,-.2),8,(.85,.9,1),1.2),('t',(0,0,1.2),10,(1,1,1),1)):
  l=bpy.data.objects.new(nm,bpy.data.lights.new(nm,'AREA'));sc.collection.objects.link(l);l.data.energy=en;l.data.size=sz;l.data.color=col;l.location=loc;l.rotation_euler=(Vector((0,0,-.02))-Vector(loc)).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.lens=70
for nm,d in (('v2_34',(.55,-.85,.18)),('v2_front',(0,-1,.05)),('v2_side',(1,0,.03)),('v2_back',(-.6,.8,.3))):
  pos=Vector(d).normalized()*.95;cam.location=pos;cam.rotation_euler=(Vector((0,-.01,-.03))-pos).to_track_quat('-Z','Y').to_euler();sc.render.filepath='/home/claude/hm/'+nm+'.png';bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath='/home/claude/hm/helmet_v2.blend')
