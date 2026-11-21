# embed every baked marine type into the game (window.SKINT) and copy its maps into vu/tex/marine
import json,os,shutil,glob,re
V='/home/claude/vu/v52.html';s=open(V).read()
D={}
for f in sorted(glob.glob('/home/claude/lp/*/skin_*.json')):
  t=os.path.basename(f)[5:-5];D[t]=json.load(open(f))
  for x in glob.glob(os.path.dirname(f)+'/tex/*'):shutil.copy(x,'/home/claude/vu/tex/marine/')
# the data ships as a supporting script (keeps the page under its size limit)
open('/home/claude/vu/tex/marine/skint.js','w').write('window.SKINT='+json.dumps(D,separators=(',',':'))+';\n')
if 'src="tex/marine/skint.js"' not in s:
  i=s.index('window.SKINT=');i0=s.rindex('<script>',0,i);j=s.index('</script>',i)+len('</script>')
  s=s[:i0]+'<script src="tex/marine/skint.js"></script>\n<script>window.SKINT=window.SKINT||{};</script>'+s[j:]
  open(V,'w').write(s);print('embedded',list(D),sum(len(json.dumps(d)) for d in D.values())//1024,'KB')
