# Keegan's backlog (after 26.10 Green Again, 2026-11-26)

Every item here was requested by Keegan in his session. The details of the destruction pass are in `destruction-plan.md`.

## Standing rules (from Keegan)
- **Real textures always.** Every new or reworked asset uses scanned CC0 textures (Poly Haven / ambientCG), plus a shared hand-made UNSC trim sheet (bolts, vents, panel seams, stencils, hazard strips). No more flat-coloured blocks.
- **Procedural generation.** Prefabs and their placement are rule- and seed-driven so they work on any map. Hand-placed overrides are allowed for story maps.
- **Art style.** UNSC deployed prefab, made elsewhere and set down here. A mix of Halo Wars 1 and the Halo Reach colony look: realistic but stylised, with bold silhouettes, and a **lived-in** feel.
- **Infantry must never skate or clip.** Animations use foot locking. Units are visible while they shoot, take cover and move.
- **QA gates on every asset (run by script before Keegan sees anything):**
  - Nothing floating: every part rests on the ground or on another part.
  - No flipped or mirrored textures or stencils.
  - Lights make sense: door lamps over doors, floodlights aimed at work areas, beacons on mast tops.
  - Close-up turntables (front, side, 3/4, close-up) at game-camera distance, not only sheets.
  - Reference images from Keegan's `3D Objects/DawgsUprising/references` folder.

## Outpost direction (Keegan 11-26): semi-prefab locations in the style of Helldivers 2
- Locations are built from hand-made kits that snap together by rule: modules with sockets for doors, annexes, barrier lines and lights. A lived-in clutter layer goes on top: cable runs, crates and fuel cells by doors, tyre ruts, worn paths, lights on poles, litter.
- **Size tiers per map:** mostly small (1-3 modules) and medium (4-7 modules with entrenchments), plus **one large landmark** (a ring farm or relay station). They must not compete with the bases.
- **Entrenched positions, all part of the generator:** trench runs (revetted with sheet steel and sandbags), gun pits, deployable barrier lines with firing slits, and garrisonable prefab bunkers. These are the same cover points the cover system uses.
- **Farms become Halo Reach ring farms:** concentric crop rings about **60 m across** (2-3 rings) with a sweeping centre-pivot irrigation arm and a hub of space-colony equipment: silos, a processing module, a water tower, solar arrays. It is the large landmark candidate.
- **Sensor relay:** an original design in the spirit of the Helldivers 2 lidar node, in the colony-prefab style. A deployable tripod with a spinning scanner head and beam, a cabled power cell, a barrier ring and a warning beacon, set inside emplacements. Gameplay:
  - A watchtower-style vision bonus while held/garrisoned.
  - **A new ping ability:** its owner can reveal a chosen spot anywhere on the map, with a cooldown.
- Concept round 3 was rated "close, one more round". Round 4 applies all of the above.

## Shipped in 26.10
- Fixed black conifers: the cone tree species had no crown radius, so their shading went to NaN.
- A finished or rebuilt building fills in the craters on its plot (`craterFill`).
- The little flags on facility buildings are removed (`facMesh` strips the `flagMat` cloth and its pole).

## Queue, in Keegan's order: art first, then behaviour
1. **Concept round 4:** semi-prefab POI kit (small/medium tiers), ring farm landmark, sensor relay with emplacements, entrenchment kit; QA gates and turntables. Then sign-off → bake → swap out the blockouts.
2. **Base platform ("apron") retexture:** military concrete (expansion joints, oil stains, tyre marks), a bevelled bolted steel kerb, worn paint lines and chevrons. Craters break or alter the apron where they land; rebuilding fills them back in (fill is done).
3. **Visible garrisons with firing positions:** slots at windows, doors and roof edges; soldiers stand, crouch or lean and are visible while they shoot; the roof fades out on hover; soldiers walk in and out through the door with an animation.
4. **Cover system:** cover points on prefabs, barriers, trenches, pits and wrecks; snapping to the side facing the enemy (crouch behind low cover, lean from tall cover); moving to a nearby spot when there's no line of fire; suppression; vaulting. **Craters stay a small passive bonus only** (Keegan 11-26).
5. **Infantry animation bank:** Mixamo clips retargeted onto our marine rig with foot locking (crouch idle and walk, cover lean, crouched fire, fire through a window, vault, step through a doorway, prone and crawl, flinch). Keegan downloads them from a list; Claude retargets them.
6. **Procedural kit assembly:** rule-based layouts (door faces the road, annexes on free sides, barriers toward the nearest base); biome, faction and wear dressing; placement on mostly flat ground with the footprint flattened.
7. **Environment:**
   - Forest-floor textures and clutter.
   - Tree-trunk blending (root flare, contact AO decal, litter ring).
   - Bush card fix.
   - Stylised selection rings for every unit and building.
   - A Devtest map with every biome.
8. **Harbours and settlements near water:** quays, piers and seawalls, generated procedurally, to the same apron and texture standard.

## Known issues
- A `computeBoundingSphere NaN` console warning appears on load (it predates 26.2). The source has not been found yet.
