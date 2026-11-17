# Dawgs Uprising: Unity 6 port

A playable Unity version of the browser RTS: the Test Town map, a skirmish against the Crimson Legion AI, the game's
HUD and its unit orders and movement, Blender-made infantry (with idle animations), trees, grass, railway, and
weathered ground and building surfaces. Everything here is built from data exported out of the web game
(v24.3) by the editor tools under **Dawgs** in Unity's menu bar.

## Open it

1. Install **Unity 6000.3.27f2** with Unity Hub (the URP template's modules are enough).
2. Clone this repo with Git LFS (see the main README), then in Unity Hub: **Add > Add project from disk** and pick
   this `unity-slice/` folder. (It is separate from the `unity/` project on the `unity-switch` branch, which carries
   the C# SIM port; the two can be merged later.)
3. The first open takes a while: Unity builds its `Library/` cache (never commit it).
4. Open `Assets/Dawgs/Scenes/DawgsSkirmish.unity` and press **Play**.
   `DawgsTestTown.unity` is the same map playing back a recorded 1v1 from the web game.

## Controls (same as the browser game)

Groups of four or more ordered a long way march in formation at the slowest unit's pace (armour in columns,
infantry in ranks, artillery at the back); units keep their personal space, back up to close spots behind them
instead of turning round, and go after whoever shoots them (on a leash).

| Input | Does |
|---|---|
| Left-drag / click | select (Shift adds, double-click picks every one of that type on screen) |
| Right-click | move, attack the enemy under the cursor, or escort (guard) the friendly unit under it |
| Right-drag (2+ units) | spread the selection along the line you draw, facing across it |
| Right-drag from an enemy | draw a circle: attack every enemy inside it, one after another |
| F / H / G | fight-move / halt / guard: click one of your units to follow and protect it |
| Ctrl+A | select every military unit |
| Tab | scoreboard (armies, zones, units, kills, losses, income) |
| M | full-screen map (click or drag to move the camera) |
| Mouse at a screen edge | pan |
| Z X C, Shift+Z, Shift+X ... | train units at the base on the Recruit card |
| WASD / arrows | pan |
| Mouse wheel, + / - | zoom (towards the cursor) |
| Middle drag | orbit the camera; with Shift, pan (swap the two in Esc > Interface) |
| Home | reset the camera view |
| Space | jump home |
| Shift+1-9 / 1-9 | save / recall a control group |
| P, Esc | pause / menu (sound and interface settings) |
| Shift+M | mute the music |

## The Dawgs menu

| Menu item | Rebuilds |
|---|---|
| Build Test Town Slice | materials, meshes, prop prefabs, terrain, lighting, camera, music, then the environment upgrade, into `Scenes/DawgsTestTown.unity` |
| Build Playable Skirmish | the HUD, thumbnails and minimap, game objects, into `Scenes/DawgsSkirmish.unity` |
| Build Rigged Units | animated unit prefabs from `Assets/Dawgs/Rigged/*.fbx`, with the soldiers' idle moves |
| Upgrade Environment | the Blender trees (3 LODs, wind), grass detail layers and the modelled railway, in both scenes |
| Upgrade Ground and Buildings | the terrain's grass / meadow / bare earth / sand (height-blended), weathered concrete, paving and roofing on the buildings, sharper facades with shiny glass, in both scenes |

Everything under `Assets/Dawgs/Generated/` and the two scenes come from these menus. If you rebuild, commit the
regenerated files together in one commit.

## Layout

```
Assets/Dawgs/
  Data/        exported from the web game: game_data.json (rules, orders, movement), world.bytes (baked map meshes),
               terrain, instances.json (props), units.bytes, env_*.bytes (Blender trees / grass / track),
               ground_splat.raw (where each ground surface goes), grass_cover.raw
  Editor/      the Dawgs menu builders (DawgsSliceBuilder, DawgsPlayBuilder, DawgsRigBuilder, DawgsEnvBuilder,
               DawgsSurfaceBuilder)
  Runtime/     camera, replay, unit rigs, DawgsPrefs (settings);  Runtime/Game/ the playable skirmish
               (DawgsGame sim, DawgsUnit, DawgsGrid pathing, DawgsCommand input, DawgsHud UI Toolkit HUD, DawgsFx)
  Shaders/     Dawgs/Lit (with wall / paving / roofing detail, grime and glass), Dawgs/Unlit, Dawgs/Foliage (wind)
  UI/          DawgsHud.uss: the browser HUD's CSS, ported
  Rigged/      infantry and vehicles from Blender (FBX)
  Textures/    Surface/ (Blender-rendered ground, concrete, paving, roofing, facades), Env/, Ground/, Baked/
  Audio/
DawgsRig/      Blender sources: du_infantry.py (soldiers and their animations), du_rig.py (vehicles), du_env.py
               (trees, grass, railway, ballast texture), du_surfaces.py (ground and building surfaces),
               du_ground.py (where grass, meadow, earth and sand go), du_grass_mask.py (where grass grows),
               dawgs_infantry.blend, dawgs_rigs.blend, dawgs_env.blend
```

## Remaking the Blender art

The scripts find this folder by themselves (or set `DAWGS_ROOT` to it).
- Soldiers: open `DawgsRig/dawgs_infantry.blend` in Blender 5.2+, run `du_infantry.py`, call `run()`. Clips: Idle, Walk,
  LookAround, CheckAmmo, Stretch, AdjustGear, KneelDown, KneelIdle, KneelUp. Then **Dawgs > Build Rigged Units**.
- Trees, grass, railway: in Blender 5.2, `import du_env; du_env.run()` writes `Data/env_*.bytes` and
  `Textures/Env/ballast*.png`. Then **Dawgs > Upgrade Environment**.
- Ground and building surfaces: in Blender, `import du_surfaces; du_surfaces.run()` renders `Textures/Surface/*`.
- Where the ground surfaces go: `python du_ground.py`, then where grass grows: `python du_grass_mask.py` (Python 3
  with numpy and Pillow). Then **Dawgs > Upgrade Ground and Buildings**.

## Team rules for this folder

- Pull before you start, push small commits when you're done (`unity: ...`).
- **One person per scene.** `.unity` files are in Git LFS and can't be merged: claim a scene before editing it.
- Never commit `Library/`, `Temp/`, `Logs/`, `UserSettings/` or the `.csproj` / `.slnx` files (they're ignored).
- Commit the `.meta` files: Unity's references between assets live in them.
- Unity's AI package (`com.unity.ai.assistant`) is installed so Claude can drive the editor. Its "NoSubscription"
  message only means Unity's own AI features need a Unity AI plan; it doesn't affect the game.
