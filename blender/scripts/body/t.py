import bpy
bpy.ops.mesh.primitive_uv_sphere_add()
sc=bpy.context.scene
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c'));sc.collection.objects.link(cam);cam.location=(4,-4,3);cam.rotation_euler=(1.1,0,.78);sc.camera=cam
sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=200;sc.render.resolution_y=200;sc.render.filepath='/home/claude/mar/t.png'
bpy.ops.render.render(write_still=True);print('ok')
