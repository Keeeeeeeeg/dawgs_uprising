# pass 8 variety/boot/cape sheet: 6 riflemen with different seeds, sniper front+back, boot close-up
import os
exec(open('/home/claude/body/body8.py').read());exec(open('/home/claude/body/qa5.py').read())
ALL=[]
def M3(name,x,yaw=0,label=None,**k):
  kind=k.get('weap','rifle');PP=pose(name,x,yaw,kind=kind);made,bo=marine(PP,**k);ALL.append((label or name,made));print('\nREACH',label or name,[(a,round(b,2)) for a,b in PP['_reach']],PP.get('_var'));return made
SEEDS=[int(v) for v in os.environ.get('SEEDS','51,52,53,54,55,56').split(',')]
for i,sd in enumerate(SEEDS):M3('neutral',i*.9,label='rf%d'%sd,seed=sd)
for i,sd in enumerate(SEEDS):M3('neutral',i*.9,math.pi,label='rb%d'%sd,seed=sd) if 0 else None
M3('neutral',6.0,label='sniperF',seed=21,head='sniper',gear='light',weap='sniper');M3('neutral',6.9,math.pi,label='sniperB',seed=21,head='sniper',gear='light',weap='sniper')
M3('jog',8.2,label='jog',seed=60)
TOT=0
for lab,made in ALL:TOT+=len(qa(made,lab))
print('\nQA TOTAL',TOT)
if os.environ.get('QAONLY'):raise SystemExit
put('floor',box((4,0,-.005),(16,6,.01)),FLOOR)
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
which=os.environ.get('SHOTS','var,varback,sniper,boots').split(',')
if 'var' in which:shot('b8_var',(.35,-.9,.1),(2.25,0,.95),5.6,(2400,1100))
if 'varback' in which:shot('b8_varback',(-.4,.9,.15),(2.25,0,.95),5.6,(2400,1100))
if 'sniper' in which:shot('b8_sniper',(.3,-.9,.1),(6.45,0,1.0),2.2,(1400,1100),fill=40)
if 'boots' in which:shot('b8_boots',(.7,-.7,.25),(0.0,0,.15),.75,(1100,800),fill=40)
