# Dawgs Uprising: handoff (2026-11-25, from Keegan's Claude session)

Read this first, then `docs/roadmap.md` (full history and backlog), `docs/ventora-conventions.md` (engine rules + pitfalls) and `docs/team-playbook.md`. (The same docs also live in Keegan's claude.ai project "RTS Game" under `claude/`; if one is missing here, ask Keegan to upload it.)

## Where things are
- **Live game (source of truth):** artifact https://claude.ai/code/artifact/f19e611d-226f-4d81-b847-d27ca14a589b (shared with the org; Andrew also publishes to it). Current version **25.74.1**. Its published files hold everything the game needs: `index.html` (one big page), `tex/veh/vtex.js` (baked vehicles), `tex/marine/skint.js` (skinned marines), `tex/fort/*`, `env/*` (skies, terrain colour + normal maps, water normals, foliage atlas `env/foliage/foliage_ground_c.webp`, rocks `env/rocks/rocks.js` + `rocks_c.jpg`), `sfx/*` (sound bank + `credits.json`), `music/*`. Also `envtest.html` (old scenery test page, no longer linked).
- To work on it: Artifact `read` the URL (you get index.html); read other published files with `path`. Edit locally, bump `GAME_VERSION`, add a `CHANGELOG` entry with `by:'<who>'`, `node --check` every inline script, test in Playwright (route a fake host to your local folder; swiftshader), re-read live before publishing and merge if someone published in between, then publish with `url` = the artifact and `files` for any changed assets.
- **The previous session's cloud workspace is NOT transferable** (tools, cloud Blender scripts, sound tools, QA scripts are gone with it). Blender sources that matter were mirrored to Keegan's PC: `~/3D Objects/DawgsUprising/work/` (veh/*.py models + vbake.py, env pack sources) and `.../overnight/` sheets. Keegan's desktop Blender (RTX 2070, OptiX) is driven through the Blender MCP; use a separate scene `claude_work`, never touch his own scenes.
- Sound Board (private to Keegan; ask him to share): https://claude.ai/artifact/2RqBPcSvzpuUZkWAxCmhc9

## Shipped (newest first)
- 25.74.1: menu tanks no longer miss left-side pods/gun/chute (menu decoder skipped every part ending in 'L'; now only hullL/turretL).
- 25.74 Dry Fire: Keegan's liked sounds in game: w_burst1-3 = dry M16 3-round burst (Freesound 145206; burst2/3 pitched .95/1.05), w_mg1-5 = single rounds of 383796, w_hmg1-4 = rounds of 396324; x_boom5 -6 dB; credits.json updated.
- 25.73.1: Performance mode scatters half the rocks.
- 25.73 Grounded: soft contact shade under scattered rocks.
- 25.72.1: menu explosions no longer white out.
- 25.72 Meadow: ground cover sways + per-plant tint.
- 25.71 Windbreak: trees sway in the wind, clustered leaf shading (treeMat in the tree section; wind clock `window.__TW`, advanced in the frame loop).
- 25.70 Bedrock: PROCEDURAL rocks (rule-based scatter from terrain splat/slope/noise, excluded from water/roads/yards/bases; `ENVRK` helper decodes env/rocks), map rock outcrops rebuilt from scanned rocks, terrain shader height-blend + normal-map relief + macro tint.
- 25.69 Opening Shot: main menu battle uses baked tanks + SAM sites (menu-local decoder `mvkMesh`, since game code lives inside the battle boot function), sky-pack skies, new ground maps.
- 25.68 Open Skies: skyboxes + time-of-day picker (skirmish/horde/carrier setup), campaign/grand strategy rotate skies, new terrain maps, water normals, camera-following ground cover (shrink-fade, lit with an up normal), team-colour rim, `#tune` panel (sliders + ground cover on/off).
- 25.67.x: heavy tank ht_k, round wheels, SAM 4096 + scale 1.15, Freesound explosions/cannons, flagpole removed.

## Direction agreed with Keegan
- Scenery is PROCEDURAL: rules place everything from a seed (terrain material, rocks, plants, trees, later battle wear); map makers keep only the gameplay layout. Already rule-based: terrain splat, trees (also harvestable by Construction Rovers via G.setTrees), ground cover, rocks.
- Look target: Halo Wars, stylised but grounded.
- Trees: real textured trees that DON'T look flat: crowns of intersecting textured leaf-cluster cards (alpha-tested, from a scanned branch) with spherical/bent normals per crown, bark texture on trunks, 2 LODs, placed by the existing tree rules; keep harvest ids (TREE_INST).
- Work order (Keegan): (1) main menu attract mode, (2) audio, (3) tank treads + 4096 rebake, (4) scenery (trees, shorelines, desert/arctic checks, colour grading, contact shade under buildings, tuning-slider defaults).

## 1. Main menu battle: rebuild as a real-engine "attract mode"
- Problem: the menu backdrop (`MenuBG` IIFE, visual-only fake battle) has its own effects, movement and models: medium fires one slow shell (not the rotary burst), no new scenery (old dome/ground/cone trees), units drive through barriers (no collision), infantry are single men not squads, deaths use old models, some old kit models remain.
- Direction: replace it with an ATTRACT MODE that boots the real game (small map, AI vs AI, both sides fighting in view, fog off, HUD hidden, cinematic camera path, sim sounds at menu volume) behind the menu, torn down (existing MenuBG.stop path / bootWith) when a real battle starts. Everything then matches the game automatically.
- Watch: load time and GPU cost on the menu (small map + PERF-like settings), memory freed on teardown, no saves/stats from the attract battle, music stays the menu track.

## 2. Audio
- Cause of the echo/distant feel: free gun/explosion sources are outdoor range recordings (reflections baked in, distant mics) + long tails stacking in fights.
- APPROVED source: **Sonniss GDC Game Audio Bundles** (royalty-free for games; raw files may not be redistributed, so never commit them to this repo). Keegan downloads a bundle and extracts weapon/explosion/impact/debris/mechanism/UI folders to `~/3D Objects/DawgsUprising/sfx_refs`.
- Still to REPLACE: rifles (w_rifle1-5), pistols (w_pistol1-3), snipers (w_sniper1-3), shotguns (w_shot1-3), l_clank, l_steps, m_debris1-4, m_metal1-5, u_ping, w_node1/2, w_rocket1, w_sam, x_collapse2, x_dull. Approved as is: ambient beds, interface (except u_ping), generators/pumps/fire, other engine loops, the 25.74 bursts/MG/HMG. Synthetic layered gunshots (pass 2) were rejected: never add sine thumps / noise cracks.
- Rifle candidates waiting on Keegan's pick on the Sound Board: p4_rifle_a1/a2 (single rounds of the liked M16 burst), p4_rifle_b1/b2 (M4, Freesound 259758).
- Processing: trim to onset, hold 30-100 ms, fade/de-reverb the room tail, low shelf, 35 Hz cut, gentle tanh, normalise; automatic fire round by round. A/B on the Sound Board before shipping.
- Engine: one shared short biome reverb send + distance model (near = bright/loud, far = lowpassed/quieter) + a light limiter on the SFX bus. Also: DEVTEST "Sounds" tab listing every sound by the unit/action that triggers it, with a still of the unit and a play button.

## 3. Tank treads
- Track ribbons as their own groups with UVs along the loop + tiled tread texture from each tank's real links, scrolled by speed; wheels spin; rebake light/medium/heavy at RES 4096 on Keegan's desktop Blender.

## Known issues
- Swiftshader (headless) can't show the ground cover; check it on a real GPU.
- Rocks add ~320k tris close up (incl. shadows); small stones use the 100-tri LOD without shadows.
- aa1 top view loses the ground scorch fan in the bake (cause unknown).
- Performance on real hardware with the new scenery not yet checked.
