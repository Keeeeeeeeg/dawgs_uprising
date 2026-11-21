# (v13) helmet that FLOWS with the visor: the shell is moulded into a soft channel round the red-line outline, its face
# edge follows the visor's lower line and sweeps down the cheeks, and a rubber gasket runs the full border of the window.
# Smoothed lens (least-squares fitted surface: no wavy reflections), darker smoked team-colour lens.
# Head kinds: helmet(V,off) with V['cap'] 'full' | 'skull' (cut-down shell under a boonie). sniper_head / spotter_head.
import numpy as np, random
exec(open('/home/claude/hm/helmet12.py').read().split('def helmet(')[0])
GH1=M('ghillie',(.055,.065,.03),.95);GH2=M('ghillie2',(.1,.09,.045),.95);GH3=M('ghillie3',(.035,.04,.02),.95);BOON=M('boonie',(.06,.07,.04),.9)
def cloth(name,col,sc=300):
  m=M(name,col,.95);nt=m.node_tree;N=nt.nodes;b=N['Principled BSDF'];tc=N.new('ShaderNodeTexCoord');w=N.new('ShaderNodeTexWave');w.inputs['Scale'].default_value=sc;w.inputs['Distortion'].default_value=4
  nt.links.new(tc.outputs['Object'],w.inputs['Vector']);bu=N.new('ShaderNodeBump');bu.inputs['Strength'].default_value=.35;nt.links.new(w.outputs['Fac'],bu.inputs['Height']);nt.links.new(bu.outputs['Normal'],b.inputs['Normal']);return m
SCARF=cloth('scarf',(.07,.075,.05))
def lensmat(i,tc):return M('lens%d'%i,tuple(c*.2 for c in tc),.04,.6)
NU,NV=160,90;H0,A,Bh=-.115,.118,.135;VX=.118
def _sq(x):return max(0,1-(abs(x)/VX)**6)**(1/6)
def vtop(x):
  t=.034-.022*(x/VX)**2;b0=-.046+.024*(x/VX)**2;m=(t+b0)/2;return m+(t-m)*_sq(x)
def vbot(x):
  t=.034-.022*(x/VX)**2;b0=-.046+.024*(x/VX)**2;m=(t+b0)/2;return m+(b0-m)*_sq(x)+.03*math.exp(-(x/.024)**2)*_sq(x)
OUT=[]
for i in range(121):x=-VX+2*VX*i/120;OUT.append((x,vbot(x)))
for i in range(119,0,-1):x=-VX+2*VX*i/120;OUT.append((x,vtop(x)))
OUTA=np.array(OUT)
def inside(x,z):return abs(x)<VX and vbot(x)<z<vtop(x)
def odist(x,z):return float(np.min(np.hypot(OUTA[:,0]-x,OUTA[:,1]-z)))
def faceedge(x):   # top of the face opening: 1.6 cm under the visor's lower line, sweeping down the cheeks past the visor ends
  ax=abs(x)
  if ax<=VX:return vbot(x)-.016
  return vbot(math.copysign(VX,x))-.016-.11*min(1,(ax-VX)/.05)**1.6
def helmet(V,off,lens=None):
  objs=[];H1=.128 if V.get('cap','full')=='full' else .096
  def L(name,bm,mat,**k):
    o=link(name,bm,mat,**k);o.location=off;objs.append(o);return o
  def prof(z,c):
    if z>=0:t=z/H1;return (1-min(1,t)**2.4)**(1/2.4)
    fl=.55+.75*(1-max(0,c));w=1-.03*math.exp(-((z+.012)/.008)**2);return w*(1+fl*(-z)**1.35*1.6)
  def front_y(x,z,inset):
    k=prof(z,1.0);e=2/2.3;u=min(.999,abs(x)/(A*k));sn=u**(1/e);c=max(0,1-sn*sn)**.5
    return -(Bh*k*c**e)-.004+inset
  bm=bmesh.new();rings=[]
  for j in range(NV+1):
    z=H0+(H1-H0)*j/NV;ring=[]
    for i in range(NU):
      a=i/NU*2*math.pi;c,sn=math.cos(a),math.sin(a);e=2/2.3;k=prof(z,-c)
      x,y=A*k*math.copysign(abs(sn)**e,sn),Bh*k*math.copysign(abs(c)**e,c)-.004
      # MOULD: press the shell into a soft channel round the visor (deepest at the window, fading out over 2.6 cm)
      if y<-.03 and -.09<z<.09:
        d=0 if inside(x,z) else odist(x,z);s=max(0,1-d/.026);s=s*s*(3-2*s);y+=.0075*s*(-y/.14)
      ring.append(bm.verts.new((x,y,z)))
    rings.append(ring)
  for j in range(NV):
    for i in range(NU):bm.faces.new((rings[j][i],rings[j][(i+1)%NU],rings[j+1][(i+1)%NU],rings[j+1][i]))
  top=bm.verts.new((0,-.004,H1));[bm.faces.new((rings[NV][i],rings[NV][(i+1)%NU],top)) for i in range(NU)];bm.faces.new(list(reversed(rings[0])))
  bmesh.ops.recalc_face_normals(bm,faces=bm.faces);sh=L('shell',bm,SHELL)
  def prism(outline,y0,y1,name):
    bm=bmesh.new();fv=[bm.verts.new((x,y0,z)) for x,z in outline];bv=[bm.verts.new((x,y1,z)) for x,z in outline]
    bm.faces.new(fv);bm.faces.new(list(reversed(bv)));n=len(outline)
    for i in range(n):bm.faces.new((fv[i],fv[(i+1)%n],bv[(i+1)%n],bv[i]))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces);o=link(name,bm,DARK);o.location=off;o.hide_render=True;return o
  # face opening that follows the visor (no more box cut): curve along the visor's lower line, down the cheeks
  fo=[(x,faceedge(x)) for x in np.linspace(-.17,.17,141)]+[(.17,-.3),(-.17,-.3)]
  win=[(x,z-.002) for x,z in OUT[:121]]+[(x,z+.002) for x,z in OUT[121:]]
  WC=prism(win,-.3,-.06,'wcut')
  for c in [prism(fo,-.3,-.035,'fcut'),link('cut',box((0,0,-.2),(.5,.6,.17)),DARK),WC]:
    c.location=off;c.hide_render=True
    m=sh.modifiers.new('bo','BOOLEAN');m.object=c;m.operation='DIFFERENCE';m.solver='EXACT'
  so=sh.modifiers.new('s','SOLIDIFY');so.thickness=.012;so.offset=-1
  # smooth lens: fit y(x,z) = sum c * x^2i * z^j to the moulded contour, then sit it 1.5 cm behind
  X,Z,Y=[],[],[]
  for x in np.linspace(-VX-.012,VX+.012,40):
    for z in np.linspace(-.07,.05,20):X.append(x);Z.append(z);Y.append(front_y(x,z,0))
  X,Z,Y=map(np.array,(X,Z,Y));Bm=np.stack([X**(2*i)*Z**j for i in range(4) for j in range(4)],1);C=np.linalg.lstsq(Bm,Y,rcond=None)[0]
  def fy(x,z):return float(sum(C[i*4+j]*x**(2*i)*z**j for i in range(4) for j in range(4)))
  def sheet(inset,mat,name,pad=0.0):
    bm=bmesh.new();NXs,NZs=140,30;G2=[]
    for i in range(NXs+1):
      x=-(VX+pad)+2*(VX+pad)*i/NXs;lo=vbot(x)-.004-pad;hi=vtop(x)+.004+pad;G2.append([bm.verts.new((x,fy(x,lo+(hi-lo)*j/NZs)+inset,lo+(hi-lo)*j/NZs)) for j in range(NZs+1)])
    for i in range(NXs):
      for j in range(NZs):bm.faces.new((G2[i][j],G2[i+1][j],G2[i+1][j+1],G2[i][j+1]))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces);o=L(name,bm,mat);s2=o.modifiers.new('s','SOLIDIFY');s2.thickness=.003;return o
  sheet(.016,lens or VIS,'lens');sheet(.03,DARK,'liner',pad=.005)
  # gasket: rubber bead round the WHOLE window border, bedded where the shell meets the lens
  bm=bmesh.new();rings2=[];P=[(x,z) for x,z in OUT];n=len(P);RS=8
  for i in range(n):
    x,z=P[i];xa,za=P[(i-1)%n];xb,zb=P[(i+1)%n];tx,tz=xb-xa,zb-za;l=math.hypot(tx,tz);tx/=l;tz/=l;nx,nz=tz,-tx   # in-plane normal (outward)
    cx,cz=x+nx*.002,z+nz*.002;y=fy(cx,cz)+.007
    rings2.append([bm.verts.new((cx+nx*.0045*math.cos(a2),y-.0045*math.sin(a2),cz+nz*.0045*math.cos(a2))) for a2 in [k/RS*2*math.pi for k in range(RS)]])
  for i in range(n):
    a_,b_=rings2[i],rings2[(i+1)%n]
    for k in range(RS):bm.faces.new((a_[k],a_[(k+1)%RS],b_[(k+1)%RS],b_[k]))
  bmesh.ops.recalc_face_normals(bm,faces=bm.faces);L('gasket',bm,RUB)
  if V.get('scanner'):
    # (v16) SCANNER add-on: a modular side unit clamped over the right ear, a hinged arm, and a swing-down monocle screen in
    # front of the right eye in the army colour with faint HUD marks (replaces the plain green eyepiece)
    tc=V.get('scancol',(.25,.75,.3));SCN=M('scanner',tuple(c*.55 for c in tc),.06,.2,1.6)
    L('scnMod',box((-.153,.0,.012),(.03,.075,.052)),PLATE,bev=.006);L('scnClamp',box((-.142,.0,.045),(.016,.06,.012)),DARK,bev=.003)
    bmh=bmesh.new();bmesh.ops.create_cone(bmh,cap_ends=True,segments=14,radius1=.012,radius2=.012,depth=.02);bmesh.ops.rotate(bmh,cent=(0,0,0),matrix=Matrix.Rotation(1.5708,3,'Y'),verts=bmh.verts);bmesh.ops.translate(bmh,vec=(-.17,-.03,.025),verts=bmh.verts);L('scnHinge',bmh,METL)
    sx0,sz0=-.062,.004;sy0=fy(sx0,sz0)-.026
    for dx in (0,-.008):
      pass
    facet('scnArm',[(-.172+d,-.03,.033) for d in (0,.009)]+[(-.172+d,-.03,.017) for d in (0,.009)]+[(-.158+d,-.135,.03) for d in (0,.009)]+[(-.158+d,-.135,.016) for d in (0,.009)],DARK,off,objs,bev=.002)
    facet('scnArm2',[(-.158+d,-.135,.03) for d in (0,.009)]+[(-.158+d,-.135,.016) for d in (0,.009)]+[(-.098,sy0-.004+d,.028) for d in (0,.009)]+[(-.098,sy0-.004+d,.014) for d in (0,.009)],DARK,off,objs,bev=.002)
    R=Matrix.Rotation(-.32,3,'Z')
    L('scnFrame',box((sx0,sy0,sz0),(.066,.008,.048),R),DARK,bev=.004)
    L('scnLens',box((sx0-.0,sy0-.0045,sz0),(.056,.002,.038),R),SCN)
    for k,(hx,hz,w) in enumerate(((-.012,.008,.018),(.008,-.006,.012),(.0,-.013,.026))):L('scnHud',box((sx0+hx,sy0-.0058,sz0+hz),(w,.0006,.0015),R),EYE)
  else:L('eye',box((-.058,fy(-.058,.006)+.014,.006),(.026,.002,.016),Matrix.Rotation(-.35,3,'Z')),EYE)
  # (v14) the mask is ONE PIECE with the shell: its top is a row of points buried in the shell lip all along the face edge,
  # the snout grows forward and down from there, then it is boolean-UNIONED into the solidified shell (chin module too) and
  # the visor window is cut AGAIN through the result, so no mask material can ever reach into the lens (no nose-bridge clip).
  Mp=[]
  for x in np.linspace(-.125,.125,9):
    ze=faceedge(x)+.007;Mp.append((x,front_y(x,ze,.006),ze))
  for sx in (1,-1):Mp+=[(sx*.13,.0,-.06),(sx*.128,.0,-.11),(sx*.12,-.07,-.062),(sx*.11,-.075,-.13),(sx*.08,-.128,-.064),(sx*.06,-.15,-.16),(sx*.034,-.152,-.054),(sx*.024,-.2,-.165)]
  Mp+=[(0,-.156,-.04),(0,-.215,-.1),(0,-.212,-.172),(0,-.17,-.19)]
  # robust version (EXACT union of shell + hull failed on some point sets): the mask and chin are their own meshes in the
  # SAME steel, their top rows buried 6 mm deep in the shell lip, and each is trimmed by the visor window prism (a convex
  # hull minus a prism is always clean), so they read as one piece and can never reach into the lens.
  bv=sh.modifiers.new('b','BEVEL');bv.width=.003;bv.segments=3;bv.limit_method='ANGLE';bv.angle_limit=.5
  for nm,bmx in (('mask',hull(Mp)),('chin',box((0,-.205,-.15),(.05,.03,.04) if V.get('chin','filter')=='filter' else (.044,.03,.045),Matrix.Rotation(.35,3,'X')))):
    o=link(nm,bmx,SHELL,smooth=False);o.location=off;objs.append(o);o.modifiers.clear()
    m=o.modifiers.new('w','BOOLEAN');m.object=WC;m.operation='DIFFERENCE';m.solver='EXACT'
    b=o.modifiers.new('b','BEVEL');b.width=.004;b.segments=2;b.limit_method='ANGLE';b.angle_limit=.6
    dg=bpy.context.evaluated_depsgraph_get();n=len(o.evaluated_get(dg).data.polygons)
    if n<20:print('WARN',nm,n);m.solver='FLOAT'
  for sx in (1,-1):
    L('slotV',box((sx*.105,-.1,-.098),(.006,.012,.06),Matrix.Rotation(sx*.75,3,'Z')),DARK,bev=.002)
    for i in range(V.get('vents',0)+1):L('vent',box((sx*(.127-i*.006),-.025-i*.018,-.09),(.005,.012,.032),Matrix.Rotation(sx*(.2+i*.2),3,'Z')),DARK,bev=.002)
  if V.get('chin','filter')=='filter':L('chinF',box((0,-.222,-.152),(.034,.004,.024),Matrix.Rotation(.35,3,'X')),DARK,bev=.002)
  else:L('chinF',box((0,-.221,-.152),(.03,.004,.03),Matrix.Rotation(.35,3,'X')),DARK,bev=.004)
  for sx in (1,-1):L('ear',box((sx*.13,.012,-.03),(.018,.055,.05)),PLATE,bev=.008)
  if V.get('side')=='lamp':L('lamp',box((.148,-.02,.01),(.018,.04,.022)),DARK,bev=.003)
  if V.get('side')=='antenna':L('ant',box((-.14,.05,.13),(.003,.003,.26),Matrix.Rotation(-.25,3,'X')),DARK)
  if V.get('top')=='mount':
    L('mount',box((0,-.105,.085),(.06,.03,.01),Matrix.Rotation(-.75,3,'X')),DARK,bev=.003);L('mountP',box((0,-.1,.08),(.075,.045,.006),Matrix.Rotation(-.75,3,'X')),PLATE,bev=.002)
  if V.get('top')=='nvg':
    for sx in (1,-1):L('tube',box((sx*.02,-.13,.1),(.022,.04,.022),Matrix.Rotation(-.4,3,'X')),DARK,bev=.004)
  L('neck',box((0,.0,-.16),(.15,.15,.07)),RUB,bev=.03)
  return objs,prof,H1
def tuft(L,r,x,y,z,a2,tilt,ln=None):
  ln=ln or r.uniform(.03,.08);w=r.uniform(.012,.024)
  rot=Matrix.Rotation(-a2,3,'Z')@Matrix.Rotation(tilt,3,'X')@Matrix.Rotation(r.uniform(-.5,.5),3,'Y')
  L('tuft',box((x,y,z-ln*.35),(w,.003,ln),rot),(GH1,GH2,GH3)[r.randrange(3)])
def sniper_head(off,lens):
  objs,prof,H1=helmet({'cap':'skull','vents':0,'chin':'filter'},off,lens);r=random.Random(7)
  def L(name,bm,mat,**k):
    o=link(name,bm,mat,**k);o.location=off;objs.append(o);return o
  # boonie sized to the skull cap: elliptical crown, brim flat at the front (clears the visor), drooping at the sides
  bm=bmesh.new();Nb=64;RR=[]
  for j in range(13):
    t=j/12;z=.05+.088*math.sin(t*math.pi/2)**.8;k=1-.1*t-.55*t**6
    RR.append([bm.verts.new((math.sin(i/Nb*2*math.pi)*.134*k,math.cos(i/Nb*2*math.pi)*.152*k-.004,z-.012*(1-math.cos(i/Nb*4*math.pi))*t**4)) for i in range(Nb)])
  for j in range(12):
    for i in range(Nb):bm.faces.new((RR[j][i],RR[j][(i+1)%Nb],RR[j+1][(i+1)%Nb],RR[j+1][i]))
  tp=bm.verts.new((0,-.004,.124));[bm.faces.new((RR[12][i],RR[12][(i+1)%Nb],tp)) for i in range(Nb)]
  bmesh.ops.recalc_face_normals(bm,faces=bm.faces);L('crown',bm,BOON)
  bm=bmesh.new();inner=[];outer=[]
  for i in range(Nb):
    a2=i/Nb*2*math.pi;s,c=math.sin(a2),math.cos(a2);dr=-.006-.03*abs(s)**1.5*(1 if c<.3 else 1-((c-.3)/.7))
    inner.append(bm.verts.new((s*.134,c*.152-.004,.052)));outer.append(bm.verts.new((s*.212,c*.232-.004,.052+dr)))
  for i in range(Nb):bm.faces.new((inner[i],inner[(i+1)%Nb],outer[(i+1)%Nb],outer[i]))
  o=L('brim',bm,BOON);o.modifiers.new('s','SOLIDIFY').thickness=.006
  bm=bmesh.new();a=[];b=[]
  for i in range(Nb):
    a2=i/Nb*2*math.pi;s,c=math.sin(a2),math.cos(a2);a.append(bm.verts.new((s*.136,c*.154-.004,.055)));b.append(bm.verts.new((s*.133,c*.15-.004,.072)))
  for i in range(Nb):bm.faces.new((a[i],a[(i+1)%Nb],b[(i+1)%Nb],b[i]))
  L('band',bm,GH1)
  # ghillie: crown + brim + mantle, FRAMING the mask (strips hang down the cheeks; visor and snout stay clear)
  for i in range(560):
    a2=r.uniform(0,2*math.pi);rad=min(r.uniform(0,.21)**.8*1.1,.21);z=(.142-.4*max(0,rad-.07)**1.5 if rad<.135 else .1-rad*.25)+r.uniform(-.004,.01);tilt=r.uniform(.3,1.1) if rad>.135 else r.uniform(1.0,1.5)
    if r.random()<.45:a2=r.uniform(-math.pi*.72,math.pi*.72);rad=r.uniform(.13,.2);z=r.uniform(-.2,.04);tilt=r.uniform(.05,.45)
    x,y=math.sin(a2)*rad,math.cos(a2)*rad
    if y<-.06 and abs(x)<.105:continue          # visor + snout clear
    if y<-.12 and z<.05:continue
    ln=None
    if y<-.03 and abs(x)>=.105 and rad>.14:ln=r.uniform(.06,.11);tilt=r.uniform(.05,.3)   # long strips hanging down the cheeks
    tuft(L,r,x,y,z,a2,tilt,ln)
  bm=bmesh.new();G2=[]
  for j in range(9):
    t=j/8;G2.append([bm.verts.new((math.sin(a2)*(.15+.05*t),math.cos(a2)*(.165+.06*t),.045-.25*t)) for a2 in [(-.62+1.24*i/24)*math.pi for i in range(25)]])
  for j in range(8):
    for i in range(24):bm.faces.new((G2[j][i],G2[j][i+1],G2[j+1][i+1],G2[j+1][i]))
  o=L('drape',bm,GH3);o.modifiers.new('s','SOLIDIFY').thickness=.005
  for i in range(30):
    a2=r.uniform(0,2*math.pi);rad=r.uniform(.08,.2);x,y=math.sin(a2)*rad,math.cos(a2)*rad
    if y<-.06:continue
    bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=1,radius=.025);bmesh.ops.scale(bm,vec=(1,1,.5),verts=bm.verts);bmesh.ops.translate(bm,vec=(x,y,.11-rad*.25),verts=bm.verts);L('leaf',bm,GH3 if r.random()<.5 else GH1,smooth=False)
  return objs
def spotter_head(off,lens):
  objs,prof,H1=helmet({'cap':'full','vents':1,'chin':'round','side':'antenna','scanner':True,'scancol':globals().get('SCANCOL',(.25,.75,.3))},off,lens);r=random.Random(11)
  def L(name,bm,mat,**k):
    o=link(name,bm,mat,**k);o.location=off;objs.append(o);return o
  # helmet net + a light sprig of ghillie on the crown and the back of the skirt (same family, lighter than the sniper)
  for i in range(170):
    a2=r.uniform(0,2*math.pi);z=r.uniform(-.06,H1*.95);k=prof(z,-math.cos(a2))*1.02;x,y=math.sin(a2)*A*k,math.cos(a2)*Bh*k
    if y<-.05 and z<.07:continue
    tuft(L,r,x,y,z+.02,a2,r.uniform(.35,.8) if z>.05 else r.uniform(.1,.4),r.uniform(.035,.065))
  # scrim scarf wrapped twice round the neck and the bottom of the mask, tail over the left shoulder
  for wrap,(zc,rx,ry,th) in enumerate(((-.17,.148,.168,.016),(-.198,.156,.166,.018))):
    bm=bmesh.new();Ns=72;RS=10;rings=[]
    for i in range(Ns):
      a2=i/Ns*2*math.pi;s,c=math.sin(a2),math.cos(a2);lump=1+.18*math.sin(a2*5+wrap*2)+.1*math.sin(a2*11);cz=zc+.012*math.sin(a2*3+wrap)
      if c<-.2:cz-=.02*(-c)   # dips under the chin
      cx,cy=s*rx,c*ry;rings.append([bm.verts.new((cx+s*th*lump*math.cos(b2),cy+c*th*lump*math.cos(b2),cz+th*1.5*lump*math.sin(b2))) for b2 in [k/RS*2*math.pi for k in range(RS)]])
    for i in range(Ns):
      for k in range(RS):bm.faces.new((rings[i][k],rings[i][(k+1)%RS],rings[(i+1)%Ns][(k+1)%RS],rings[(i+1)%Ns][k]))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces);L('scarf',bm,SCARF)
  bm=bmesh.new();G2=[]
  for j in range(13):
    t=j/12;row=[]
    for i in range(6):w=-.035+.07*i/5;row.append(bm.verts.new((-.1-.05*t+w*.8,.12+.06*t+w*.3,-.19-.17*t+.012*math.sin(t*9+i))))
    G2.append(row)
  for j in range(12):
    for i in range(5):bm.faces.new((G2[j][i],G2[j][i+1],G2[j+1][i+1],G2[j+1][i]))
  o=L('tail',bm,SCARF);o.modifiers.new('s','SOLIDIFY').thickness=.008
  # binocular pouch strap across the chest top as a small spotter tell
  L('bino',box((.07,-.08,-.25),(.09,.05,.04)),DARK,bev=.008)
  return objs
# (v17) OFFICER: a peaked service cap over the skull-cap shell and the standard visor + angular mask (army-colour lens),
# with vent grilles on the mask cheeks. Original badge: a gold ring round a green roundel with a four-point star.
PATENT=M('patent',(.012,.012,.014),.12,.2);CAPC=cloth('capcloth',(.07,.078,.055),420);GOLDM=M('gold',(.62,.45,.14),.3,.95);BADGE=M('badgegreen',(.1,.35,.12),.35,.3)
def officer_head(off,lens):
  objs,prof,H1=helmet({'cap':'skull','vents':0,'chin':'filter'},off,lens)
  def L(name,bm,mat,**k):
    o=link(name,bm,mat,**k);o.location=off;objs.append(o);return o
  Nc=64
  def ring(z,a,b,lift=0.0):return [Vector((math.sin(t)*a,math.cos(t)*b-.004,z+lift*max(0,-math.cos(t))**1.5)) for t in [i/Nc*2*math.pi for i in range(Nc)]]
  # crown: from the band up to a wide oval top that rises at the front (the saddle of a service cap)
  R=[ring(.088,.134,.15),ring(.11,.146,.168,.012),ring(.13,.158,.182,.03),ring(.142,.162,.186,.045),ring(.148,.158,.18,.05)]
  bm=bmesh.new();V=[[bm.verts.new(p) for p in r] for r in R]
  for j in range(len(V)-1):
    for i in range(Nc):bm.faces.new((V[j][i],V[j][(i+1)%Nc],V[j+1][(i+1)%Nc],V[j+1][i]))
  c=bm.verts.new((0,-.03,.165));[bm.faces.new((V[-1][i],V[-1][(i+1)%Nc],c)) for i in range(Nc)]
  bm.faces.new([V[0][i] for i in reversed(range(Nc))]);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);L('crown',bm,CAPC)
  # band
  bm=bmesh.new();A=[bm.verts.new(p) for p in ring(.048,.133,.149)];B=[bm.verts.new(p) for p in ring(.09,.136,.152)]
  for i in range(Nc):bm.faces.new((A[i],A[(i+1)%Nc],B[(i+1)%Nc],B[i]))
  bmesh.ops.recalc_face_normals(bm,faces=bm.faces);o=L('band',bm,DARK);o.modifiers.new('s','SOLIDIFY').thickness=.006
  # visor brim: the front half of an annulus, angled down over the eyes
  bm=bmesh.new();inn=[];out=[]
  for i in range(25):
    t=math.pi*(.5+i/24);a=math.sin(t);b=math.cos(t)
    inn.append(bm.verts.new((a*.135,b*.151-.004,.05)));out.append(bm.verts.new((a*.15,b*.151-.004-.075*max(0,-b)**1.2,.05-.028*max(0,-b))))
  for i in range(24):bm.faces.new((inn[i],inn[i+1],out[i+1],out[i]))
  o=L('brim',bm,PATENT);o.modifiers.new('s','SOLIDIFY').thickness=.006
  # chin cord across the front of the band, with buttons
  bm=bmesh.new();pr=None
  for i in range(31):
    t=math.pi*(.62+.76*i/30);p=Vector((math.sin(t)*.1405,math.cos(t)*.1565-.004,.072))
    rr=[bm.verts.new(p+Vector((0,.003*math.cos(a2),.003*math.sin(a2)))) for a2 in [k/6*6.283 for k in range(6)]]
    if pr:[bm.faces.new((pr[k],pr[(k+1)%6],rr[(k+1)%6],rr[k])) for k in range(6)]
    pr=rr
  L('cord',bm,GOLDM)
  for sx in (1,-1):
    t=math.pi*(1+sx*.38);b2=bmesh.new();bmesh.ops.create_uvsphere(b2,u_segments=10,v_segments=6,radius=.007);bmesh.ops.translate(b2,vec=(math.sin(t)*.139,math.cos(t)*.155-.004,.072),verts=b2.verts);L('button',b2,GOLDM)
  # badge on the raised front of the crown
  ctr=Vector((0,-.18,.135));n=Vector((0,-1,.25)).normalized()
  def disc(r,d,mat,name,seg=32,off2=0):
    b2=bmesh.new();bmesh.ops.create_cone(b2,cap_ends=True,segments=seg,radius1=r,radius2=r,depth=d)
    bmesh.ops.transform(b2,matrix=Matrix.Translation(ctr+n*off2)@n.to_track_quat('Z','Y').to_matrix().to_4x4(),verts=b2.verts);return L(name,b2,mat)
  disc(.026,.01,GOLDM,'badgeR');disc(.02,.006,BADGE,'badgeC',off2=.004)
  st=[];Rq=n.to_track_quat('Z','Y').to_matrix()
  for k in range(8):
    a2=k/8*6.283;rr=.014 if k%2==0 else .005;st.append(ctr+n*.0075+Rq@Vector((math.sin(a2)*rr,math.cos(a2)*rr,0)))
  b2=bmesh.new();vs=[b2.verts.new(p) for p in st];b2.faces.new(vs);r2=bmesh.ops.extrude_face_region(b2,geom=b2.faces[:]);bmesh.ops.translate(b2,vec=n*.0015,verts=[g for g in r2['geom'] if isinstance(g,bmesh.types.BMVert)]);L('star',b2,GOLDM)
  # vent grilles on the mask cheeks (the reference's side vents), three slats each side
  for sx in (1,-1):
    L('grilleB',box((sx*.118,-.072,-.1),(.012,.05,.06),Matrix.Rotation(sx*.62,3,'Z')),DARK,bev=.003)
    for k in range(3):L('slat',box((sx*(.123+.0),-.068-.0,-.08-k*.018),(.008,.05,.006),Matrix.Rotation(sx*.62,3,'Z')),PLATE,bev=.0015)
  return objs
