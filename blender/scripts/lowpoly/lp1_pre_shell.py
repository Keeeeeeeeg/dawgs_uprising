# Phase B step 1: low-poly game meshes + per-part 1024 bakes (colour, normal, mask) for the rifleman, from the pass-8 high-poly
import os,sys,math
exec(open('/home/claude/body/body8.py').read())
SEED=int(os.environ.get('SEED','51'))
TYPE=os.environ.get('TYPE','rifle');OUTD='/home/claude/lp/'+TYPE+'/';os.makedirs(OUTD,exist_ok=True)
KIND=os.environ.get('KIND','rifle')
P=pose('game',0,0,kind=KIND);made,bo=marine(P,seed=SEED,head=os.environ.get('HEAD','rifle'),gear=os.environ.get('GEAR','std'),weap=KIND)
dg=bpy.context.evaluated_depsgraph_get()
def root(o):
  while o.parent:o=o.parent
  return o
G={'body':[],'helmet':[],'weapon':[]}
for o in bpy.data.objects:
  if o.type not in('MESH','FONT') or o.hide_render:continue
  r=root(o).name
  g='weapon' if r.startswith('wpn_') else 'helmet' if r.startswith('head') else 'body'
  G[g].append(o)
TARGET={'body':int(os.environ.get('TB','4200')),'helmet':1000,'weapon':1000};LOD={'body':850,'helmet':350,'weapon':350}
TEAMNAMES=('stripe',)
def is_team(o):
  n=o.name.split('.')[0];m=o.active_material.name if o.active_material else ''
  return n in TEAMNAMES or m.startswith('stripe') or 'lens' in m.lower() or m.startswith('patch')
def is_glow(o):
  m=o.active_material
  if not m or not m.use_nodes:return False
  b=m.node_tree.nodes.get('Principled BSDF')
  return b is not None and b.inputs['Emission Strength'].default_value>2.0
DROP_LOD={'strip','lace','lug','rivet','fuze','buckle','paulS','kneeStrap','shinStrap','tongue','knuckle','flap','ksnap','bpFlap','packFlap','whipS','radio','rollStrap','etoolGrip','shStrap','strap','patch','tape','armband','canteen','nade','cargo','shinR','anklePl','heel','stripe','sten','gun'}
def tri_n(me):return sum(len(p.vertices)-2 for p in me.polygons)
def make_low(g,target,lod=False,name=None):
  """per-part decimation (keeps each piece's shape): find one ratio r so that sum(max(minT, n_i*r)) ~ target, decimate each
  part, then join. LOD drops small parts first."""
  srcs=[o for o in G[g] if o.type=='MESH' and not o.get('bake')]
  if lod and g=='body':srcs=[o for o in srcs if o.name.split('.')[0] not in DROP_LOD]
  mes=[]
  for o in srcs:
    ev=o.evaluated_get(dg);me=bpy.data.meshes.new_from_object(ev);me.transform(o.matrix_world);mes.append((o,me,tri_n(me)))
  if g!='body':   # small hard parts: one joined mesh decimated as a whole keeps the helmet/gun shapes better
    bm=bmesh.new()
    for o,me,n in mes:bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=.0004);me=bpy.data.meshes.new(name or 'low_'+g);bm.to_mesh(me);bm.free()
    lo=bpy.data.objects.new(name or 'low_'+g,me);bpy.context.scene.collection.objects.link(lo);n0=tri_n(me)
    bpy.context.view_layer.objects.active=lo
    if lod:   # LOD: voxel-remesh the fused part first (clean blob that keeps the silhouette), then decimate
      rm=lo.modifiers.new('r','REMESH');rm.mode='VOXEL';rm.voxel_size={'helmet':.009,'weapon':.006}[g];bpy.ops.object.modifier_apply(modifier='r');n0=tri_n(lo.data)
    d=lo.modifiers.new('d','DECIMATE');d.ratio=min(1,target/n0);d.use_collapse_triangulate=True
    bpy.ops.object.modifier_apply(modifier='d')
    a=lo.data.attributes.new('part','INT','FACE');pid=PARTS.setdefault(g,len(PARTS))
    for k in range(len(lo.data.polygons)):a.data[k].value=pid*16
    print('\n',lo.name,'tris',tri_n(lo.data));return lo,srcs
  minT=8 if lod else 12
  lo_r,hi_r=0.0,1.0
  for _ in range(40):
    r=(lo_r+hi_r)/2;tot=sum(min(n,max(2 if o.name.split('.')[0]=='strip' else minT,n*r)) for o,_,n in mes)
    if tot>target:hi_r=r
    else:lo_r=r
  r=lo_r;objs=[]
  for o,me,n in mes:
    ob=bpy.data.objects.new('lp_'+o.name,me);bpy.context.scene.collection.objects.link(ob);ob['src']=o.name.split('.')[0];ob['side']=o.get('side',-1)
    want=min(n,max(2 if o.name.split('.')[0]=='strip' else minT,n*r))   # ghillie strips may fall to a single card
    if want<n*.98:
      d=ob.modifiers.new('d','DECIMATE');d.ratio=want/n;d.use_collapse_triangulate=True
      bpy.context.view_layer.objects.active=ob;bpy.ops.object.modifier_apply(modifier='d')
    # remember the source part on every face (skinning reads it)
    me2=ob.data;lay=me2.attributes.new('part','INT','FACE');pid=PARTS.setdefault(ob['src'],len(PARTS))
    for k in range(len(me2.polygons)):lay.data[k].value=pid*16+(int(ob['side'])+1)
    objs.append(ob)
  for o in bpy.context.selected_objects:o.select_set(False)
  for ob in objs:ob.select_set(True)
  bpy.context.view_layer.objects.active=objs[0];bpy.ops.object.join();lo=bpy.context.view_layer.objects.active;lo.name=name or 'low_'+g;lo.select_set(False)
  print('\n',lo.name,'ratio %.3f'%r,'tris',tri_n(lo.data))
  return lo,srcs
PARTS={}
CLOTHK=float(os.environ.get('CLOTHK','1.6'))
def uv(lo,cloth_ids=None):
  for o in bpy.context.selected_objects:o.select_set(False)
  bpy.context.view_layer.objects.active=lo;lo.select_set(True)
  bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
  bpy.ops.uv.smart_project(angle_limit=math.radians(60),island_margin=.004,area_weight=0.0)
  bpy.ops.uv.average_islands_scale()
  if cloth_ids:
    bm=bmesh.from_edit_mesh(lo.data);ul=bm.loops.layers.uv.active;pl=bm.faces.layers.int.get('part');bm.faces.ensure_lookup_table()
    par=list(range(len(bm.faces)))
    def fnd(i):
      while par[i]!=i:par[i]=par[par[i]];i=par[i]
      return i
    for e in bm.edges:
      if len(e.link_faces)!=2:continue
      f1,f2=e.link_faces;ok=True
      for v in e.verts:
        a=[l[ul].uv for l in f1.loops if l.vert==v][0];b=[l[ul].uv for l in f2.loops if l.vert==v][0]
        if (a-b).length>1e-5:ok=False
      if ok:par[fnd(f1.index)]=fnd(f2.index)
    isl={}
    for f in bm.faces:isl.setdefault(fnd(f.index),[]).append(f)
    for fs in isl.values():
      if pl is None or sum(1 for f in fs if f[pl]//16 in cloth_ids)*2<len(fs):continue
      ls=[l for f in fs for l in f.loops];c=sum((l[ul].uv for l in ls),Vector((0,0)))/len(ls)
      for l in ls:l[ul].uv=c+(l[ul].uv-c)*CLOTHK
    bmesh.update_edit_mesh(lo.data)
  bpy.ops.uv.pack_islands(margin=.003,rotate=True)
  bpy.ops.object.mode_set(mode='OBJECT');lo.select_set(False)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=int(os.environ.get('BS','8'));sc.cycles.device='CPU'
def bake(g,lo,srcs,kind,img,tag=None):
  mat=bpy.data.materials.new('bk_'+g);mat.use_nodes=True;nt=mat.node_tree
  tn=nt.nodes.new('ShaderNodeTexImage');tn.image=img;nt.nodes.active=tn
  lo.data.materials.clear();lo.data.materials.append(mat)
  for o in bpy.context.selected_objects:o.select_set(False)
  hs=[o for o in G[g] if o.type in('MESH','FONT')]
  for o in hs:o.select_set(True)
  lo.select_set(True);bpy.context.view_layer.objects.active=lo
  b=sc.render.bake;b.use_selected_to_active=True;b.cage_extrusion=.012;b.max_ray_distance=.04;b.margin=4
  if kind=='color':
    b.use_pass_direct=False;b.use_pass_indirect=False;b.use_pass_color=True;bpy.ops.object.bake(type='DIFFUSE')
  elif kind=='normal':
    b.normal_space='TANGENT';bpy.ops.object.bake(type='NORMAL')
  else:bpy.ops.object.bake(type='EMIT')
  img.filepath_raw=OUTD+'%s_%s.png'%(tag or g,kind);img.file_format='PNG';img.save()
def mask_mats(g,on):
  # temporarily give every high part an emission material: R = army colour area (stripe, lens, patch), G = glow
  if on:
    for o in G[g]:
      if o.type not in('MESH','FONT'):continue
      o['_m']=[s.material.name if s.material else '' for s in o.material_slots]
      r=1.0 if is_team(o) else 0.0;gl=1.0 if is_glow(o) else 0.0
      key='mk_%d%d'%(r,gl);m=bpy.data.materials.get(key)
      if not m:
        m=bpy.data.materials.new(key);m.use_nodes=True;nt=m.node_tree;nt.nodes.clear();e=nt.nodes.new('ShaderNodeEmission');e.inputs[0].default_value=(r,gl,0,1);o2=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(e.outputs[0],o2.inputs[0])
      for s in o.material_slots:s.material=m
      if not o.material_slots:o.data.materials.append(m)
  else:
    for o in G[g]:
      if '_m' in o:
        for s,n in zip(o.material_slots,o['_m']):s.material=bpy.data.materials.get(n)
RES=int(os.environ.get('RES','1024'))
LOWS={}
SHAREW=os.environ.get('SHAREW')=='1'
for g in ('helmet','weapon','body'):
  lo,srcs=make_low(g,TARGET[g])
  LOWS[g]=lo
  LOWS[g+'L'],_=make_low(g,LOD[g],lod=True,name='lod_'+g)
  if g=='weapon' and SHAREW:continue
  uv(lo,[PARTS[n] for n in ('torso','thigh','shin','uarm','farm') if n in PARTS] if g=='body' else None)
  for kind in ('color','normal','mask'):
    img=bpy.data.images.new('%s_%s'%(g,kind),RES,RES,alpha=False)
    if kind=='normal':img.colorspace_settings.name='Non-Color'
    if kind=='mask':mask_mats(g,True)
    bake(g,lo,srcs,kind,img)
    if kind=='mask':mask_mats(g,False)
    print(' baked',g,kind,flush=True)
# far LOD: body + helmet + rifle joined into ONE mesh with one 512 bake (one draw call per soldier at RTS zoom)
G['all']=G['body']+G['helmet']+G['weapon']
for o in bpy.context.selected_objects:o.select_set(False)
for g in ('body','helmet','weapon'):LOWS[g+'L'].select_set(True)
bpy.context.view_layer.objects.active=LOWS['bodyL'];bpy.ops.object.join();al=bpy.context.view_layer.objects.active;al.name='lod_all';al.select_set(False)
uv(al,[PARTS[n] for n in ('torso','thigh','shin','uarm','farm') if n in PARTS])
for kind in ('color','normal','mask'):
  img=bpy.data.images.new('allL_%s'%kind,RES//2,RES//2,alpha=False)
  if kind=='normal':img.colorspace_settings.name='Non-Color'
  if kind=='mask':mask_mats('all',True)
  bake('all',al,None,kind,img,tag='allL')
  if kind=='mask':mask_mats('all',False)
LOWS['allL']=al
print(' lod all tris',tri_n(al.data))
import json
json.dump(PARTS,open(OUTD+'parts.json','w'))
exec(open('/home/claude/lp/lp_export.py').read())
bpy.ops.wm.save_as_mainfile(filepath=OUTD+'lp1.blend')
