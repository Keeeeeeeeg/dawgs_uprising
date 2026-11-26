# Keegan's backlog (after 26.15 Dug In, 2026-11-26)

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
- **Farms become Halo Reach ring farms:** concentric crop rings about **60 m across** (2-3 rings) with a sweeping centre-pivot irrigation arm and a hub of space-colony equipment.
- **Sensor relay:** an original design in the spirit of the Helldivers 2 lidar node, in the colony-prefab style. Watchtower-style vision while held; a ping that reveals any spot on the map, with a cooldown.
- **Universal positions system (agreed 11-26):** one snap/cover system built from the wall-manning code and applied to every structure. Positions carry facing, stance, cover value, firing arc and access; they degrade with damage; the AI scores them the same way; exported from Blender as `POS_*` empties. Hero-piece approach: one asset taken to final quality first as the reference for the rest.

## Shipped overnight (11-26)
- **26.12 Hardstand:** scanned concrete apron with expansion joints and stains; kerbs get scanned detail.
- **26.13 Forest Floor:** leaf-litter floor under woods; dark contact patches at the foot of trunks.
- **26.14 Brackets:** buildings get the stylised selection ring (picked building in city view, inspected enemy building, selected enemy/neutral base). Devtest has every biome: snow west, green middle, desert on the Airbase island, a wood in each.
- **26.15 Dug In:**
  - **Sensor Relay landmark**, one per map (not Horde, carrier or Moon), placed on the flat spot nearest the map centre with its own RNG stream (`seed^0x7e1a7`), so existing outposts don't move. Kind `relay` in `BALANCE.sites.kinds` (gar 2, vis); tuning in `BALANCE.relay` (visR 105, pingR 42, pingT 14 s, cd 90 s).
  - Holding it (infantry inside → `q.relF`) gives the team sight of visR round it. **Relay ping** (V, button beside Missile) is the command `{k:'relayping',x,z}` → `G.reveals` stamped into both the player fog and the AI team grids. The AI pings the nearest hostile base it can't see.
  - **Entrenchments:** `map.trenches` (segments, own RNG `seed^0x3e9c1`). A kinked trench in front of medium military outposts (65%) and two curved runs round the relay. Infantry in one take `BALANCE.entrench.coverInf` (0.5) of the damage (`G.inTrench`, cell grid). Drawn with scanned hessian sandbags (Poly Haven hessian_230), timber posts and a scanned dirt floor (`env/trench/`). Trees are kept out of them.
  - The relay and trench art is placeholder until the round-4 concept pieces are built.

## Queue, in Keegan's order: art first, then behaviour
1. **Concept round 5** from Keegan's reference images (he adds them to `references/`), using the hero-piece approach. Then sign-off → bake → swap out the blockouts (relay and trenches first).
2. **Apron × craters:** craters break or alter the apron where they land (the fill on rebuild is done).
3. **Visible garrisons with firing positions** (window/door/roof slots, visible shooters, roof fades on hover, door walk-in animation).
4. **Universal positions / cover system** (see above). Trenches and gun pits become position sets. **Craters stay a small passive bonus only.**
5. **Infantry animation bank:** Mixamo clips retargeted onto our marine rig with foot locking. Keegan needs a short walkthrough of how Mixamo works first.
6. **Procedural kit assembly** (door faces the road, annexes on free sides, barriers toward the nearest base; biome/faction/wear dressing).
7. **Environment:** bush card fix (still open).
8. **Harbours and settlements near water:** quays, piers and seawalls, procedural, to the same apron and texture standard.

## Known issues
- A `computeBoundingSphere NaN` console warning appears on load (it predates 26.2). The source has not been found yet.
- An occasional tree from the forest clusters can still stand at a trench edge (the exclusion covers the scattered trees only).
- An own base selected shows the existing wall glow plus the pad ring; the big bracket ring is only for enemy/neutral bases.
