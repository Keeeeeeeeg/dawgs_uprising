const SIM=require('./load.js')(process.argv[2]);
const G=SIM.createGame({map:'dawgs',mode:'ffa',ai:[{p:0}],seed:1});const {hv,VW}=G.map;
const h=(x,z)=>hv[Math.round((z-G.Z0)/G.CELL)*VW+Math.round((x-G.X0)/G.CELL)];
for(const z of G.zones.filter(z=>z.cove)){const c=z.cove;const s=[];for(let t=-4;t<=1.01;t+=.25)s.push(h(c.ax+(c.bx-c.ax)*t,c.az+(c.bz-c.az)*t).toFixed(1));console.log(z.name,z.cove.R,s.join(' '));}
