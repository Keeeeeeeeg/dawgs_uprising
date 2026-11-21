exec(open('/home/claude/anim/pose2.py').read().split('def game_idle')[0])
for o in list(bpy.data.objects):bpy.data.objects.remove(o)
V={'A':(-1.55,.55,-.36),'B':(-1.3,-.25,-.33),'C':(-1.42,0.0,-.35),'D':(-1.25,-.55,-.3)}
for i,(k,(sh,ft,hy)) in enumerate(V.items()):
  O={'thigh.R':[0,0,0],'shin.R':[0,0,sh],'foot.R':[0,0,ft],'thigh.L':[0,0,1.25],'shin.L':[0,0,-1.3],'foot.L':[0,0,.05],'hips':[0,.15,0],'spine':[0,0,.05]}
  mesh('k'+k,'rifle',O,hy,off=(0,i*1.3,0))
me=bpy.data.meshes.new('fl');me.from_pydata([(-2,-2,0),(2,-2,0),(2,6,0),(-2,6,0)],[],[(0,1,2,3)]);fl=bpy.data.objects.new('fl',me);bpy.context.scene.collection.objects.link(fl)
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL'
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=5
for nm,loc,rot in (('side',(8,2,.45),(math.pi/2,0,math.pi/2)),('q',(6,-4,2.5),(1.15,0,.95))):
  cam.location=loc;cam.rotation_euler=rot;sc.render.resolution_x,sc.render.resolution_y=1600,700
  sc.render.filepath='/home/claude/anim/kneel_%s.png'%nm;bpy.ops.render.render(write_still=True)
