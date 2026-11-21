import json,glob,os,shutil
D={}
os.makedirs('/home/claude/vu/tex/veh',exist_ok=True)
for f in glob.glob('/home/claude/veh/*/v_*.json'):
  t=os.path.basename(f)[2:-5];D[t]=json.load(open(f))
  for x in glob.glob(os.path.dirname(f)+'/tex/*'):shutil.copy(x,'/home/claude/vu/tex/veh/')
open('/home/claude/vu/tex/veh/vtex.js','w').write('window.VTEX='+json.dumps(D,separators=(',',':'))+';\n')
print('vehicles',list(D))
