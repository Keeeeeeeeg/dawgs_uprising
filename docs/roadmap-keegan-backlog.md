# Keegan's backlog (after 26.10 Green Again, 2026-11-26)

Every item here was requested by Keegan in his session. The details of the destruction pass are in `destruction-plan.md`.

## Standing rules (from Keegan)
- **Real textures always.** Every new or reworked asset uses scanned CC0 textures (Poly Haven / ambientCG), plus a shared hand-made UNSC trim sheet (bolts, vents, panel seams, stencils, hazard strips). No more flat-coloured blocks.
- **Procedural generation.** Prefabs and their placement are rule- and seed-driven so they work on any map. Hand-placed overrides are allowed for story maps.
- **Art style.** UNSC deployed prefab, made elsewhere and set down here. A mix of Halo Wars 1 and the Halo Reach colony look: realistic but stylised, with bold silhouettes.
- **Infantry must never skate or clip.** Animations use foot locking. Units are visible while they shoot, take cover and move.

## Shipped in 26.10
- Fixed black conifers: the cone tree species had no crown radius, so their shading went to NaN.
- A finished or rebuilt building fills in the craters on its plot (`craterFill`).
- The little flags on facility buildings are removed (`facMesh` strips the `flagMat` cloth and its pole).

## Queue, in Keegan's order: art first, then behaviour

### 1. Outpost kit art (concept round 3 sent 11-26, waiting on sign-off)
- Round 3 sheets are in Keegan's `work/bld` folder (`concept3_*.jpg`); script `bconc10.py`, textures in `work/bld/tex`.
- Status: real CC0 scans, prefab modules on skids and jacks, rubble made from each building's own broken walls and roof sheets.
- After sign-off: bake per-prefab textures plus the trim sheet → game models with damage stages → swap out the blockouts.

### 2. Base platform ("apron") retexture
- Base aprons, pads and kerbs are flat untextured blocks. Re-do them with scanned concrete plus metal edging and markings, mapped in world space.
- Craters should break or alter the apron where they land. Rebuilding fills them back in (fill is done).

### 3. Visible garrisons with firing positions
- Each building gets set slots at its windows, doors and roof edges. Soldiers stand, crouch or lean at a slot and are visible while they shoot.
- The roof fades out on hover or selection.
- Soldiers walk in and out through the door with an animation.

### 4. Cover system
- Cover points on prefabs, barriers, wrecks, craters and walls.
- Squads snap to the side facing the enemy: crouched behind low cover, leaning out from tall cover.
- They move to another spot nearby when they have no line of fire.
- Suppression: going prone or ducking, with lower accuracy.
- Vaulting over low cover.
- **Craters as cover/garrison points:** they currently only give the passive coverInf 0.85. Keegan wants them usable like foxholes.

### 5. Infantry animation bank (Mixamo mocap retargeted onto our marine rig, with foot locking)
- Clips needed: crouch idle, crouched walk, cover lean, crouched fire, fire through a window, vault, step through a doorway, prone and crawl, suppressed flinch.
- Keegan downloads the clips from a list (Mixamo is free with an Adobe account); Claude retargets them in Blender.

### 6. Procedural kit assembly
- Outposts are assembled from modules by rule: door faces the road, annex goes on a free side, barriers face the nearest base.
- Dressing varies by biome and faction, and wear varies with how war-torn the map is.
- Placement prefers mostly flat areas, and the terrain under the footprint is flattened.

### 7. Environment
- **Forest floor:** extra ground textures and clutter under trees (leaf litter, needles, roots, ferns, fallen branches, mushrooms) so woods read differently from open grass.
- **Tree trunk blending:** a root flare in the geometry, a dark contact/AO decal at the base, and a litter decal where the trunk meets the ground.
- **Shrubbery:** fix the broken bush cards (stray thin planes, flat clumps).
- **Selection rings:** every unit and building gets the new stylised selection circle.
- **Devtest map:** include every biome along the map (temperate, desert, arctic, plus moon where possible).

### 8. Harbours and settlements near water (Keegan's earlier request, now on the roadmap)
- Rework harbours with quays, piers and seawalls, generated procedurally for any settlement near water.
- Same apron and texture standard as everything else.

## Known issues
- A `computeBoundingSphere NaN` console warning appears on load (it predates 26.2). The source has not been found yet.
