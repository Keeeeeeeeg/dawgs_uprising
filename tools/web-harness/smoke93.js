const S=require('./load.js')(process.argv[2]);
for(const [map,mode] of [['twinvalleys','ffa'],[Object.keys(S.MAPS||{})[2]||'twinvalleys','ffa']]){
 const G=S.createGame({map,mode,ai:[{p:0},{p:1},{p:2},{p:3}].slice(0,4),seed:7});let mx=0,mn=1e9,n=0;
 for(let t=0;t<900;t+=.25){G.update(.25);for(const u of G.units)if(u.alive&&u.def.plane&&u.pstate==='out'){const a=G.unitY(u)-G.heightAt(u.x,u.z);mx=Math.max(mx,a);mn=Math.min(mn,a);n++;}}
 console.log(map,'units',G.units.filter(u=>u.alive).length,'plane samples',n,'AGL',mn.toFixed(1),mx.toFixed(1));}
