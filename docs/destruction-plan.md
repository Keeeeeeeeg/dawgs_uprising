# Destruction update (Keegan, 2026-11-25)

Owner: Keegan's session. Shipped so far:
- **26.3 Shell Holes**
- **26.4 Timber**
- **26.5 Impact Sites**
- **26.6 Outposts**
- **26.7 Flattened**
- **26.8 Live Wire**
- **26.9 Hold the House**

## Shipped

### 26.3 Shell Holes: craters are sim ground
- The SIM keeps craters (`BALANCE.crater`). `craterAt` makes them at projectile impacts. The angle comes from a hash of the position, so it is deterministic.
- `heightAt` = `baseH` + `crOff`, looked up through an 8 m bucket grid.
- The renderer draws craters from the `'crater'` event. Craters dug in the fog are deferred until the spot is seen.
- No craters on shorelines, in zones, on decks, or on roads (`G.setPaved`).
- Shallower: `deep` .2, `deepMax` .75. Bowls slow units and give infantry cover.
- Bowl texture: `env/crater/*`.
- Render order: terrain -20, crater passes -0.5..-0.3.

### 26.4 Timber: destructible trees
- `BALANCE.treeFall`. `treeBlast` in the sim sets `t.fall` (topple/snap/shred).
- Tree cover and woods concealment for infantry.
- Renderer destruction bank: rod-pivot physics, splinter debris, instanced stumps.

### 26.5 Impact Sites
- Aircraft and Zeppelin crash craters are sim ground: `airDown` runs a fixed-step fall prediction, and the renderer steps its falls the same way.

### 26.6 Outposts: placement + damage stages (PLACEHOLDER blockouts)
- Map generation (`buildMap`) adds `type:'site'` props with `k` = kind, `set`, `fam` and `circles` (rectangles approximated by circles).
- They use their own RNG stream (`seed^0x51735`), so existing props keep their places.
- Skipped on moon, Horde and carrier maps.
- `BALANCE.sites`: kinds (w/d/h/hp/rubbleK/gar/vis/inc/topple), set layouts per family, biome swaps, perArea 7 (sqrt area scaling), maxSets 10, spacing 90, zoneGap 45.
- The sim reuses the prop pipeline: `propHit`/`propFall`/`propCover`. `SITEK(q)` gives hp and rubbleK.
- Renderer: `siteBuild` (blockout per kind), `siteTick` (polls hp 4x/s; stages: scorch + smoke, then fire + sag), `siteFall`:
  - Prefab modules slump.
  - Concrete and stone (cottage, checkpoint, sandcrete pod, containers, silo) leave stubs and a heap.
  - `topple` kinds fall whole.

### 26.7 Flattened
- `map.crush` / `G.crush`: crates, barrels, bales, fence runs, drums and signs around each set.
- `crushAt` runs in `stepToward` for tracked and wheeled movers, and splash weapons scatter them. The `'crush'` event flattens the instanced mesh.
- Farmsteads get wall or hedge segments (each its own `site` prop, `rubbleK` 0, so shelling opens a gap).
- Ramming is not done yet.

### 26.8 Live Wire
- Roadside pylon runs (3 pylons). Renderer catenary wires (`WIRES`) snap with sparks when a pylon falls and hang from the next one.

### 26.9 Hold the House: garrisons
- `BALANCE.garrison`. Sim fields: `u.garGo` (walking to the door), `u.inBld` (prop index), `q.garF`.
- Orders and status: `applyCmd {k:'garrison',pi,ids}`; capacity is `gar*perSquad`; any other order ejects (`orderAs`).
- Combat: units inside count as `posted` (no chasing), with range x1.2 and `visK` 1.25/1.6.
- Damage: dmgK .6, artK .3 (artillery/bombs/missiles/mac/shells/cas), flushK 1.8 (flame/charge/acid).
- Collapse ejects the occupants (`garCollapse`, crush 45). A held fuel station pays $1.5/s.
- AI (`garEcon`, 1 Hz): garrisons a building within 40 m when an enemy is within 70 m, and leaves at heavy damage.
- UI: right-click a garrisonable site with infantry selected. Pips over the roof (`drawGarBars`). Units inside are hidden.
- Tested headless: 6 men in; artillery damage 30% vs bullets 60%; firing out works; collapse throws them out alive; the AI moves in.

## Concept round 1 (sheets in Keegan's `work/bld`, script `bconc4.py`) — answers
- **Direction approved:** colony prefab modules, chunky trim, hazard accents. Next round adds Halo Wars heft: armoured door frames, reinforced roof edges, louvered vents, bolted plates, bigger stencils.
- **Keep every piece.** Add a **crashed dropship hull** (original design) and a **sensor post** that gives a watchtower-style vision effect.
- **Rubble mixes by type:** prefab modules slump; concrete and stone leave stubs and a heap.
- **Fixes for round 2:**
  - Sandbag-nest tarp (smaller, darker camo net).
  - Chunkier burnt truck.
  - The desert well is missing.
  - Rubble walls on the arctic hut and container stack stand too tall.
  - Ribbed olive barn shell.

## Still to do
- Concept round 2 → sign-off → bake real art (pre-fractured chunks with light physics) → swap out the blockouts.
- Tanks ramming walls and hedgerows.
- The sensor post's vision effect (currently `vis` only applies to garrisoned kinds).
- Garrison polish: muzzle flashes at the windows, and selecting occupants by clicking the building.

## Performance budget
- **Sim:** grids everywhere; nothing loops over every object per tick. The exception is `garEcon` at 1 Hz, which loops over the sites (~30).
- **Craters:** merged meshes. Trees: instanced stumps and capped logs. Debris is capped.
- **Outposts:** each blockout group is baked per material (a few draw calls per piece). Crushables are one InstancedMesh per kind. Wires are lines.
- **Planned with the real art:** collapse chunks as temporary rigid bodies that sleep and merge into static rubble; LOD drops shadows on small props and rubble; PERF skips chunk physics.
- The number of sets is gameplay, so it can't vary with PERF; PERF only cuts visual detail.
