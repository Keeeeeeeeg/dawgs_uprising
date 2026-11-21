// load SIM from an artifact html file (harness adds a few internals for offline tools)
const fs=require('fs');
module.exports=function(file){
  const h=fs.readFileSync(file,'utf8');
  const s=h.indexOf('const SIM = (function');const e=h.indexOf('})();',h.indexOf('return {BALANCE,baseMix'))+5;
  let code=h.slice(s,e).replace('return {BALANCE,baseMix','return {__terrain(m,seed,zones){useMap(m);m.zonesFinal=zones||[];const r=buildMap(seed);return Object.assign(r,{GW,GH,X0,Z0,CELL,W:WORLD_W,H:WORLD_H});},coastDist,landRaw,NAMESETS,BALANCE,baseMix');
  return new Function(code+'\nreturn SIM;')();
};
