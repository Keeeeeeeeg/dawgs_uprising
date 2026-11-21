// render pass/water/zones/plots per map to PNG (via raw RGB -> python)
const SIM=require('./load.js')(process.argv[2]);const out=process.argv[3]||'img';const only=process.argv[4];
const fs=require('fs');fs.mkdirSync(out,{recursive:true});
const S=+process.env.S||2; // px per cell
const COL={hq:[255,255,255],fortress:[220,60,60],town:[250,210,60],airbase:[80,160,255]};
const KC={mil:[255,120,0],eco:[0,230,120],fort:[180,0,220]};
for(const [id,m] of Object.entries(SIM.MAPS)){
  if(m.hidden&&!(only&&id===only))continue;if(only&&id!==only)continue;
  const n=m.maxPlayers;const ai=[];for(let i=1;i<n;i++)ai.push({p:i-1});
  const G=SIM.createGame({map:id,mode:'ffa',ai,seed:1234});
  const {pass,wpass,hv,VW}=G.map,GW=G.GW,GH=G.GH,W=GW*S,H=GH*S;const px=Buffer.alloc(W*H*3);
  const set=(x,y,c)=>{if(x<0||y<0||x>=W||y>=H)return;const k=(y*W+x)*3;px[k]=c[0];px[k+1]=c[1];px[k+2]=c[2];};
  for(let j=0;j<GH;j++)for(let i=0;i<GW;i++){const h=hv[j*VW+i];let c;
    if(wpass[j*GW+i])c=[20,40,110];else if(h<0)c=[60,90,150];else if(pass[j*GW+i]){const g=Math.max(0,Math.min(1,h/7));c=[60+80*g,120+60*g,50+50*g];}else c=[90,70,60];
    for(let a=0;a<S;a++)for(let b=0;b<S;b++)set(i*S+a,j*S+b,c);}
  const toP=(x,z)=>[Math.round((x-G.X0)/G.CELL*S),Math.round((z-G.Z0)/G.CELL*S)];
  const disc=(x,z,r,c,ring)=>{const [cx,cy]=toP(x,z),R=r/G.CELL*S;for(let y=-R-1;y<=R+1;y++)for(let x2=-R-1;x2<=R+1;x2++){const d=Math.hypot(x2,y);if(ring?Math.abs(d-R)<1:d<=R)set(cx+x2|0,cy+y|0,c);}};
  for(const st of G.streets||[])for(let i=1;i<st.pts.length;i++){const [a,b]=st.pts[i-1],[c,d]=st.pts[i];for(let t=0;t<=1;t+=.1)disc(a+(c-a)*t,b+(d-b)*t,st.w/2,[60,60,60]);}
  for(const z of G.zones){disc(z.x,z.z,z.r,COL[z.type],true);if(z.home!=null)disc(z.x,z.z,4,[255,255,255]);
    if(z.air){const a=z.air;for(let t=0;t<=1;t+=.01)disc(a.a.x+(a.b.x-a.a.x)*t,a.a.z+(a.b.z-a.a.z)*t,1,[200,200,255]);}
    for(const p of z.plots){disc(p.x,p.z,2.2,KC[p.kind]);if(p.water&&z.port)disc(p.water.x,p.water.z,1,[0,255,255]);}
    if(z.port)disc(z.x,z.z,z.r+2,[0,255,255],true);}
  fs.writeFileSync(`${out}/${id}.rgb`,px);fs.writeFileSync(`${out}/${id}.json`,JSON.stringify({W,H}));
}
