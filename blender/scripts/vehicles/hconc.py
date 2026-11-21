# Heavy tank silhouette concepts (quick blockouts): 4 articulated track pods + twin cannons; three hull/turret ideas.
# A tall blocky fortress, B low wide brute, C stepped ziggurat. ~7.6 m. Renders each alone (same cameras) for a lineup.
import os,sys
exec(open('/home/claude/veh/vlib.py').read())
OLIVE=(.07,.078,.055)
PAINT=vpaint('paint',OLIVE,mud=1.4,wear=1.2,dust=1.2,rust=.6,hk=1.2);STEEL=M('steel',(.04,.041,.043),.42,.7);TRK=M('trk',(.05,.047,.043),.6,.6)
TEAM=M('team',(.05,.24,.04),.65);GLOW=M('glow',(.35,1,.5),.2,0,6)
def H(pts,mat=None,bev=.02):return link('p',hull(pts),mat or PAINT,bev=bev)
def B(c,s,mat=None,bev=.02):return link('b',xf(box((0,0,0),s),Matrix.Translation(c)),mat or PAINT,bev=bev)
def pods(L=2.5,Hh=.95,W=.75,X=2.05,Y=1.75,leg=True):
  for sx in (1,-1):
    for sy in (1,-1):
      x0=sx*X;y0=sy*Y;r=Hh/2
      # track loop = rounded slab, link band, wheels showing on the outside, armoured pod top
      pts=[(x0+dx*(L/2-r)+r*math.cos(a)*(1 if dx>0 else -1),y,r+.04+r*math.sin(a)) for dx in (1,-1) for a in [k*math.pi/6-math.pi/2 for k in range(7)] for y in (y0-W/2,y0+W/2)]
      link('trk',hull(pts),TRK,bev=.015)
      for k in range(4):xw=x0-L/2+r+k*(L-2*r)/3;link('wheel',cyl((xw,y0+sy*(W/2-.02),r+.04),(xw,y0+sy*(W/2+.04),r+.04),r*.62,20),STEEL,bev=.006)
      H([(x0+dx,y0+dy,z) for dx in (-L/2+.15,L/2-.15) for dy in (-W/2-.06,W/2+.06) for z in (Hh*.72,Hh+.12)],PAINT)   # pod armour top
      H([(x0+dx*.9*L/2,y0+sy*(W/2+.07),z) for dx in (-1,1) for z in (Hh*.35,Hh+.1)]+[(x0+dx*.85*L/2,y0+sy*(W/2+.12),z) for dx in (-1,1) for z in (Hh*.45,Hh+.05)],PAINT)   # side plate
      if leg:   # armoured leg/pivot from the pod to the hull
        H([(x0+dx,y,z) for dx in (-.35,.35) for y in (y0-sy*W/2,sy*1.05) for z in (Hh*.55,Hh+.35)],PAINT)
        link('pivot',cyl((x0,sy*1.05,Hh*.85),(x0,y0-sy*W/2,Hh*.85),.28,16),STEEL,bev=.01)
def guns(TX,ZG,Lg=3.6,sep=.32,mantW=.9):
  B((TX+1.5,0,ZG),(.4,mantW,.55))
  for sy in (1,-1):
    link('sleeve',cyl((TX+1.6,sy*sep,ZG),(TX+2.6,sy*sep,ZG),.11,20),PAINT,bev=.005)
    link('barrel',cyl((TX+2.6,sy*sep,ZG),(TX+1.6+Lg,sy*sep,ZG),.075,18),STEEL,bev=.004)
    link('brake',cyl((TX+1.6+Lg,sy*sep,ZG),(TX+1.9+Lg,sy*sep,ZG),.11,8),STEEL,bev=.006)
def concept(k):
  if k=='A':   # tall blocky fortress
    pods(leg=True)
    H([(x,s*y,z) for s in (1,-1) for x,y,z in ((3.4,1.25,1.0),(3.7,1.0,1.25),(3.2,1.2,2.25),(-3.6,1.45,1.0),(-3.6,1.45,2.35),(1.6,1.45,2.45),(-3.75,1.3,1.4))])
    for s in (1,-1):B((0,s*1.62,1.55),(6.4,.12,1.05))   # full slab skirts over the legs
    TX=-.2;H([(TX+x,s*y,z) for s in (1,-1) for x,y,z in ((1.4,.75,2.4),(1.55,.6,3.25),(.8,1.25,2.4),(.8,1.2,3.4),(-1.7,1.25,2.4),(-1.7,1.15,3.45),(-2.1,1.0,2.6),(-2.1,.95,3.3))])
    B((TX-.3,0,3.5),(.9,.9,.25));guns(TX,2.9,Lg=3.4)
    B((TX,1.24,3.05),(1.6,.03,.12),TEAM,0)
  elif k=='B':   # low wide brute
    pods(L=2.8,Hh=.85,W=.85,X=2.2,Y=1.95,leg=True)
    H([(x,s*y,z) for s in (1,-1) for x,y,z in ((4.0,1.2,.75),(4.05,1.0,.95),(2.2,1.35,1.75),(-3.8,1.6,.8),(-3.8,1.5,1.75),(1.0,1.6,1.8),(-3.95,1.45,1.1))])
    TX=-.6;H([(TX+x,s*y,z) for s in (1,-1) for x,y,z in ((1.6,.55,1.75),(1.35,.5,2.3),(.9,1.55,1.75),(.6,1.4,2.35),(-1.9,1.6,1.75),(-1.9,1.45,2.35),(-2.3,1.2,1.8),(-2.3,1.1,2.3))])
    guns(TX-.05,2.05,Lg=4.0,mantW=1.0);B((TX,1.53,2.1),(1.8,.03,.1),TEAM,0)
  else:   # stepped ziggurat
    pods(leg=True)
    H([(x,s*y,z) for s in (1,-1) for x,y,z in ((3.5,1.3,.95),(3.6,1.1,1.3),(-3.6,1.5,.95),(-3.6,1.5,1.4),(3.3,1.4,1.4))])
    H([(x,s*y,z) for s in (1,-1) for x,y,z in ((2.6,1.15,1.38),(2.4,1.05,1.85),(-3.3,1.3,1.38),(-3.2,1.25,1.85))])
    H([(x,s*y,z) for s in (1,-1) for x,y,z in ((1.4,.95,1.83),(1.2,.9,2.25),(-2.8,1.1,1.83),(-2.7,1.05,2.25))])
    TX=-.4;H([(TX+x,s*y,z) for s in (1,-1) for x,y,z in ((1.3,.9,2.23),(1.2,.85,2.65),(-1.8,1.15,2.23),(-1.8,1.1,2.65))])
    H([(TX+x,s*y,z) for s in (1,-1) for x,y,z in ((.7,.7,2.63),(.55,.65,3.05),(-1.5,.85,2.63),(-1.5,.8,3.05))])
    guns(TX-.15,2.45,Lg=3.6);B((TX-.4,.86,2.85),(1.4,.03,.1),TEAM,0)
  # sensor + hatch so the scale reads
  link('lens',cyl((0,0,0),(0,0,.001),.001),GLOW,bev=0)
K=os.environ.get('K','A')
for o in list(bpy.data.objects):bpy.data.objects.remove(o)
concept(K)
link('floor',box((0,0,-.01),(30,30,.02)),M('floor',(.09,.095,.08),.95))
# a 1.75 m soldier marker for scale
link('man',cyl((5.2,-3.2,0),(5.2,-3.2,1.75),.2,12),M('man',(.5,.12,.08),.6),bev=0)
shot=scene_setup(int(os.environ.get('SAMP','12')))
shot('/home/claude/veh/hc_%s_34.png'%K,(1,-1.05,.55),(0,0,1.4),10.5,(960,640))
shot('/home/claude/veh/hc_%s_side.png'%K,(0,-1,.06),(0,0,1.4),10.0,(960,520))
