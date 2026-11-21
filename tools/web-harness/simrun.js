const SIM=require('./load.js')(process.argv[2]);const mins=+process.argv[3]||6;
for(const [id,m] of Object.entries(SIM.MAPS)){if(m.hidden&&id!=='moon_dawgs')continue;
  for(const mode of ['ffa','teams']){const n=m.maxPlayers;const ai=[];for(let i=1;i<n;i++)ai.push({p:i-1,team:mode==='teams'?(i<n/2?1:2):0});
  const t0=Date.now();let G;try{G=SIM.createGame({map:id,mode,ai});
  for(let t=0;t<mins*60*10&&!G.over;t++)G.update(.1);}catch(e){console.log('ERROR',id,mode,e.stack.split('\n').slice(0,3).join(' | '));continue;}
  const own=G.factions.map(f=>G.zones.filter(z=>z.owner===f.id).length);const built=G.zones.reduce((a,z)=>a+z.plots.filter(p=>p.fac).length,0);
  const naval=G.units.filter(u=>u.alive&&u.def.naval).length;
  console.log(id.padEnd(13),mode,'zones owned',own.join(','),'facilities',built,'naval',naval,'units',G.units.filter(u=>u.alive).length,(Date.now()-t0)+'ms',G.over?'OVER':'');}}
