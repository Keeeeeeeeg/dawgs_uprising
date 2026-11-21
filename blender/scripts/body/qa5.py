# QUALITY GATE (standard for every model from now on): no floating parts, no clipping between parts that must stay apart,
# nothing under the floor. Run after building a marine: qa(made,label) -> list of issues.
def _base(o):return o.name.split('.')[0]
ARMS={'farm','vamb','glove','knuckle','elbow','finger','thumb'};UARM={'uarm'};CHEST={'pec','pecEdge','spine','lame','collar','chestB','cumm'}
POUCHN={'mags','flap','pouchS','nade','fuze','canteen','buckle','sheath','knife','strap','shStrap'}
SHOULD={'paul','paul2','stripe','paulS','collar'}
LEGP={'bootAnk','tongue','thigh','shin','thighP','knee','kneeCap','kneeStrap','kneePad','shinG','shinR','shinStrap','boot','shaft','gaiter','toecap','anklePl','heel','sole','cargo'}
LIM={'gun':.008,'leg':.012,'upperarm':.006,'arm':.005}
def qa(made,label,floor=0.0,ignore_gun_hands=True):
  dg=bpy.context.evaluated_depsgraph_get();obs=[o for o in made if o.type=='MESH' and not o.hide_render];iss=[]
  T={};WV={}
  for o in obs:   # WORLD-space trees (weapon parts are parented to an empty, so object space is not world space)
    me=o.evaluated_get(dg).data;Mw=o.matrix_world;vs=[Mw@v.co for v in me.vertices];WV[o]=vs
    T[o]=BVHTree.FromPolygons(vs,[tuple(p.vertices) for p in me.polygons])
  V=WV
  def pen(a,b):   # deepest vertex of a inside b (b treated as closed; nearest-face normal test)
    best=0.0
    D=Vector((1,.31,.17)).normalized()
    for v in V[a][::2]:
      p,n,i,d=T[b].find_nearest(v,.08)
      if p is None or d<=best:continue
      o2=v.copy();hits=0
      for _ in range(12):   # ray parity: inside a closed mesh = odd number of crossings
        h=T[b].ray_cast(o2,D,3.0)
        if h[0] is None:break
        hits+=1;o2=h[0]+D*1e-5
      if hits%2==1:best=d
    return best
  def hit(a,b):
    if not T[a].overlap(T[b]):return 0
    return max(pen(a,b),pen(b,a))
  body=[o for o in obs if _base(o)!='gun' and not o.get('bake')]
  for o in body:   # floating
    if not any(T[o].overlap(T[n]) for n in obs if n is not o):iss.append('floating '+o.name)
  guns=[o for o in obs if _base(o)=='gun']
  for o in guns:   # every weapon part must touch another weapon part
    if len(guns)>1 and not any(T[o].overlap(T[n]) for n in guns if n is not o):vs=[v.co for v in o.evaluated_get(dg).data.vertices];iss.append('floating gun part %s %s %d verts at %s'%(o.name,o.data.materials[0].name,len(o.data.vertices),[round(c,2) for c in sum(vs,Vector())/max(1,len(vs))]))
  for a in obs:
    for b in obs:
      if a.as_pointer()>=b.as_pointer():continue
      na,nb=_base(a),_base(b);sa,sb=a.get('side',-1),b.get('side',-1)
      pair=None
      if (na in ARMS and nb in CHEST) or (nb in ARMS and na in CHEST):pair='arm-chest'
      elif (na in UARM and nb in ('pec','pecEdge','lame','cumm')) or (nb in UARM and na in ('pec','pecEdge','lame','cumm')):pair='upperarm-chest'
      elif (na in ARMS|UARM and nb in POUCHN) or (nb in ARMS|UARM and na in POUCHN):pair='arm-pouch'
      elif (na in ARMS and nb in SHOULD) or (nb in ARMS and na in SHOULD):pair='arm-shoulder'
      elif (na in UARM and nb in SHOULD and sa!=sb) or (nb in UARM and na in SHOULD and sa!=sb):pair='arm-shoulder'
      elif (na in LEGP and nb in POUCHN|{'groin','pouchS'}) or (nb in LEGP and na in POUCHN|{'groin','pouchS'}):pair='leg-pouch'
      elif na in LEGP and nb in LEGP and sa in (0,1) and sb in (0,1) and sa!=sb:pair='leg-leg'
      elif 'gun' in (na,nb):
        other=nb if na=='gun' else na
        if other in CHEST|LEGP|{'paul','paul2','stripe','torso','groin','belt','thigh'} :pair='gun-'+other
      elif (na in ARMS and nb in LEGP|{'groin','belt','pouchS','nade','fuze','canteen'}) or (nb in ARMS and na in LEGP|{'groin','belt','pouchS','nade','fuze','canteen'}):pair='arm-hip/leg'
      if pair:
        n=hit(a,b)
        if n>LIM.get(pair.split('-')[0],.006):iss.append('%s %s x %s (%.0f mm)'%(pair,a.name,b.name,n*1000))
  for o in body:
    zs=[v.z for v in WV[o]]
    if zs and min(zs)<floor-.006:iss.append('below floor %s %.3f'%(o.name,min(zs)))
  print('\nQA %s: %d issues'%(label,len(iss)));[print('   ',x) for x in iss[:40]]
  return iss
