# organic bodies for the Mange concepts: a skin-modifier skeleton (nodes with radii) -> subdivision -> noisy displacement,
# painted per face by the nearest node's tag (flesh, sinew, uniform rag ...), plus hard pieces (armour scraps, bone) on top
import bpy,bmesh,math,random
from mathutils import Vector,kdtree
from mlib import G,mat
class Tree:
  def __init__(s,name):s.name=name;s.n=[];s.e=[]
  def node(s,p,r,tag='FLESH',rz=None):s.n.append((Vector(p),r,rz if rz is not None else r,tag));return len(s.n)-1
  def chain(s,a,pts,tag='FLESH'):
    i=a
    for p in pts:
      j=s.node(p[0],p[1],tag if len(p)<3 else p[2]);s.e.append((i,j));i=j
    return i
  def build(s,sub=2,disp=.012,dscale=.08,seed=1):
    me=bpy.data.meshes.new(s.name);me.from_pydata([G(*p) for p,_,_,_ in s.n],s.e,[]);ob=bpy.data.objects.new(s.name,me);bpy.context.scene.collection.objects.link(ob)
    ob.modifiers.new('sk','SKIN');sv=me.skin_vertices[0].data
    for i,(p,r,rz,t) in enumerate(s.n):sv[i].radius=(r,rz)
    sv[0].use_root=True
    m=ob.modifiers.new('sub','SUBSURF');m.levels=sub;m.render_levels=sub
    if disp>0:
      tx=bpy.data.textures.new(s.name+'_n','CLOUDS');tx.noise_scale=dscale;tx.noise_depth=2
      d=ob.modifiers.new('disp','DISPLACE');d.texture=tx;d.strength=disp;d.mid_level=.5
    bpy.context.view_layer.objects.active=ob;ob.select_set(True)
    for md in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=md.name)
    # paint: role of the nearest node (by distance minus radius)
    tags=[];
    for p,r,rz,t in s.n:
      if t not in tags:tags.append(t)
    for t in tags:me.materials.append(mat(t))
    for pl in me.polygons:
      c=pl.center;best=1e9;bt=0
      for p,r,rz,t in s.n:
        d=(c-G(*p)).length-max(r,rz)*.9
        if d<best:best=d;bt=tags.index(t)
      pl.material_index=bt;pl.use_smooth=True
    # (concept) soft colour: every vertex blends its nearest tags' colours (soft-min over distance), with grime and blotches
    from mlib import COL
    import mathutils.noise as N
    ca=me.color_attributes.new('Col','FLOAT_COLOR','CORNER');NP=[(G(*p),max(r,rz),COL.get(t,(.5,.5,.5))) for p,r,rz,t in s.n]
    vc={}
    for v in me.vertices:
      ws=0;col=Vector((0,0,0))
      for q,r,c in NP:
        d=max(0,(v.co-q).length-r*.9);w=math.exp(-d/.025);ws+=w;col+=Vector(c)*w
      col/=max(ws,1e-9);n=N.noise(v.co*18);n2=N.noise(v.co*5+Vector((3,1,2)))
      k=.78+.22*n+.12*n2;grime=max(0,min(1,.5-v.co.z*.4))   # darker low down and in blotches
      vc[v.index]=col*k*(1-.35*grime)
    for li,l in enumerate(me.loops):c=vc[l.vertex_index];ca.data[li].color=(c.x,c.y,c.z,1)
    m=bpy.data.materials.get('SKINV') or bpy.data.materials.new('SKINV');m.use_nodes=True;nt=m.node_tree;bs=nt.nodes['Principled BSDF']
    at=nt.nodes.get('Attribute') or nt.nodes.new('ShaderNodeAttribute');at.attribute_name='Col';nt.links.new(at.outputs['Color'],bs.inputs['Base Color'])
    bs.inputs['Roughness'].default_value=.42
    try:bs.inputs['Subsurface Weight'].default_value=.15;bs.inputs['Subsurface Radius'].default_value=(.02,.008,.006)
    except Exception:pass
    m['keep']=1;me.materials.clear();me.materials.append(m)
    ob.select_set(False);return ob
