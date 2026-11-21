import json,base64,struct,sys
def load(fn,name):
    D=json.load(open(fn));d=D[name];b=base64.b64decode(d['p']);v=struct.unpack('<%dh'%(len(b)//2),b)
    V=[(v[i]/1000,v[i+1]/1000,v[i+2]/1000) for i in range(0,len(v),3)];return [V[i:i+3] for i in range(0,len(V),3)]
def surf(T,x,y,side):
    best=None
    for (a,b_,c) in T:
        v0=(b_[0]-a[0],b_[1]-a[1]);v1=(c[0]-a[0],c[1]-a[1]);v2=(x-a[0],y-a[1]);den=v0[0]*v1[1]-v1[0]*v0[1]
        if abs(den)<1e-9:continue
        u=(v2[0]*v1[1]-v1[0]*v2[1])/den;w=(v0[0]*v2[1]-v2[0]*v0[1])/den
        if u<-1e-6 or w<-1e-6 or u+w>1+1e-6:continue
        z=a[2]+u*(b_[2]-a[2])+w*(c[2]-a[2])
        if best is None or z*side>best*side:best=z
    return best
def decal(T,x0,x1,y0,y1,nx,ny,side,off):
    P=[];U=[]
    for j in range(ny+1):
        for i in range(nx+1):
            x=x0+(x1-x0)*i/nx;y=y0+(y1-y0)*j/ny;z=surf(T,x,y,side)
            if z is None:return None
            P+= [round(x,3),round(y,3),round(z+side*off,3)];U+=[(i/nx) if side>0 else 1-i/nx,j/ny]
    return P,U
