# Dawgs Uprising Blender helper: parts are built in GAME coords (x forward, y up, z right-ish),
# viewed under a root empty rotated X+90 so they stand up in Blender. Exports packed Int16-mm triangle soups.
import bpy,bmesh,math,json,os,base64,struct
from mathutils import Vector,Matrix,Euler
DU_DIR=os.path.expanduser('~/3D Objects/DawgsUprising')
PREV={'TEAM':(0.15,0.4,0.9),'TEAMDK':(0.1,0.25,0.6),'ACCENT':(0.15,0.4,0.9),'GLOW':(0.6,0.9,1),'GLOWC':(0.4,0.9,1),'GLOWB':(0.4,0.7,1),'GLOWR':(1,.2,.1),
 'GLOWG':(.2,1,.3),'GLOWW':(1,1,1),'LAMP':(1,.9,.6),'GLASS':(.1,.15,.2),'DARK':(.1,.1,.11),'TIRE':(.08,.08,.08),'GUN':(.17,.18,.19),'VENT':(.1,.1,.1),
 'HAZ':(.85,.68,.17),'HAZARD':(.85,.68,.17),'STEEL':(.43,.45,.47),'HUB':(.35,.35,.31),'BLADE':(.2,.2,.22)}
def prevcol(r):
    if r in PREV:return PREV[r]
    if r.startswith('GLOW'):return (.8,.9,1)
    return (.36,.39,.42) if 'DK' not in r else (.25,.27,.3)
def rolemat(r):
    n='DU_'+r;m=bpy.data.materials.get(n)
    if not m:
        m=bpy.data.materials.new(n);m.diffuse_color=(*prevcol(r),1)
    return m
class Part:
    def __init__(s,name):s.name=name;s.bm=bmesh.new();s.roles=[]
    def _ri(s,role):
        if role not in s.roles:s.roles.append(role)
        return s.roles.index(role)
    def _add(s,tb,role,M=None):
        if M is not None:bmesh.ops.transform(tb,matrix=M,verts=tb.verts)
        ri=s._ri(role)
        for f in tb.faces:f.material_index=ri
        me=bpy.data.meshes.new('_tmp');tb.to_mesh(me);tb.free();s.bm.from_mesh(me);bpy.data.meshes.remove(me)
    def hull(s,pts,role,M=None):
        tb=bmesh.new();vs=[tb.verts.new(Vector(p)) for p in pts]
        r=bmesh.ops.convex_hull(tb,input=vs)
        dead={v for v in list(r['geom_interior'])+list(r['geom_unused']) if isinstance(v,bmesh.types.BMVert)}
        dead=[v for v in dead if v.is_valid]
        if dead:bmesh.ops.delete(tb,geom=dead,context='VERTS')
        bmesh.ops.recalc_face_normals(tb,faces=tb.faces);s._add(tb,role,M);return s
    def box(s,c,sz,role,bev=0,rot=None,taper=None):
        """c centre, sz full size; bev chamfer; taper=(kx_top,kz_top) shrinks the top face; rot=(rx,ry,rz) radians about c"""
        hx,hy,hz=sz[0]/2,sz[1]/2,sz[2]/2;pts=[]
        for X in(-1,1):
            for Y in(-1,1):
                for Z in(-1,1):
                    tx,tz=(taper if (taper and Y>0) else (1,1))
                    x,y,z=X*hx*tx,Y*hy,Z*hz*tz
                    if bev>0:
                        b=bev;pts+= [(x-X*b,y,z),(x,y-Y*b,z),(x,y,z-Z*b)]
                    else:pts.append((x,y,z))
        M=Matrix.Translation(Vector(c))@(Euler(rot,'XYZ').to_matrix().to_4x4() if rot else Matrix())
        return s.hull(pts,role,M)
    def cyl(s,a,b,r,role,seg=12,r2=None,bev=0):
        a=Vector(a);b=Vector(b);d=b-a;L=d.length;r2=r if r2 is None else r2
        q=d.normalized();up=Vector((0,0,1)) if abs(q.z)<.9 else Vector((1,0,0))
        u=q.cross(up).normalized();v=q.cross(u).normalized();pts=[]
        for i in range(seg):
            t=2*math.pi*(i+.5)/seg;c,sn=math.cos(t),math.sin(t)
            for (base,rr,ins) in ((a,r,0),(b,r2,0)):
                if bev>0:
                    pts.append(base+(u*c+v*sn)*(rr-bev)+q*(bev if base is a else -bev)*0);pts.append(base+(u*c+v*sn)*rr+q*(bev if base is a else -bev))
                else:pts.append(base+(u*c+v*sn)*rr)
        if bev>0:
            pts=[]
            for i in range(seg):
                t=2*math.pi*(i+.5)/seg;w=u*math.cos(t)+v*math.sin(t)
                pts+=[a+w*(r-bev),a+w*r+q*bev,b+w*(r2-bev),b+w*r2-q*bev]
        return s.hull([tuple(p) for p in pts],role)
    def tri_count(s):
        t=0
        for f in s.bm.faces:t+=len(f.verts)-2
        return t
    def obj(s,coll,root,loc=(0,0,0),rot=None):
        me=bpy.data.meshes.new(s.name);bm=s.bm.copy();bm.to_mesh(me);bm.free()
        for r in s.roles:me.materials.append(rolemat(r))
        o=bpy.data.objects.new(s.name,me);coll.objects.link(o);o.parent=root;o.location=loc
        if rot:o.rotation_euler=rot
        return o
    def pack(s):
        bm=s.bm.copy();bmesh.ops.triangulate(bm,faces=bm.faces);P=[];R=[]
        for f in bm.faces:
            R.append(f.material_index)
            for v in f.verts:P+= [int(round(v.co.x*1000)),int(round(v.co.y*1000)),int(round(v.co.z*1000))]
        bm.free()
        return {'roles':s.roles,'p':base64.b64encode(struct.pack('<%dh'%len(P),*P)).decode(),'r':base64.b64encode(bytes(R)).decode()}
def new_scene(name):
    sc=bpy.data.scenes.get(name)
    if sc:
        for o in list(sc.objects):bpy.data.objects.remove(o,do_unlink=True)
    else:sc=bpy.data.scenes.new(name)
    root=bpy.data.objects.new(name+'_root',None);sc.collection.objects.link(root);root.rotation_euler=(math.pi/2,0,0)
    sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL'
    sc.display.shading.show_cavity=True;sc.display.shading.show_shadows=False;sc.render.resolution_x=900;sc.render.resolution_y=560
    sc.render.film_transparent=False;sc.world=bpy.data.worlds[0] if bpy.data.worlds else bpy.data.worlds.new('w')
    return sc,root
def cam(sc,target,dist,yaw,pitch,lens=50,name='cam'):
    """target in game coords; yaw about game y (0 = looking from +z side), pitch up"""
    t=Vector((target[0],-target[2],target[1]))
    d=Vector((math.sin(yaw)*math.cos(pitch),-math.cos(yaw)*math.cos(pitch),math.sin(pitch)))
    c=bpy.data.objects.get(sc.name+'_'+name)
    if not c:
        c=bpy.data.objects.new(sc.name+'_'+name,bpy.data.cameras.new(sc.name+'_'+name));sc.collection.objects.link(c)
    c.data.lens=lens;c.location=t-d*dist*-1 if False else t+d*dist
    c.rotation_euler=(t-c.location).to_track_quat('-Z','Y').to_euler();sc.camera=c;return c
def render(sc,path):
    bpy.context.window.scene=sc;sc.render.filepath=path;bpy.ops.render.render(write_still=True)
def save_json(fn,D):
    p=os.path.join(DU_DIR,fn);open(p,'w').write(json.dumps(D,separators=(',',':')));return p
def bvh_of(parts_with_mats):
    """[(Part, Matrix)] -> BVHTree in game coords"""
    from mathutils.bvhtree import BVHTree
    V=[];F=[]
    for P,M in parts_with_mats:
        bm=P.bm.copy();bmesh.ops.triangulate(bm,faces=bm.faces);o=len(V)
        for v in bm.verts:V.append(M@v.co)
        bm.verts.index_update()
        for f in bm.faces:F.append([o+v.index for v in f.verts])
        bm.free()
    return BVHTree.FromPolygons(V,F)
def quad():
    """the quad flak cannon (after the reference image): head yaws, cradle elevates about its origin, 4 barrels each slide back on a track"""
    H=Part('qHead');C=Part('qCradle');B=Part('qBarrel')
    H.cyl((0,0,0),(0,.1,0),.62,'DARK',seg=16)
    H.cyl((0,.1,0),(0,.16,0),.6,'STEEL',seg=16,r2=.57)
    oct=lambda r,y:[(r*math.cos(a*math.pi/4+math.pi/8),y,r*math.sin(a*math.pi/4+math.pi/8)) for a in range(8)]
    H.hull(oct(.55,.16)+oct(.47,.44),'BODY')
    for z in(-.43,.43):
        H.hull([(-.3,.4,z-.045),(.3,.4,z-.045),(.18,.86,z-.045),(-.22,.86,z-.045),(-.3,.4,z+.045),(.3,.4,z+.045),(.18,.86,z+.045),(-.22,.86,z+.045)],'BODYDK')
        H.box((0,.62,z*1.1),(.16,.16,.04),'STEEL')
    H.box((-.46,.52,0),(.34,.3,.62),'BODY',bev=.03)
    H.box((-.46,.675,0),(.24,.012,.5),'BODYDK')
    H.box((-.6,.5,0),(.012,.06,.4),'TEAM')
    H.box((.33,.3,0),(.06,.1,.5),'HAZ')
    H.box((-.18,.95,-.5),(.22,.14,.12),'BODYDK',bev=.02);H.box((-.065,.95,-.5),(.012,.08,.08),'GLASS')
    C.box((-.02,0,0),(.48,.3,.46),'BODY',bev=.04)
    C.cyl((0,0,-.4),(0,0,.4),.075,'STEEL',seg=10)
    for z in(-.27,.27):
        s=1 if z>0 else -1
        C.hull([(-.42,-.21,z-.1),(-.42,.21,z-.1),(.42,.2,z-.1),(.5,.12,z-.1),(.5,-.12,z-.1),(.42,-.2,z-.1),(-.42,-.21,z+.1),(-.42,.21,z+.1),(.42,.2,z+.1),(.5,.12,z+.1),(.5,-.12,z+.1),(.42,-.2,z+.1)],'BODY')
        for y in(-.09,.09):C.box((.12,y,z+s*.104),(.72,.035,.02),'DARK')
        C.box((-.2,.0,z+s*.104),(.24,.06,.012),'BODYDK')
        C.box((.55,0,z),(.08,.36,.17),'STEEL',bev=.015)
        C.box((-.15,.212,z),(.34,.01,.1),'TEAM')
        for x in(-.3,-.22):C.box((x,.212,z),(.04,.012,.14),'VENT')
    B.cyl((-.3,0,0),(.3,0,0),.062,'GUN',seg=10)
    B.cyl((.3,0,0),(.38,0,0),.074,'STEEL',seg=10)
    B.cyl((.38,0,0),(1.42,0,0),.05,'GUN',seg=10,r2=.044)
    for x in(.55,.75,.95):B.cyl((x,0,0),(x+.06,0,0),.06,'STEEL',seg=10)
    B.box((1.5,0,0),(.16,.1,.1),'DARK',bev=.012)
    for x in(1.47,1.53):B.box((x,0,0),(.022,.105,.12),'GUN')
    return H,C,B
QUAD_BAR=[[.3,.09,.27],[.3,-.09,-.27],[.3,.09,-.27],[.3,-.09,.27]]
def tree(P,Mx):
    from mathutils.bvhtree import BVHTree
    bm=P.bm.copy();bmesh.ops.transform(bm,matrix=Mx,verts=bm.verts);t=BVHTree.FromBMesh(bm);bm.free();return t
def scale(P,k,flipY=False):
    bmesh.ops.transform(P.bm,matrix=Matrix.Diagonal((k,-k if flipY else k,k,1)),verts=P.bm.verts)
    if flipY:bmesh.ops.reverse_faces(P.bm,faces=P.bm.faces)
    return P
