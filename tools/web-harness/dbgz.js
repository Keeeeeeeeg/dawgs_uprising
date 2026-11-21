const SIM=require('./load.js')(process.argv[2]);
const G=SIM.createGame({map:process.argv[3],mode:'ffa',ai:[{p:0},{p:1},{p:2}],seed:1234});
const z=G.zones.find(z=>z.name===process.argv[4]);console.log(z.type,z.x,z.z,z.r,'spots',z.spots.length,'budget',z.budget,'coastal',z.coastal,'cove',!!z.cove,'h',G.heightAt(z.x,z.z));
let ok=0,n=0;for(let a=0;a<6.28;a+=.3)for(let r=z.r+5;r<z.r+24;r+=3){n++;const x=z.x+Math.cos(a)*r,zz=z.z+Math.sin(a)*r;if(!G.canPlace(z.owner??0,z.id,'pillbox',x,zz))ok++;}
console.log('placeable samples',ok,'/',n);
