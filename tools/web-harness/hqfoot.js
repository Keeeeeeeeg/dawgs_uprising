const s=require('fs').readFileSync(process.argv[2],'utf8');const i=s.indexOf('const WALLED=JSON.parse(')+24;const j=s.indexOf("');",i)+1;const W=JSON.parse(eval(s.slice(i,j)));
const kind=process.argv[3]||'hq',d=W[kind],K=+(process.argv[4]||1);const b=Buffer.from(d.p,'base64');const a=new Int16Array(b.buffer,b.byteOffset,b.length/2);
const C=.5,N=80,occ=new Uint8Array(N*N);const cell=(x,z)=>[Math.floor(x/C)+N/2,Math.floor(z/C)+N/2];
for(let t=0;t<a.length/9;t++){const P=[0,1,2].map(v=>[a[t*9+v*3]/1000*K,a[t*9+v*3+1]/1000,a[t*9+v*3+2]/1000*K]);const ymax=Math.max(...P.map(p=>p[1]));if(ymax<.35)continue;
  // sample the triangle
  for(let u=0;u<=1;u+=.05)for(let v=0;v<=1-u;v+=.05){const x=P[0][0]+(P[1][0]-P[0][0])*u+(P[2][0]-P[0][0])*v,z=P[0][2]+(P[1][2]-P[0][2])*u+(P[2][2]-P[0][2])*v;const [cx,cz]=cell(x,z);if(cx>=0&&cx<N&&cz>=0&&cz<N)occ[cz*N+cx]=1;}}
const BL=JSON.parse(process.argv[5]||'[]');const inB=(x,z)=>BL.some(q=>x>=q[0]&&x<=q[2-1+0]*0+q[1]&&z>=q[2]&&z<=q[3]);
let out='';for(let cz=0;cz<N;cz++){let l='';for(let cx=0;cx<N;cx++){const x=(cx-N/2+.5)*C,z=(cz-N/2+.5)*C;const o=occ[cz*N+cx],bb=inB(x,z);l+=o&&bb?'#':o?'M':bb?'s':'.';}out+=l+'\n';}
console.log(out);
