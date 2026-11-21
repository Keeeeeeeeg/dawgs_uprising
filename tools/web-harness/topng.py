import sys,json,glob
from PIL import Image
for f in glob.glob(sys.argv[1]+'/*.rgb'):
    j=json.load(open(f[:-4]+'.json'));Image.frombytes('RGB',(j['W'],j['H']),open(f,'rb').read()).save(f[:-4]+'.png')
