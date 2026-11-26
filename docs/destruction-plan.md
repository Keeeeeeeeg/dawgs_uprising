# Destruction update (Keegan, 2026-11-25)

Owner: Keegan's session. Shipped so far: **26.3 Shell Holes** and **26.4 Timber**.

## Shipped

### 26.3 Shell Holes: craters are sim ground
- The SIM keeps craters (`BALANCE.crater`). Projectile impacts create them in `craterAt` (deterministic angle from a position hash; merge logic is the same as the renderer's old code).
- `heightAt` = `baseH` + `crOff` (8 m bucket grid, early-out when there are no craters).
- The renderer draws slots from the `'crater'` event. Craters dug in the fog are deferred until the spot is seen. Slots 260-299 are screen-only crash scars (aircraft falls are renderer-only).
- No craters on shorelines, in zones (r+3), on decks, or on roads (the renderer hands the sim a road mask via `G.setPaved(mask,w)`, built from OVL at init).
- Shallower: `deep` .2, `deepMax` .75. Bowls slow vehicles (`slowVeh`) and infantry (`slowInf`). Infantry in a bowl get `coverInf`.
- Bowl texture: `env/crater/crater_c.jpg` + `crater_n.jpg`, built from the Poly Haven gravel + rock_dark scans in world space. The rim gets the same detail.
- Render order: terrain -20, crater stencil passes -0.5/-0.4/-0.3, so units inside holes stay visible.
- Devtools: `G.digCrater(x,z,r)`, `G.craterIn(x,z)`, `G.baseHeightAt`.

### 26.4 Timber: destructible trees
- `BALANCE.treeFall`: explosions (per-weapon radius, or splash*.5 if larger) knock down trees in the sim (`treeBlast`). Each tree gets `t.fall`: 1 topple, 2 snap, 3 shred (0 = a rover cut it), plus intensity `t.k`.
- Cover: infantry near standing trees take `coverInf`. In woods (`forestN` trees in the 3x3 cells around them), infantry are only acquired as new targets within `seen` x range.
- Renderer destruction bank:
  - Rod-pivot physics with a slope landing, bounce and settle.
  - Snapped trees are thrown clear of a splintered stump.
  - Shredded trees: bark splinters and leaf clumps through the debris physics, over a charred stump.
  - Logs persist (newest 60, or 24 in PERF); stumps are instanced (900).
- Fixed: textured trees (26.0) crashed `treeFall` (array material), so harvested trees had stopped falling.

## Next: flavour buildings + destruction pass (agreed answers)
- **Breaking:** staged, then collapse. Intact, damaged (holes, roof tiles missing, fire), heavily damaged, then collapse. Each model is pre-broken in Blender (cell fracture) so the chunks fall the same on every screen. Light physics brings the chunks to rest; the rubble pile gives cover.
- **Garrison:**
  - Squads fire from the windows: one squad in a small building, two in a large one. Extra range and cover.
  - **Buildings counter artillery for infantry:** garrisoned infantry take much less damage from artillery and bombs.
  - Flamers and grenades flush garrisons. When a building collapses, the occupants are thrown out or killed.
  - The AI garrisons buildings near fights and leaves them when they start to fall.
  - Some buildings (fuel station, farm) give a small income while held.
- **Sets (all four):**
  - Farmsteads: farmhouse, barn, silo, sheds, fences, hay.
  - Roadside and utility: pylons and lines, water tower, fuel station, bus shelter, signs.
  - Military leftovers: checkpoints, sandbag nests, watchtowers, burnt trucks.
  - Biome-specific: desert mud-brick and wells; arctic research huts and drums; temperate stone cottages.
- **Also break:**
  - Crushable small props: tanks flatten fences, bales, signs, crates and barrels, and they stay flattened.
  - Breachable stone walls and hedgerows: they block movement until shelled or rammed, then a gap opens.
  - Pylons topple and their wires snap and spark.
  - **Bridges survive for now.**
- **Sign-off:** a concept sheet comes first. Blender stills of each set per biome (intact, damaged, rubble); Keegan approves before any bake.
- **Placement:** procedural from the map seed (flat ground near roads, away from bases), the same on every screen.

## Known issue
- A `computeBoundingSphere NaN` console warning has appeared on load since at least 26.2. Its source has not been found yet.
