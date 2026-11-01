# Dawgs Uprising

RTS, being ported from the single-file HTML game (v22.5) to **Unity 6.3 LTS** (Unity Personal, free).
This repo is the source of truth for the whole team.

> **Engine switch (2026-10-31):** the port is moving from Godot to Unity for faster game logic (C#) and a
> higher graphics ceiling. `godot/` holds the first port (phases 1 and 2a, all tested against the web game)
> and stays as a reference until the Unity version matches it; then it is removed.

```
unity/    Unity project (open with Unity Hub, Unity 6.3 LTS)
packages/com.dawgs.sim/  the game logic (SIM): plain C#, no UnityEngine; Unity loads it as a local package
tests/SimTests/          runs the SIM's checks outside Unity:  cd tests/SimTests && dotnet run -c Release
godot/    first port in Godot (reference until the Unity port matches it)
blender/  Blender source files (.blend, via Git LFS)
web/      The original single-file HTML game, kept for reference
tools/    scripts that record the web game for the tests
```

## Setup (Unity)

1. Install **Unity Hub**: https://unity.com/download
2. In Unity Hub: **Installs → Install Editor → Unity 6.3 LTS, 6000.3.27f2** (everyone must use this exact version;
   not 6.6, which Hub marks "Recommended"). Keep the default modules.
3. Sign in and pick the free **Unity Personal** licence when Hub asks.
4. Install **Git LFS** once per machine (https://git-lfs.com), then `git lfs install`.
5. Clone, then in Unity Hub: **Add → Add project from disk** and pick the `unity` folder.

## Team rules

- **Pull before you start.** `git pull` every time you sit down, before touching anything.
- **Push when you're done.** Small commits with clear messages, e.g. `sim: port orderMove pathing`.
- **One person per scene or prefab.** Scene (`.unity`, `.tscn`) and prefab files merge badly. Claim one in the team chat before editing it, and say when you're finished.
- **Never commit Unity's `Library/`, `Temp/`, `Logs/` or `UserSettings/`, or Godot's `.godot/`.** They're in `.gitignore`. If one shows up in `git status`, stop and ask. Do commit every `.meta` file.
- **No numbers in engine code.** Every gameplay number goes in the data files (`balance.json`, the old `BALANCE` object, plus `maps.json`, `mapgen.json`, `factions.json`).
- **The SIM never touches rendering.** The game logic is plain C# with no `UnityEngine` (in Godot: no nodes). It runs and is tested outside the engine.
- Big binary files (`.blend`, `.glb`, images, audio, fonts) go through Git LFS automatically. Check `git lfs ls-files` if unsure.

## Project layout (godot/, reference until the Unity port matches it)

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
