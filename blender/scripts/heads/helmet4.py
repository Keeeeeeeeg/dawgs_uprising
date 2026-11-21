# (concept v2) full-face marine helmet: high-cut ballistic shell, goggle visor with a frame, faceted jaw guard of three plates
# (two cheek plates + a mouth piece) with vents and a chin filter. Real metres, head centre at origin, -y = front, z up.
import bpy,bmesh,math
from mathutils import Vector,Matrix
for o in list(bpy.data.objects):bpy.data.objects.remove(o)
def M(name,col,rough=.5,metal=0,emit=0,spec=.5):
  m=bpy.data.materials.new(name);m.use_nodes=True;b=m.node_tree.nodes['Principled BSDF']
  b.inputs['Base Color'].default_value=col+(1,);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
  if emit:b.inputs['Emission Color'].default_value=col+(1,);b.inputs['Emission Strength'].default_value=emit
  return m
def steel(name,col,wear=1.0,scr=1.0):
  m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;N=nt.nodes;Lk=nt.links;b=N['Principled BSDF']
  geo=N.new('ShaderNodeNewGeometry');tc=N.new('ShaderNodeTexCoord')
  edge=N.new('ShaderNodeValToRGB');edge.color_ramp.elements[0].position=.52;edge.color_ramp.elements[1].position=.58;Lk.new(geo.outputs['Pointiness'],edge.inputs[0])
  nz=N.new('ShaderNodeTexNoise');nz.inputs['Scale'].default_value=60;nz.inputs['Detail'].default_value=8;Lk.new(tc.outputs['Object'],nz.inputs['Vector'])
  nr=N.new('ShaderNodeValToRGB');nr.color_ramp.elements[0].position=.45;nr.color_ramp.elements[1].position=.6;Lk.new(nz.outputs['Fac'],nr.inputs[0])
  wearF=N.new('ShaderNodeMath');wearF.operation='MULTIPLY';Lk.new(edge.outputs['Color'],wearF.inputs[0]);Lk.new(nr.outputs['Color'],wearF.inputs[1])
  # scratches: stretched noise lines
  mp=N.new('ShaderNodeMapping');mp.inputs['Scale'].default_value=(900,40,40);Lk.new(tc.outputs['Object'],mp.inputs['Vector'])
  sc=N.new('ShaderNodeTexNoise');sc.inputs['Scale'].default_value=1;sc.inputs['Detail'].default_value=2;Lk.new(mp.outputs['Vector'],sc.inputs['Vector'])
  sr=N.new('ShaderNodeValToRGB');sr.color_ramp.elements[0].position=.68;sr.color_ramp.elements[1].position=.72;Lk.new(sc.outputs['Fac'],sr.inputs[0])
  mask=N.new('ShaderNodeMath');mask.operation='MAXIMUM';Lk.new(wearF.outputs[0],mask.inputs[0])
  scm=N.new('ShaderNodeMath');scm.operation='MULTIPLY';scm.inputs[1].default_value=.6*scr;Lk.new(sr.outputs['Color'],scm.inputs[0]);Lk.new(scm.outputs[0],mask.inputs[1])
  mk=N.new('ShaderNodeMath');mk.operation='MULTIPLY';mk.inputs[1].default_value=wear;Lk.new(mask.outputs[0],mk.inputs[0])
  # paint colour with mottling + grime in cavities (AO)
  mot=N.new('ShaderNodeTexNoise');mot.inputs['Scale'].default_value=9;Lk.new(tc.outputs['Object'],mot.inputs['Vector'])
  pc=N.new('ShaderNodeMix');pc.data_type='RGBA';pc.inputs['A'].default_value=col+(1,);pc.inputs['B'].default_value=tuple(c*.72 for c in col)+(1,);Lk.new(mot.outputs['Fac'],pc.inputs['Factor'])
  ao=N.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.02
  gr=N.new('ShaderNodeMix');gr.data_type='RGBA';gr.inputs['B'].default_value=(.025,.022,.018,1);Lk.new(pc.outputs['Result'],gr.inputs['A'])
  inv=N.new('ShaderNodeMath');inv.operation='SUBTRACT';inv.inputs[0].default_value=1;Lk.new(ao.outputs['AO'],inv.inputs[1]);Lk.new(inv.outputs[0],gr.inputs['Factor'])
  fin=N.new('ShaderNodeMix');fin.data_type='RGBA';fin.inputs['B'].default_value=(.42,.42,.4,1);Lk.new(gr.outputs['Result'],fin.inputs['A']);Lk.new(mk.outputs[0],fin.inputs['Factor'])
  Lk.new(fin.outputs['Result'],b.inputs['Base Color']);Lk.new(mk.outputs[0],b.inputs['Metallic'])
  ro=N.new('ShaderNodeMapRange');ro.inputs['To Min'].default_value=.62;ro.inputs['To Max'].default_value=.3;Lk.new(mk.outputs[0],ro.inputs['Value']);Lk.new(ro.outputs['Result'],b.inputs['Roughness'])
  bu=N.new('ShaderNodeBump');bu.inputs['Strength'].default_value=.12;bu.inputs['Distance'].default_value=.0006
  bn=N.new('ShaderNodeTexNoise');bn.inputs['Scale'].default_value=420;bn.inputs['Detail'].default_value=4;Lk.new(tc.outputs['Object'],bn.inputs['Vector'])
  bs=N.new('ShaderNodeMath');bs.operation='ADD';Lk.new(bn.outputs['Fac'],bs.inputs[0]);Lk.new(scm.outputs[0],bs.inputs[1]);Lk.new(bs.outputs[0],bu.inputs['Height']);Lk.new(bu.outputs['Normal'],b.inputs['Normal'])
  return m
def rubber(name,col):
  m=M(name,col,.85);nt=m.node_tree;N=nt.nodes;b=N['Principled BSDF'];tc=N.new('ShaderNodeTexCoord');n=N.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=700
  nt.links.new(tc.outputs['Object'],n.inputs['Vector']);bu=N.new('ShaderNodeBump');bu.inputs['Strength'].default_value=.25;nt.links.new(n.outputs['Fac'],bu.inputs['Height']);nt.links.new(bu.outputs['Normal'],b.inputs['Normal']);return m
SHELL=steel('shell',(.1,.105,.095));PLATE=steel('plate',(.085,.088,.083),1.2,1.3);DARK=rubber('dark',(.02,.02,.02));VIS=M('visor',(.01,.012,.015),.04,.7);EYE=M('eye',(.2,1,.45),.3,0,10);RUB=rubber('rubber',(.015,.015,.015));METL=M('metal',(.25,.25,.25),.3,.9)
def link(name,bm,mat,bev=0,sol=0,smooth=True,segs=2):
  me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free();o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o);me.materials.append(mat)
  for p in me.polygons:p.use_smooth=smooth
  if sol:s=o.modifiers.new('s','SOLIDIFY');s.thickness=sol;s.offset=-1
  if bev:b=o.modifiers.new('b','BEVEL');b.width=bev;b.segments=segs;b.limit_method='ANGLE';b.angle_limit=.6
  o.modifiers.new('w','WEIGHTED_NORMAL');return o
def sphere_cut(r,s,keep,u=72,v=48):
  bm=bmesh.new();bmesh.ops.create_uvsphere(bm,u_segments=u,v_segments=v,radius=r)
  for vv in bm.verts:vv.co=Vector((vv.co.x*s[0],vv.co.y*s[1],vv.co.z*s[2]))
  bmesh.ops.delete(bm,geom=[vv for vv in bm.verts if not keep(vv.co)],context='VERTS');return bm
def hull(pts):
  bm=bmesh.new();vs=[bm.verts.new(p) for p in pts];bmesh.ops.convex_hull(bm,input=vs);return bm
def box(c,s,rot=None):
  bm=bmesh.new();bmesh.ops.create_cube(bm,size=1);bmesh.ops.scale(bm,vec=s,verts=bm.verts)
  if rot:bmesh.ops.rotate(bm,cent=(0,0,0),matrix=rot,verts=bm.verts)
  bmesh.ops.translate(bm,vec=c,verts=bm.verts);return bm

VIS=M('visor',(.22,.5,.72),.05,.65);FAB=M('fabric',(.06,.065,.055),.9)
def helmet(V,off):
  """V: variant dict: mask (full|open), vents (0..2), top (none|mount|nvg), side (lamp|pod|antenna), chin (filter|round)"""
  objs=[]
  def L(name,bm,mat,**k):
    o=link(name,bm,mat,**k);o.location=off;objs.append(o);return o
  def rimz(a):a=abs(a);return .036 if a<.62 else (.036+(a-.62)/.5*(-.085) if a<1.12 else (-.05 if a<2.3 else -.07))
  # shell: a full sphere with clean boolean cuts (face opening over the visor, rising cut behind the ears, nape)
  bm=bmesh.new();bmesh.ops.create_uvsphere(bm,u_segments=96,v_segments=64,radius=.13)
  for v in bm.verts:
    x,y,z=v.co.x*1.02,v.co.y*1.12,v.co.z*.95
    k=max(0,y)/.145;x*=1-.1*k;z-=.012*k*k           # narrower and a touch lower toward the back
    ax=abs(x);lim=.112+.02*max(0,z)/.12             # flatter sides
    if ax>lim:x=math.copysign(lim+(ax-lim)*.35,x)
    if y<0:z+=.006*max(0,-y)/.14                     # a slightly taller brow
    v.co=Vector((x,y,z))
  sh=L('shell',bm,SHELL)
  bw=sphere_cut(.1345,(1.0,1.13,.95),lambda c:c.y<-.03 and .03<c.z<.058 and abs(c.x)<.118,u=96,v=64)
  L('brow',bw,SHELL,sol=.009,bev=.003)   # brow band
  def cutter(c,sz,rot=None):
    o=link('cut',box(c,sz,rot),DARK);o.location=off;o.hide_render=True;o.display_type='WIRE';return o
  cuts=[cutter((0,-.1,-.13),(.36,.2,.33)),cutter((0,0,-.2),(.4,.5,.2)),cutter((0,.03,-.1),(.4,.12,.12),Matrix.Rotation(.5,3,'X')),cutter((0,.14,-.15),(.4,.12,.12))]
  for c in cuts:
    m=sh.modifiers.new('bo','BOOLEAN');m.object=c;m.operation='DIFFERENCE';m.solver='EXACT'
    sh.modifiers.move(len(sh.modifiers)-1,0)
  so=sh.modifiers.new('s','SOLIDIFY');so.thickness=.011;so.offset=-1
  bv=sh.modifiers.new('b','BEVEL');bv.width=.004;bv.segments=3;bv.limit_method='ANGLE';bv.angle_limit=.6
  for md in ('w',):
    if md in sh.modifiers:sh.modifiers.move(sh.modifiers.find(md),len(sh.modifiers)-1)
  L('lens',sphere_cut(.124,(1.05,1.2,1),lambda c:c.y<-.035 and -.04<c.z<.03 and abs(c.x)<.112),VIS,sol=.003)
  L('frame',sphere_cut(.122,(1.06,1.2,1),lambda c:(c.y<-.025 and -.05<c.z<.038 and abs(c.x)<.122) and not (c.y<-.035 and -.04<c.z<.03 and abs(c.x)<.112)),PLATE,sol=.008,bev=.002)
  L('eye',sphere_cut(.1265,(1.05,1.2,1),lambda c:c.y<-.1 and -.012<c.z<.014 and -.078<c.x<-.045,u=96,v=64),EYE)
  if V['mask']=='full':
    P=[]
    for s_ in (1,-1):P+=[(s_*.125,.02,-.045),(s_*.122,-.04,-.05),(s_*.105,-.1,-.052),(s_*.075,-.135,-.052),(s_*.12,.025,-.105),(s_*.112,-.04,-.12),(s_*.09,-.095,-.14),(s_*.06,-.13,-.15)]
    P+=[(0,-.16,-.052),(-.04,-.162,-.06),(.04,-.162,-.06),(0,-.188,-.105),(-.035,-.18,-.115),(.035,-.18,-.115),(0,-.16,-.158),(-.03,-.148,-.158),(.03,-.148,-.158)]
    mk=L('mask',hull(P),PLATE,bev=.006,segs=3,smooth=False)
    for s_ in (1,-1):   # panel grooves and vents
      L('groove',box((s_*.085,-.122,-.1),(.004,.006,.085),Matrix.Rotation(s_*.6,3,'Z')),DARK)
      for i in range(V['vents']+2):L('vent',box((s_*(.122-i*.006),-.03-i*.022,-.09),(.006,.014,.036),Matrix.Rotation(s_*(.25+i*.2),3,'Z')),DARK,bev=.002)
    if V['chin']=='filter':
      L('filter',box((0,-.186,-.112),(.04,.012,.032)),DARK,bev=.003)
      for i in range(3):L('slot',box((0,-.1925,-.1-i*.01),(.03,.003,.003)),METL)
    else:
      L('filterR',(lambda bm:(bmesh.ops.create_cone(bm,cap_ends=True,segments=20,radius1=.02,radius2=.018,depth=.016),bmesh.ops.rotate(bm,cent=(0,0,0),matrix=Matrix.Rotation(math.pi/2,3,'X'),verts=bm.verts),bmesh.ops.translate(bm,vec=(0,-.185,-.11),verts=bm.verts),bm)[3])(bmesh.new()),DARK,bev=.002)
  else:   # open face: a balaclava under the shell, a boom mic
    L('bala',sphere_cut(.106,(1,1.08,1.2),lambda c:c.z<-.03 or (c.y>-.06)),FAB)
    L('boom',box((.07,-.09,-.07),(.006,.08,.006),Matrix.Rotation(.9,3,'Z')),DARK)
    L('mic',box((.035,-.125,-.075),(.016,.012,.012)),DARK,bev=.003)
  for s_ in (1,-1):
    L('rail',box((s_*.135,.0,.0),(.007,.09,.013)),METL,bev=.002)
    L('hinge',box((s_*.13,.0,-.07),(.014,.03,.03)),DARK,bev=.004)
  if V['side']=='lamp':L('lamp',box((.147,-.03,.0),(.016,.035,.02)),DARK,bev=.003)
  if V['side'] in('pod','antenna'):L('pod',box((-.14,.01,-.005),(.02,.05,.045)),PLATE,bev=.006)
  if V['side']=='antenna':L('ant',box((-.145,.04,.12),(.003,.003,.24),Matrix.Rotation(-.25,3,'X')),DARK)
  if V['top']=='mount':L('mount',box((0,-.105,.07),(.05,.02,.016),Matrix.Rotation(-.7,3,'X')),DARK,bev=.003)
  if V['top']=='nvg':
    L('mount',box((0,-.105,.07),(.05,.02,.016),Matrix.Rotation(-.7,3,'X')),DARK,bev=.003)
    for s_ in (1,-1):L('tube',(lambda bm,s_=s_:(bmesh.ops.create_cone(bm,cap_ends=True,segments=16,radius1=.013,radius2=.015,depth=.045),bmesh.ops.rotate(bm,cent=(0,0,0),matrix=Matrix.Rotation(math.pi/2-.4,3,'X'),verts=bm.verts),bmesh.ops.translate(bm,vec=(s_*.02,-.13,.085),verts=bm.verts),bm)[3])(bmesh.new()),DARK,bev=.002)
  L('neck',(lambda bm:(bmesh.ops.create_cone(bm,cap_ends=False,segments=40,radius1=.08,radius2=.072,depth=.07),bmesh.ops.translate(bm,vec=(0,.01,-.15),verts=bm.verts),bm)[2])(bmesh.new()),RUB)
  return objs
VARS=[('Rifleman A',{'mask':'full','vents':0,'top':'mount','side':'lamp','chin':'filter'}),
      ('Rifleman B',{'mask':'full','vents':1,'top':'nvg','side':'lamp','chin':'round'}),
      ('Leader',{'mask':'full','vents':2,'top':'mount','side':'antenna','chin':'filter'}),
      ('Officer / sniper',{'mask':'open','vents':0,'top':'none','side':'pod','chin':'filter'})]
for i,(n,V) in enumerate(VARS):helmet(V,(i*.36-.54,0,0))
# render: neutral studio, a sage rim light, 3/4 hero + turnarounds
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=128;sc.render.resolution_x,sc.render.resolution_y=(1600,520);sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
w=bpy.data.worlds.new('W');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(.03,.034,.03,1)
for nm,loc,en,col,sz in (('k',(1.5,-2,1.2),160,(1,.97,.92),2.5),('r',(-2,1.6,.9),120,(.65,1,.8),2),('f',(-1,-2,-.3),35,(.85,.9,1),3),('t',(0,0,2),40,(1,1,1),3)):
  l=bpy.data.objects.new(nm,bpy.data.lights.new(nm,'AREA'));sc.collection.objects.link(l);l.data.energy=en;l.data.size=sz;l.data.color=col;l.location=loc;l.rotation_euler=(Vector((0,0,-.02))-Vector(loc)).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=1.5
for nm,d in (('v4_34',(.5,-.85,.2)),):
  pos=Vector(d).normalized()*3;cam.location=pos;cam.rotation_euler=(Vector((0,-.01,-.03))-pos).to_track_quat('-Z','Y').to_euler();sc.render.filepath='/home/claude/hm/'+nm+'.png';bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath='/home/claude/hm/helmet_v4.blend')
