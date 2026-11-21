def vpaint(name,col,mud=1.0,wear=1.0,dust=1.0,scale=1.0,rust=0.0,dustcol=(.2,.18,.13),mudcol=((.07,.055,.035),(.13,.1,.065)),hk=1.0):
  """olive-grey paint, baked-in weathering: AO grime, chipped edges showing steel, fine scratches, dust on up-facing
  surfaces, mud splashed up the lower hull (fades out by ~1 m), streaks running down vertical faces"""
  m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;N=nt.nodes;Lk=nt.links;b=N['Principled BSDF']
  geo=N.new('ShaderNodeNewGeometry');tc=N.new('ShaderNodeTexCoord');sep=N.new('ShaderNodeSeparateXYZ');Lk.new(geo.outputs['Position'],sep.inputs[0])
  def noise(sc,det=4,vec=None,dist=0):
    n=N.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=sc;n.inputs['Detail'].default_value=det;n.inputs['Distortion'].default_value=dist;Lk.new(vec or tc.outputs['Object'],n.inputs['Vector']);return n
  def ramp(inp,a,b2):
    r=N.new('ShaderNodeValToRGB');r.color_ramp.elements[0].position=a;r.color_ramp.elements[1].position=b2;Lk.new(inp,r.inputs[0]);return r
  def math_(op,a,b2=None,v=None):
    q=N.new('ShaderNodeMath');q.operation=op
    if isinstance(a,(int,float)):q.inputs[0].default_value=a
    else:Lk.new(a,q.inputs[0])
    if b2 is not None:
      if isinstance(b2,(int,float)):q.inputs[1].default_value=b2
      else:Lk.new(b2,q.inputs[1])
    return q.outputs[0]
  def mix(f,A,B):
    q=N.new('ShaderNodeMix');q.data_type='RGBA'
    for k,v in (('A',A),('B',B)):
      if isinstance(v,tuple):q.inputs[k].default_value=v+(1,)
      else:Lk.new(v,q.inputs[k])
    if isinstance(f,(int,float)):q.inputs['Factor'].default_value=f
    else:Lk.new(f,q.inputs['Factor'])
    return q.outputs['Result']
  # paint mottling (large soft patches + faded panels)
  mot=noise(1.6*scale,3);pc=mix(mot.outputs['Fac'],col,tuple(c*.78 for c in col))
  mot2=noise(7*scale,5);pc=mix(math_('MULTIPLY',ramp(mot2.outputs['Fac'],.45,.75).outputs['Color'],.35),pc,tuple(min(1,c*1.18) for c in col))
  # streaks down vertical faces (stretched noise in z)
  mp=N.new('ShaderNodeMapping');mp.inputs['Scale'].default_value=(18,18,1.2);Lk.new(tc.outputs['Object'],mp.inputs['Vector'])
  stk=ramp(noise(3,3,mp.outputs['Vector']).outputs['Fac'],.55,.8)
  pc=mix(math_('MULTIPLY',stk.outputs['Color'],.35+.25*rust),pc,(.045,.04,.03))
  if rust:   # rust weeping from seams and bolts: a second, sparser streak layer in rust brown
    mp3=N.new('ShaderNodeMapping');mp3.inputs['Scale'].default_value=(30,30,1.6);Lk.new(tc.outputs['Object'],mp3.inputs['Vector'])
    rs=ramp(noise(4,4,mp3.outputs['Vector']).outputs['Fac'],.66,.82);pc=mix(math_('MULTIPLY',rs.outputs['Color'],.55*rust),pc,(.13,.06,.025))
  # AO grime in crevices
  ao=N.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.12
  pc=mix(math_('MULTIPLY',math_('SUBTRACT',1,ao.outputs['AO']),1.2),pc,(.02,.019,.015))
  # dust on top surfaces
  nz=N.new('ShaderNodeSeparateXYZ');Lk.new(geo.outputs['Normal'],nz.inputs[0])
  up=ramp(nz.outputs['Z'],.7,.98);dn=noise(1.3,3)
  dmask=math_('MULTIPLY',math_('MULTIPLY',up.outputs['Color'],ramp(dn.outputs['Fac'],.45,.8).outputs['Color']),.3*dust)
  pc=mix(dmask,pc,dustcol)
  # mud: splashed up from the ground, thick at the bottom, broken edge
  hz=N.new('ShaderNodeMapRange');hz.inputs['From Min'].default_value=(1.05+.3*max(0,mud-1))*hk;hz.inputs['From Max'].default_value=.15*hk;Lk.new(sep.outputs['Z'],hz.inputs['Value'])   # hk: mud line height scale (smaller vehicles)
  mn=noise(3.2,6,None,.8);mudm=ramp(math_('ADD',math_('MULTIPLY',hz.outputs['Result'],.85),math_('MULTIPLY',mn.outputs['Fac'],.5)),.62-.12*max(0,mud-1),.72-.1*max(0,mud-1))
  mudf=math_('MULTIPLY',mudm.outputs['Color'],mud)
  mudc=mix(noise(14,4).outputs['Fac'],mudcol[0],mudcol[1])
  pc=mix(mudf,pc,mudc)
  # chipped edges + scratches -> bare steel
  edge=ramp(geo.outputs['Pointiness'],.565,.62);chips=ramp(noise(22,6).outputs['Fac'],.55-.06*max(0,wear-1),.63-.05*max(0,wear-1))
  mp2=N.new('ShaderNodeMapping');mp2.inputs['Scale'].default_value=(500,25,25);mp2.inputs['Rotation'].default_value=(0,.3,.7);Lk.new(tc.outputs['Object'],mp2.inputs['Vector'])
  scr=ramp(noise(1,2,mp2.outputs['Vector']).outputs['Fac'],.76,.78)
  wm=math_('MULTIPLY',math_('MAXIMUM',math_('MULTIPLY',edge.outputs['Color'],chips.outputs['Color']),math_('MULTIPLY',scr.outputs['Color'],.3)),wear*.8)
  wm=math_('MULTIPLY',wm,math_('SUBTRACT',1,mudf))
  fin=mix(wm,pc,(.22,.22,.21))
  Lk.new(fin,b.inputs['Base Color']);Lk.new(wm,b.inputs['Metallic'])
  ro=N.new('ShaderNodeMapRange');ro.inputs['To Min'].default_value=.72;ro.inputs['To Max'].default_value=.38;Lk.new(wm,ro.inputs['Value']);Lk.new(ro.outputs['Result'],b.inputs['Roughness'])
  bu=N.new('ShaderNodeBump');bu.inputs['Strength'].default_value=.18;bu.inputs['Distance'].default_value=.002
  Lk.new(math_('ADD',math_('MULTIPLY',noise(160,5).outputs['Fac'],.5),math_('MULTIPLY',mudf,.8)),bu.inputs['Height']);Lk.new(bu.outputs['Normal'],b.inputs['Normal'])
  return m
