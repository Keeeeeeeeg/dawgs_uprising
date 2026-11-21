# Boarding Marine CONCEPT (Keegan, 2026-11-19): naval boarding troops, visually the opposite of the camo riflemen.
# Sealed deck-grey armour, hazard-orange + army-colour stripes, sealed helmet with ONE horizontal visor slit and a rebreather
# (they cross water by walking the bottom), mag-lock boots, compact combat shotgun (original design), breacher with shaped
# charges, a back-mounted folding boarding shield that slams down for SHIELD WALL. Built on body8 (same skeleton/poses).
import os
os.environ['NOHEAD']='1'
exec(open('/home/claude/body/body8.py').read());exec(open('/home/claude/body/qa5.py').read())
exec(open('/home/claude/wpn/weapons7.py').read().split('# ------------------------------------------------------------------------------------------------------------- RIFLE')[0]) if 'P2' not in globals() else None
# ---- materials: deck grey instead of woodland camo
CAMO=cloth('decksuit',(.042,.046,.052),420)
exec(open('/home/claude/body/vpaint_src.py').read())
ARM=vpaint('deckplate',(.2,.205,.2),mud=.45,wear=1.6,dust=.3,rust=.8,dustcol=(.42,.43,.41),mudcol=((.24,.25,.24),(.33,.34,.32)))
WEB=cloth('webgrey',(.03,.032,.034),500);POUCH=cloth('pouchgrey',(.045,.048,.05),380)
HAZ=M('hazard',(.75,.26,.02),.5);JETG=M('jetglow',(.3,.75,1),.2,0,6);HAZK=M('hazardk',(.02,.02,.02),.6)
TEAMC=(.16,.62,.12);TEAMM=vpaint('team',(.06,.17,.045),mud=.6,wear=1.5,dust=.4,rust=.5,dustcol=(.42,.43,.41),mudcol=((.24,.25,.24),(.33,.34,.32)))
SLIT=M('slit',(.25,.9,.35),.2,0,9)
CHG=M('charge',(.09,.085,.06),.7);DET=M('det',(.7,.05,.03),.4,0,3)
# ---- the combat shotgun (model units, origin = grip, x forward, z up, +y left); scaled .8 like the rifle
def w_shotgun(par):
  rec=_new('receiver',P2([(-.09,.0),(.28,.0),(.3,.02),(.3,.085),(.12,.1),(-.06,.1),(-.1,.07)],-.024,.024),GMET,par,bev=.002)
  CUT(rec,MERGE([BX((.1+k*.05,.024,.055),(.03,.012,.02)) for k in range(3)]+[BX((.06,-.024,.06),(.07,.01,.025))]),par)   # side vents, ejection port
  _new('barrel',CY((.28,0,.065),(.66,0,.065),.016,18),GUN,par,bev=0)
  _new('tube',CY((.28,0,.028),(.56,0,.028),.017,18),GMET,par,bev=0)
  sh=_new('shroud',P2([(.3,.012),(.6,.012),(.62,.03),(.62,.09),(.3,.095)],-.027,.027),POLYD,par,bev=.002)
  def ov(c,ln,ht):
    c=Vector(c);bm=CY(c-Vector((0,.04,0)),c+Vector((0,.04,0)),ht/2,16);bmesh.ops.scale(bm,vec=(ln/ht,1,1),space=Matrix.Translation(-c),verts=bm.verts);return bm
  CUT(sh,MERGE([ov((.34+k*.06,0,.07),.04,.014) for k in range(5)]+[ov((.37+k*.06,0,.035),.04,.012) for k in range(4)]),par)
  br=_new('breacher',CY((.64,0,.065),(.72,0,.065),.024,8),GMET,par,bev=.001)   # standoff muzzle with teeth
  CUT(br,MERGE([BX((.715,math.cos(k*.785)*.025,.065+math.sin(k*.785)*.025),(.02,.012,.012)) for k in range(8)]),par)
  _new('fgrip',P2([(.33,.012),(.4,.012),(.395,-.05),(.36,-.065),(.34,-.06)],-.017,.017),POLYD,par,bev=.002)   # vertical foregrip
  _new('drum',CY((.06,-.035,-.03),(.06,.035,-.03),.075,24),POLYD,par,bev=.002)   # drum magazine under the receiver
  _new('drumW',CY((.06,-.039,-.03),(.06,.039,-.03),.03,16),GMET,par,bev=.001)
  _new('grip',P2([(-.06,.005),(-.005,.005),(-.015,-.04),(-.03,-.1),(-.075,-.1),(-.068,-.04),(-.08,.0)],-.016,.016),POLYD,par,bev=.002)
  _new('guard',P2([(-.005,.0),(.03,.0),(.035,-.03),(.0,-.035),(-.003,-.025),(.025,-.025),(.022,-.006),(-.003,-.006)],-.006,.006),POLYD,par,bev=.001)
  st=_new('stock',P2([(-.1,.08),(-.1,.015),(-.3,.0),(-.33,-.035),(-.36,-.035),(-.36,.095),(-.33,.095),(-.3,.085)],-.02,.02),POLYD,par,bev=.002)
  CUT(st,P2([(-.13,.06),(-.13,.03),(-.29,.02),(-.29,.07)],-.03,.03),par)   # skeleton window
  _new('pad',P2([(-.36,-.04),(-.375,-.04),(-.375,.1),(-.36,.1)],-.022,.022),RUB,par,bev=.002)
  _new('rail',BX((.12,0,.105),(.3,.022,.01)),PARK,par,bev=.001)
  f=_new('sight',P2([(.03,.11),(.08,.11),(.075,.15),(.035,.15)],-.016,.016),POLYD,par,bev=.001);CUT(f,BX((.055,0,.135),(.06,.024,.022)),par)
  _new('pane',BX((.055,0,.135),(.002,.026,.024)),GLASS,par,bev=0);_new('ret',BX((.055,0,.135),(.003,.004,.004)),EYE,par,bev=0)
  _new('light',CY((.5,-.03,.04),(.58,-.03,.04),.012,12),GMET,par,bev=0);_new('lens',CY((.58,-.03,.04),(.585,-.03,.04),.011,12),EYE,par,bev=0)
  bake_text(par,'DU-S12',Vector((.12,.0245,.03)),(0,1,0),.012)
w_rifle=w_shotgun
# ---- boarding shield: stowed (on the back) or deployed (planted upright with a kickstand); local x right, y out, z up
def shield(F,deployed,made,team=TEAMC,W2=.8,H=1.3):
  def T(p):return F[0]+F[1]@Vector(p)
  def add(nm,bm,mat,bev=.006):o=put(nm,bm,mat,bev=bev,smooth=False);made.append(o);return o
  pts=[(sx*W2/2,y,z) for sx in (1,-1) for y in (0,.03) for z in (0,H)]+[(sx*W2*.42,y,H+.06) for sx in (1,-1) for y in (0,.03)]
  add('shield',hullT(pts,F),ARM,.008)
  for z0 in (.06,.18):   # hazard chevrons along the foot
    for k in range(6):x=-W2/2+.02+k*.095;add('chev',hullT([(x,y,z0) for y in (.018,.036)]+[(x+.05,y,z0) for y in (.018,.036)]+[(x+.08,y,z0+.06) for y in (.018,.036)]+[(x+.03,y,z0+.06) for y in (.018,.036)],F),HAZ if (k%2==0) else HAZK,.0)
  add('shStripe',hullT([(sx*.03,y,z) for sx in (1,-1) for y in (.03,.036) for z in (.27,H-.28)],F),TEAMM,.0)
  add('port',hullT([(sx*.12,y,z) for sx in (1,-1) for y in (.028,.04) for z in (H-.2,H-.16)],F),HAZK,.0)   # view port
  for sx in (1,-1):add('hinge',tube(T((sx*W2/2,.015,.08)),T((sx*W2/2,.015,H-.08)),.012,.012,NS=10,NR=1),GUN)
  for zz in (H*.42,H*.52):add('gripPost',tube(T((0,.022,zz)),T((0,-.058,zz)),.012,.012,NS=8,NR=1),GUN)
  add('grip',tube(T((0,-.05,H*.42-.01)),T((0,-.05,H*.52+.01)),.014,.014,NS=10,NR=1),RUB)
  if deployed:
    for sx in (1,-1):add('stand',tube(T((sx*.24,.012,.6)),T((sx*.26,-.5,.014)),.012,.012,NS=8,NR=1),GUN)
# ---- sealed boarding helmet (local: -y forward, z up, origin = head centre)
def cyl(a,b,r,seg=16):return tube(Vector(a),Vector(b),r,r,NS=seg,NR=1)
def board_head(made,team=TEAMC):
  """(v2, Keegan) the Dawgs helmet family: the riflemen's shell (ear + neck flare, gasket visor, steel mask), in deck grey,
  with a glowing horizontal scan slit across the smoked lens and a rebreather: grilled filter on the chin, twin cheek
  canisters with hazard caps, hoses. Everything ray-cast onto the helmet so it sits on the surface."""
  global SHELL,PLATE
  S0,P0=SHELL,PLATE;SHELL=ARM;PLATE=ARM
  objs,prof,H1=helmet({'cap':'full','vents':2,'chin':'round','top':'none','side':'none'},(0,0,0),lensmat(77,team))
  SHELL,PLATE=S0,P0
  made+=objs;dg=bpy.context.evaluated_depsgraph_get()
  trees=[BVHTree.FromObject(o,dg) for o in objs if o.type=='MESH']
  def hit(p,d):
    best=None
    for t in trees:
      h=t.ray_cast(Vector(p),Vector(d).normalized(),1.0)
      if h[0] is not None and (best is None or h[3]<best[2]):best=(h[0],h[1].normalized(),h[3])
    return best
  def add(nm,bm,mat,bev=.002,sm=False):o=put(nm,bm,mat,bev=bev,smooth=sm);made.append(o);return o
  pts=[hit((x/10*.1,-.5,.002),(0,1,0)) for x in range(-10,11)]
  pts=[p for p in pts if p]
  for a,b in zip(pts,pts[1:]):
    add('slit',hull([tuple(q[0]+q[1]*o+Vector((0,0,dz))) for q in (a,b) for o in (-.001,.0022) for dz in (-.0045,.0045)]),SLIT,0)
  ch=hit((0,-.5,-.13),(0,1,0))
  if ch:
    c,n=ch[0],ch[1]
    add('filter',cyl(c-n*.006,c+n*.03,.03,18),GUN,.002)
    for k in range(3):add('filterRib',cyl(c+n*(.008+k*.008),c+n*(.012+k*.008),.033,18),HAZK,0)
  for sx in (1,-1):
    sd=hit((sx*.4,-.13,-.1),(-sx,0,0))
    if not sd:continue
    a=sd[0]-sd[1]*.004;ax=Vector((0,.35,-1)).normalized();cpos=a+sd[1]*.024
    add('canister',cyl(cpos-ax*.045,cpos+ax*.045,.022,16),GUNP,.002);add('canCap',cyl(cpos-ax*.06,cpos-ax*.044,.023,16),HAZ,.001)
    add('canBand',cyl(a,cpos+sd[1]*.0,.012,10),GUN,0)
    if ch:
      p0=cpos+ax*.04;p1=ch[0]+Vector((sx*.025,0,0))
      for k in range(6):
        t0,t1=k/6,(k+1)/6;q0=p0.lerp(p1,t0)+Vector((0,-.012*math.sin(t0*math.pi),-.01*math.sin(t0*math.pi)));q1=p0.lerp(p1,t1)+Vector((0,-.012*math.sin(t1*math.pi),-.01*math.sin(t1*math.pi)))
        add('hose',cyl(q0,q1,.0075,10),RUB,0)
# ---- body build: marine() + armour extras (hazard bands, mag boots, charges, stowed shield) + the sealed head
def boarder(PP,seed,role='shot',deploy=False,label=''):
  PP['gauntlet']=True;wp='can' if role in('shield','plant') else 'rifle'
  made,bo=marine(PP,seed=seed,gear='light',weap=wp,head='rifle')
  if wp=='can':   # the breacher carries nothing but the shield: drop the loader's can
    for e in [o for o in bpy.data.objects if o.name.startswith('wpn_can')]:
      for c in list(e.children):
        if c in made:made.remove(c)
        bpy.data.objects.remove(c)
      bpy.data.objects.remove(e)
    def ok(o):
      try:o.name;return True
      except ReferenceError:return False
    made[:]=[o for o in made if ok(o)]
  Pp,Rp=Vector(PP['pelvis'][0]),PP['pelvis'][1];Rc=Rp@PP.get('chest',Matrix.Identity(3));Cc=Pp+Rp@Vector((0,0,.3));FC=(Cc,Rc);J=PP['_j']
  def add(nm,bm,mat,bev=.004):o=put(nm,bm,mat,bev=bev,smooth=False);made.append(o);return o
  # remove the cloth pack / pouches that read as infantry kit, keep plates
  for sd in 'RL':   # mag-lock boot plates under each sole + hazard band round each shin
    a=J['ank'+sd];k=J['knee'+sd];d=(k-a).normalized()
    add('magplate',tube(Vector((a.x,a.y,.065)),Vector((a.x,a.y,.05)),.062,.062,NS=16,NR=1),GUN,0)
    add('haz',tube(a+d*.17,a+d*.2,.083,.083,NS=18,NR=1),HAZ,0)
    bk=Rp@Vector((0,1,0));bk.z=0;bk.normalize()   # water-jet thrusters on the boot heels: nozzle, glowing ring
    for off in (-.03,.03):
      sdv=bk.cross(Vector((0,0,1)))*off;h0=Vector((a.x,a.y,.075))+bk*.035+sdv;h1=h0+bk*.07+Vector((0,0,.012))
      add('jet',tube(h0,h1,.02,.024,NS=14,NR=1),GUN,0);add('jetGlow',tube(h1-bk*.006,h1+bk*.003,.019,.019,NS=14,NR=1),JETG,0)
  for o in made[-16:]:   # (game bake) boot parts: left/right for the skin weights (the right side is -x)
    if o.name.split('.')[0] in('magplate','haz','jet','jetGlow'):
      cx_=sum((o.matrix_world@v.co).x for v in o.data.vertices)/max(1,len(o.data.vertices));o['side']=0 if cx_<0 else 1
  for sx in (1,-1):add('hazC',hullT([(sx*x,y,z) for x in (.06,.1) for y in (-.13,-.168) for z in (.04,.065)],FC),HAZ,.0)
  if role=='demo':   # shaped charges on the chest straps + detonator on the left shoulder
    for i,(x,z) in enumerate(((-.07,.12),(.07,.12),(-.07,.02),(.07,.02))):
      add('charge',boxT((x,-.2,z),(.06,.03,.075),FC),CHG,.004);add('cap',boxT((x,-.218,z+.025),(.02,.01,.012),FC),DET,.001)
    add('det',boxT((.14,-.12,.2),(.04,.03,.06),FC),GUNP,.004);add('detL',boxT((.14,-.137,.215),(.012,.004,.008),FC),DET,0)
  # stowed shield on the back (clamshell), or deployed in front of him
  if role=='shield':   # carried at his right side by the back grip, face out
    hR=Vector(PP['gun'][0]);Rs=Rp@Matrix(((0,-1,0),(1,0,0),(0,0,1)));n0=len(made);shield((hR-Rs@Vector((0,-.05,1.3*.47)),Rs),False,made)
    se=bpy.data.objects.new('wpn_shield',None);bpy.context.scene.collection.objects.link(se)   # (game bake) the shield is the breacher's 'weapon': it rides his right hand
    for o in made[n0:]:o.parent=se
  # head
  hc=Cc+Rc@Vector((0,-.01,.37));J.setdefault('neck',Cc+Rc@Vector((0,-.01,.24)));J.setdefault('headc',hc)   # (game bake) joints the NOHEAD body skipped
  emp=bpy.data.objects.new('head',None);bpy.context.scene.collection.objects.link(emp)
  if PP.get('look') is not None:d=(Vector(PP['look'])-hc).normalized();Rh=(-d).to_track_quat('Y','Z').to_matrix()
  else:Rh=Rc
  before=set(bpy.data.objects);hm=[];board_head(hm)
  for o in set(bpy.data.objects)-before:
    if o is not emp:o.parent=emp   # cutters too (the shell's window booleans follow the head)
  emp.matrix_world=Matrix.Translation(hc)@Rh.to_4x4();made+=hm;return made
ALL=[]
def B(name,x,yaw,label,kind='rifle',**k):
  PP=pose(name,x,yaw,kind=kind);m=boarder(PP,label=label,**k);ALL.append((label,m));return PP
B('neutral',0,0,'shotgunner',seed=61)
B('neutral',1.0,math.pi*.75,'back',seed=62)
B('neutral',2.0,0,'demo',seed=63,role='demo')
B('game',3.1,0,'breacher',kind='can',seed=64,role='shield')
B('game',4.4,0,'planted',kind='can',seed=66,role='plant')
shield((Vector((4.4,-.62,0)),Rz(math.pi)),True,ALL[-1][1])
B('split',5.5,-.25,'behind',seed=65)
TOT=0
for lab,made in ALL:TOT+=len(qa(made,lab,floor=0.0))
print('\nQA TOTAL',TOT)
if os.environ.get('QAONLY'):raise SystemExit
put('floor',box((2.8,0,-.005),(11,5,.01)),FLOOR)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=int(os.environ.get('SAMP','24'));sc.cycles.use_denoising=True;sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
w=bpy.data.worlds.new('W');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(.03,.034,.038,1)
LT=[]
for nm,off,en,col,sz in (('k',(2,-6,5),700,(1,.97,.92),6),('r',(-5,5,3),420,(.75,.9,1),6),('f',(-2,-7,1),180,(.85,.9,1),8),('t',(0,0,8),250,(1,1,1),10)):
  l=bpy.data.objects.new(nm,bpy.data.lights.new(nm,'AREA'));sc.collection.objects.link(l);l.data.energy=en;l.data.size=sz;l.data.color=col;LT.append((l,Vector(off)))
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
def shot(nm,d,tgt,osc,res):
  tgt=Vector(tgt)
  for l,off in LT:l.location=tgt+off;l.rotation_euler=(tgt-l.location).to_track_quat('-Z','Y').to_euler()
  cam.data.ortho_scale=osc;sc.render.resolution_x,sc.render.resolution_y=res;pos=tgt+Vector(d).normalized()*14;cam.location=pos;cam.rotation_euler=(tgt-pos).to_track_quat('-Z','Y').to_euler()
  sc.render.filepath='/home/claude/body/'+nm+'.png';bpy.ops.render.render(write_still=True);print('shot',nm,flush=True)
which=os.environ.get('SHOTS','line,head,breach,gun').split(',')
if 'line' in which:shot('bm_line',(.25,-1,.18),(2.75,0,.9),6.6,(2000,900))
if 'head' in which:shot('bm_head',(.6,-1,.2),(0,-.02,1.62),.55,(800,800))
if 'breach' in which:shot('bm_breach',(.5,-1,.12),(3.1,0,.95),1.9,(900,1000))
if 'gun' in which:shot('bm_gun',(0,-1,.05),(0,-.25,1.1),.9,(900,700));shot('bm_hand',(.3,-1,.3),(0,-.25,1.0),.45,(800,800));shot('bm_boot',(-.6,1,.25),(1.0,0,.12),.75,(900,700))
bpy.ops.wm.save_as_mainfile(filepath='/home/claude/body/boarding_marine.blend')
