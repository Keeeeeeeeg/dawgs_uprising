import sys
from PIL import Image
# combine three preview views into one strip
ims=[Image.open(p) for p in sys.argv[2:]]
w,h=ims[0].size;c=Image.new('RGB',(w*len(ims),h))
for i,im in enumerate(ims):c.paste(im,(i*w,0))
c.resize((c.width*2//3,c.height*2//3)).save(sys.argv[1])
