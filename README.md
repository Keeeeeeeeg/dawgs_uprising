# Dawgs Uprising

RTS, being ported from the single-file HTML game (v22.5) to **Unity 6.3 LTS** (Unity Personal, free).
This repo is the source of truth for the whole team.

> **Engine switch (2026-10-31):** the port moved from Godot to Unity for faster game logic (C#) and a
> higher graphics ceiling. The Unity SIM now matches everything the Godot port did (phases 1 and 2a).
> `godot/` is kept only as code to read: its data and test recordings moved to `data/` and `tests/golden/`,
> so it no longer runs. It will be deleted.

```
unity/                   Unity project (open with Unity Hub, Unity 6.3 LTS)
packages/com.dawgs.sim/  the game logic (SIM): plain C#, no UnityEngine; Unity loads it as a local package
data/                    every gameplay number and map: balance, maps, mapgen, factions, version
tests/SimTests/          runs the SIM's checks outside Unity (see "Run the tests")
tests/golden/            recordings of the web game that the checks compare against
web/                     the original single-file HTML game (v22.5, frozen during the port)
tools/                   Node scripts that record the web game into tests/golden/ and export data/
blender/                 Blender source files (.blend, via Git LFS)
godot/                   the first port, code only (to be deleted)
```

## Setup (Unity)

1. Install **Unity Hub**: https://unity.com/download
2. In Unity Hub: **Installs → Install Editor → Unity 6.3 LTS, 6000.3.27f2** (everyone must use this exact version;
   not 6.6, which Hub marks "Recommended"). Keep the default modules.
3. Sign in and pick the free **Unity Personal** licence when Hub asks.
4. Install **Git LFS** once per machine (https://git-lfs.com), then `git lfs install`.
5. Install the **.NET 10 SDK** (https://dotnet.microsoft.com/download) to run the SIM tests.
6. Clone the whole repo (Unity reads the SIM from `packages/` next to `unity/`), then in Unity Hub:
   **Add → Add project from disk** and pick the `unity` folder.

## Team rules

- **Pull before you start.** `git pull` every time you sit down, before touching anything.
- **Push when you're done.** Small commits with clear messages, e.g. `sim: port orderMove pathing`.
- **One person per scene or prefab.** Scene (`.unity`) and prefab files merge badly. Claim one in the team chat before editing it, and say when you're finished.
- **Never commit Unity's `Library/`, `Temp/`, `Logs/` or `UserSettings/`.** They're in `.gitignore`. If one shows up in `git status`, stop and ask. Do commit every `.meta` file, including the ones Unity writes in `packages/`.
- **No numbers in engine code.** Every gameplay number goes in the data files in `data/` (`balance.json`, the web game's `BALANCE` object, plus `maps.json`, `mapgen.json`, `factions.json`).
- **The SIM never touches rendering.** The game logic is plain C# with no `UnityEngine`. It runs and is tested outside the engine.
- Big binary files (`.blend`, `.glb`, images, audio, fonts) go through Git LFS automatically. Check `git lfs ls-files` if unsure.

## The SIM (`packages/com.dawgs.sim`)

The web game's SIM script, in C#. Unity loads it as a local package; the tests compile the same files.

- **Deterministic.** Same seed and same commands give the same battle on every machine (multiplayer relies on it).
  Random numbers only from `Rng`; `sin`, `cos`, `atan2`, `pow`, `hypot` and `round` only through `DMath`, which gives
  V8's exact results. Never `System.Random`, `UnityEngine.Random`, `Mathf`, or `Math.Sin`-style calls; doubles,
  not floats or `Vector3` (32-bit), except where the web game itself uses 32-bit arrays.
- **No engine, files or clocks.** The assembly has `noEngineReferences`. It takes the data files' text
  (`GameData.FromJson`), so Unity can hand it the files and the tests can read them from disk.
- **Typed data.** `Bind` fills typed classes from the JSON; a key with no matching field is an error, so data typos
  show up at once (keys starting with `_` are notes and skipped).
- **Follows the web code.** Same order of operations and same field names, so it can be checked line by line.

## Run the tests

From the repo root:
```
cd tests/SimTests
dotnet run -c Release
```
It prints one line per check and `TESTS PASSED n/n` when everything matches the web game. Run it before every push.
A check that crashes counts as a failure. The checks compare the SIM with recordings of the web game in
`tests/golden/`; when `web/` changes, re-record them with the scripts in `tools/` and commit them with the port change.

## Port status

- [x] Repo, LFS and folder setup
- [x] Unity 6.3 LTS project (URP) with the SIM as a local package
- [x] SIM phase 1: exact maths, maps, Chaos Isles, terrain, pathfinding, spatial hash, unit/base tables (identical to web v22.5)
- [x] SIM phase 2a: battle setup (armies, bases, start slots) and build plots (runways, streets, quays, plots, levelling)
- [x] SIM phase 2b: units, orders (move, attack-move, attack, stop, formations, stances, guard), movement, combat, projectiles (ground units, helicopters and boats; checked tick by tick against 5 web scenarios)
- [ ] SIM: the rest of the core loop (starting garrisons and squads, rovers and construction, recruiting, healing)
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
