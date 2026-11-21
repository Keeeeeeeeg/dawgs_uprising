exec(open('/home/claude/anim/pose2.py').read())
for o in list(bpy.data.objects):bpy.data.objects.remove(o)
mesh('rest','rifle',{},0,(0,0,0))
O,h=game_idle();mesh('idle','rifle',O,h,(1.2,0,0))
O2,h2=game_idle(lowready=False);mesh('idle2','rifle',O2,h2,(2.4,0,0))
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL'
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
def shot(nm,d,t,osc,res=(1500,900)):
  t=Vector(t);cam.data.ortho_scale=osc;sc.render.resolution_x,sc.render.resolution_y=res;cam.location=t+Vector(d).normalized()*8;cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath='/home/claude/anim/'+nm;bpy.ops.render.render(write_still=True)
shot('dbg_front.png',(0,1,.15),(1.2,0,.75),3.6)
shot('dbg_side.png',(1,0,.1),(1.2,0,.75),2.0,(1300,1000))
shot('dbg_feet.png',(.4,1,.4),(1.2,0,.12),1.2,(1400,700))
