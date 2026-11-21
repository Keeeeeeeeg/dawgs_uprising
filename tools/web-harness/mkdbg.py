s=open('/home/claude/vu/v52.html').read()
s=s.replace("    for(const S of G.sectors){const zs=S.zones.map(i=>G.zones[i]).filter(z=>z.wall);if(zs.length<2)continue;","    G.__RC=RC;G.__cell=cellOf;for(const S of G.sectors){const zs=S.zones.map(i=>G.zones[i]).filter(z=>z.wall);if(zs.length<2)continue;",1)
open('/tmp/ct/dbg.html','w').write(s)
