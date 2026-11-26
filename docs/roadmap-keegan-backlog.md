# Keegan's backlog (after 26.17 Footing, 2026-11-26)

Every item here was requested by Keegan in his session. The details of the destruction pass are in `destruction-plan.md`. Design language from Keegan's reference images: `3D Objects/DawgsUprising/references/DESIGN_LANGUAGE.md` (12 vehicle and location references next to it).

## Standing rules (from Keegan)
- **Real textures always, weathered.** Every new or reworked asset uses scanned CC0 textures (Poly Haven / ambientCG) plus a shared UNSC trim sheet, with a weathered look: darker lower third, edge wear, dust and stains. No flat-coloured blocks. In the code, `weatherize(mat, tex, mean, {scale, k, grime})` (26.16) adds world-space triplanar scanned detail and grime to any material.
- **Procedural generation.** Prefabs and their placement are rule- and seed-driven so they work on any map. Hand-placed overrides are allowed for story maps.
- **Art style.** UNSC deployed prefab, made elsewhere and set down here, in a Halo Wars 1 and Halo Reach colony mix with a **lived-in** feel. See DESIGN_LANGUAGE.md for the details: faceted slab-armour vehicles, olive paint with stencils and one accent stripe, pod-and-catwalk outposts.
- **Infantry must never skate or clip.** Visible in and out of cover and buildings.
- **QA gates on every asset:** nothing floating, no flipped textures, lights placed sensibly, close-up turntables, checked against the reference images.

## Outpost direction: semi-prefab locations in the style of Helldivers 2
(unchanged; see the 26.15 notes) Small and medium kits plus one large landmark. Entrenchments are built into the generator. Ring farms, the sensor relay, and the universal positions/cover system built from the wall-manning code, using the hero-piece approach.

## Shipped 11-26
- **26.12 Hardstand**, **26.13 Forest Floor**, **26.14 Brackets**, **26.15 Dug In** (sensor relay + ping, entrenchments): see git history and the in-game changelog.
- **26.16 Strike Art** (Andrew): loading screen art.
- **26.17 Footing:**
  - **Motion-captured locomotion.** The Mixamo Pro Rifle Pack, downloaded by Keegan to `Downloads/`, is retargeted onto our marine rig (legs, hips, spine, head; our arms keep the weapon grip) and stored in `anim/bank.js`: 48 clips as int16 quaternions, about 190 KB.
    - `locoClip()` blends the 2 nearest of 8 directions × the 2 nearest gaits (walk/run/sprint, or crouch-walk while engaging).
    - Every clip is phase-locked to the left heel strike. The phase advances by distance over the clip's own stride, so feet don't skate.
    - The extractor is `/home/claude/anim/x/ex.html` (three r128 FBXLoader in Playwright): world-space delta from the Mixamo T-pose, C = Ry(90°), bind-direction correction.
  - **Leg IK** (`legIK`): the hips drop to the downhill foot, analytic two-bone IK keeps the knee plane, the ankle tilts to the ground normal (capped at 30°), and stance feet are locked. Skipped on walls, decks, roofs, prone, swimming and climbing.
  - **Ballistic missile renamed Tactical Nuke** (UI text and the Nuke Silo; internal names unchanged).
  - **Forest litter:** only in green woods (4+ trees within 11 m), with ragged noise-broken edges.
  - Build pads in scanned concrete.
  - The flag-pole leftovers are removed (matched in world space).
  - Cactus get a ribbed skin.
  - Fallback rocks get the scanned rock texture.

## Queue (Keegan 11-26 afternoon, roughly in his order)
1. **Infantry pass**
   - **Ankles crazy on some kits:** the rocket team's kneeling loader shows a twisted rear foot. Fix the kneel pose per kit and check every template in close-up turntables.
   - Weapon grips (hands on the weapon per kit), the rig, and full-resolution marine textures.
   - **Three-man MG crews** (gunner, loader, spotter) with set-up and tear-down.
   - **Flag bearer rework:** better model, a proper banner with cloth sway, a two-handed grip, and the plant/wave animation redone.
   - **Boarding Marines' breacher shield:**
     - collapsed into a tight hourglass silhouette while moving, unfolding when deployed;
     - detail and style in our design language.
   - **More clips into the bank** (`anim/bank.js`), as described below.
     - Wire up the clips the bank already holds: deaths (6 directions), crouch turns and stand turns (for turning on the spot), jump up/loop/down (vaulting trenches and walls).
     - Then add more from Mixamo: cover sneak left/right, shield-face and rub-eyes reactions, prone hit, kneel↔prone↔stand transitions, firing while walking/running, reload, grenade throw. Keegan downloads them in Chrome or Edge (the in-app browser can't save files).
   - **Squads only:** roll the single-man **Deck Marine** into a regular rifle squad, and the single-man **Boarding Marine** into the Boarding Marines squad.
   - Sounds and small details: footsteps per surface, gear rattle, reload and handling sounds.
   - **Performance for crowds:** bake the clip bank into a vertex-animation texture so far squads animate on the GPU with instancing; full skinning plus IK only near the camera.
2. **Biomes look consistent**
   - **Desert:** sand-dune texture in some areas and exposed rough rock with wadis around the mountains. Cactus with real scanned detail and better shapes. Desert scrub instead of forest litter.
   - **Arctic:** snow ground under the woods (no brown litter discs), snow-laden conifers, scanned snow and ice. **Icebergs** reshaped into natural forms (tall tabular cliffs with blue ice faces, wave-cut notches and small growlers; not low-poly domes) with a scanned ice texture and subsurface tint.
   - **Shrubbery to modern RTS standard:** the current bushes read as flat cards and fronds. The approach:
     - mesh clusters with alpha-tested cards from scanned plant atlases;
     - normals bent to a sphere so lighting reads as one volume;
     - a two-tone colour gradient from base to tip and wind sway;
     - contact AO at the base;
     - distance LOD, then an impostor;
     - placement rules: shrubs cluster at wood edges, rocks and walls, not evenly sprinkled.
3. **Buildings overhaul:** every building and its flat colours get scanned materials and weathering via `weatherize` and a UNSC trim sheet, then a per-building rework following DESIGN_LANGUAGE.md.
4. **Wrecks use the real model:** anything dead on the map (the old box "heavy tank" wrecks and others) uses the in-game model of that unit, burnt (charred material, smoke and soot), not a stand-in.
5. **Tactical nuke effect:**
   - Today the mushroom cloud is a flat sprite that turns with the camera.
   - Rebuild it as volumetric: a stack of noise-shaded spheres or particles with a rising stem, a rolling cap with an inner glow, a ground ring of dust (all camera-independent), heat haze and a shockwave.
6. **Spawn-in clutter: placement rules.**
   - The units a base spawns, and the facilities and props round a base, overlap and clip, so the design looks busy.
   - Rules to add to the generator:
     - keep-out footprints per building, pad and road;
     - a spawn/rally apron per building, with units leaving along a lane;
     - a minimum gap between pads;
     - props only in designated clutter slots;
     - spawned vehicles placed in free parking slots, never on top of each other;
     - a clean road-facing front.
7. **The concrete bunker prop becomes a small fortifiable location:** a colony-prefab mini outpost in the diffuse layout (a bunker module, a trench or sandbag ring, a gun pit, crates and a light), with snappable cover positions.
8. **Concept round 5** from Keegan's reference images (now in `references/`), hero-piece first.
9. Then the earlier queue:
   - apron × craters
   - visible garrisons with firing positions
   - the universal positions/cover system
   - procedural kit assembly
   - harbours

## Known issues
- A `computeBoundingSphere NaN` console warning appears on load (it predates 26.2).
- An occasional tree from the forest clusters can stand at a trench edge.
- The pack has two zips (`Pro Rifle Pack.zip`, `Rifle 8-Way Locomotion Pack.zip`) holding the same 49 clips. Some files only parse from one of them in the r128 FBXLoader, so the extractor takes each clip from whichever zip parses.
