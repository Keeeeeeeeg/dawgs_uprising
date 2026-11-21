# (v15) per-man variants + BAKE DETAILS: small high-frequency pieces (rivets, seams, stencils, patches, tape, cable, grille
# slats) that go in collection 'BakeDetail' and are flagged o['bake']=1. On the game mesh they will NOT exist as geometry:
# they are baked into the normal + colour maps of the low-poly helmet (next pipeline step).
exec(open('/home/claude/hm/h13lib.py').read())
from mathutils.bvhtree import BVHTree
STEN=M('stencil',(.55,.55,.5),.75);TAPE=M('tape',(.09,.1,.07),.85);VELC=cloth('velcro',(.05,.055,.045),900);BRASS=M('brass',(.45,.35,.15),.35,.9)
BAKE=bpy.data.collections.new('BakeDetail');bpy.context.scene.collection.children.link(BAKE)
def bake_obj(name,bm,mat,off,bev=0,smooth=True):
  o=link(name,bm,mat,bev=bev,smooth=smooth);o.location=off;o['bake']=1
  bpy.context.scene.collection.objects.unlink(o);BAKE.objects.link(o);return o
def frame(n):   # rotation whose local z = surface normal, local y as close to world up as possible
  return n.to_track_quat('Z','Y').to_matrix()
def variant(seed,off,lens,force=None):
  r=random.Random(seed)
  V={'cap':'full','vents':r.randrange(3),'chin':r.choice(['filter','filter','round']),'top':r.choice(['mount','mount','nvg','none','rail']),'side':r.choice(['lamp','lamp','antenna','pod','none'])}
  if force:V.update(force)
  if V.get('scanner') and V['side']=='lamp':V['side']='antenna'
  objs,prof,H1=helmet(V,off,lens)
  dg=bpy.context.evaluated_depsgraph_get()
  trees=[(o,BVHTree.FromObject(o,dg)) for o in objs if o.name.split('.')[0] in('shell','mask','chin','ear')]
  O=Vector(off)
  def hit(p,d):   # cast from p (helmet-local) along d; returns local point + normal on the nearest surface
    best=None
    for o,t in trees:
      h=t.ray_cast(Vector(p),Vector(d).normalized(),1)
      if h[0] is not None and (best is None or h[3]<best[2]):best=(h[0],h[1],h[3],o.name)
    return best
  def stud(name,p,d,r_=.0032,h=.0025,mat=PLATE):
    b=hit(p,d)
    if not b:return
    bm=bmesh.new();bmesh.ops.create_cone(bm,cap_ends=True,segments=10,radius1=r_,radius2=r_*.8,depth=h);R=frame(b[1])
    bmesh.ops.transform(bm,matrix=Matrix.Translation(b[0]+b[1]*h*.3)@R.to_4x4(),verts=bm.verts);bake_obj(name,bm,mat,off)
  def plate(name,p,d,w,hgt,th,mat,rot=0):
    b=hit(p,d)
    if not b:return None
    bm=box((0,0,0),(w,hgt,th));R=frame(b[1])@Matrix.Rotation(rot,3,'Z');bmesh.ops.transform(bm,matrix=Matrix.Translation(b[0]+b[1]*th*.4)@R.to_4x4(),verts=bm.verts)
    return bake_obj(name,bm,mat,off,bev=min(w,hgt,th)*.3)
  def text(s,p,d,size,mat=STEN):
    b=hit(p,d)
    if not b:return
    cu=bpy.data.curves.new('t','FONT');cu.body=s;cu.size=size;cu.extrude=.0004;cu.align_x='CENTER';cu.align_y='CENTER'
    o=bpy.data.objects.new('sten',cu);BAKE.objects.link(o);o['bake']=1;o.data.materials.append(mat)
    o.matrix_world=Matrix.Translation(O+b[0]+b[1]*.0006)@frame(b[1]).to_4x4()
  # rivets: a row along each cheek of the mask, two on each ear plate
  for sx in (1,-1):
    for k in range(3):stud('rivet',(sx*.3,-.03-k*.035,-.07-k*.025),(-sx,-.2,0))
    for k in (-1,1):stud('rivet',(sx*.3,.012+k*.03,-.012),(-sx,0,0),.0028,.002,METL)
  # stencilled serial on the left side of the shell, and a roster number on the back
  text('%s-%02d'%(r.choice(['DU','K9','DG']),r.randrange(1,99)),(-.3,.03,.045),(1,0,0),.013)
  text(str(r.randrange(1,9)),(0,.4,.06),(0,-1,0),.022)
  # seam: a welded band round the brow above the visor channel (some men), or a crown seam strip front to back
  if r.random()<.5:
    for k in range(17):
      a2=-.75+1.5*k/16;stud('weld',(math.sin(a2)*.4,-math.cos(a2)*.4,.062),(-math.sin(a2),math.cos(a2),-.05),.0022,.0016,METL)
  else:
    for k in range(9):
      t=k/8;z=.06+.065*math.sin(t*math.pi);y=-.09+.2*t;plate('seam',(0,y,.4),(0,0,-1),.006,.022,.0012,DARK)
  # tape wrap across the crown or the side, an IR/name patch on the back (velcro), cable from eyepiece to the ear plate
  if r.random()<.6:plate('tape',(r.uniform(-.05,.05),.0,.4),(0,0,-1),.03,.07,.0015,TAPE,r.uniform(-.6,.6))
  if r.random()<.7:plate('patch',(.0,.4,.0),(0,-1,0),.045,.03,.002,VELC)
  if r.random()<.6 and not V.get('scanner'):
    bm=bmesh.new();pr=None
    for k in range(13):
      t=k/12;p=Vector((-.075-.07*t,-.115+.11*t+.01*math.sin(t*3.1),.0-.02*math.sin(t*3.1)));b=hit(p+Vector((-.1,-.1,0)),Vector((1,1,0)))
      c=(b[0]+b[1]*.004) if b else p;ring=[bm.verts.new(c+Vector((0,.0025*math.cos(a2),.0025*math.sin(a2)))) for a2 in [i/6*2*math.pi for i in range(6)]]
      if pr:[bm.faces.new((pr[i],pr[(i+1)%6],ring[(i+1)%6],ring[i])) for i in range(6)]
      pr=ring
    bake_obj('cable',bm,DARK,off)
  # chin filter slats
  if V['chin']=='filter':
    for k in range(3):plate('slat',(0,-.4,-.143-k*.008),(0,1,-.35),.03,.0025,.0015,METL)
  # little brass valve or a scuffed dent marker on some masks
  if r.random()<.5:stud('valve',(.3,-.12,-.13),(-1,-.3,0),.005,.004,BRASS)
  return objs
