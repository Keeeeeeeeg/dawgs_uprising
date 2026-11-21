// all-AI battles on the rebuilt maps: errors, captures, ships, units on decks, ships under spans
const S=require('./load.js')(process.argv[2]);const mins=+process.argv[3]||12;
for(const id of ['twinvalleys','fourcrowns','hexfall']){const n=S.MAPS[id].maxPlayers,ai=[];for(let i=0;i<n;i++)ai.push({p:i%4});
  const t0=Date.now();let G;try{G=S.createGame({map:id,mode:'ffa',ai:ai.slice(1),seed:7});
    // the human slot plays as AI too
    let onDeck=0,under=0,naval=0;
    for(let t=0;t<mins*60*4&&!G.over;t++){G.update(.25);
      if(t%40===0){for(const u of G.units){if(!u.alive)continue;const c=G.cellOf?G.cellOf(u.x,u.z):-1;
        if(G.deckCell){const i=Math.floor((u.x-G.X0)/G.CELL),j=Math.floor((u.z-G.Z0)/G.CELL),k=j*G.GW+i;if(G.deckCell[k]===2){if(u.def.naval)under++;else if(!u.def.air)onDeck++;}}
        if(u.def.naval)naval++;}}}
    const own=G.factions.map(f=>G.zones.filter(z=>z.owner===f.id).length);
    console.log(id.padEnd(12),'s',((Date.now()-t0)/1000).toFixed(0),'owned',own.join(','),'neutral',G.zones.filter(z=>z.owner==null).length,'ship-samples',naval,'on deck',onDeck,'ships under',under,'over',!!G.over);
  }catch(e){console.log('ERROR',id,e.stack.split('\n').slice(0,4).join(' | '));}}
