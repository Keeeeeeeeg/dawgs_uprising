# Detailed weapon models (pass 6) — high-poly sources for the texture bake. Built from SIDE PROFILES extruded across the
# weapon and cut with EXACT booleans (slots, windows, holes, flutes, grooves), bevelled + weighted normals, so each piece is
# a crafted part instead of a block. Our own designs in the silhouettes of Keegan's references (no copied markings).
# Local frame: x forward, z up, +y = the weapon's LEFT, pistol grip at the origin. exec() this inside body*.py (uses its
# materials M/steel/cloth, GUN, OLIVEP, RUB, DARK, METL, BRASS, REDM, LASER, TUBE, STEN, DIAL).
import bmesh,math
from mathutils import Vector,Matrix
GMET=steel('gunmetal',(.03,.032,.034),0,.7);PARK=steel('parker',(.02,.021,.02),0,.5)
POLY=M('olivepoly2',(.075,.085,.05),.7);POLYD=M('blackpoly',(.018,.018,.017),.75);BRZ=M('bronze',(.36,.25,.11),.32,.85);GLASS=M('scopeglass',(.04,.07,.06),.04,.6)
_WP=[]
def _new(name,bm,mat,par,bev=.0018,segs=2,smooth=False,ang=.55):
  me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free();o=bpy.data.objects.new('gun',me);bpy.context.scene.collection.objects.link(o);me.materials.append(mat);o.parent=par
  for p in me.polygons:p.use_smooth=True
  if bev:b=o.modifiers.new('b','BEVEL');b.width=bev;b.segments=segs;b.limit_method='ANGLE';b.angle_limit=ang;b.harden_normals=True
  o.modifiers.new('w','WEIGHTED_NORMAL').keep_sharp=True;_WP.append(o);return o
def P2(pts,y0,y1):
  """side profile (x,z) extruded across y0..y1"""
  bm=bmesh.new();vs=[bm.verts.new((x,y0,z)) for x,z in pts];f=bm.faces.new(vs)
  r=bmesh.ops.extrude_face_region(bm,geom=[f]);bmesh.ops.translate(bm,vec=(0,y1-y0,0),verts=[g for g in r['geom'] if isinstance(g,bmesh.types.BMVert)])
  bmesh.ops.recalc_face_normals(bm,faces=bm.faces);return bm
def T2(pts,x0,x1):
  """top profile (x,y)... (y,z) cross-section extruded along x"""
  bm=bmesh.new();vs=[bm.verts.new((x0,y,z)) for y,z in pts];f=bm.faces.new(vs)
  r=bmesh.ops.extrude_face_region(bm,geom=[f]);bmesh.ops.translate(bm,vec=(x1-x0,0,0),verts=[g for g in r['geom'] if isinstance(g,bmesh.types.BMVert)])
  bmesh.ops.recalc_face_normals(bm,faces=bm.faces);return bm
def CY(a,b,r,seg=24,r2=None):
  a,b=Vector(a),Vector(b);d=b-a;L=d.length;bm=bmesh.new();bmesh.ops.create_cone(bm,cap_ends=True,segments=seg,radius1=r,radius2=r if r2 is None else r2,depth=L)
  q=Vector((0,0,1)).rotation_difference(d.normalized());bmesh.ops.transform(bm,matrix=Matrix.Translation((a+b)/2)@q.to_matrix().to_4x4(),verts=bm.verts);return bm
def BX(c,s,rot=None):
  bm=bmesh.new();bmesh.ops.create_cube(bm,size=1);bmesh.ops.scale(bm,vec=s,verts=bm.verts)
  if rot:bmesh.ops.rotate(bm,cent=(0,0,0),matrix=rot,verts=bm.verts)
  bmesh.ops.translate(bm,vec=c,verts=bm.verts);return bm
def TOR(c,R,r,axis='y',seg=20,rs=8):
  bm=bmesh.new();vv=[]
  for i in range(seg):
    a=i/seg*6.283;ring=[]
    for j in range(rs):
      b=j/rs*6.283;p=Vector(((R+r*math.cos(b))*math.cos(a),r*math.sin(b),(R+r*math.cos(b))*math.sin(a)))
      if axis=='x':p=Vector((p.y,p.x,p.z))
      ring.append(bm.verts.new(Vector(c)+p))
    vv.append(ring)
  for i in range(seg):
    for j in range(rs):bm.faces.new((vv[i][j],vv[(i+1)%seg][j],vv[(i+1)%seg][(j+1)%rs],vv[i][(j+1)%rs]))
  return bm
def MERGE(bms):
  out=bmesh.new();me=bpy.data.meshes.new('t')
  for b in bms:b.to_mesh(me);b.free();out.from_mesh(me)
  bpy.data.meshes.remove(me);return out
def CUT(o,bm,par):
  c=_new('cut',bm,DARK,par,bev=0);c.hide_render=True;c.hide_viewport=False;c.display_type='WIRE';_WP.remove(c)
  m=o.modifiers.new('cut','BOOLEAN');m.object=c;m.operation='DIFFERENCE';m.solver='EXACT';m.use_hole_tolerant=True;m.use_self=True;o.modifiers.move(len(o.modifiers)-1,0);_CUTS.append(c);return o
_CUTS=[]
def rail(par,x0,x1,z,w=.022,h=.01,mat=None):
  o=_new('rail',BX(((x0+x1)/2,0,z+h/2),(x1-x0,w,h)),mat or PARK,par,bev=.001)
  n=int((x1-x0)/.01);CUT(o,MERGE([BX((x0+.005+k*.01,0,z+h*.85),(.005,w+.01,h*.5)) for k in range(n)]),par);return o
def bake_text(par,s,c,n,size,mat=None):
  cu=bpy.data.curves.new('t','FONT');cu.body=s;cu.size=size;cu.extrude=.0003;cu.align_x='CENTER';cu.align_y='CENTER'
  o=bpy.data.objects.new('sten',cu);bpy.context.scene.collection.objects.link(o);o.data.materials.append(mat or STEN);o.parent=par;o['bake']=1
  o.matrix_parent_inverse=Matrix.Identity(4);o.matrix_basis=Matrix.Translation(c)@Vector(n).to_track_quat('Z','Y').to_matrix().to_4x4();return o
def sym(pts):return [(x,y,z) for x,y,z in pts]+[(x,-y,z) for x,y,z in pts]
def hullL(pts):bm=bmesh.new();vs=[bm.verts.new(p) for p in pts];bmesh.ops.convex_hull(bm,input=vs);return bm
# ------------------------------------------------------------------------------------------------------------- RIFLE
def w_rifle(par):
  """(v8, Keegan's design language, our own rifle) long rifle-length handguard with OVAL cooling slots, full-length rail with
  a BUILT-IN ANGLED FOREGRIP, a STRAIGHT magazine swept BACKWARD, the pistol grip moulded into a SKELETONISED thumbhole
  stock ending in a compact ANGULAR butt, and TALL HOLOGRAPHIC iron sights (frames with glowing glass panes)."""
  UP,BOT=.105,.045
  # upper receiver + ejection port, forward assist, charging handle
  up=_new('upper',P2([(-.07,BOT),(.2,BOT),(.2,UP),(-.07,UP)],-.03,.03),GMET,par)
  CUT(up,BX((.08,-.03,.078),(.075,.012,.02)),par);_new('port',BX((.08,-.022,.078),(.072,.006,.018)),PARK,par,bev=.0005)
  _new('fa',CY((-.03,-.03,.085),(.012,-.03,.085),.01,16),GMET,par);_new('ch',P2([(-.1,.088),(-.07,.088),(-.07,.098),(-.095,.098),(-.105,.093)],-.018,.018),PARK,par)
  # long handguard (.2 -> .66) with two rows of OVAL cooling slots + a row of small ovals underneath
  hg=_new('handguard',T2([(-.034,.03),(-.034,.093),(-.025,.103),(.025,.103),(.034,.093),(.034,.03),(.024,.02),(-.024,.02)],.2,.66),GMET,par)
  ov=[]
  def oval(c,ln,ht,axis):
    c=Vector(c);bm=CY(c-axis*.06,c+axis*.06,ht/2,16);bmesh.ops.scale(bm,vec=(ln/ht,1,1),space=Matrix.Translation(-c),verts=bm.verts);return bm
  for k in range(9):
    x=.235+k*.046
    ov.append(oval((x,0,.074),.036,.013,Vector((0,1,0))));ov.append(oval((x+.023,0,.047),.028,.01,Vector((0,1,0))))
    ov.append(oval((x+.012,0,.03),.026,.009,Vector((0,0,1))))
  CUT(hg,MERGE(ov),par)
  _new('hgnose',T2([(-.035,.026),(-.035,.094),(-.026,.104),(.026,.104),(.035,.094),(.035,.026),(.025,.017),(-.025,.017)],.655,.672),PARK,par)
  rail(par,-.07,.67,UP,.024,.011)
  # BUILT-IN ANGLED FOREGRIP moulded into the bottom of the handguard (raked back toward the shooter)
  # (v9, Keegan's reference) ANGLED FOREGRIP: a slim wedge on the handguard's underside, tall at the rear (a short
  # near-vertical thumb-stop lip) with a long ramp rising toward the muzzle, hollow side pockets and a lip at the rear base
  afg=_new('afg',P2([(.47,.026),(.64,.026),(.63,.018),(.505,-.04),(.488,-.05),(.474,-.048),(.468,-.03)],-.017,.017),POLY,par,bev=.003)   # tall stop at the REAR (toward the shooter), ramp rising toward the muzzle
  CUT(afg,MERGE([P2([(.5,.012),(.6,.012),(.515,-.026)],y0,y1) for y0,y1 in ((.011,.03),(-.03,-.011))]),par)
  _new('afgclamp',BX((.555,0,.024),(.17,.044,.008)),PARK,par,bev=.001)
  # lower / magwell, raked BACK to match the swept magazine; trigger guard; mag release
  R=.42      # backward sweep angle of the mag (rad)
  def sw(x,z):return (x+math.tan(R)*z,z)   # shear: lower points move back as they go down
  lw=_new('lower',P2([(-.035,BOT),(.2,BOT),(.2,.02),sw(.19,-.03),sw(.19,-.055),sw(.09,-.055),sw(.09,-.02),(.07,-.014),(-.01,-.014),(-.035,.0)],-.026,.026),GMET,par)
  CUT(lw,P2([sw(.1,-.06),sw(.18,-.06),sw(.18,-.03),sw(.1,-.03)],-.021,.021),par)
  _new('mrel',CY((.07,-.022,.01),(.07,-.031,.01),.007,12),PARK,par);_new('bcatch',BX((.06,.0272,.02),(.02,.004,.012)),PARK,par,bev=.0005)
  _new('sel',P2([(-.01,.03),(.02,.025),(.022,.031),(-.008,.036)],.025,.031),PARK,par)
  # STRAIGHT box magazine swept backward, ribbed sides, baseplate
  top=-.03;bot=-.2
  mpts=[sw(.098,top),sw(.182,top),sw(.182,bot),sw(.098,bot)]
  m=_new('mag',P2(mpts,-.018,.018),POLYD,par,bev=.002)
  CUT(m,MERGE([P2([sw(.11,-.06-k*.024),sw(.17,-.06-k*.024),sw(.17,-.066-k*.024),sw(.11,-.066-k*.024)],.015,.03) for k in range(6)]),par)
  _new('mbase',P2([sw(.092,bot+.004),sw(.188,bot+.004),sw(.19,bot-.016),sw(.09,bot-.016)],-.023,.023),POLY,par,bev=.003)
  # trigger guard: one closed bow from the magwell back to the grip; curved trigger blade inside it
  tg=_new('guard',P2([(.075,-.01),(.078,-.022),(.062,-.054),(-.012,-.054),(-.016,-.04),(-.006,-.01)],-.006,.006),GMET,par,bev=.0015)
  CUT(tg,P2([(.064,-.017),(.054,-.046),(-.004,-.046),(-.006,-.017)],-.012,.012),par)
  tb=[(.03+.006*math.sin(t*1.4),-.014-.026*t) for t in [k/6 for k in range(7)]];_new('trig',P2(tb+[(x-.007,z) for x,z in reversed(tb)],-.003,.003),PARK,par,bev=.0005)
  # SKELETONISED thumbhole stock with the PISTOL GRIP moulded in, compact ANGULAR butt
  out=[(-.07,UP-.004),(-.29,UP-.004),(-.31,UP-.018),(-.33,.07),(-.33,-.06),(-.305,-.09),(-.13,-.095),(-.088,-.128),(-.045,-.132),(-.026,-.115),(-.012,-.04),(-.01,-.012),(-.035,.0),(-.07,BOT)]
  st=_new('stock',P2(out,-.025,.025),POLY,par,bev=.003)
  CUT(st,MERGE([P2([(-.065,.005),(-.047,-.07),(-.07,-.088),(-.115,-.08),(-.128,-.03),(-.105,.018)],-.05,.05),     # thumbhole behind the grip
                P2([(-.15,.06),(-.29,.06),(-.3,.045),(-.3,-.05),(-.29,-.065),(-.16,-.065),(-.14,-.04),(-.14,.04)],-.05,.05)]),par)   # skeleton window
  _new('cheek',P2([(-.13,UP-.01),(-.28,UP-.01),(-.28,UP+.012),(-.15,UP+.008)],-.022,.022),POLYD,par,bev=.004)
  pad=_new('pad',P2([(-.328,.088),(-.352,.08),(-.358,.02),(-.352,-.075),(-.328,-.09)],-.03,.03),RUB,par,bev=.004)
  CUT(pad,MERGE([BX((-.356,0,-.06+k*.03),(.01,.07,.008)) for k in range(5)]),par)
  _new('qd',CY((-.315,.02,-.02),(-.315,.03,-.02),.008,14),PARK,par)
  # long barrel past the handguard, gas block, slotted compensator
  _new('barrel',CY((.66,0,.062),(.79,0,.062),.0105,20),PARK,par);_new('gas',BX((.675,0,.062),(.02,.03,.03)),GMET,par,bev=.002)
  cp=_new('comp',CY((.78,0,.062),(.86,0,.062),.017,24),GMET,par);CUT(cp,MERGE([BX((.795+k*.02,0,.075),(.009,.05,.02)) for k in range(3)]),par)
  # TALL HOLOGRAPHIC iron sights: tall angular frames with a glowing holo pane + reticle dot
  for x,h,w in ((.62,.075,.032),(-.03,.07,.04)):
    fr=_new('holo',P2([(x-.014,UP+.011),(x+.014,UP+.011),(x+.012,UP+.011+h),(x-.012,UP+.011+h)],-w/2,w/2),POLYD,par,bev=.002)
    CUT(fr,BX((x,0,UP+.011+h*.58),(.06,w-.012,h*.62)),par)
    _new('pane',BX((x,0,UP+.011+h*.58),(.003,w-.008,h*.66)),GLASS,par,bev=0)
    _new('ret',BX((x-.002,0,UP+.011+h*.58),(.002,.004,.004)),EYE,par,bev=0)
    _new('hbase',BX((x,0,UP+.014),(.034,w+.004,.012)),PARK,par,bev=.002)
  _new('loop',TOR((.2,.038,.008),.011,.0025,'x',18,6),PARK,par);_new('loopb',BX((.2,.033,.018),(.012,.006,.012)),PARK,par,bev=.001)
  bake_text(par,'DU-A4',Vector((.1,.0262,.02)),(0,1,0),.011);bake_text(par,'S  1  F',Vector((-.0,-.0262,.032)),(0,-1,0),.007)
# ------------------------------------------------------------------------------------------------------------- LMG
def w_mg(par,bip):
  # MG42-inspired: boxy pressed receiver, hinged feed cover with ramp rear sight, perforated round shroud with the barrel
  # change window, conical booster, slim straight stock, separate pistol grip, side box mag (left), short belt, big bipod
  rc=_new('recv',P2([(-.1,.0),(.34,.0),(.34,.125),(-.07,.125),(-.1,.11)],-.042,.042),GMET,par,bev=.002)
  CUT(rc,MERGE([BX((.1,-.042,.07),(.16,.012,.014)),BX((.05,0,.0),(.1,.03,.01))]),par)            # cocking slot (right), ejection port
  _new('chandle',BX((.17,-.0475,.07),(.018,.025,.012)),PARK,par,bev=.002)
  _new('cover',P2([(-.04,.125),(.31,.125),(.31,.145),(.18,.158),(.0,.158),(-.04,.14)],-.038,.038),GMET,par,bev=.003)
  _new('latch',CY((-.035,0,.13),(-.035,0,.165),.012,14),PARK,par)
  _new('rsight',P2([(.2,.158),(.3,.158),(.3,.17),(.21,.18)],-.01,.01),PARK,par,bev=.001)
  for k in range(6):_new('rib',BX((.04+k*.04,0,.159),(.004,.07,.004)),GMET,par,bev=.0005)
  # (v7) LONGER shroud (to 1.12) with MG42-style OVAL cooling vents in staggered rows, a long oval barrel-change port
  sh=_new('shroud',CY((.34,0,.07),(1.12,0,.07),.036,32),GMET,par,bev=.0015)
  holes=[]
  def oval(x,ang,ln=.05,ht=.013):
    r=math.radians(ang);n=Vector((0,math.cos(r),math.sin(r)));c=Vector((x,0,.07))+n*.036
    bm=CY(c-n*.022,c+n*.022,ht/2,14);bmesh.ops.scale(bm,vec=(ln/ht,1,1),space=Matrix.Translation(-c),verts=bm.verts)
    q=Vector((0,1,0)).rotation_difference(n)    # keep the long axis along the barrel
    return bm
  for k in range(12):
    x=.39+k*.058
    for j,a2 in enumerate((90,45,0,135,180)):
      xo=x+(.029 if j%2 else 0)
      if xo>1.09:continue
      if a2==180 and .5<xo<.82:continue
      holes.append(oval(xo,a2))
  win=CY((.66,-.06,.07),(.66,-.02,.07),.016,20);bmesh.ops.scale(win,vec=(9.5,1,1),space=Matrix.Translation(-Vector((.66,-.04,.07))),verts=win.verts);holes.append(win)   # barrel-change port (right)
  CUT(sh,MERGE(holes),par)
  _new('jacketR',CY((.34,0,.07),(.38,0,.07),.039,32),GMET,par);_new('jacketF',CY((1.08,0,.07),(1.12,0,.07),.039,32),GMET,par)
  _new('barrelin',CY((.34,0,.07),(1.18,0,.07),.012,16),PARK,par)
  _new('booster',CY((1.12,0,.07),(1.22,0,.07),.037,24,.025),GMET,par);_new('muz',CY((1.22,0,.07),(1.26,0,.07),.017,16),PARK,par)
  for k in range(4):_new('bring',CY((1.13+k*.02,0,.07),(1.138+k*.02,0,.07),.039-.003*k,24),PARK,par)
  _new('fsight',P2([(1.03,.104),(1.05,.104),(1.046,.132),(1.036,.132)],-.004,.004),PARK,par,bev=.0005);_new('fsb',BX((1.04,0,.104),(.034,.03,.006)),GMET,par,bev=.001)
  _new('bhandle',P2([(.44,.0),(.62,.0),(.6,-.02),(.46,-.02)],-.06,-.05),POLYD,par,bev=.003);_new('bharm',BX((.47,-.046,.03),(.01,.016,.07)),PARK,par);_new('bharm2',BX((.59,-.046,.03),(.01,.016,.07)),PARK,par)
  # stock: slim straight MG42-style wedge, butt plate, sling slot; separate raked pistol grip with stippling bands
  stk=_new('stock',P2([(-.1,.112),(-.46,.09),(-.46,-.02),(-.1,.03)],-.026,.026),POLY,par,bev=.004)
  CUT(stk,P2([(-.32,.03),(-.36,.03),(-.36,.012),(-.32,.016)],-.05,.05),par)
  _new('butt',P2([(-.46,.096),(-.475,.096),(-.475,-.028),(-.46,-.028)],-.03,.03),RUB,par,bev=.003)
  g=_new('grip',P2([(-.03,.012),(.025,.012),(.018,-.05),(.025,-.08),(.0,-.115),(-.05,-.11),(-.055,-.05)],-.018,.018),POLYD,par,bev=.004)
  CUT(g,MERGE([BX((-.012,0,-.035-k*.016),(.07,.05,.004),Matrix.Rotation(-.3,3,'Y')) for k in range(4)]),par)
  tg=_new('guard',P2([(.025,-.002),(.08,-.002),(.076,-.045),(.03,-.04)],-.006,.006),GMET,par,bev=.001);CUT(tg,P2([(.032,-.008),(.072,-.008),(.068,-.038),(.035,-.034)],-.01,.01),par)
  _new('trig',P2([(.045,-.004),(.052,-.004),(.054,-.03),(.047,-.028)],-.003,.003),PARK,par)
  # side BOX MAGAZINE (left): angular bevelled case with a door, latch and handle; short belt into the feed tray
  bx=_new('box',P2([(.03,.06),(.25,.06),(.27,.03),(.27,-.16),(.24,-.19),(.06,-.19),(.03,-.16)],.044,.17),POLY,par,bev=.006)
  _new('door',P2([(.06,.03),(.24,.03),(.24,-.16),(.06,-.16)],.168,.174),POLYD,par,bev=.003)
  _new('dlatch',BX((.15,.176,.02),(.04,.006,.012)),PARK,par,bev=.001);_new('dhandle',TOR((.15,.112,.07),.03,.005,'x',20,8),PARK,par)
  _new('tray',BX((.12,.05,.1),(.1,.02,.02)),GMET,par,bev=.002)
  for k in range(6):
    x=.08+k*.018;_new('rnd',CY((x,.04,.102),(x,.075,.102),.0065,10),BRASS,par,bev=0);_new('link',BX((x,.058,.102),(.006,.036,.016)),PARK,par,bev=0)
  bake_text(par,'DU-G42',Vector((.12,.0425,.06)),(0,1,0),.012)
  _bipod(par,1.0,.03,bip,.48)
def _bipod(par,hx,hz,bip,L):
  """large bipod: clamp, hinge, telescoping legs with collars and feet. hang = dangling, fold = along the barrel,
  ground = feet planted at world height bip[1] (computed through the weapon's world matrix)"""
  _new('bclamp',CY((hx-.03,0,hz+.04),(hx+.03,0,hz+.04),.04,20),GMET,par)
  W=par.matrix_world;inv=W.inverted();F=W.to_3x3()
  for sy in (-1,1):
    top=Vector((hx,sy*.02,hz))
    if bip[0]=='ground':
      tw=W@top;ew=tw+F@Vector((.1,sy*.15,0));ew.z=bip[1]+.016;end=inv@ew
    elif bip[0]=='fold':end=Vector((hx-.34,sy*.035,hz-.03))
    else:end=inv@(W@top+Vector((0,0,-L))+F@Vector((-.07,sy*.07,0)))
    d=(end-top);_new('leg',CY(top,top+d*.55,.011,14),PARK,par);_new('legl',CY(top+d*.5,end,.0085,14),PARK,par)
    _new('collar',CY(top+d*.5,top+d*.56,.014,14),GMET,par);_new('foot',CY(end-d.normalized()*.004,end+d.normalized()*.016,.006,10,.03),POLYD,par)
  _new('hinge',CY((hx,-.03,hz),(hx,.03,hz),.012,14),PARK,par)
# ------------------------------------------------------------------------------------------------------------- SNIPER
def w_sniper(par,bip):
  # bullpup slab body with stepped top + window cuts, thumbhole, mag behind the grip, long M-LOK handguard, fluted heavy
  # barrel + big brake, large variable scope on a tall one-piece mount, folding carry handle, monopod, big bipod
  b=_new('body',P2([(-.47,.11),(-.12,.12),(.3,.12),(.31,.03),(.06,.03),(.05,-.01),(.0,-.008),(-.03,-.075),(-.1,-.075),(-.12,-.02),(-.3,-.02),(-.32,-.06),(-.47,-.07)],-.034,.034),GMET,par,bev=.0025)
  win=[P2([(x,.07),(x+.06,.07),(x+.06,.098),(x,.098)],-.06,.06) for x in (-.38,-.29,-.2,-.11,.0,.09,.18)]
  win.append(P2([(-.085,-.06),(-.04,-.06),(-.02,-.04),(-.02,-.012),(-.04,.002),(-.085,.002),(-.1,-.015),(-.1,-.045)],-.06,.06))   # thumbhole
  CUT(b,MERGE(win),par)
  _new('wback',BX((-.04,0,.084),(.48,.05,.022)),PARK,par,bev=0)                                 # dark insert seen through the windows
  _new('grip',P2([(-.02,.0),(.03,.0),(.024,-.04),(.03,-.06),(.012,-.085),(-.025,-.08)],-.018,.018),POLYD,par,bev=.003)
  tg=_new('guard',P2([(.03,.0),(.085,.0),(.08,-.045),(.032,-.04)],-.006,.006),GMET,par,bev=.001);CUT(tg,P2([(.036,-.006),(.076,-.006),(.072,-.038),(.038,-.034)],-.01,.01),par)
  _new('trig',P2([(.048,-.002),(.055,-.002),(.057,-.028),(.05,-.026)],-.003,.003),PARK,par)
  m=_new('mag',P2([(-.27,-.02),(-.15,-.02),(-.15,-.17),(-.27,-.17)],-.03,.03),POLYD,par,bev=.003);CUT(m,MERGE([BX((-.21,.03,-.05-k*.025),(.1,.008,.006)) for k in range(5)]),par)
  _new('mbase',BX((-.21,0,-.177),(.13,.066,.016)),POLY,par,bev=.003)
  pad=_new('pad',P2([(-.47,.115),(-.5,.112),(-.5,-.075),(-.47,-.075)],-.036,.036),RUB,par,bev=.005);CUT(pad,MERGE([BX((-.5,0,-.05+k*.03),(.01,.08,.008)) for k in range(5)]),par)
  for k in range(2):_new('spacer',P2([(-.47+k*.0,.115),(-.468,.115),(-.468,-.075),(-.47,-.075)],-.035,.035),POLY,par,bev=0)
  _new('cheek',P2([(-.42,.108),(-.18,.114),(-.18,.14),(-.38,.14)],-.028,.028),POLYD,par,bev=.004)
  _new('mono',CY((-.38,0,-.07),(-.38,0,-.16),.009,14),PARK,par);_new('monof',CY((-.38,0,-.16),(-.38,0,-.17),.02,16),POLYD,par)
  rail(par,-.15,.86,.12,.024)
  hg=_new('handguard',T2([(-.035,.035),(-.035,.11),(-.025,.12),(.025,.12),(.035,.11),(.035,.035),(.025,.026),(-.025,.026)],.3,.86),GMET,par)
  CUT(hg,MERGE([P2([(.33+k*.05,.06),(.36+k*.05,.06),(.36+k*.05,.085),(.33+k*.05,.085)],-.05,.05) for k in range(10)]+[BX((.33+k*.05+.015,0,.026),(.03,.04,.012)) for k in range(10)]),par)
  bl=_new('barrel',CY((.86,0,.073),(1.32,0,.073),.018,28),PARK,par)
  CUT(bl,MERGE([BX((1.07,.018*math.cos(k*1.047),.073+.018*math.sin(k*1.047)),(.34,.009,.009),Matrix.Rotation(k*1.047,3,'X')) for k in range(6)]),par)   # flutes
  bk=_new('brake',P2([(1.31,.045),(1.43,.045),(1.43,.1),(1.31,.1)],-.035,.035),GMET,par,bev=.004)
  CUT(bk,MERGE([BX((1.34+k*.028,0,.073),(.014,.09,.034)) for k in range(3)]+[CY((1.42,0,.073),(1.45,0,.073),.012,12)]),par)
  # scope: tall mount, two clamp rings with screws, 34 mm tube, turrets, parallax knob, big objective + sunshade, eyepiece
  _new('mount',P2([(-.08,.132),(.26,.132),(.26,.15),(.2,.165),(.0,.165),(-.08,.15)],-.022,.022),GMET,par,bev=.003)
  for x in (.0,.18):
    _new('ring',CY((x-.012,0,.21),(x+.012,0,.21),.03,28),GMET,par);_new('ringb',BX((x,0,.175),(.024,.04,.03)),GMET,par,bev=.002)
    for sy in (-1,1):_new('screw',CY((x,sy*.026,.2),(x,sy*.036,.2),.004,8),PARK,par)
  _new('tube',CY((-.08,0,.21),(.3,0,.21),.022,28),PARK,par)
  _new('erect',CY((.05,0,.21),(.13,0,.21),.028,28),PARK,par)
  _new('el',CY((.09,0,.234),(.09,0,.268),.02,24),GMET,par);_new('elc',CY((.09,0,.268),(.09,0,.276),.018,24),DIAL,par)
  _new('wd',CY((.09,-.02,.21),(.09,-.052,.21),.017,24),GMET,par);_new('px',CY((.09,.02,.21),(.09,.045,.21),.014,24),GMET,par)
  _new('objb',CY((.3,0,.21),(.38,0,.21),.022,28,.038),PARK,par);_new('obj',CY((.38,0,.21),(.48,0,.21),.039,28),PARK,par)
  _new('shade',CY((.48,0,.21),(.56,0,.21),.039,28),GMET,par);_new('lensO',CY((.554,0,.21),(.561,0,.21),.036,28),GLASS,par,bev=0)
  _new('eyeb',CY((-.14,0,.21),(-.08,0,.21),.03,28,.022),PARK,par);_new('eye',CY((-.17,0,.21),(-.14,0,.21),.031,28),POLYD,par);_new('lensE',CY((-.174,0,.21),(-.168,0,.21),.026,28),GLASS,par,bev=0)
  # folding carry handle on the handguard rail
  _new('hpost',P2([(.56,.13),(.58,.13),(.585,.175),(.56,.175)],-.01,.01),GMET,par,bev=.002);_new('hpost2',P2([(.7,.13),(.72,.13),(.72,.175),(.695,.175)],-.01,.01),GMET,par,bev=.002)
  _new('hbar',CY((.56,0,.178),(.72,0,.178),.011,16),POLYD,par)
  bake_text(par,'DU-S12  12.7',Vector((-.25,.0342,.04)),(0,1,0),.012)
  _bipod(par,.8,.03,bip,.48)
# ------------------------------------------------------------------------------------------------------------- LAUNCHER
def w_rocket(par,laser):
  # TWIN full-length tubes, front + rear end rings, flared venturis, chunky centre module with a ribbed bronze cooling
  # band, sight box on the left, front grip, pistol grip with guard, bent stock arm with a shoulder pad, red warheads,
  # laser emitter (+ beam while aiming)
  for sy in (-1,1):
    y=sy*.047
    _new('tube',CY((-.55,y,.14),(.66,y,.14),.044,28),TUBE,par,bev=.001)
    _new('ringF',CY((.62,y,.14),(.7,y,.14),.05,28),POLYD,par);_new('ringR',CY((-.6,y,.14),(-.52,y,.14),.05,28),POLYD,par)
    _new('vent',CY((-.6,y,.14),(-.7,y,.14),.046,28,.064),PARK,par)
    _new('war',CY((.7,y,.14),(.78,y,.14),.037,24),GMET,par);_new('tip',CY((.78,y,.14),(.88,y,.14),.036,24,.004),REDM,par)
    for x in (-.35,.4):_new('band',CY((x,y,.14),(x+.025,y,.14),.047,28),POLYD,par)
  _new('bridgeF',BX((.64,0,.14),(.05,.06,.05)),POLYD,par,bev=.004);_new('bridgeR',BX((-.56,0,.14),(.05,.06,.05)),POLYD,par,bev=.004)
  _new('core',T2([(-.095,.08),(-.11,.14),(-.095,.2),(.095,.2),(.11,.14),(.095,.08)],-.07,.24),POLYD,par,bev=.006)
  bz=_new('fins',T2([(-.1,.085),(-.115,.14),(-.1,.195),(.1,.195),(.115,.14),(.1,.085)],-.02,.19),BRZ,par,bev=.002)
  CUT(bz,MERGE([BX((-.005+k*.017,0,.14),(.008,.3,.16)) for k in range(12)]),par)
  _new('sight',P2([(.0,.2),(.16,.2),(.16,.24),(.03,.25),(.0,.235)],.04,.1),GMET,par,bev=.004);_new('sglass',BX((.161,.07,.222),(.003,.05,.026)),STRIPE,par,bev=0)
  _new('fmount',BX((.32,0,.112),(.06,.07,.03)),GMET,par,bev=.003);_new('fgrip',P2([(.3,.104),(.34,.104),(.345,.0),(.32,-.04),(.295,.0)],-.018,.018),POLYD,par,bev=.004)
  _new('grip',P2([(-.03,.096),(.03,.096),(.025,.0),(.03,-.03),(.005,-.07),(-.04,-.065),(-.045,-.01)],-.018,.018),POLYD,par,bev=.004)
  tg=_new('guard',P2([(.03,.08),(.1,.08),(.095,.03),(.04,.02)],-.006,.006),GMET,par,bev=.001);CUT(tg,P2([(.037,.072),(.09,.072),(.086,.036),(.045,.028)],-.01,.01),par)
  _new('trig',P2([(.05,.08),(.057,.08),(.06,.05),(.053,.052)],-.003,.003),PARK,par)
  _new('arm1',P2([(-.04,-.05),(-.03,-.03),(-.3,.03),(-.31,.01)],-.012,.012),GMET,par,bev=.002);_new('arm2',P2([(-.31,.01),(-.29,.03),(-.33,.096),(-.35,.09)],-.012,.012),GMET,par,bev=.002)
  _new('apad',P2([(-.3,.0),(-.38,.0),(-.4,.03),(-.38,.06),(-.3,.06)],-.03,.03),RUB,par,bev=.006)
  _new('emit',BX((.2,-.085,.14),(.06,.03,.035)),GMET,par,bev=.003);_new('lens',CY((.23,-.085,.14),(.234,-.085,.14),.008,12),LASER,par,bev=0)
  if laser>0:_new('beam',CY((.234,-.085,.14),(.234+laser,-.085,.14),.0022,8),LASER,par,bev=0)
  bake_text(par,'DU-R2  HE',Vector((.1,.0915,.14)),(0,1,0),.014,STEN)
# ------------------------------------------------------------------------------------------------------------- PISTOL
def w_pistol(par):
  """officer's sidearm in the rifle's design language: angular slide with OVAL cooling ports and rear serrations,
  integrated compensator, dust-cover rail, squared trigger guard moulded into the frame, raked angular grip with a
  beavertail and stippling bands, flared mag base, small tall HOLOGRAPHIC sights"""
  sl=_new('slide',P2([(-.07,.07),(.13,.07),(.15,.062),(.15,.035),(-.07,.035),(-.075,.05)],-.014,.014),GMET,par,bev=.0015)
  def ov(c,ln,ht):
    c=Vector(c);bm=CY(c-Vector((0,.03,0)),c+Vector((0,.03,0)),ht/2,16);bmesh.ops.scale(bm,vec=(ln/ht,1,1),space=Matrix.Translation(-c),verts=bm.verts);return bm
  CUT(sl,MERGE([ov((.035+k*.03,0,.054),.022,.009) for k in range(3)]+[BX((-.06+k*.006,0,.053),(.0025,.04,.03)) for k in range(5)]+[BX((.0,-.014,.056),(.035,.008,.012))]),par)
  _new('barrelT',BX((.0,0,.07),(.03,.012,.004)),PARK,par,bev=.0005)
  cmp=_new('comp',P2([(.15,.068),(.19,.064),(.19,.036),(.15,.036)],-.014,.014),GMET,par,bev=.0015);CUT(cmp,MERGE([BX((.165+k*.013,0,.07),(.005,.012,.02)) for k in range(2)]),par)
  _new('muz',CY((.188,0,.052),(.194,0,.052),.006,14),POLYD,par,bev=0)
  fr=_new('frame',P2([(-.065,.035),(.15,.035),(.15,.02),(.06,.018),(.055,-.025),(.0,-.025),(-.01,.0),(-.065,.012)],-.0125,.0125),POLYD,par,bev=.0015)
  CUT(fr,P2([(.008,.012),(.048,.012),(.046,-.016),(.012,-.016)],-.03,.03),par)
  for k in range(3):_new('rslot',BX((.09+k*.018,0,.022),(.008,.03,.006)),PARK,par,bev=.0005)
  _new('trig',P2([(.024,.02),(.03,.02),(.032,-.008),(.026,-.007)],-.002,.002),PARK,par,bev=.0004)
  g=_new('grip',P2([(-.06,.012),(-.005,.0),(-.012,-.03),(-.025,-.085),(-.07,-.085),(-.068,-.04),(-.08,.008),(-.075,.016)],-.015,.015),POLYD,par,bev=.002)
  CUT(g,MERGE([BX((-.04,.015,-.03-k*.016),(.04,.004,.004),Matrix.Rotation(.2,3,'Y')) for k in range(3)]+[BX((-.04,-.015,-.03-k*.016),(.04,.004,.004),Matrix.Rotation(.2,3,'Y')) for k in range(3)]),par)
  _new('mbase',P2([(-.075,-.083),(-.02,-.083),(-.018,-.094),(-.078,-.094)],-.017,.017),POLY,par,bev=.002)
  for x,h in ((.125,.026),(-.055,.024)):
    f=_new('holo',P2([(x-.008,.068),(x+.008,.068),(x+.007,.07+h),(x-.007,.07+h)],-.011,.011),POLYD,par,bev=.001)
    CUT(f,BX((x,0,.07+h*.6),(.03,.016,h*.55)),par);_new('pane',BX((x,0,.07+h*.6),(.002,.018,h*.6)),GLASS,par,bev=0);_new('ret',BX((x-.0015,0,.07+h*.6),(.0015,.003,.003)),EYE,par,bev=0)
  _new('slrel',BX((.02,.0135,.03),(.025,.004,.006)),PARK,par,bev=.0005);_new('safety',BX((-.05,.0135,.04),(.015,.004,.006)),PARK,par,bev=.0005)
  bake_text(par,'DU-P1',Vector((.08,.0142,.045)),(0,1,0),.006)
# ------------------------------------------------------------------------------------------------------------- COLOURS
def w_flag(par,team=(.16,.62,.12)):
  """the colours: a staff (local x = up the pole) with a finial, cross-bar and a waving banner (black field, army-colour
  column, gold rules) — the left hand holds the staff low, the right hand higher up"""
  _new('staff',CY((-.55,0,0),(1.75,0,0),.013,16),POLYD,par,bev=0)
  _new('ferrule',CY((-.6,0,0),(-.54,0,0),.015,16),GMET,par,bev=0)
  _new('finial',CY((1.75,0,0),(1.85,0,0),.022,16,.003),GOLDM if 'GOLDM' in globals() else BRZ,par,bev=0)
  _new('collar',CY((1.71,0,0),(1.75,0,0),.019,16),BRZ,par,bev=0);_new('xbar',CY((1.66,-.0,0),(1.66,0,.68),.008,12),POLYD,par,bev=0)
  # banner hangs from the cross-bar along local +z, waving
  NU,NV=24,16;bm=bmesh.new();G2=[]
  for i in range(NU+1):
    u=i/NU;row=[]
    for j in range(NV+1):
      v=j/NV;z=u*.68;x=1.66-v*.5;y=.05*math.sin(u*5.5+v*1.5)*u+.02*math.sin(v*7)*u
      row.append(bm.verts.new((x,y,z)))
    G2.append(row)
  fl=bmesh.new()
  for i in range(NU):
    for j in range(NV):
      f=bm.faces.new((G2[i][j],G2[i+1][j],G2[i+1][j+1],G2[i][j+1]));uc=(i+.5)/NU;f.material_index=1 if .4<uc<.6 else (2 if .36<uc<.4 or .6<uc<.64 else 0)
  me=bpy.data.meshes.new('banner');bm.to_mesh(me);bm.free();o=bpy.data.objects.new('gun',me);bpy.context.scene.collection.objects.link(o);o.parent=par
  for m in (cloth('bannerblack',(.02,.022,.02),300),M('bannerteam',team,.8),M('bannergold',(.6,.45,.15),.5,.6)):me.materials.append(m)
  for p in me.polygons:p.use_smooth=True
  o.modifiers.new('s','SOLIDIFY').thickness=.004;_WP.append(o)
def build_weapon(kind,G,bip=('hang',0),laser=0.0):
  """returns the objects; G = (origin, 3x3 rotation) in world space"""
  global _WP,_CUTS;_WP=[];_CUTS=[]
  par=bpy.data.objects.new('wpn_'+kind,None);bpy.context.scene.collection.objects.link(par);par.matrix_world=Matrix.Translation(G[0])@G[1].to_4x4()
  {'rifle':lambda:w_rifle(par),'mg':lambda:w_mg(par,bip),'sniper':lambda:w_sniper(par,bip),'rocket':lambda:w_rocket(par,laser),'pistol':lambda:w_pistol(par),'flag':lambda:w_flag(par)}[kind]()
  # bake the modifier stacks (EXACT booleans, bevels) into plain meshes and drop the cutters: many weapons in one scene
  # otherwise re-evaluate dozens of booleans per frame (renders ran out of memory)
  dg=bpy.context.evaluated_depsgraph_get()
  for o in _WP:
    if o.modifiers:
      me=bpy.data.meshes.new_from_object(o.evaluated_get(dg));old=o.data;o.modifiers.clear();o.data=me
      if old.users==0:bpy.data.meshes.remove(old)
  for c in _CUTS:
    me=c.data;bpy.data.objects.remove(c)
    if me.users==0:bpy.data.meshes.remove(me)
  return _WP
