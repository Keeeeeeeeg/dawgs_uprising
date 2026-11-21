// node mapplot.js file.html mapId seed -> /tmp/ct/mp/<map>.json (terrain + zones + rails + bridges + roads-free)
const S=require('./load.js')(process.argv[2]);const fs=require('fs');const [map,seed]=[process.argv[3],+(process.argv[4]||1)];
const n=S.MAPS[map].maxPlayers;const ai=[];for(let i=0;i<n-1;i++)ai.push({p:i%4});
const t0=Date.now();const G=S.createGame({map,mode:'ffa',ai,seed});
const m=G.map,GW=(m.VW-1),GH=(m.VH-1);
const out={map,GW,GH,W:S.MAPS[map].W,H:S.MAPS[map].H,ms:Date.now()-t0,hv:[],pass:[],wpass:[],zones:G.zones.map(z=>({n:z.name,t:z.type,x:z.x,z:z.z,city:!!z.city,port:!!z.port,coastal:z.coastal,r:z.r})),
  rails:(G.rails||[]).map(L=>L.open?L.pts:L.pts.concat([L.pts[0]])),bridges:(G.bridges||[]).map(b=>({a:b.a,b:b.b,s0:b.s0,s1:b.s1,H:b.H,high:!!b.high})),sectors:G.sectors.map(s=>({n:s.name,z:s.zones}))};
const st=2;for(let j=0;j<GH;j+=st){const r=[],p=[],w=[];for(let i=0;i<GW;i+=st){r.push(+m.hv[j*m.VW+i].toFixed(1));p.push(m.pass[j*GW+i]);w.push(m.wpass[j*GW+i]);}out.hv.push(r);out.pass.push(p);out.wpass.push(w);}
fs.writeFileSync('/tmp/ct/mp/'+map+'.json',JSON.stringify(out));console.log(map,'ok',out.ms+'ms',G.zones.length,'zones',(G.rails||[]).length,'rails',out.zones.filter(z=>z.city).map(z=>z.n),'ports',out.zones.filter(z=>z.port).length);
