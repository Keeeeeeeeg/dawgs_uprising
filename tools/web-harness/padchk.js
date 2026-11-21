const SIM=require('./load.js')(process.argv[2]);
for(const map of ['fourcrowns','twinvalleys']){const G=SIM.createGame({map,mode:'ffa',ai:[{p:0},{p:1},{p:2}]});
for(const z of G.zones.filter(z=>z.wall&&!z.wall.light)){let mn=1e9,mx=-1e9;
  for(let i=0;i<400;i++){const a=Math.random()*6.283,r=Math.random()*8;const h=G.heightAt(z.x+Math.cos(a)*r,z.z+Math.sin(a)*r);mn=Math.min(mn,h);mx=Math.max(mx,h);}
  console.log(map,z.type,z.name,'z.y',z.y.toFixed(3),'ground',mn.toFixed(3),mx.toFixed(3));}}
