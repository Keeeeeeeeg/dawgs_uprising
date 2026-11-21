import json,sys,numpy as np,matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
for mp in sys.argv[1:]:
  D=json.load(open('/tmp/ct/mp/%s.json'%mp));hv=np.array(D['hv']);P=np.array(D['pass']);Wp=np.array(D['wpass'])
  W,H=D['GW']*2.5,D['GH']*2.5;ext=[-W/2,W/2,H/2,-H/2]
  fig,ax=plt.subplots(figsize=(13,13*H/W));img=np.zeros(hv.shape+(3,))
  land=hv>0;img[...]=[.12,.29,.40];img[Wp==1]=[.15,.38,.55];img[land]=[.42,.52,.30];img[(land)&(P==0)]=[.55,.45,.35];img[hv>5]=[.75,.7,.65]
  img[(P==1)&(hv<=0)]=[.95,.75,.2]   # deck cells (passable over water)
  ax.imshow(img,extent=ext,interpolation='nearest')
  for L in D['rails']:ax.plot([p[0] for p in L],[p[1] for p in L],'k-',lw=1.2)
  for b in D['bridges']:ax.plot([b['a'][0],b['b'][0]],[b['a'][1],b['b'][1]],'-',color='#ffd000' if b['high'] else '#ff6000',lw=1)
  C={'hq':'s','fortress':'8','town':'o','airbase':'^'}
  for z in D['zones']:
    ax.add_patch(plt.Circle((z['x'],z['z']),z['r'],fill=False,ec='w',lw=.6))
    ax.plot(z['x'],z['z'],marker='*' if z['city'] else C[z['t']],ms=12 if z['city'] else 7,color='#ff4fd8' if z['city'] else 'w',mec='k')
    if z['port']:ax.plot(z['x']+12,z['z']+8,'D',ms=5,color='#4fd1c5',mec='k')
    ax.text(z['x'],z['z']+z['r']+10,z['n'],fontsize=6,ha='center',color='w')
  for q in D.get('pits',[]):ax.plot(q[0],q[1],'X',ms=11,color='#40ffe0',mec='k')
  ax.set_title('%s  (%d ms)'%(mp,D['ms']));plt.tight_layout();plt.savefig('/tmp/ct/mp/%s.png'%mp,dpi=75);plt.close()
