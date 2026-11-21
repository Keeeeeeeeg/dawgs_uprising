import sys;sys.argv=[''];exec(open('/home/claude/hm/h13lib.py').read())
TEAMS=[(.25,.75,.3),(.85,.15,.12),(.55,.3,.85),(.2,.5,.9),(.9,.68,.2)]
G=lensmat(0,TEAMS[0])
helmet({'cap':'full','vents':0,'top':'mount','side':'lamp','chin':'filter'},(-.55,0,0),G)
sniper_head((0,0,0),G);spotter_head((.55,0,0),G)
if 0:
 for i,tc in enumerate(TEAMS):helmet({'cap':'full','vents':i%3,'top':('mount','nvg','mount','none','mount')[i],'side':'lamp','chin':('filter','round')[i%2]},(i*.42-.84,0,-.75),lensmat(i+1,tc))
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=int(sys.argv[-1]) if sys.argv[-1].isdigit() else 64;sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
sc.cycles.samples=64
w=bpy.data.worlds.new('W');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(.03,.034,.03,1)
for nm,loc,en,col,sz in (('k',(1.5,-2,1.2),160,(1,.97,.92),2.5),('r',(-2,1.6,.9),120,(.65,1,.8),2),('f',(-1,-2,-.3),35,(.85,.9,1),3),('t',(0,0,2),40,(1,1,1),3)):
  l=bpy.data.objects.new(nm,bpy.data.lights.new(nm,'AREA'));sc.collection.objects.link(l);l.data.energy=en;l.data.size=sz;l.data.color=col;l.location=loc;l.rotation_euler=(Vector((0,0,-.02))-Vector(loc)).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
def shot(nm,d,tgt,osc,res):
  cam.data.ortho_scale=osc;sc.render.resolution_x,sc.render.resolution_y=res;pos=Vector(tgt)+Vector(d).normalized()*3;cam.location=pos;cam.rotation_euler=(Vector(tgt)-pos).to_track_quat('-Z','Y').to_euler();sc.render.filepath='/home/claude/hm/'+nm+'.png';bpy.ops.render.render(write_still=True)
shot('v13b_34',(.5,-.85,.2),(0,-.01,-.03),1.7,(1800,620))
shot('v13b_front',(0,-1,.06),(0,-.01,-.03),1.7,(1800,620))
shot('v13b_back',(-.6,.75,.3),(0,-.01,-.03),1.7,(1800,620))
#shot('v13b_teams',(.35,-.9,.12),(0,-.01,-.78),2.0,(2000,520))
shot('v13b_close',(.45,-.88,.15),(-.55,-.04,-.02),.42,(900,700))
bpy.ops.wm.save_as_mainfile(filepath='/home/claude/hm/helmet_v13.blend')
