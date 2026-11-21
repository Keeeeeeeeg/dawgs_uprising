import os
exec(open('/home/claude/body/body6.py').read());exec(open('/home/claude/body/qa5.py').read())
ALL=[]
def M3(name,x,yaw=0,label=None,**k):
  kind=k.get('weap','rifle');made,bo=marine(pose(name,x,yaw,kind=kind),**k);ALL.append((label or name,made));return made
M3('colours',0.0,label='bearer',seed=41,gear='std',weap='flag');M3('officer',.95,label='officer',seed=42,head='officer',gear='light',weap='pistol')
M3('colours',2.6,math.pi*.75,label='bearer_b',seed=41,gear='std',weap='flag');M3('officer',3.4,math.pi*.75,label='officer_b',seed=42,head='officer',gear='light',weap='pistol')
build_weapon('pistol',(Vector((5.5,0,1.0)),Matrix.Identity(3)))
TOT=0
for lab,made in ALL:TOT+=len(qa(made,lab))
print('\nQA TOTAL',TOT)
if os.environ.get('QAONLY'):raise SystemExit
put('floor',box((2,0,-.005),(14,6,.01)),FLOOR)
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
  if fill:fl=bpy.data.objects.new('fill',bpy.data.lights.new('fill','AREA'));sc.collection.objects.link(fl);fl.data.energy=fill;fl.data.size=1.5;fl.location=tgt+Vector(d).normalized()*2+Vector((0,0,.5));fl.rotation_euler=(tgt-fl.location).to_track_quat('-Z','Y').to_euler()
  cam.data.ortho_scale=osc;sc.render.resolution_x,sc.render.resolution_y=res;pos=tgt+Vector(d).normalized()*14;cam.location=pos;cam.rotation_euler=(tgt-pos).to_track_quat('-Z','Y').to_euler();sc.render.filepath='/home/claude/body/'+nm+'.png';bpy.ops.render.render(write_still=True)
  if fl:bpy.data.objects.remove(fl)
which=os.environ.get('SHOTS','party,back,head,pistol').split(',')
if 'party' in which:shot('b6_party',(.35,-.9,.12),(.48,0,1.2),2.9,(1600,1500))
if 'back' in which:shot('b6_party_b',(.35,-.9,.12),(3.0,0,1.2),2.9,(1600,1500))
if 'head' in which:shot('b6_officer_head',(.5,-.85,.15),(.95,-.05,1.6),.5,(1000,900),fill=40)
if 'pistol' in which:shot('b6_pistol',(.35,.9,.2),(5.55,0,1.0),.36,(1400,900),fill=60)
bpy.ops.wm.save_as_mainfile(filepath='/home/claude/body/colour_party.blend')
