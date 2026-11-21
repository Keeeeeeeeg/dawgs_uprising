#!/bin/bash
python3 /home/claude/tools/mkdbg.py
names=()
for a in "$@"; do set -- $a; node /home/claude/tools/rcplot2.js $1 $2 $3 $4 $5; python3 - $1_$3 $3 $4 $5 <<'P'
import json,sys,matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt,numpy as np
D=json.load(open('/tmp/ct/rc2.json'));R=np.array(D['R']);cx,cz,r=map(float,sys.argv[2:5])
fig,ax=plt.subplots(figsize=(6,6));B=R[R[:,2]==1];ax.scatter(B[:,0],B[:,1],s=3,c='#bbb',marker='s')
for L in D['rails']:
    P=L['pts']+[L['pts'][0]];ax.plot([p[0] for p in P],[p[1] for p in P],'b.-',ms=2)
    for st in L['st']:ax.plot([st[0][0],st[1][0]],[st[0][1],st[1][1]],'k',lw=4);ax.plot(*st[2],'go');ax.plot(*st[3],'ro')
ax.plot(cx,cz,'mx',ms=14,mew=3);ax.set_xlim(cx-r,cx+r);ax.set_ylim(cz-r,cz+r);ax.set_aspect('equal');plt.savefig('/tmp/ct/rc_%s.png'%sys.argv[1],dpi=55)
P
names+=("$1_$3"); done
python3 -c "
import sys;from PIL import Image;ims=[Image.open('/tmp/ct/rc_%s.png'%n) for n in sys.argv[1:]]
w,h=ims[0].size;o=Image.new('RGB',(w*len(ims),h),'white');[o.paste(im,(i*w,0)) for i,im in enumerate(ims)];o.save('/tmp/ct/rc4.png')" "${names[@]}"
