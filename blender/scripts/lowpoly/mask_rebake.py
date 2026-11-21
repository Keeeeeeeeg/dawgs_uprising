# (v25.45) re-bake only the army-colour/glow masks from a saved lp1.blend: the 'team' material parts (pauldrons, knee caps,
# chest-plate edges) now count as army colour as well as the stripe, lens and patches. Then re-export the mask PNGs.
import bpy,os,sys
from PIL import Image
TYPE=os.environ['TYPE'];OUTD='/home/claude/lp/'+TYPE+'/'
bpy.ops.wm.open_mainfile(filepath=OUTD+'lp1.blend')
def root(o):
  while o.parent:o=o.parent
  return o
G={'body':[],'helmet':[],'weapon':[]}
LOWN={'low_body','low_helmet','low_weapon','lod_all','lod_body','lod_helmet','lod_weapon'}
for o in bpy.data.objects:
  if o.type not in('MESH','FONT') or o.hide_render or o.name in LOWN or o.name.startswith('hi_'):continue
  r=root(o).name;g='weapon' if r.startswith('wpn_') else 'helmet' if r.startswith('head') else 'body';G[g].append(o)
G['all']=G['body']+G['helmet']+G['weapon']
def is_team(o):
  n=o.name.split('.')[0];m=o.active_material.name if o.active_material else ''
  return n=='stripe' or m.startswith('stripe') or 'lens' in m.lower() or m.startswith('patch') or m=='team'
def is_glow(o):
  m=o.active_material
  if not m or not m.use_nodes:return False
  b=m.node_tree.nodes.get('Principled BSDF')
  return b is not None and b.inputs['Emission Strength'].default_value>2.0
def mkm(r,gl):
  key='mk2_%d%d'%(r,gl);m=bpy.data.materials.get(key)
  if not m:
    m=bpy.data.materials.new(key);m.use_nodes=True;nt=m.node_tree;nt.nodes.clear();e=nt.nodes.new('ShaderNodeEmission');e.inputs[0].default_value=(r,gl,0,1);o2=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(e.outputs[0],o2.inputs[0])
  return m
FL={o.name:(1 if is_team(o) else 0,1 if is_glow(o) else 0) for o in G['all']}
for o in G['all']:
  m=mkm(*FL[o.name])
  for s in o.material_slots:s.material=m
  if not o.material_slots:o.data.materials.append(m)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=4;sc.cycles.device='CPU'
RES=1024
jobs=[('body','low_body',RES,'body'),('helmet','low_helmet',RES,'helmet'),('all','lod_all',RES//2,'allL')]
if bpy.data.objects.get('low_weapon') and os.environ.get('SHAREW')!='1':jobs.append(('weapon','low_weapon',RES,'weapon'))
for g,ln,res,tag in jobs:
  lo=bpy.data.objects[ln];img=bpy.data.images.new(tag+'_mask2',res,res,alpha=False)
  mat=bpy.data.materials.new('bk2');mat.use_nodes=True;nt=mat.node_tree;tn=nt.nodes.new('ShaderNodeTexImage');tn.image=img;nt.nodes.active=tn
  lo.data.materials.clear();lo.data.materials.append(mat)
  for o in bpy.context.selected_objects:o.select_set(False)
  for o in G[g]:o.select_set(True)
  lo.hide_render=False;lo.hide_set(False);lo.select_set(True);bpy.context.view_layer.objects.active=lo
  b=sc.render.bake;b.use_selected_to_active=True;b.cage_extrusion=.012;b.max_ray_distance=.04;b.margin=4
  bpy.ops.object.bake(type='EMIT')
  img.filepath_raw=OUTD+'%s_mask.png'%tag;img.file_format='PNG';img.save()
  m=Image.open(OUTD+'%s_mask.png'%tag).convert('RGB');m=m.resize((m.width//2,m.height//2));
  m.save(OUTD+'tex/%s_%s_m.png'%(TYPE,tag),optimize=True);print(' mask',TYPE,tag,flush=True)
