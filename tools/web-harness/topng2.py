import sys,json,glob
from PIL import Image
for f in glob.glob('bal_*.rgb'):
    j=json.load(open(f[:-4]+'.json'));Image.frombytes('RGB',(j['W'],j['H']),open(f,'rb').read()).save(f[:-4]+'.png')
