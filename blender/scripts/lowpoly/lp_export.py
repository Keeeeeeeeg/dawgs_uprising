# Phase B step 2: skeleton + weights + export of the low meshes to the game's skinned format (raw game coords: x fwd, y up,
# z right, mm), with UVs and normals; textures as tex/marine/<type>_<part>[L]_<map>.(jpg|png)
import json,base64,struct
KR=float(os.environ.get('KR','.812'))     # Blender metres -> raw game units (the old marine's hips at .80)
def cv(v):return Vector((-v.y*KR,v.z*KR,-v.x*KR))
J=P['_j'];Rp=P['pelvis'][1];up=Rp@Vector((0,0,1))
KIND=globals().get('KIND','rifle');gO,gR=P['gun'];WS=WSCALE.get(KIND,1)
SUPPORT=KIND in('can','spare','binos')
MUZ={'binos':(0,0,0),'can':(0,0,0),'spare':(.46,0,0),'rifle':(.86,0,.065),'mg':(1.27,0,.07),'rocket':(.84,0,.14),'sniper':(1.3,0,.09),'pistol':(.2,0,.03),'flag':(1.66,0,0)};MAGP={'binos':(0,0,0),'can':(0,0,-.1),'spare':(0,0,0),'rifle':(.13,0,-.1),'mg':(.14,.1,-.06),'rocket':(-.1,0,.14),'sniper':(-.2,0,-.05),'pistol':(-.03,0,-.06),'flag':(0,0,0)}
if os.environ.get('BOARD'):MUZ['rifle']=(.72,0,.065)   # the boarding shotgun
muz=gO+gR@(Vector(MUZ[KIND])*WS);magp=gO+gR@(Vector(MAGP[KIND])*WS)
toe={s:J['ank'+s]+Vector((0,-.2,-.05)) for s in 'RL'}
NKM=J['neck']+(J['headc']-J['neck'])*.45   # (polish 11-20) a NECK bone between the chest and the head: the head turn is shared, the collar/mask stop clipping, hoses bend
BON=[('hips',None,J['pelvis'],J['pelvis']+up*.15),('spine','hips',J['pelvis']+up*.15,J['chest']),('chest','spine',J['chest'],J['neck']),
 ('neck','chest',J['neck'],NKM),('head','neck',NKM,J['headc']+up*.12),('aim','chest',(J['shR']+J['shL'])/2,(J['shR']+J['shL'])/2+Vector((0,-.1,0)))]
for s in 'RL':BON+=[('thigh.'+s,'hips',J['hip'+s],J['knee'+s]),('shin.'+s,'thigh.'+s,J['knee'+s],J['ank'+s]),('foot.'+s,'shin.'+s,J['ank'+s],toe[s])]
for s in 'RL':BON+=[('arm.'+s,'chest',J['sh'+s],J['el'+s]),('fore.'+s,'arm.'+s,J['el'+s],J['wr'+s]),('hand.'+s,'fore.'+s,J['wr'+s],J['hand'+s])]
# (pass 10) armed: the gun pivots at the butt in the shoulder pocket (child of the chest) and the arms follow it by IK in the
# game; support kits: the carried item rides the right hand
GH=gO if SUPPORT else J['shR'] if KIND=='pistol' else gO+gR@BUTT[KIND]   # the officer's pistol swings from the shoulder
BON+=[('gun','hand.R' if SUPPORT else 'chest',GH,GH+gR@Vector((.2,0,0))),('mag','gun',magp,magp+gR@Vector((0,0,-.06)))]
SHH_=globals().get('SHH') or {}
if SHH_:   # (v5) the breacher's trifold shield: a hinge bone per wing (child of the shield's gun bone); the game swings them open
  for s_ in 'RL':BON.append(('wing.'+s_,'gun',SHH_[s_][0],SHH_[s_][1]))
NAMES=[b[0] for b in BON];IDX={n:i for i,n in enumerate(NAMES)}
SEG={n:(cv(h),cv(t)) for n,p,h,t in BON}
def segd(p,n):
  a,b=SEG[n];ab=b-a;t=max(0,min(1,(p-a).dot(ab)/max(1e-9,ab.length_squared)));return (p-(a+ab*t)).length
CHESTR={'rackcan','rackstrap','pec','pecEdge','spine','lame','collar','chestB','cumm','shStrap','strap','mags','flap','nade','fuze','radio','whipS','sheath','knife','ksnap','pack','packFlap','roll','rollStrap','etoolH','etoolB','etoolGrip','can','spare','spareCap','frame','case','fin','panel','dial','knob','toggle','lamp','batt','battCap','dish','dishHub','whip','whipBase','blade','cord','handset','cape','strip'}
HIPR={'belt','buckle','pouchS','canteen','groin','buttpack','bpFlap'}
INV={v:k for k,v in PARTS.items()}
def cands(part,side):
  S='R' if side in (0,10) else 'L'
  if part=='helmet':return ['head'],False
  if part=='weapon':return ['gun'],False
  if part=='torso':return ['hips','spine','chest'],True
  if part in('shield','chev','shStripe','shEdge','shPlate','shFrame','shSpine','shBolt','shBrow','shPad','port','hinge','gripPost','grip','stand'):return ['gun'],False
  if part=='ribhose':return ['chest','neck','head'],True
  if part=='neck':return ['chest','neck','head'],True
  if part in('wing','wPlate','wEdge','wHinge'):return ['wing.'+S],False
  if part=='hipF':return ['hips','thigh.'+S],True   # (polish) the pelvis runs down into the thigh
  if part=='crotch':return ['hips','thigh.R','thigh.L'],True   # (v3) the rebreather hoses bend from the back pack into the helmet
  if part=='hazF':return ['fore.'+S],False   # the breacher's shield rides the hand
  if part in('magplate','haz','jet','jetGlow'):return ['foot.'+S] if part!='haz' else ['shin.'+S],False
  if part in CHESTR:return ['chest'],False
  if part in HIPR:return ['hips'],False
  if part in('paul','paul2','stripe','paulS'):return ['arm.'+S],False
  if part in('uarm','elbow','armband','tape','patch'):return ['arm.'+S,'fore.'+S],True
  if part=='farm':return ['fore.'+S,'hand.'+S],True
  if part=='vamb':return ['fore.'+S],False
  if part in('glove','knuckle','finger','thumb'):return ['hand.'+S],False
  if part=='thigh':return ['hips','thigh.'+S,'shin.'+S],True
  if part in('thighP','cargo'):return ['thigh.'+S],False
  if part in('knee','kneeCap','kneeStrap','kneePad'):return ['shin.'+S],False
  if part=='shin':return ['thigh.'+S,'shin.'+S,'foot.'+S],True
  if part in('shinG','shinR','shinStrap'):return ['shin.'+S],False
  if part in('gaiter','shaft','boot','bootAnk','toecap','sole','lug','lace','tongue','heel','anklePl'):return ['foot.'+S],False
  return ['chest'],False
CONN={}
for n,p,h,t in BON:
  CONN.setdefault(n,{n});
  if p:CONN.setdefault(p,{p});CONN[n].add(p);CONN[p].add(n)
def shell_weights(lo):
  # (B2) skin weights for the continuous shell: each vertex takes the bones of the nearest high-poly source part (so a
  # pauldron vertex starts on the arm, a pec vertex on the chest), then weights diffuse a few rings across the surface,
  # only between connected bones (no left/right thigh bleed), and the two strongest are kept
  from mathutils.bvhtree import BVHTree
  me=lo.data;pl=me.attributes['part'].data;sid=PARTS.get('shell')
  if sid is None:return {}
  S=set()
  for p in me.polygons:
    if pl[p.index].value//16==sid:S.update(p.vertices)
  if not S:return {}
  dg2=bpy.context.evaluated_depsgraph_get();trees=[]
  for o in G['body']:
    if o.type!='MESH' or o.get('bake'):continue
    try:trees.append((BVHTree.FromObject(o,dg2),o.matrix_world.inverted(),o.name.split('.')[0],o.get('side',-1)))
    except Exception:pass
  W={}
  for vi in S:
    p=me.vertices[vi].co;best=None
    for t,mi,nm,sd in trees:
      h=t.find_nearest(mi@p,.2)
      if h[0] is not None and (best is None or h[3]<best[0]):best=(h[3],nm,sd)
    nm,sd=(best[1],best[2]) if best else ('torso',-1)
    cs,cloth=cands(nm,sd);gp=cv(p)
    if len(cs)==1:W[vi]={IDX[cs[0]]:1.0}
    else:
      ds=sorted((segd(gp,c),c) for c in cs);(d0,b0),(d1,b1)=ds[0],ds[1]
      if b1 in CONN[b0] and d1-d0<.05:w0=.5+.5*min(1,(d1-d0)/.05);W[vi]={IDX[b0]:w0,IDX[b1]:1-w0}
      else:W[vi]={IDX[b0]:1.0}
  nb={vi:set() for vi in S}
  for ed in me.edges:
    a,b=ed.vertices
    if a in S and b in S:nb[a].add(b);nb[b].add(a)
  prim={vi:max(W[vi],key=W[vi].get) for vi in S};NI={i:n for n,i in IDX.items()}
  for it in range(int(os.environ.get('SHELL_SMOOTH','5'))):
    W2={}
    for vi in S:
      ok={IDX[n] for n in CONN[NI[prim[vi]]]}
      if it>=2:   # (polish) the arm/chest blend stays narrow (2 rings): a wide blend stretched the shoulder texture when the arm swings
        pn_=NI[prim[vi]]
        if pn_.startswith('arm.'):ok.discard(IDX['chest'])
        elif pn_=='chest':ok-={IDX['arm.R'],IDX['arm.L']}
      acc=dict(W[vi]);c=1.0
      for u in nb[vi]:
        for b,w in W[u].items():
          if b in ok:acc[b]=acc.get(b,0)+w
        c+=1
      W2[vi]={b:w/c for b,w in acc.items()}
    W=W2
  out={}
  for vi,d in W.items():
    top=sorted(d.items(),key=lambda x:-x[1])[:2];s=sum(w for _,w in top)
    out[vi]=(top[0][0],top[1][0] if len(top)>1 else top[0][0],top[0][1]/s)
  print(' shell weights',len(out),'verts');return out
def export_mesh(lo,group):
  me=lo.data;me.calc_loop_triangles();uvl=me.uv_layers.active.data;att=me.attributes['part'].data;CN=me.corner_normals
  SHW=shell_weights(lo) if group=='body' else {}
  Pp=[];UV=[];N=[];SI=[];SW=[];n=0
  for tr in me.loop_triangles:
    code=att[tr.polygon_index].value;part=INV.get(code//16,'?');side=code%16-1
    if group in('helmet','weapon') and part not in('wing','wPlate','wEdge','wHinge'):part=group
    cs,cloth=cands(part,side)
    if part=='shell':
      for li,vi in zip(tr.loops,tr.vertices):
        p=cv(me.vertices[vi].co);u=uvl[li].uv;nn=cv(Vector(CN[li].vector)).normalized()
        Pp+=[int(round(c*1000)) for c in p];UV+=[int(round(max(0,min(1,u.x))*65535)),int(round(max(0,min(1,u.y))*65535))];N+=[max(-127,min(127,int(round(c*127)))) for c in nn]
        b0,b1,w0=SHW.get(vi,(IDX['chest'],IDX['chest'],1.0));SI+=[b0,b1];SW.append(int(round(w0*255)))
      n+=1;continue
    for li,vi in zip(tr.loops,tr.vertices):
      p=cv(me.vertices[vi].co);u=uvl[li].uv;nn=cv(Vector(CN[li].vector)).normalized()
      Pp+=[int(round(c*1000)) for c in p];UV+=[int(round(max(0,min(1,u.x))*65535)),int(round(max(0,min(1,u.y))*65535))];N+=[max(-127,min(127,int(round(c*127)))) for c in nn]
      if len(cs)==1 or not cloth:SI+=[IDX[cs[0]]]*2;SW.append(255)
      else:
        ds=sorted((segd(p,c),c) for c in cs);(d0,b0),(d1,b1)=ds[0],ds[1]
        con=dict((x[0],x[1]) for x in BON)
        if (con[b1]==b0 or con[b0]==b1) and d1-d0<.05:w0=.5+.5*min(1,(d1-d0)/.05);SI+=[IDX[b0],IDX[b1]];SW.append(int(round(w0*255)))
        else:SI+=[IDX[b0]]*2;SW.append(255)
    n+=1
  b64=lambda fmt,a:base64.b64encode(struct.pack(fmt%len(a),*a)).decode()
  return {'n':n,'p':b64('<%dh',Pp),'uv':b64('<%dH',UV),'nm':b64('<%db',N),'si':base64.b64encode(bytes(SI)).decode(),'sw':base64.b64encode(bytes(SW)).decode()}
res={'bones':[[n,(IDX[p] if p else -1),[round(c,4) for c in cv(h)]] for n,p,h,t in BON],'parts':{},'tex':TYPE,
     'rig':{'support':SUPPORT,'oneHand':KIND=='pistol','gfwd':[round(c,4) for c in (cv(gR@Vector((1,0,0)))/KR)],'gup':[round(c,4) for c in (cv(gR@Vector((0,0,1)))/KR)],'torso':[0,0,0],'arms':[0,0,0],'muz':[round(c,4) for c in cv(muz)],'mag':[round(c,4) for c in cv(magp)],**({'wings':{s_:[round(c,4) for c in (cv(SHH_[s_][1])-cv(SHH_[s_][0])).normalized()] for s_ in 'RL'}} if SHH_ else {})}}
for g in ('body','helmet','weapon'):
  if g=='weapon' and SHAREW:res['parts'][g]='rifle';continue
  res['parts'][g]=export_mesh(LOWS[g],g);print('\n export',g,res['parts'][g]['n'])
res['parts']['allL']=export_mesh(LOWS['allL'],'all');print(' export allL',res['parts']['allL']['n'])
json.dump(res,open(OUTD+'skin_%s.json'%TYPE,'w'))
# textures for the game: colour as JPG, normal + mask as PNG (mask: 256/128 is enough)
from PIL import Image
os.makedirs(OUTD+'tex',exist_ok=True)
from PIL import ImageEnhance
for g,L in (('body',''),('helmet',''),('weapon',''),('all','L')):
  if g=='weapon' and SHAREW:continue
  c=Image.open(OUTD+'%s%s_color.png'%(g,L)).convert('RGB')
  if g in('body','all'):c=ImageEnhance.Color(ImageEnhance.Contrast(c).enhance(1.3)).enhance(1.15)   # the camo bakes flat: lift it
  c.save(OUTD+'tex/%s_%s%s_c.jpg'%(TYPE,g,L),quality=86)
  Image.open(OUTD+'%s%s_normal.png'%(g,L)).convert('RGB').save(OUTD+'tex/%s_%s%s_n.jpg'%(TYPE,g,L),quality=90)
  m=Image.open(OUTD+'%s%s_mask.png'%(g,L)).convert('RGB');m=m.resize((m.width//2,m.height//2));m.save(OUTD+'tex/%s_%s%s_m.png'%(TYPE,g,L),optimize=True)
