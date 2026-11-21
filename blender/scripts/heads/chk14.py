import sys;exec(open('/home/claude/hm/h13lib.py').read())
G=lensmat(0,(.25,.75,.3))
for k,V in enumerate([{'cap':'full','vents':0,'top':'mount','side':'lamp','chin':'filter'},{'cap':'skull','chin':'filter'},{'cap':'full','vents':1,'chin':'round'}]):helmet(V,(k*.5,0,0),G)
dg=bpy.context.evaluated_depsgraph_get()
for o in bpy.data.objects:
  if o.name.split('.')[0] in('shell','mask','chin'):print(o.name,len(o.evaluated_get(dg).data.polygons))
