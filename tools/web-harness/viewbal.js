// render balanced.json layouts over terrain
const SIM=require('./load.js')(process.argv[2]);const B=require('./balanced.json');const fs=require('fs');
const {PNG}=(()=>({PNG:null}))();
for(const [id,b] of Object.entries(B)){if(process.argv[3]&&id!==process.argv[3])continue;const m=SIM.MAPS[id];const T=SIM.__terrain(m,20261017,[]);
  const S=2,W=T.GW*S,H=T.GH*S,px=Buffer.alloc(W*H*3);const set=(x,y,c)=>{if(x<0||y<0||x>=W||y>=H)return;const k=(y*W+x)*3;px[k]=c[0];px[k+1]=c[1];px[k+2]=c[2];};
  for(let j=0;j<T.GH;j++)for(let i=0;i<T.GW;i++){const c=T.wpass[j*T.GW+i]?[20,40,110]:T.pass[j*T.GW+i]?[70,130,60]:T.hv[j*(T.GW+1)+i]<0?[60,90,150]:[90,70,60];for(let a=0;a<S;a++)for(let q=0;q<S;q++)set(i*S+a,j*S+q,c);}
  const COL={hq:[255,255,255],fortress:[220,60,60],town:[250,210,60],airbase:[80,160,255]};
  for(const z of b.zones){const cx=(z[2]-T.X0)/T.CELL*S,cy=(z[3]-T.Z0)/T.CELL*S,R={hq:16,fortress:11,town:10,airbase:13}[z[1]]/T.CELL*S;
    const port=z[1]!=='airbase'&&SIM.coastDist(m,z[2],z[3],{hq:16,fortress:11,town:10}[z[1]])<Infinity;
    for(let y=-R-3;y<=R+3;y++)for(let x=-R-3;x<=R+3;x++){const d=Math.hypot(x,y);if(d<=R)set(cx+x|0,cy+y|0,COL[z[1]]);else if(port&&d<R+3)set(cx+x|0,cy+y|0,[0,255,255]);}}
  fs.writeFileSync(`bal_${id}.rgb`,px);fs.writeFileSync(`bal_${id}.json`,JSON.stringify({W,H}));}
