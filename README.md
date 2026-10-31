# Dawgs Uprising

RTS, being ported from the single-file HTML game (v21.5) to **Godot 4.7.2**.
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
| `sim/` | SIM script | Pure logic. `RefCounted` only, no `Node`, deterministic, seeded RNG. |
| `render/` | Renderer and HUD script | Reads SIM state, draws it. Never changes the SIM directly; sends commands. |
| `menus/` | Menus and campaign script | Main menu, battle setup, campaign, settings, changelog. |
| `data/` | `BALANCE` | `balance.json` plus `version.json` (version and changelog). |
| `tests/` | Node headless harness | Headless SIM checks (`godot --headless`). |

## Port status

- [x] Repo, LFS and folder setup
- [ ] Godot project skeleton (sim / render / menus / data)
- [ ] SIM: core loop, units, orders, pathing grid
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
