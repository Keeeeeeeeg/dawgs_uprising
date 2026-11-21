exec(open('/home/claude/hm/h15var.py').read())
G=lensmat(0,(.25,.75,.3))
for i in range(6):variant(100+i,(i*.42-1.05,0,0),G)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=64;sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
w=bpy.data.worlds.new('W');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(.03,.034,.03,1)
for nm,loc,en,col,sz in (('k',(1.5,-2,1.2),160,(1,.97,.92),2.5),('r',(-2,1.6,.9),120,(.65,1,.8),2),('f',(-1,-2,-.3),35,(.85,.9,1),3),('t',(0,0,2),40,(1,1,1),3)):
  l=bpy.data.objects.new(nm,bpy.data.lights.new(nm,'AREA'));sc.collection.objects.link(l);l.data.energy=en;l.data.size=sz;l.data.color=col;l.location=loc;l.rotation_euler=(Vector((0,0,-.02))-Vector(loc)).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
def shot(nm,d,tgt,osc,res):
  cam.data.ortho_scale=osc;sc.render.resolution_x,sc.render.resolution_y=res;pos=Vector(tgt)+Vector(d).normalized()*3;cam.location=pos;cam.rotation_euler=(Vector(tgt)-pos).to_track_quat('-Z','Y').to_euler();sc.render.filepath='/home/claude/hm/'+nm+'.png';bpy.ops.render.render(write_still=True)
shot('v15_34',(.5,-.85,.2),(0,-.01,-.03),2.6,(2000,560))
shot('v15_side',(-1,-.25,.15),(-1.05,-.01,-.03),.5,(800,640))
shot('v15_back',(-.5,.85,.25),(-.21,-.01,-.03),.5,(800,640))
bpy.ops.wm.save_as_mainfile(filepath='/home/claude/hm/helmet_v15.blend')
