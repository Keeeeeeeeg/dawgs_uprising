# light tank v3e next to a Dawgs rifleman, at the relative scale the game draws them (soldier x .74 of his model metres:
# skinned raw .812 x SKIN_K .91; vehicles 1:1), plus a 1.8 m reference figure note in the caption
import os
exec(open('/home/claude/body/body8.py').read())
before=set(bpy.data.objects)
PP=pose('neutral',0,0,kind='rifle');made,bo=marine(PP,seed=51,head='rifle',gear='std',weap='rifle')
newo=[o for o in set(bpy.data.objects)-before]
root=bpy.data.objects.new('soldier',None);bpy.context.scene.collection.objects.link(root)
for o in newo:
  if o.parent is None:o.parent=root
K=float(os.environ.get('SK','.74'));root.scale=(K,K,K);root.location=(.9,-2.35,0);root.rotation_euler=(0,0,-.5)
with bpy.data.libraries.load('/home/claude/veh/lt_v3.blend') as (src,dst):
  dst.objects=[n for n in src.objects if n not in('cam','k','r','f','t','floor')]
for o in dst.objects:
  if o is not None:bpy.context.scene.collection.objects.link(o)
src=open('/home/claude/veh/vlib.py').read();exec('def scene_setup'+src.split('def scene_setup',1)[1].split('\ndef cloth')[0])
put('floor',box((0,-1,-.01),(14,12,.02)),FLOOR)
shot=scene_setup(int(os.environ.get('SAMP','24')))
shot('/home/claude/veh/cmp_34.png',(1.0,-1.25,.55),(.3,-.9,.9),6.0,(1600,1100))
shot('/home/claude/veh/cmp_front.png',(.25,-1,.12),(.5,-1.2,.95),5.2,(1500,1000))
