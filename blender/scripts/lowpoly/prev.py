import bpy,os
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath='/home/claude/lp/lp1.blend')
sc=bpy.context.scene
LOWS=[o for o in bpy.data.objects if o.name.startswith('low_')];LODS=[o for o in bpy.data.objects if o.name.startswith('lod_')]
for o in LOWS+LODS:
  g=o.name.split('_')[1];print(o.name,sum(len(p.vertices)-2 for p in o.data.polygons))
  m=bpy.data.materials.new('tex_'+o.name);m.use_nodes=True;nt=m.node_tree;b=nt.nodes['Principled BSDF']
  ci=nt.nodes.new('ShaderNodeTexImage');ci.image=bpy.data.images.load('/home/claude/lp/%s_color.png'%(g+('L' if o in LODS else '')),check_existing=True)
  ni=nt.nodes.new('ShaderNodeTexImage');ni.image=bpy.data.images.load('/home/claude/lp/%s_normal.png'%(g+('L' if o in LODS else '')),check_existing=True);ni.image.colorspace_settings.name='Non-Color'
  mi=nt.nodes.new('ShaderNodeTexImage');mi.image=bpy.data.images.load('/home/claude/lp/%s_mask.png'%(g+('L' if o in LODS else '')),check_existing=True);mi.image.colorspace_settings.name='Non-Color'
  nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(ni.outputs[0],nm.inputs[1]);nt.links.new(nm.outputs[0],b.inputs['Normal'])
  # army colour where mask R: mix the baked colour toward Dawgs green; glow where mask G
  sp=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(mi.outputs[0],sp.inputs[0])
  mx=nt.nodes.new('ShaderNodeMix');mx.data_type='RGBA';mx.inputs[7].default_value=(.16,.62,.12,1);nt.links.new(sp.outputs[0],mx.inputs[0]);nt.links.new(ci.outputs[0],mx.inputs[6]);nt.links.new(mx.outputs[2],b.inputs['Base Color'])
  b.inputs['Roughness'].default_value=.6;b.inputs['Emission Color'].default_value=(.3,1,.4,1);nt.links.new(sp.outputs[1],b.inputs['Emission Strength'])
  o.data.materials.clear();o.data.materials.append(m)
  o.location.x+= .9 if o in LOWS else 1.8
for o in bpy.data.objects:
  if o.type=='LIGHT' or o.type=='CAMERA':bpy.data.objects.remove(o)
sc.render.engine='CYCLES';sc.cycles.samples=40;sc.view_settings.view_transform='AgX'
w=bpy.data.worlds.new('W');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(.03,.034,.03,1)
for nm,off,en in (('k',(2,-6,5),700),('r',(-5,5,3),400),('f',(-2,-7,1),200)):
  l=bpy.data.objects.new(nm,bpy.data.lights.new(nm,'AREA'));sc.collection.objects.link(l);l.data.energy=en;l.data.size=6;t=Vector((.9,0,1));l.location=t+Vector(off);l.rotation_euler=(t-l.location).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
def shot(nm,d,t,osc,res):
  t=Vector(t);cam.data.ortho_scale=osc;sc.render.resolution_x,sc.render.resolution_y=res;cam.location=t+Vector(d).normalized()*12;cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath='/home/claude/lp/'+nm;bpy.ops.render.render(write_still=True)
shot('lp_front.png',(.3,-1,.1),(.9,0,.95),3.0,(1800,1000))
shot('lp_head.png',(.3,-1,.1),(.9,0,1.62),1.5,(1800,600))
