# Marine builder helpers (cloud bpy). All inputs in GAME raw coords (x fwd, y up, z right); blender = (x,-z,y).
import bpy,bmesh,math,json,base64,struct
from mathutils import Vector,Matrix

def G(x,y,z):return Vector((x,-z,y))
def ungame(v):return (v.x,v.z,-v.y)

MATS={}
COL={'UNIFORM':(.23,.24,.24),'VEST':(.37,.39,.42),'PLATE':(.47,.49,.51),'PLATEDK':(.30,.32,.34),'BOOT':(.15,.15,.14),'SKIN':(.6,.48,.38),
     'GUN':(.16,.17,.17),'GUNLT':(.24,.25,.25),'ACCENT':(.35,.75,.2),'PACK':(.26,.27,.25),'AMMO':(.28,.29,.24),'STRAP':(.18,.18,.17),'LENS':(.35,.54,.6),'BRASS':(.72,.56,.18),'GHILLIE':(.30,.32,.21),'GHILLIE2':(.42,.40,.27),'CANVAS':(.42,.40,.32)}
def mat(role):
  if role in MATS:return MATS[role]
  m=bpy.data.materials.get(role) or bpy.data.materials.new(role);m.diffuse_color=COL.get(role,(1,0,1))+(1,);MATS[role]=m;return m

class Part:
  def __init__(s,name):
    s.name=name;s.bm=bmesh.new();s.roles=[]
  def _add(s,bm2,role):
    # merge bm2 into s.bm, tagging faces
    me=bpy.data.meshes.new('tmp');bm2.to_mesh(me);bm2.free()
    ri=s.role_index(role);n0=len(s.bm.faces)
    s.bm.from_mesh(me);bpy.data.meshes.remove(me)
    s.bm.faces.ensure_lookup_table()
    for f in s.bm.faces[n0:]:f.material_index=ri
  def role_index(s,role):
    if role not in s.roles:s.roles.append(role)
    return s.roles.index(role)
  def ellip(s,role,c,r,seg=10,rings=7,rot=None):
    bm=bmesh.new();bmesh.ops.create_uvsphere(bm,u_segments=seg,v_segments=rings,radius=1)
    M=Matrix.Diagonal((r[0],r[2],r[1],1))
    if rot:M=rot@M
    bmesh.ops.transform(bm,matrix=M,verts=bm.verts);bmesh.ops.translate(bm,vec=G(*c),verts=bm.verts);s._add(bm,role)
  def cap(s,role,a,b,r1,r2,seg=8,rings=2,squash=1.0):
    """tapered capsule from a to b (game coords) with hemispherical-ish ends"""
    A=G(*a);B=G(*b);d=B-A;L=d.length;ax=d.normalized()
    up=Vector((0,0,1)) if abs(ax.z)<.9 else Vector((1,0,0))
    u=ax.cross(up).normalized();v=ax.cross(u).normalized()
    bm=bmesh.new();loops=[]
    prof=[]
    # end cap rings (hemisphere approximated)
    for k in range(rings,0,-1):
      t=k/(rings+1)*math.pi/2;prof.append((-r1*math.sin(t),r1*math.cos(t)))
    prof.append((0,r1));prof.append((L,r2))
    for k in range(1,rings+1):
      t=k/(rings+1)*math.pi/2;prof.append((L+r2*math.sin(t),r2*math.cos(t)))
    for (h,rr) in prof:
      ring=[]
      for i in range(seg):
        an=2*math.pi*i/seg;ring.append(bm.verts.new(A+ax*h+u*(math.cos(an)*rr)+v*(math.sin(an)*rr*squash)))
      loops.append(ring)
    for j in range(len(loops)-1):
      for i in range(seg):
        bm.faces.new((loops[j][i],loops[j][(i+1)%seg],loops[j+1][(i+1)%seg],loops[j+1][i]))
    t0=bm.verts.new(A-ax*r1);t1=bm.verts.new(B+ax*r2)
    for i in range(seg):
      bm.faces.new((loops[0][(i+1)%seg],loops[0][i],t0));bm.faces.new((loops[-1][i],loops[-1][(i+1)%seg],t1))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces);s._add(bm,role)
  def box(s,role,c,size,bev=0.0,rot=None,seg=1,taper=None):
    bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
    if taper:  # taper: scale of the +y (game up) face in (x,z)
      for vv in bm.verts:
        if vv.co.z>0:vv.co.x*=taper[0];vv.co.y*=taper[1]
    bmesh.ops.scale(bm,vec=Vector((size[0],size[2],size[1])),verts=bm.verts)
    if bev>0:
      bmesh.ops.bevel(bm,geom=list(bm.edges)+list(bm.verts),offset=bev,segments=seg,profile=.5,affect='EDGES',clamp_overlap=True)
    if rot:bmesh.ops.transform(bm,matrix=rot,verts=bm.verts)
    bmesh.ops.translate(bm,vec=G(*c),verts=bm.verts);s._add(bm,role)
  def cyl(s,role,a,b,r,seg=8,r2=None):
    A=G(*a);B=G(*b);d=B-A;L=d.length;ax=d.normalized()
    bm=bmesh.new();bmesh.ops.create_cone(bm,cap_ends=True,segments=seg,radius1=r,radius2=r if r2 is None else r2,depth=L)
    q=Vector((0,0,1)).rotation_difference(ax)
    bmesh.ops.transform(bm,matrix=q.to_matrix().to_4x4(),verts=bm.verts);bmesh.ops.translate(bm,vec=(A+B)/2,verts=bm.verts);s._add(bm,role)
  def finish(s):
    bmesh.ops.triangulate(s.bm,faces=s.bm.faces)
    me=bpy.data.meshes.new(s.name);s.bm.to_mesh(me)
    for r in s.roles:me.materials.append(mat(r))
    ob=bpy.data.objects.new(s.name,me);bpy.context.scene.collection.objects.link(ob);s.ob=ob;return ob

def rotY(a):  # rotation about GAME y (blender z)
  return Matrix.Rotation(a,4,'Z')
def rotZ(a):  # rotation about GAME z (blender -y): pitch in x-y plane
  return Matrix.Rotation(-a,4,'Y')
def rotX(a):  # about GAME x (blender x): roll
  return Matrix.Rotation(-a,4,'X')

def pack(ob,off=(0,0,0)):
  """export object as game-coord packed triangles (int16 mm), positions minus off (game)"""
  dg=bpy.context.evaluated_depsgraph_get();ev=ob.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();P=[];R=[]
  M=ob.matrix_world
  for t in me.loop_triangles:
    for vi in t.vertices:
      g=ungame(M@me.vertices[vi].co);P+= [int(round((g[0]-off[0])*1000)),int(round((g[1]-off[1])*1000)),int(round((g[2]-off[2])*1000))]
    R.append(t.material_index)
  roles=[m.name.split('.')[0] for m in ob.data.materials]
  return {'roles':roles,'p':base64.b64encode(struct.pack('<%dh'%len(P),*P)).decode(),'r':base64.b64encode(bytes(R)).decode(),'n':len(R)}

def place(ob,off):
  ob.location=G(*off)

def render(path,obs,view=(1,-1,.55),res=(700,700),ortho=1.1,target=(0,.8,0)):
  sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL'
  sc.display.shading.show_shadows=False;sc.display.shading.show_cavity=True
  sc.render.resolution_x,sc.render.resolution_y=res;sc.render.film_transparent=False
  for o in sc.objects:
    if o.type=='MESH':o.hide_render=o.name not in obs
  cam=sc.objects.get('CAM')
  if not cam:
    cam=bpy.data.objects.new('CAM',bpy.data.cameras.new('CAM'));sc.collection.objects.link(cam)
  cam.data.type='ORTHO';cam.data.ortho_scale=ortho*2
  T=G(*target);d=G(*view).normalized()
  cam.location=T+d*5;cam.rotation_euler=(T-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam
  sc.render.filepath=path;bpy.ops.render.render(write_still=True)
