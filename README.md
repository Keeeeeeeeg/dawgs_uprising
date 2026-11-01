# Dawgs Uprising

RTS, being ported from the single-file HTML game (v22.5) to **Godot 4.7.2**.
This repo is the source of truth for the whole team.

```
godot/    Godot project (open godot/project.godot)
blender/  Blender source files (.blend, via Git LFS)
web/      The original single-file HTML game, kept for reference
```

## Setup

1. Install **Godot 4.7.2** (standard build, not .NET): https://godotengine.org/download
2. Install **Git LFS** once per machine: https://git-lfs.com, then run
   ```
   git lfs install
   ```
3. Clone:
   ```
   git clone https://github.com/Keeeeeeeeg/dawgs_uprising.git
   cd dawgs_uprising
   git lfs pull
   ```
4. Open Godot, click **Import**, and pick `godot/project.godot`.
5. Press **F5** to run. The first open takes a moment while Godot builds its `.godot/` cache.

## Team rules

- **Pull before you start.** `git pull` every time you sit down, before touching anything.
- **Push when you're done.** Small commits with clear messages, e.g. `sim: port orderMove pathing`.
- **One person per scene file.** `.tscn` files merge badly. Claim a scene in the team chat before editing it, and say when you're finished.
- **Never commit `.godot/`.** It's in `.gitignore`. If it ever shows up in `git status`, stop and ask.
- **No numbers in engine code.** Every gameplay number goes in `godot/data/balance.json` (the old `BALANCE` object).
- **The SIM never touches rendering.** Nothing under `godot/sim/` may use nodes, scenes, input or the renderer.
- Big binary files (`.blend`, `.glb`, images, audio, fonts) go through Git LFS automatically. Check `git lfs ls-files` if unsure.

## Project layout (godot/)

| Folder | Web version equivalent | Rule |
|---|---|---|
| `sim/` | SIM script | Pure logic. `RefCounted` only, no `Node`, deterministic, seeded RNG. Use `dmath.gd` for sin/cos/atan2/pow/hypot/round, and plain floats or `[x, z]` arrays, never `Vector2`/`Vector3` (32-bit). |
| `render/` | Renderer and HUD script | Reads SIM state, draws it. Never changes the SIM directly; sends commands. |
| `menus/` | Menus and campaign script | Main menu, battle setup, campaign, settings, changelog. |
| `data/` | `BALANCE` and map/army data | `balance.json`, `maps.json`, `mapgen.json`, `factions.json`, `version.json` (version and changelog). |
| `tests/` | Node headless harness | Headless SIM checks (see below). |

Other folders: `web/` holds the web game the port is based on (v22.5, frozen during the port), and `tools/extract_balance.js` regenerates balance numbers from it without running it.

**Run the tests:** open `tests/run_tests.tscn` and press **F6**, or from the repo root:
```
godot --headless --path godot res://tests/run_tests.tscn
```
It prints `TESTS PASSED n/n` when everything is fine. Run it before every push. A check that crashes counts as a failure. If the run never finishes, a script failed to compile: look in the Debugger's **Errors** tab.

**Commit the `.uid` files.** Godot 4.7 writes a `something.gd.uid` next to each script the first time it opens the project. They belong in git; `.godot/` does not.

## Port status

- [x] Repo, LFS and folder setup
- [x] Godot project skeleton (30/30 tests pass in Godot 4.7.2) (sim / render / menus / data)
- [x] SIM phase 1: exact maths, maps, terrain, pathfinding, spatial hash, unit/base tables (identical to web v22.5)
- [ ] SIM: core loop, units, orders, movement, combat
- [ ] SIM: zones, base types, capture, garrisons
- [ ] SIM: walls, gates, team grids, manning
- [ ] SIM: air (airbase cycle, carriers), naval
- [ ] SIM: AI (`aiThink`, `carrierAI`)
- [ ] SIM: fog of war
- [ ] SIM: determinism check (`stateHash` matches across runs)
- [ ] Renderer: terrain, camera, units, buildings
- [ ] Renderer: Blender models (HQ, Fortress, light perimeters)
- [ ] Renderer: effects, scorch, tone mapping, art direction
- [ ] HUD: selection, command bar, minimap
- [ ] Menus: main menu, battle setup, settings, changelog
- [ ] Campaign: ocean of continents, carrier fleets
- [ ] Tutorial (Training Grounds)
- [ ] Music rotation
- [ ] Multiplayer (lockstep, rejoin)
