exec(open('/home/claude/body/body.py').read())
import importlib,os
# current in-game marine for the lineup (marine.py without its scene clear), scaled to the same height
src=open('/home/claude/mar/marine.py').read().replace("for o in list(bpy.data.objects):bpy.data.objects.remove(o)","")
src=src.split("if __name__=='__main__':")[0];NS={'__name__':'mar'};sys.path.insert(0,'/home/claude/mar');before=set(bpy.data.objects);exec(src,NS);NS['build']('rifle')
old=[o for o in set(bpy.data.objects)-before if o.type=='MESH'];eo=bpy.data.objects.new('old',None);bpy.context.scene.collection.objects.link(eo)
for o in old:
  o.parent=eo
  for m in o.data.materials:
    if m:
      m.use_nodes=True
    if m and m.node_tree and 'Principled BSDF' in m.node_tree.nodes:m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=m.diffuse_color;m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.6
# turnaround row (x -1.8..), stances (x 2..), roles (x 6..)
ROWS={}
for i,(nm,yaw) in enumerate((('neutral',0),('neutral',math.pi/2),('neutral',math.pi))):marine(pose(nm,i*.85-1.7,yaw),seed=3)
eo.matrix_world=Matrix.Translation((.85,0,0))@Rz(-math.pi/2).to_4x4()@Matrix.Scale(1.0,4)
bpy.context.view_layer.update()
zs=[(eo.matrix_world@ (o.matrix_local@Vector(c))).z for o in old for c in o.bound_box];h=max(zs)-min(zs);k=1.75/h;print('old height raw',h,'scale',k)
eo.matrix_world=Matrix.Translation((.85,0,-min(zs)*k))@Rz(-math.pi/2).to_4x4()@Matrix.Scale(k,4)
for i,nm in enumerate(('relaxed','aim','jog')):marine(pose(nm,3+i*.9,0),seed=10+i)
marine(pose('neutral',7.0,0),head='sniper',seed=21,gear='light',weap='sniper')
marine(pose('neutral',7.9,0),head='spotter',seed=22,gear='radio',weap='rifle')
marine(pose('neutral',8.8,0),seed=23,gear='ammo',weap='mg')
marine(pose('shoulder',9.7,0),seed=24,gear='rocket',weap='rocket')
fl=put('floor',box((4,0,-.005),(16,4,.01)),FLOOR)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=int(os.environ.get('SAMP','48'));sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
w=bpy.data.worlds.new('W');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(.03,.034,.03,1)
for nm,loc,en,col,sz in (('k',(6,-6,6),900,(1,.97,.92),6),('r',(-5,6,4),500,(.65,1,.8),6),('f',(3,-8,1),200,(.85,.9,1),8),('t',(4,0,9),300,(1,1,1),10)):
  l=bpy.data.objects.new(nm,bpy.data.lights.new(nm,'AREA'));sc.collection.objects.link(l);l.data.energy=en;l.data.size=sz;l.data.color=col;l.location=loc;l.rotation_euler=(Vector((4,0,1))-Vector(loc)).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
def shot(nm,d,tgt,osc,res):
  cam.data.ortho_scale=osc;sc.render.resolution_x,sc.render.resolution_y=res;pos=Vector(tgt)+Vector(d).normalized()*12;cam.location=pos;cam.rotation_euler=(Vector(tgt)-pos).to_track_quat('-Z','Y').to_euler();sc.render.filepath='/home/claude/body/'+nm+'.png';bpy.ops.render.render(write_still=True)
import os
which=os.environ.get('SHOTS','turn,stance,roles').split(',')
if 'turn' in which:shot('b1_turn',(0,-1,.05),(-.42,0,.95),4.0,(2000,1000))
if 'stance' in which:shot('b1_stance',(.45,-.88,.12),(3.9,0,.9),3.3,(1700,1000))
if 'roles' in which:shot('b1_roles',(.4,-.9,.1),(8.35,0,.95),4.1,(2000,1000))
bpy.ops.wm.save_as_mainfile(filepath='/home/claude/body/marine_v2_body.blend')
