import sys,json;sys.path.insert(0,'/home/claude/anim')
from idles import *
from PIL import Image,ImageDraw
ks=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else list(POSES)
ims=[]
for k in ks:
  clear();n=mesh(k,'rifle',comb(BASE,POSES[k]),BASEH).name
  render('/tmp/pz_%s.png'%k,[n],view=(1,.2,.75),res=(260,400),ortho=.85,target=(0.05,.85,0))
  im=Image.open('/tmp/pz_%s.png'%k).convert('RGB');ImageDraw.Draw(im).text((8,8),k,fill=(255,255,0));ims.append(im)
W=Image.new('RGB',(260*len(ims),400))
for i,im in enumerate(ims):W.paste(im,(260*i,0))
W.save('/home/claude/anim/sheet.png')
