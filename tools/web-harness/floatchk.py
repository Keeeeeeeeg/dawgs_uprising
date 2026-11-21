import json,sys,bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
def islands(a):
    n=len(a)//9;key={};vid=[]
    for i in range(n*3):
        k=(round(a[i*3],3),round(a[i*3+1],3),round(a[i*3+2],3));vid.append(key.setdefault(k,len(key)))
    par=list(range(len(key)))
    def f(x):
        while par[x]!=x:par[x]=par[par[x]];x=par[x]
        return x
    for t in range(n):
        a0,b0,c0=vid[t*3],vid[t*3+1],vid[t*3+2];par[f(a0)]=f(b0);par[f(b0)]=f(c0)
    isl={}
    for t in range(n):isl.setdefault(f(vid[t*3]),[]).append(t)
    return list(isl.values())
def check(a,eps=float(__import__("os").environ.get("EPS",".012"))):
    I=islands(a);info=[]
    for ts in I:
        vs=[];ps=[]
        for t in ts:
            b=len(vs);
            for j in range(3):vs.append(Vector(a[(t*3+j)*3:(t*3+j)*3+3]))
            ps.append((b,b+1,b+2))
        c=sum(vs,Vector())/len(vs)
        mn=Vector((min(v.x for v in vs),min(v.y for v in vs),min(v.z for v in vs)));mx=Vector((max(v.x for v in vs),max(v.y for v in vs),max(v.z for v in vs)))
        # inflate a little so parts that merely touch count as joined
        vi=[v+(v-c).normalized()*eps if (v-c).length>1e-6 else v for v in vs]
        info.append(dict(n=len(ts),c=c,mn=mn,mx=mx,bvh=BVHTree.FromPolygons(vi,ps),vs=vs,ts=ts))
    m=len(info);par=list(range(m))
    def f(x):
        while par[x]!=x:par[x]=par[par[x]];x=par[x]
        return x
    for i in range(m):
        A=info[i]
        for j in range(i+1,m):
            B=info[j]
            if f(i)==f(j):continue
            if any(A['mn'][k]-eps>B['mx'][k]+eps or B['mn'][k]-eps>A['mx'][k]+eps for k in range(3)):continue
            if A['bvh'].overlap(B['bvh']):par[f(i)]=f(j);continue
            # one fully inside the other (no surface crossing): a vertex of the smaller is inside the bigger
            S,Bg=(A,B) if A['n']<B['n'] else (B,A)
            v=S['vs'][0];hits=0
            o=v
            for _ in range(60):
                loc,nor,idx,d=Bg['bvh'].ray_cast(o,Vector((.37,.83,.41)).normalized())
                if loc is None:break
                hits+=1;o=loc+Vector((.37,.83,.41)).normalized()*1e-4
            if hits%2==1:par[f(i)]=f(j)
    groups={}
    for i in range(m):groups.setdefault(f(i),[]).append(i)
    gs=sorted(groups.values(),key=lambda g:-sum(info[i]['n'] for i in g))
    return info,gs
if __name__=='__main__':
    D=json.load(open(sys.argv[1]));only=sys.argv[2:] 
    for t,a in D.items():
        if only and t not in only:continue
        info,gs=check(a)
        if len(gs)>1:
            print(t,'islands',len(info),'groups',len(gs))
            for g in gs[1:]:
                n=sum(info[i]['n'] for i in g);mn=[min(info[i]['mn'][k] for i in g) for k in range(3)];mx=[max(info[i]['mx'][k] for i in g) for k in range(3)]
                print('   tris',n,'box',[round(x,2) for x in mn],[round(x,2) for x in mx])
