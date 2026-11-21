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
  edge=N.new('ShaderNodeValToRGB');edge.color_ramp.elements[0].position=.545;edge.color_ramp.elements[1].position=.58;Lk.new(geo.outputs['Pointiness'],edge.inputs[0])
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
SHELL=steel('shell',(.1,.105,.095),0,.9);PLATE=steel('plate',(.085,.088,.083),0,.8);DARK=rubber('dark',(.02,.02,.02));VIS=M('visor',(.01,.012,.015),.04,.7);EYE=M('eye',(.2,1,.45),.3,0,10);RUB=rubber('rubber',(.015,.015,.015));METL=M('metal',(.25,.25,.25),.3,.9)
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


def facet(name,pts,mat,off,objs,bev=.0035):
  o=link(name,hull(pts),mat,bev=bev,segs=2,smooth=False);o.location=off;objs.append(o);return o
def helmet(V,off):
  """(v7, from the reference) a ROUND ballistic shell with a crisp rim, a smooth wrap visor with a nose notch, and an ANGULAR faceted mask"""
  objs=[]
  def L(name,bm,mat,**k):
    o=link(name,bm,mat,**k);o.location=off;objs.append(o);return o
  # (v8) shell: the classic WW2 German steel-helmet silhouette: a tall rounded dome, a slight waist (the step), then a skirt
  # that flares out and down over the ears and the nape, short at the front. Lofted: radius per ring = profile(z) x plan shape
  bm=bmesh.new();NU,NV=96,56;H0,H1=-.115,.128;A,Bh=.118,.135;rings=[]
  def prof(z,c):   # c = cos(angle): 1 front, -1 back
    if z>=0:t=z/H1;return (1-t**2.4)**(1/2.4)
    fl=.55+.75*(1-max(0,c))                       # skirt flare: strong at the sides and back, small at the front
    w=1-.03*math.exp(-((z+.012)/.008)**2)          # the waist step
    return w*(1+fl*(-z)**1.35*1.6)
  for j in range(NV+1):
    t=j/NV;z=H0+(H1-H0)*t;ring=[]
    for i in range(NU):
      a=i/NU*2*math.pi;c,sn=math.cos(a),math.sin(a);e=2/2.3;k=prof(z,-c)
      ring.append(bm.verts.new((A*k*math.copysign(abs(sn)**e,sn),Bh*k*math.copysign(abs(c)**e,c)-.004,z)))
    rings.append(ring)
  for j in range(NV):
    for i in range(NU):bm.faces.new((rings[j][i],rings[j][(i+1)%NU],rings[j+1][(i+1)%NU],rings[j+1][i]))
  top=bm.verts.new((0,-.004,H1));[bm.faces.new((rings[NV][i],rings[NV][(i+1)%NU],top)) for i in range(NU)];bm.faces.new(list(reversed(rings[0])))
  bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
  sh=L('shell',bm,SHELL)
  def cutter(c,sz,rot=None):
    o=link('cut',box(c,sz,rot),DARK);o.location=off;o.hide_render=True;return o
  for c in [cutter((0,-.14,-.105),(.205,.2,.27)),cutter((0,-.24,-.1),(.42,.2,.27)),cutter((0,0,-.2),(.5,.6,.17))]:
    m=sh.modifiers.new('bo','BOOLEAN');m.object=c;m.operation='DIFFERENCE';m.solver='EXACT';sh.modifiers.move(len(sh.modifiers)-1,0)
  so=sh.modifiers.new('s','SOLIDIFY');so.thickness=.012;so.offset=-1
  bv=sh.modifiers.new('b','BEVEL');bv.width=.0035;bv.segments=3;bv.limit_method='ANGLE';bv.angle_limit=.5
  # mount plate on the front-top and a raised strip over the crown (reference)
  L('mount',box((0,-.105,.085),(.06,.03,.01),Matrix.Rotation(-.75,3,'X')),DARK,bev=.003)
  L('mountP',box((0,-.1,.08),(.075,.045,.006),Matrix.Rotation(-.75,3,'X')),PLATE,bev=.002)
  # (v10) SUNKEN CHANNEL visor: a window cut into the shell (rounded corners, top and sides follow the helmet), the lens set
  # back inside it on a surface that follows the shell's own contour, a dark liner behind, and a rubber seal along the bottom
  VX=.118
  def _sq(x):return max(0,1-(abs(x)/VX)**6)**(1/6)
  def vtop(x):
    t=.034-.022*(x/VX)**2;b0=-.046+.024*(x/VX)**2;m=(t+b0)/2;return m+(t-m)*_sq(x)
  def vbot(x):
    t=.034-.022*(x/VX)**2;b0=-.046+.024*(x/VX)**2;m=(t+b0)/2;return m+(b0-m)*_sq(x)+.03*math.exp(-(x/.024)**2)*_sq(x)
  VT=.034
  def front_y(x,z,inset):   # the shell's front surface at (x,z), pulled in by `inset` along the depth
    tt=max(0,(z)/H1);k=prof(z,1.0) if z<0 else (1-min(1,tt)**2.4)**(1/2.4)
    e=2/2.3;u=min(.999,abs(x)/(A*k));sn=u**(1/e);c=max(0,1-sn*sn)**.5
    return -(Bh*k*c**e)-.004+inset
  # window cutter: a prism along y with the visor outline (rounded top corners)
  bm=bmesh.new();outline=[];N=60
  for i in range(N+1):x=-VX+2*VX*i/N;outline.append((x,vbot(x)-.003))
  for i in range(N-1,0,-1):x=-VX+2*VX*i/N;outline.append((x,vtop(x)+.002))
  fv=[bm.verts.new((x,-.3,z)) for x,z in outline];bv=[bm.verts.new((x,-.06,z)) for x,z in outline]
  bm.faces.new(fv);bm.faces.new(list(reversed(bv)))
  n=len(outline)
  for i in range(n):bm.faces.new((fv[i],fv[(i+1)%n],bv[(i+1)%n],bv[i]))
  bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
  wc=link('wcut',bm,DARK);wc.location=off;wc.hide_render=True
  m=sh.modifiers.new('win','BOOLEAN');m.object=wc;m.operation='DIFFERENCE';m.solver='EXACT';sh.modifiers.move(len(sh.modifiers)-1,0)
  # the lens: a curved sheet on the shell contour, 1.4 cm behind the surface
  def sheet(inset,mat,name,pad=0.0):
    bm=bmesh.new();NXs,NZs=80,16;G2=[]
    for i in range(NXs+1):
      x=-(VX+pad)+2*(VX+pad)*i/NXs;col=[]
      for j in range(NZs+1):
        z=(vbot(x)-.004-pad)+((vtop(x)+.004+pad)-(vbot(x)-.004-pad))*j/NZs;col.append(bm.verts.new((x,front_y(x,z,inset),z)))
      G2.append(col)
    for i in range(NXs):
      for j in range(NZs):bm.faces.new((G2[i][j],G2[i+1][j],G2[i+1][j+1],G2[i][j+1]))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces);o=L(name,bm,mat);s2=o.modifiers.new('s','SOLIDIFY');s2.thickness=.003;return o
  sheet(.014,VIS,'lens');sheet(.03,DARK,'liner',pad=.01)
  # rubber seal along the bottom of the window, following the notch
  bm=bmesh.new();prev=None
  for i in range(61):
    x=-VX*.985+2*VX*.985*i/60;z=vbot(x)-.006;y=front_y(x,z,.006)
    ring=[bm.verts.new((x,y+.006*math.cos(a2),z+.0045*math.sin(a2))) for a2 in [k/6*2*math.pi for k in range(6)]]
    if prev:
      for k in range(6):bm.faces.new((prev[k],prev[(k+1)%6],ring[(k+1)%6],ring[k]))
    prev=ring
  L('seal',bm,RUB)
  ex=-.058;ez=.006;L('eye',box((ex,front_y(ex,ez,.012),ez),(.026,.002,.016),Matrix.Rotation(-.35,3,'Z')),EYE)
  if V['mask']=='full':
    # the angular part: a faceted mask whose top centre tucks up into the nose notch; cheeks angle back to the ear
    Mp=[]
    for sx in (1,-1):Mp+=[(sx*.13,.0,-.054),(sx*.128,.0,-.11),(sx*.12,-.07,-.056),(sx*.11,-.075,-.13),(sx*.08,-.128,-.056),(sx*.06,-.15,-.16),(sx*.034,-.155,-.05),(sx*.024,-.2,-.165)]
    Mp+=[(0,-.162,-.024),(0,-.215,-.1),(0,-.212,-.172),(0,-.17,-.19)]
    facet('mask',Mp,PLATE,off,objs,bev=.004)
    for sx in (1,-1):
      L('slotV',box((sx*.105,-.1,-.095),(.006,.012,.06),Matrix.Rotation(sx*.75,3,'Z')),DARK,bev=.002)   # long cheek slot (reference)
      for i in range(V['vents']+1):L('vent',box((sx*(.127-i*.006),-.025-i*.018,-.088),(.005,.012,.032),Matrix.Rotation(sx*(.2+i*.2),3,'Z')),DARK,bev=.002)
    # chin module: a squared box under the snout
    if V['chin']=='filter':L('chin',box((0,-.205,-.15),(.05,.03,.04),Matrix.Rotation(.35,3,'X')),PLATE,bev=.004);L('chinF',box((0,-.222,-.152),(.034,.004,.024),Matrix.Rotation(.35,3,'X')),DARK,bev=.002)
    else:L('chin',box((0,-.205,-.15),(.04,.03,.045),Matrix.Rotation(.35,3,'X')),DARK,bev=.008)
  else:
    L('bala',box((0,-.03,-.1),(.2,.2,.12)),FAB,bev=.035)
    L('boom',box((.075,-.11,-.07),(.006,.09,.006),Matrix.Rotation(.9,3,'Z')),DARK)
  for sx in (1,-1):L('ear',box((sx*.128,.0,-.03),(.02,.06,.05)),PLATE,bev=.008)
  if V['side']=='lamp':L('lamp',box((.145,-.03,.01),(.018,.04,.022)),DARK,bev=.003)
  if V['side']=='antenna':L('ant',box((-.14,.05,.13),(.003,.003,.26),Matrix.Rotation(-.25,3,'X')),DARK)
  if V['top']=='nvg':
    for sx in (1,-1):L('tube',box((sx*.02,-.13,.1),(.022,.04,.022),Matrix.Rotation(-.4,3,'X')),DARK,bev=.004)
  L('neck',box((0,.0,-.16),(.15,.15,.07)),RUB,bev=.03)
  return objs
VARS=[('Rifleman A',{'mask':'full','vents':0,'top':'mount','side':'lamp','chin':'filter'}),
      ('Rifleman B',{'mask':'full','vents':1,'top':'nvg','side':'lamp','chin':'round'}),
      ('Leader',{'mask':'full','vents':2,'top':'mount','side':'antenna','chin':'filter'}),
      ('Officer / sniper',{'mask':'open','vents':0,'top':'none','side':'pod','chin':'filter'})]
TEAMS=[(.25,.75,.3),(.85,.15,.12),(.55,.3,.85),(.2,.5,.9),(.9,.68,.2)]   # Dawgs, Crimson Legion, Iron Covenant, Ear Gaugers, Tribal Skull
for i,tc in enumerate(TEAMS):
  globals()['VIS']=M('visor%d'%i,tc,.05,.55);helmet(VARS[i%3][1] if i<3 else VARS[0][1],(i*.4-.8,0,0))
# render: neutral studio, a sage rim light, 3/4 hero + turnarounds
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=64;sc.render.resolution_x,sc.render.resolution_y=(2000,520);sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
w=bpy.data.worlds.new('W');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(.03,.034,.03,1)
for nm,loc,en,col,sz in (('k',(1.5,-2,1.2),160,(1,.97,.92),2.5),('r',(-2,1.6,.9),120,(.65,1,.8),2),('f',(-1,-2,-.3),35,(.85,.9,1),3),('t',(0,0,2),40,(1,1,1),3)):
  l=bpy.data.objects.new(nm,bpy.data.lights.new(nm,'AREA'));sc.collection.objects.link(l);l.data.energy=en;l.data.size=sz;l.data.color=col;l.location=loc;l.rotation_euler=(Vector((0,0,-.02))-Vector(loc)).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=1.9
for nm,d in (('v12_34',(.5,-.85,.2)),('v12_front',(0,-1,.06)),):
  pos=Vector(d).normalized()*3;cam.location=pos;cam.rotation_euler=(Vector((0,-.01,-.03))-pos).to_track_quat('-Z','Y').to_euler();sc.render.filepath='/home/claude/hm/'+nm+'.png';bpy.ops.render.render(write_still=True)
cam.data.ortho_scale=.55;sc.render.resolution_x,sc.render.resolution_y=(700,600);pos=Vector((-3,-.2,.25));cam.location=Vector((-.8,0,-.02))+pos;cam.rotation_euler=(Vector((-.8,-.02,-.02))-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath='/home/claude/hm/v12_side.png';bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath='/home/claude/hm/helmet_v12.blend')
