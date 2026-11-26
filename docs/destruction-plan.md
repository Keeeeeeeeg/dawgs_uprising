# Destruction update (Keegan, 2026-11-25)

Owner: Keegan's session. Shipped so far: **26.3 Shell Holes**, **26.4 Timber**, **26.5 Impact Sites**.

## Shipped

### 26.3 Shell Holes: craters are sim ground
- The SIM keeps craters (`BALANCE.crater`). `craterAt` makes them at projectile impacts; the angle comes from a hash of the position, so it's deterministic, and the merge logic is the same as the renderer's old code.
- `heightAt` = `baseH` + `crOff`. Craters sit in an 8 m bucket grid, with an early-out when there are none.
- The renderer draws slots from the `'crater'` event. Craters dug in the fog are deferred until the spot is seen. Slots 260-299 are screen-only scars and are now unused for aircraft.
- No craters on shorelines, in zones (r+3), on decks, or on roads. Roads come from a mask the renderer hands the sim: `G.setPaved(mask,w)`, built from OVL at init.
- Shallower: `deep` .2, `deepMax` .75. Bowls slow units (`slowVeh`/`slowInf`); infantry in a bowl get `coverInf`.
- Bowl texture: `env/crater/crater_c.jpg` + `_n.jpg` (Poly Haven gravel + rock_dark), in world space.
- Render order: terrain -20, crater stencil passes -0.5/-0.4/-0.3, so units in holes stay visible.

### 26.4 Timber: destructible trees
- `BALANCE.treeFall`. `treeBlast` in the sim sets `t.fall` (1 topple / 2 snap / 3 shred; 0 = a rover cut it) and `t.k`.
- Cover: infantry near trees get `coverInf`. In woods, infantry are only acquired as new targets within `seen` x range.
- Renderer bank:
  - Rod-pivot physics with a slope landing, bounce and settle.
  - Snapped trees are thrown clear of a splintered stump.
  - Shredded trees: bark and leaf debris over a charred stump.
  - Instanced stumps.

### 26.5 Impact Sites
- Aircraft crash craters are sim ground too:
  - `airDown(u)` runs the screen's fall in fixed 20 ms steps from the same start and queues a crater (`airDownTick`).
  - The renderer's falls now step at a fixed 20 ms too, so the wreck lands on the hole.
  - Zeppelin crashes dig 3 sim craters (`zepDownTick`) and blast the trees under them.
- Log budget: the newest 40 logs (16 in PERF); each clears after 150 s.

## Next: flavour buildings + destruction pass (agreed answers)
- **Placement:** SMALL sets SPREAD across the countryside. They are cover points and mini-objectives, and must not compete with the established settlements where the big battles happen. Procedural from the map seed: flat ground near roads, well away from zones, a minimum spacing between sets. 1 to 4 pieces per set.
- **Art direction:** UNSC-inspired, Halo Wars realistic-but-stylised.
  - Chunky chamfered forms, readable silhouettes from the RTS camera.
  - Military-industrial materials: corrugated steel, concrete, olive and grey paint, hazard stripes, stencilled numbers.
  - Weathering is baked into normals; team colour only through the mask.
  - Even farm and roadside pieces read as frontier-colony prefab: modular habitat units, cargo containers, water reclaimers, comms masts, prefab barns. Not rustic European cottages.
- **Breaking:** staged, then collapse: intact → damaged → heavily damaged → collapse. Each building is pre-broken in Blender (cell fracture); the chunks fall with light physics into rubble that gives cover.
- **Garrison:**
  - Squads fire from the windows (1 squad small, 2 large).
  - **Buildings counter artillery for infantry:** garrisoned infantry take much less damage from artillery and bombs.
  - Flamers and grenades flush them out. When a building collapses, the occupants are thrown out or killed.
  - The AI uses buildings.
  - Some buildings give a small income while held.
- **Sets:**
  - Farmsteads.
  - Roadside and utility.
  - Military leftovers.
  - Biome variants (desert, arctic, temperate).
- **Also break:**
  - Crushable small props.
  - Breachable walls and hedgerows.
  - Pylons and lines.
  - **Bridges survive for now.**
- **Sign-off:** concept sheet first; Keegan approves before any bake.

## Performance budget (destruction)
- **Sim:** everything sits on grids (craters 8 m buckets, trees 2.5 m cells, buildings will use the same pattern). Nothing loops over every object per tick.
- **Craters:** one merged mesh per pass (300 slots), with uploads only for changed slots.
- **Trees:** stumps are one InstancedMesh. Logs are capped and age out. Debris is capped at 180 small pieces and skipped off-screen (`fxNear`).
- **Buildings (planned):**
  - Each intact building is instanced per type.
  - Damage stages are swapped meshes (no per-frame cost).
  - Collapse chunks are temporary rigid bodies that sleep and then merge into a static rubble mesh.
  - Fractured pieces reuse each building's texture atlas, so there are no new materials per piece.
  - LOD: rubble and small props drop shadows beyond mid range.
  - PERF mode halves set density and skips chunk physics (straight to rubble).
