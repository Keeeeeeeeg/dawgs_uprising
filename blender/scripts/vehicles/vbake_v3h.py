# Phase C bake + export: low-poly game meshes from a vehicle source script (lt.py), one shared 2048 atlas (colour, normal, mask)
# for the close-up parts (hull, turret, each barrel, each skirt panel), and a 1024 far LOD split into hull + turret.
import os,sys,math,json,base64,struct
SRC=os.environ.get('VSRC','/home/claude/veh/lt.py');TYPE=os.environ.get('TYPE','ltank');OUTD='/home/claude/veh/'+TYPE+'/';os.makedirs(OUTD+'tex',exist_ok=True)
src=open(SRC).read();exec(src.split('# ------------------------------------------------------------------ QA:')[0])
import bmesh
from mathutils import Vector,Matrix
dg=bpy.context.evaluated_depsgraph_get()
FONTS=[o for o in bpy.data.objects if o.type=='FONT']
# bake source: every high part (modifiers applied) joined into ONE object (Cycles crashed baking from ~1000 objects)
_hs=[]
for o in P+FONTS:
  me=bpy.data.meshes.new_from_object(o.evaluated_get(dg));me.transform(o.matrix_world);ob=bpy.data.objects.new('hi_'+o.name,me);bpy.context.scene.collection.objects.link(ob);_hs.append(ob)
for o in bpy.context.selected_objects:o.select_set(False)
for o in _hs:o.select_set(True)
bpy.context.view_layer.objects.active=_hs[0];bpy.ops.object.join();HI=bpy.context.view_layer.objects.active;HI.name='HIGH';HI.select_set(False)
HIGH=[HI]
DROP={'bolt','skirtBolt','cage','cageRing','chuteRib','louvre','jerryCap','toolClamp','brakeSlot','shieldSlot','link','grouser','guide','tooth','cupScope','periscope','exClamp','tarpStrap','cable','grab','smokeCap','apsEye','jacketRib','basketPost'}
TARGET={'hull':5600,'turret':2800,'gunL':450,'gunR':450,'skirt':40}
GID={}
def tri_n(me):return sum(len(p.vertices)-2 for p in me.polygons)
def lowpart(objs,target,name,minT=12):
  mes=[]
  for o in objs:
    me=bpy.data.meshes.new_from_object(o.evaluated_get(dg));me.transform(o.matrix_world);mes.append((o,me,tri_n(me)))
  lo,hi=0.0,1.0
  for _ in range(40):
    r=(lo+hi)/2;tot=sum(min(n,max(minT,n*r)) for _,_,n in mes)
    if tot>target:hi=r
    else:lo=r
  r=lo;obs=[]
  for o,me,n in mes:
    ob=bpy.data.objects.new('lp_'+o.name,me);bpy.context.scene.collection.objects.link(ob);want=min(n,max(minT,n*r))
    if want<n*.98:
      d=ob.modifiers.new('d','DECIMATE');d.ratio=want/n;d.use_collapse_triangulate=True;bpy.context.view_layer.objects.active=ob;bpy.ops.object.modifier_apply(modifier='d')
    obs.append(ob)
  return obs
def ribbon(pts,y0,y1,th=.05):
  """the low-poly track: a closed band following the track centre line (the links + grousers are baked onto it)"""
  P2=[Vector((x,0,z)) for x,z in pts];bm=bmesh.new();C=Vector(((SPX+IDX)/2*LS,0,.45*LS));rows=[]
  n=len(P2)
  for i,p in enumerate(P2):
    d=(P2[(i+1)%n]-P2[i-1]).normalized();nr=Vector((d.z,0,-d.x))
    if nr.dot(p-C)<0:nr=-nr
    rows.append([bm.verts.new(p+nr*o+Vector((0,y,0))) for o,y in ((th*.9,y0),(th*.9,y1),(-th*.4,y1),(-th*.4,y0))])
  for i in range(n):
    a,b=rows[i],rows[(i+1)%n]
    for k in range(4):bm.faces.new((a[k],a[(k+1)%4],b[(k+1)%4],b[k]))
  bmesh.ops.recalc_face_normals(bm,faces=bm.faces);me=bpy.data.meshes.new('trk');bm.to_mesh(me);bm.free()
  ob=bpy.data.objects.new('track',me);bpy.context.scene.collection.objects.link(ob);return ob
# ---- close-up low parts, tagged with their group
groups={}
for o in P:groups.setdefault(o['grp'],[]).append(o)
LOW=[]
def tag(obs,g):
  gi=GID.setdefault(g,len(GID))
  for ob in obs:
    a=ob.data.attributes.new('grp','INT','FACE')
    for k in range(len(ob.data.polygons)):a.data[k].value=gi
  LOW.extend(obs)
for g,objs in groups.items():
  if g=='track':continue
  keep=[o for o in objs if o.name.split('.')[0] not in DROP]
  tgt=TARGET.get(g,TARGET['skirt'] if g.startswith('skirt') else 400)
  tag(lowpart(keep,tgt,g,minT=6 if g.startswith('skirt') else 12),g)
for sy in (1,-1):tag([ribbon([(x*LS,z*LS) for x,z in TRACK_PTS],(sy*TY-TW/2)*LS,(sy*TY+TW/2)*LS)],'hull')   # (v3g) track ribbon at the model's overall scale
def join(obs,name):
  for o in bpy.context.selected_objects:o.select_set(False)
  for o in obs:o.select_set(True)
  bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join();j=bpy.context.view_layer.objects.active;j.name=name;j.select_set(False);return j
low=join(LOW,'low_all');print('\n low tris',tri_n(low.data),{g:i for g,i in GID.items()})
def uv(o,cloth=None):
  for q in bpy.context.selected_objects:q.select_set(False)
  bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
  bpy.ops.uv.smart_project(angle_limit=math.radians(60),island_margin=.003,area_weight=0.0);bpy.ops.uv.average_islands_scale();bpy.ops.uv.pack_islands(margin=.002,rotate=True)
  bpy.ops.object.mode_set(mode='EDIT');bpy.ops.object.mode_set(mode='OBJECT');o.select_set(False)
uv(low)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=int(os.environ.get('BS','4'));sc.cycles.device='CPU'
def m_team(m):return bool(m) and m.name.startswith('stripe')
def m_glow(m):return bool(m) and m.use_nodes and 'Principled BSDF' in m.node_tree.nodes and m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value>2.0
def mkmat(r,gl):
  key='mk_%d%d'%(r,gl);m=bpy.data.materials.get(key)
  if not m:
    m=bpy.data.materials.new(key);m.use_nodes=True;nt=m.node_tree;nt.nodes.clear();e=nt.nodes.new('ShaderNodeEmission');e.inputs[0].default_value=(r,gl,0,1);o2=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(e.outputs[0],o2.inputs[0])
  return m
def mask_mats(on):
  # per material slot (HIGH is one joined object, so the test must be per slot, not per object)
  if on:
    for o in HIGH:
      o['_m']=[s.material.name if s.material else '' for s in o.material_slots]
      for s in o.material_slots:s.material=mkmat(1 if m_team(s.material) else 0,1 if m_glow(s.material) else 0)
  else:
    for o in HIGH:
      for s,n in zip(o.material_slots,o['_m']):s.material=bpy.data.materials.get(n)
def bake(lo,kind,res,tag):
  img=bpy.data.images.new(tag+kind,res,res,alpha=False)
  if kind=='normal':img.colorspace_settings.name='Non-Color'
  mat=bpy.data.materials.new('bk');mat.use_nodes=True;tn=mat.node_tree.nodes.new('ShaderNodeTexImage');tn.image=img;mat.node_tree.nodes.active=tn
  lo.data.materials.clear();lo.data.materials.append(mat)
  for o in bpy.context.selected_objects:o.select_set(False)
  for o in HIGH:o.select_set(True)
  lo.select_set(True);bpy.context.view_layer.objects.active=lo
  b=sc.render.bake;b.use_selected_to_active=True;b.cage_extrusion=.03;b.max_ray_distance=.08;b.margin=6
  if kind=='mask':mask_mats(True)
  if kind=='color':b.use_pass_direct=False;b.use_pass_indirect=False;b.use_pass_color=True;bpy.ops.object.bake(type='DIFFUSE')
  elif kind=='normal':b.normal_space='TANGENT';bpy.ops.object.bake(type='NORMAL')
  else:bpy.ops.object.bake(type='EMIT')
  if kind=='mask':mask_mats(False)
  img.filepath_raw=OUTD+tag+'_'+kind+'.png';img.file_format='PNG';img.save();print(' baked',tag,kind,flush=True)
RES=int(os.environ.get('RES','2048'))
for k in ('color','normal','mask'):bake(low,k,RES,'v')
# ---- far LOD: hull (+ skirts) and turret (+ barrels) decimated, joined, own UVs and a 1024 bake, split again
import copy
def sub(src,gids,name,target):
  o=src.copy();o.data=src.data.copy();o.name=name;sc.collection.objects.link(o)
  bm=bmesh.new();bm.from_mesh(o.data);lay=bm.faces.layers.int['grp'];bmesh.ops.delete(bm,geom=[f for f in bm.faces if f[lay] not in gids],context='FACES');bm.to_mesh(o.data);bm.free()
  if target:
    n=tri_n(o.data);d=o.modifiers.new('d','DECIMATE');d.ratio=min(1,target/max(1,n));bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier='d')
  return o
HULLG=[i for g,i in GID.items() if g=='hull' or g.startswith('skirt')];TURG=[i for g,i in GID.items() if g in('turret','gunL','gunR')]
lh=sub(low,HULLG,'lodHull',2000);lt_=sub(low,TURG,'lodTur',1000)
for o in (lh,lt_):
  a=o.data.attributes.get('lodp') or o.data.attributes.new('lodp','INT','FACE')
  for k in range(len(o.data.polygons)):a.data[k].value=0 if o is lh else 1
lod=join([lh,lt_],'lod');uv(lod)
for k in ('color','normal','mask'):bake(lod,k,RES//2,'vL')
# ---- export (game coords: x fwd, y up, z = -Blender y; mm)
def cv(v):return (v.x,v.z,-v.y)
def export(o,attr,val):
  me=o.data;me.calc_loop_triangles();ul=me.uv_layers.active.data;CN=me.corner_normals;at=me.attributes[attr].data
  Pp=[];U=[];N=[]
  for tr in me.loop_triangles:
    if at[tr.polygon_index].value!=val:continue
    for li,vi in zip(tr.loops,tr.vertices):
      p=cv(me.vertices[vi].co);n=cv(Vector(CN[li].vector));u=ul[li].uv
      Pp+=[int(round(c*1000)) for c in p];U+=[int(round(max(0,min(1,u.x))*65535)),int(round(max(0,min(1,u.y))*65535))];N+=[max(-127,min(127,int(round(c*127)))) for c in n]
  b64=lambda fmt,a:base64.b64encode(struct.pack(fmt%len(a),*a)).decode()
  return {'p':b64('<%dh',Pp),'uv':b64('<%dH',U),'nm':b64('<%db',N),'n':len(Pp)//9}
res={'tex':TYPE,'parts':{}}
for g,i in GID.items():res['parts'][g]=export(low,'grp',i);print(' export',g,res['parts'][g]['n'])
res['parts']['hullL']=export(lod,'lodp',0);res['parts']['turretL']=export(lod,'lodp',1);print(' lod',res['parts']['hullL']['n'],res['parts']['turretL']['n'])
def gv(v):return [round(c,4) for c in cv(Vector(v)*LS)]   # rig points are in design units: apply the overall scale
res['rig']={'pivot':gv((TX*SX,0,ZR)),'muz':[gv(Mg@Vector((MX+1.13,sy*.14,MZ))+Vector((TX*SX-TX,0,0))) for sy in (1,-1)],'exhaust':gv((-1.9*SX,-.98*SY,1.11)),
  'skirts':[g for g in GID if g.startswith('skirt')],'tracks':[[gv((x*SX,sy*TY,0))[0],gv((0,sy*TY,0))[2]] for sy in (1,-1) for x in (-1.5,1.4)],'recoil':round(.09*LS,4)}
json.dump(res,open(OUTD+'v_%s.json'%TYPE,'w'))
from PIL import Image,ImageEnhance
for t in ('v','vL'):
  Image.open(OUTD+t+'_color.png').convert('RGB').save(OUTD+'tex/%s_%s_c.jpg'%(TYPE,t),quality=87)
  Image.open(OUTD+t+'_normal.png').convert('RGB').save(OUTD+'tex/%s_%s_n.jpg'%(TYPE,t),quality=90)
  m=Image.open(OUTD+t+'_mask.png').convert('RGB');m=m.resize((m.width//2,m.height//2));m.save(OUTD+'tex/%s_%s_m.png'%(TYPE,t),optimize=True)
bpy.ops.wm.save_as_mainfile(filepath=OUTD+'bake.blend')
