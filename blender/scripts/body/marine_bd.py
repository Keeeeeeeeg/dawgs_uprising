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
  # (v3, Keegan) a BIG drum magazine: ribbed polymer drum, steel face plates, a hazard-orange rim band, winding key, feed neck
  DC=(.15,0,-.095);DR=.118;DW=.046
  _new('drumNeck',BX((.15,0,-.005),(.075,.036,.05)),GMET,par,bev=.002)
  _new('drum',CY((DC[0],-DW,DC[2]),(DC[0],DW,DC[2]),DR,32),POLYD,par,bev=.003)
  for yy in (-DW-.004,DW+.004):
    _new('drumFace',CY((DC[0],yy*.9,DC[2]),(DC[0],yy,DC[2]),DR*.82,32),ARM,par,bev=.001)   # deck-grey steel face plates
    for a in range(4):
      ca,sa=math.cos(a*.785),math.sin(a*.785);sg=1 if yy>0 else -1
      _new('drumSpoke',hull([(DC[0]+ca*r0+ss*.007*sa,yy+sg*o,DC[2]+sa*r0-ss*.007*ca) for r0 in (-DR*.78,DR*.78) for ss in (-1,1) for o in (-.001,.005)]),GMET,par,bev=.001)
  for k in (-1,1):_new('drumRib',CY((DC[0],k*.024-.004,DC[2]),(DC[0],k*.024+.004,DC[2]),DR+.005,32),POLYD,par,bev=.001)
  _new('drumHaz',CY((DC[0],-.009,DC[2]),(DC[0],.009,DC[2]),DR+.004,32),HAZ,par,bev=.001)
  _new('drumW',CY((DC[0],DW+.004,DC[2]),(DC[0],DW+.016,DC[2]),.026,16),GMET,par,bev=.001)
  _new('drumKey',BX((DC[0],DW+.0175,DC[2]),(.07,.008,.014)),GMET,par,bev=.002)
  for a in range(6):_new('drumBolt',CY((DC[0]+math.cos(a*1.047)*.075,DW+.001,DC[2]+math.sin(a*1.047)*.075),(DC[0]+math.cos(a*1.047)*.075,DW+.01,DC[2]+math.sin(a*1.047)*.075),.006,8),GMET,par,bev=0)
  _new('grip',P2([(-.06,.005),(-.005,.005),(-.015,-.04),(-.03,-.1),(-.075,-.1),(-.068,-.04),(-.08,.0)],-.016,.016),POLYD,par,bev=.002)
  _new('guard',P2([(-.005,.006),(.03,.006),(.035,-.03),(.0,-.035),(-.003,-.025),(.025,-.025),(.022,-.006),(-.003,-.006)],-.006,.006),POLYD,par,bev=.001)
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
SHH={}   # (v5) the carried shield's wing hinge lines in world space (lp_export turns them into the wingR/wingL bones)
def shield(F,deployed,made,team=TEAMC,W2=.8,H=1.3):
  """(v5, Keegan) the centre panel keeps the old size (0.8 x 1.3 m); two WINGS on hinges fold flat over its face while carried and
  swing out (24 deg back from the centre plane) when he braces against fire: small to carry, big to defend. Halo 2 barricade
  design language (original): angular chamfered top, inset armour frame, raised spine with the army stripe, browed view slit,
  bolt clusters, hazard edging; two handles and a forearm pad on the back. Built OPEN; the game folds the wings."""
  def T(p):return F[0]+F[1]@Vector(p)
  def add(nm,bm,mat,bev=.006,side=None):
    o=put(nm,bm,mat,bev=bev,smooth=False);made.append(o)
    if side is not None:o['side']=side
    return o
  C=W2/2;WG=.27;A=.42;TH=.034;ca,sa=math.cos(A),math.sin(A)
  def wpt(sx,u,z,t):n=(sx*sa,ca);b=(sx*(C+.012+u*ca),-u*sa);return (b[0]+n[0]*t,b[1]+n[1]*t,z)
  # centre panel: chamfered top corners, a thinner bevelled lip all round
  add('shield',hullT([(x,y,z) for x in (-C,C) for y in (0,TH) for z in (0,H-.1)]+[(x,y,H) for x in (-C*.7,C*.7) for y in (0,TH)],F),ARM,.01)
  for x0,x1,z0,z1 in ((-C+.03,C-.03,.04,.08),(-C+.03,C-.03,H-.16,H-.12)):   # inset frame: top and bottom rails
    add('shFrame',hullT([(x,y,z) for x in (x0,x1) for y in (TH-.004,TH+.012) for z in (z0,z1)],F),GUN,.004)
  for sx in (1,-1):add('shFrame',hullT([(sx*x,y,z) for x in (C-.07,C-.03) for y in (TH-.004,TH+.012) for z in (.04,H-.12)],F),GUN,.004)   # side rails
  add('shSpine',hullT([(x,y,z) for x in (-.06,.06) for y in (TH-.004,TH+.018) for z in (.16,H-.24)]+[(x,TH+.026,z) for x in (-.035,.035) for z in (.2,H-.28)],F),ARM,.006)   # raised centre spine
  add('shStripe',hullT([(sx*.02,y,z) for sx in (1,-1) for y in (TH+.022,TH+.03) for z in (.24,H-.32)],F),TEAMM,.0)
  for sx in (1,-1):   # armour plates either side of the spine, stepped
    add('shPlate',hullT([(sx*x,y,z) for x in (.085,C-.085) for y in (TH-.004,TH+.01) for z in (.2,.62)]+[(sx*x,TH+.014,z) for x in (.1,C-.1) for z in (.24,.58)],F),ARM,.005)
    add('shPlate',hullT([(sx*x,y,z) for x in (.085,C-.085) for y in (TH-.004,TH+.01) for z in (.68,H-.3)]+[(sx*x,TH+.014,z) for x in (.1,C-.1) for z in (.72,H-.34)],F),ARM,.005)
    for zz in (.1,H-.2):   # bolt clusters in the frame corners
      for dx,dz in ((0,0),(.018,0),(0,.018)):bx=sx*(C-.05)-sx*dx;add('shBolt',hullT([(bx+ox,y,zz+dz+oz) for ox in (-.006,.006) for oz in (-.006,.006) for y in (TH-.012,TH+.02)],F),GUN,.002)
  add('port',hullT([(sx*.13,y,z) for sx in (1,-1) for y in (TH-.004,TH+.014) for z in (H-.235,H-.19)],F),HAZK,.0)   # view slit
  add('shBrow',hullT([(sx*x,y,z) for sx in (1,-1) for x in (.15,) for y in (TH,TH+.045) for z in (H-.185,H-.17)]+[(sx*.17,TH,H-.165) for sx in (1,-1)],F),GUN,.003)   # brow over the slit
  for k in range(5):   # hazard band across the top
    x=-C*.62+k*C*1.24/5;add('shEdge',hullT([(xx,y,zz) for xx in (x,x+C*1.24/5*.78) for y in (TH-.004,TH+.008) for zz in (H-.05,H-.012)],F),HAZK if k%2 else HAZ,.0)
  for z0 in (.1,):   # hazard chevrons along the foot rail
    for k in range(6):x=-C+.06+k*.115;add('chev',hullT([(x,y,z0) for y in (TH-.004,TH+.008)]+[(x+.05,y,z0) for y in (TH-.004,TH+.008)]+[(x+.08,y,z0+.045) for y in (TH-.004,TH+.008)]+[(x+.03,y,z0+.045) for y in (TH-.004,TH+.008)],F),HAZ if (k%2==0) else HAZK,.0)
  # wings (side 0 = right = -x... the bake reads 'side': 0 -> R): built open, hinged on the panel's edges
  for sx in (1,-1):
    sd=0 if sx<0 else 1
    add('wing',hullT([wpt(sx,u,z,t) for t in (0,TH*.8) for u,z in ((-.004,.02),(-.004,H-.12),(WG,.07),(WG,H-.3))],F),ARM,.008,sd)
    add('wPlate',hullT([wpt(sx,u,z,t) for t in (TH*.8-.004,TH*.8+.012) for u,z in ((.035,.2),(WG-.04,.22),(.035,H-.36),(WG-.04,H-.42))],F),ARM,.005,sd)
    for k in range(6):
      z=.14+k*(H-.5)/6;add('wEdge',hullT([wpt(sx,u,zz,t) for u in (WG-.045,WG-.006) for t in (TH*.8-.004,TH*.8+.008) for zz in (z,z+(H-.5)/6*.8)],F),HAZ if k%2==0 else HAZK,.0,sd)
    h0,h1=T((sx*(C+.006),TH*.5,.05)),T((sx*(C+.006),TH*.5,H-.15))
    add('wHinge',tube(h0,h1,.017,.017,NS=12,NR=1),GUN,.0,sd)
    if not deployed:SHH['R' if sx<0 else 'L']=(h0.copy(),h1.copy())
  # the back: two vertical handles where his hands go, and a padded forearm rest
  for x,z0,z1 in ((.15,H*.38,H*.5),(-.15,H*.54,H*.66)):
    for zz in (z0,z1):add('gripPost',hullT([(x+ox,y,zz+oz) for ox in (-.01,.01) for oz in (-.01,.01) for y in (.02,-.08)],F),GUN,.002)
    add('grip',tube(T((x,-.07,z0-.005)),T((x,-.07,z1+.005)),.015,.015,NS=12,NR=1),RUB)
  add('shPad',hullT([(x,y,z) for x in (-.07,.07) for y in (.006,-.035) for z in (H*.42,H*.6)],F),RUB,.01)
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
    add('magplate',tube(Vector((a.x,a.y,.065)),Vector((a.x,a.y,.05)),.078,.078,NS=16,NR=1),GUN,0)
    add('haz',tube(a+d*.17,a+d*.2,.083,.083,NS=18,NR=1),HAZ,0)
    bk=Rp@Vector((0,1,0));bk.z=0;bk.normalize()   # water-jet thrusters on the boot heels: nozzle, glowing ring
    for off in (-.03,.03):
      sdv=bk.cross(Vector((0,0,1)))*off;h0=Vector((a.x,a.y,.075))+bk*.035+sdv;h1=h0+bk*.07+Vector((0,0,.012))
      add('jet',tube(h0,h1,.02,.024,NS=14,NR=1),GUN,0);add('jetGlow',tube(h1-bk*.006,h1+bk*.003,.019,.019,NS=14,NR=1),JETG,0)
  for o in made[-16:]:   # (game bake) boot parts: left/right for the skin weights (the right side is -x)
    if o.name.split('.')[0] in('magplate','haz','jet','jetGlow'):
      cx_=sum((o.matrix_world@v.co).x for v in o.data.vertices)/max(1,len(o.data.vertices));o['side']=0 if cx_<0 else 1
  for sx in (1,-1):add('hazC',hullT([(sx*x,y,z) for x in (.06,.1) for y in (-.13,-.168) for z in (.04,.065)],FC),HAZ,.0)
  # (v3, Keegan) more ORANGE: bands that hug the forearms and shins (radius measured from the parts already built there)
  def hug(a,b,t,w,names):
    ax=(b-a);L=ax.length;ax=ax/L;c0=a+ax*(L*t);r=0
    for o in made:
      if o.type!='MESH' or o.name.split('.')[0] not in names:continue
      mw=o.matrix_world
      for v in o.data.vertices:
        p=mw@v.co;q=p-c0;tt=q.dot(ax)
        if abs(tt)<w:
          rr=(q-ax*tt).length
          if rr<.1:r=max(r,rr)
    return c0,ax,r+.003
  for sd in 'RL':
    for t0,w0 in ((.5,.012),(.72,.01)):
      c0,ax,r=hug(J['el'+sd],J['wr'+sd],t0,w0,('farm',));o=add('hazF',tube(c0-ax*w0,c0+ax*w0,r,r,NS=20,NR=1),HAZ,0);o['side']=0 if sd=='R' else 1
    c0,ax,r=hug(J['ank'+sd],J['knee'+sd],.62,.016,('shinG','shin','gaiter','shaft'));o=add('haz',tube(c0-ax*.016,c0+ax*.016,r,r,NS=20,NR=1),HAZ,0);o['side']=0 if sd=='R' else 1
  dg=bpy.context.evaluated_depsgraph_get();TR=[BVHTree.FromObject(o,dg) for o in made if o.type=='MESH']
  def surf(lp):   # a chest-frame point pushed onto the front of the armour
    w0=Cc+Rc@Vector((lp[0],-.5,lp[2]));d=Rc@Vector((0,1,0));best=None
    for t in TR:
      h=t.ray_cast(w0,d,1.0)
      if h[0] is not None and (best is None or h[3]<best[1]):best=(h[0],h[3])
    return best[0] if best else None
  for x0,x1 in ((-.11,-.035),(.035,.11)):   # orange chest panels on both pecs, laid on the plate
    ps=[surf((x,0,z)) for x in (x0,x1) for z in (.13,.2)]
    if all(ps):n=Rc@Vector((0,-1,0));add('chestHaz',hull([tuple(q+n*o) for q in ps for o in (.001,.007)]),HAZ,.0)
  # rebreather pack high on the back + two RIBBED HOSES curling over the shoulders into the helmet's cheek canisters
  add('rbPack',boxT((0,.16,.2),(.16,.07,.13),FC),GUNP,.006);add('rbBand',boxT((0,.196,.2),(.162,.004,.03),FC),HAZ,.0)
  for sx in (1,-1):add('rbTank',tube(Cc+Rc@Vector((sx*.055,.21,.12)),Cc+Rc@Vector((sx*.055,.21,.3)),.03,.03,NS=16,NR=1),GUN,0)
  hcW=Cc+Rc@Vector((0,-.01,.37))
  for sx in (1,-1):
    P0=Cc+Rc@Vector((sx*.06,.17,.29));P1=Cc+Rc@Vector((sx*.22,.12,.3));P2=hcW+Rc@Vector((sx*.2,-.02,-.13));P3=hcW+Rc@Vector((sx*.115,-.06,-.1))   # out round the helmet's neck flare, into the jaw
    pts=[];N=26
    for i in range(N+1):
      t=i/N;u_=1-t;pts.append(P0*u_**3+P1*3*u_*u_*t+P2*3*u_*t*t+P3*t**3)
    bms=[]
    for i in range(N):bms.append(tube(pts[i],pts[i+1],.0105 if i%2 else .0135,.0105 if i%2 else .0135,NS=12,NR=1))
    o=add('ribhose',MERGE(bms),RUB,0);o['side']=0 if sx<0 else 1
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
if os.environ.get('AUDIT'):   # (v3 polish) every pair of parts: how deep does one sink into the other? (touching is fine)
  for lab,made in ALL:
    if lab not in os.environ.get('AUDIT').split(','):continue
    dg=bpy.context.evaluated_depsgraph_get();obs=[o for o in made if o.type=='MESH' and not o.hide_render and not o.get('bake')];T={};V={}
    for o in obs:
      me=o.evaluated_get(dg).data;Mw=o.matrix_world;vs=[Mw@v.co for v in me.vertices];V[o]=vs;T[o]=BVHTree.FromPolygons(vs,[tuple(q.vertices) for q in me.polygons])
    D=Vector((1,.31,.17)).normalized();res=[]
    def pen(a,b):
      best=(0.0,None)
      for v in V[a][::max(1,len(V[a])//300)]:
        p_,n_,i_,d_=T[b].find_nearest(v,.08)
        if p_ is None or d_<=best[0]:continue
        o2=v.copy();hits=0
        for _ in range(12):
          h=T[b].ray_cast(o2,D,3.0)
          if h[0] is None:break
          hits+=1;o2=h[0]+D*1e-5
        if hits%2==1:best=(d_,v)
      return best
    for i,a in enumerate(obs):
      for b in obs[i+1:]:
        if not T[a].overlap(T[b]):continue
        d1,p1=pen(a,b);d2,p2=pen(b,a)
        d,pp=(d1,p1) if d1>=d2 else (d2,p2)
        if d>.006:res.append((d,_base(a),_base(b),a.get('side',-1),b.get('side',-1),pp))
    res.sort(key=lambda r:-r[0]);print('\nAUDIT',lab,len(res),'pairs deeper than 6 mm')
    agg={}
    for d,na,nb,sa,sb,pp in res:
      k=tuple(sorted((na,nb)));agg.setdefault(k,[]).append((d,pp))
    for k,v in sorted(agg.items(),key=lambda kv:-max(x[0] for x in kv[1]))[:60]:print('  %-12s x %-12s n=%d max %.0f mm at %s'%(k[0],k[1],len(v),max(x[0] for x in v)*1000,[round(c,2) for c in max(v,key=lambda x:x[0])[1]]))
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
  sc.render.filepath='/home/claude/body/'+os.environ.get('PFX','')+nm+'.png';bpy.ops.render.render(write_still=True);print('shot',nm,flush=True)
which=os.environ.get('SHOTS','line,head,breach,gun').split(',')
if 'line' in which:shot('bm_line',(.25,-1,.18),(2.75,0,.9),6.6,(2000,900))
if 'head' in which:shot('bm_head',(.6,-1,.2),(0,-.02,1.62),.55,(800,800))
if 'breach' in which:shot('bm_breach',(.5,-1,.12),(3.1,0,.95),1.9,(900,1000))
if 'prop' in which:shot('bm_front',(0,-1,0),(0,0,.95),2.1,(700,1000));shot('bm_side',(1,0,0),(0,0,.95),2.1,(700,1000))
if 'feet' in which:shot('bm_feetS',(1,-.15,.08),(0,-.02,.15),.6,(900,600));shot('bm_feetF',(0,-1,.12),(0,-.02,.15),.6,(900,600))
if 'hose' in which:shot('bm_hose',(-.55,1,.35),(0,.0,1.45),.75,(900,900))
if 'gun' in which:shot('bm_gun',(0,-1,.05),(0,-.25,1.1),.9,(900,700));shot('bm_hand',(.3,-1,.3),(0,-.25,1.0),.45,(800,800));shot('bm_boot',(-.6,1,.25),(1.0,0,.12),.75,(900,700))
bpy.ops.wm.save_as_mainfile(filepath='/home/claude/body/boarding_marine.blend')
