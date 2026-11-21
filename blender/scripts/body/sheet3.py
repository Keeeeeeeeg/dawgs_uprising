import os
exec(open('/home/claude/body/body3.py').read())
SAND=cloth('sandbag',(.26,.23,.15),250)
def M3(name,x,yaw=0,**k):
  kind=k.get('weap','rifle');return marine(pose(name,x,yaw,kind=kind),**k)
for i,yaw in enumerate((0,math.pi/2,math.pi)):
  made,bo=M3('neutral',i*.85-1.7,yaw,seed=3)
  if i==0:CHK=bo
for i,nm in enumerate(('neutral','split','wide','jog')):M3(nm,2.5+i*.95,seed=10+i)
M3('prone',6.3,seed=31,weap='mg',gear='ammo');M3('cover',8.7,seed=32,weap='mg',gear='ammo');M3('carry',9.9,seed=33,weap='mg',gear='ammo')
r=random.Random(5)
for lay in range(4):
  for row,y in enumerate((-.42,-.66,-.9)):
    for k in range(5):
      x=8.7-.72+k*.36+(.18 if lay%2 else 0)+r.uniform(-.02,.02)
      if x>8.7+.8:continue
      put('bag',ell((x,y,.1+lay*.19),(.19,.13,.1),Rz(r.uniform(-.1,.1))),SAND)
M3('neutral',12.0,seed=21,head='sniper',gear='light',weap='sniper');M3('wide',12.95,seed=22,head='spotter',gear='comms');M3('carry',13.9,seed=23,weap='mg',gear='ammo');M3('shoulder',14.85,seed=24,weap='rocket',gear='rocket')
dg=bpy.context.evaluated_depsgraph_get();TR={o.name:BVHTree.FromObject(o,dg) for o in CHK}
for o in CHK:
  if not any(TR[o.name].overlap(TR[n]) for n in TR if n!=o.name):print('FLOATING',o.name)
put('floor',box((6.5,0,-.005),(22,6,.01)),FLOOR)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=int(os.environ.get('SAMP','40'));sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
w=bpy.data.worlds.new('W');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(.03,.034,.03,1)
LT=[]
for nm,off,en,col,sz in (('k',(2,-6,5),700,(1,.97,.92),6),('r',(-5,5,3),420,(.65,1,.8),6),('f',(-2,-7,1),180,(.85,.9,1),8),('t',(0,0,8),250,(1,1,1),10)):
  l=bpy.data.objects.new(nm,bpy.data.lights.new(nm,'AREA'));sc.collection.objects.link(l);l.data.energy=en;l.data.size=sz;l.data.color=col;LT.append((l,Vector(off)))
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
def shot(nm,d,tgt,osc,res,fill=0):
  tgt=Vector(tgt)
  for l,off in LT:l.location=tgt+off;l.rotation_euler=(tgt-l.location).to_track_quat('-Z','Y').to_euler()
  fl=None
  if fill:
    fl=bpy.data.objects.new('fill',bpy.data.lights.new('fill','AREA'));sc.collection.objects.link(fl);fl.data.energy=fill;fl.data.size=1.5;fl.location=tgt+Vector(d).normalized()*2+Vector((0,0,.5));fl.rotation_euler=(tgt-fl.location).to_track_quat('-Z','Y').to_euler()
  cam.data.ortho_scale=osc;sc.render.resolution_x,sc.render.resolution_y=res;pos=tgt+Vector(d).normalized()*14;cam.location=pos;cam.rotation_euler=(tgt-pos).to_track_quat('-Z','Y').to_euler();sc.render.filepath='/home/claude/body/'+nm+'.png';bpy.ops.render.render(write_still=True)
  if fl:bpy.data.objects.remove(fl)
which=os.environ.get('SHOTS','turn,stance,mg,roles,comms,legs,torso').split(',')
if 'turn' in which:shot('b3_turn',(0,-1,.05),(-.85,0,.92),3.5,(1800,1000))
if 'stance' in which:shot('b3_stance',(.4,-.9,.12),(3.93,0,.9),4.2,(2000,1000))
if 'mg' in which:shot('b3_mg',(.6,-.75,.4),(8.0,.2,.45),5.0,(2000,1100))
if 'roles' in which:shot('b3_roles',(.4,-.9,.1),(13.42,0,.95),4.2,(2000,1000))
if 'comms' in which:shot('b3_comms',(.75,.6,.25),(12.95,.15,1.15),1.0,(1000,1000),fill=60)
if 'legs' in which:shot('b3_legs',(.55,-.8,.15),(-1.7,0,.33),.95,(1000,900),fill=40)
if 'torso' in which:shot('b3_torso',(.85,-.45,.12),(-1.7,0,1.18),.8,(1000,900),fill=40)
bpy.ops.wm.save_as_mainfile(filepath='/home/claude/body/marine_v2_body3.blend')
