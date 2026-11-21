# Read this first (for every Claude working in this repo)

This is **Dawgs Uprising**, a browser RTS built with Keegan, who is the art director and signs off every design. Before you do anything else, read these in order:

1. `docs/team-playbook.md`: how we roll content out (family design → vertical slices), how to claim a group, the art standard, and the shipping rules.
2. `docs/conventions.md`: engine conventions, the **INFANTRY STANDARD**, and the pitfalls list. Read the pitfalls even if you skim the rest.
3. `docs/roadmap.md`: decisions, status, and what's in progress (newest at the bottom).

The same docs also live in the claude.ai project "RTS Game" (`claude/team-playbook.md`, `claude/ventora-conventions.md`, `claude/roadmap.md`). Those are the live copies: check them for newer edits, and update both when you change something.

## Hard rules
- **Claim before you work.** One person per family. Add yourself under "In progress" in the roadmap.
- **The live game is the claude.ai artifact.** Always build on the live published version, merge if someone published in between, bump `GAME_VERSION`, and add a `CHANGELOG` entry with `by:'<name>'`. Commit each publish here as `web/live/index.html`.
- **Code safety.**
  - Run `node --check` on every `<script>` block before you publish.
  - Never put a `//` comment in the middle of a line that has more code after it.
  - Every gameplay number goes in `BALANCE`.
- **Art.**
  - Designs are original; references set the language only.
  - QA must report 0 issues before you show renders.
  - Keegan approves Cycles stills before any bake.
- **Blender.** Run one bake job at a time. The scripts use absolute paths under `/home/claude/` (body, lp, wpn, veh, hm, mg, tools, vu): symlink `blender/scripts/*` and `tools/web-harness` to those, or adjust the paths.

## Layout (this repo also holds the Godot and Unity ports: `godot/`, `unity-slice/`, `web/dawgs_uprising_v22.5.html` and `tools/*.js` belong to the port work; follow README.md rules there)
- `web/live/index.html`: the CURRENT web game (the live claude.ai artifact), committed on every publish
- `docs/`: team playbook, conventions, roadmap (mirrors of the claude.ai project docs)
- `blender/scripts/body/`: marines (`body8.py` is the base body; `marine_bd.py` is the Boarding Marines; `qa5.py` is the QA gate; `vpaint_src.py`)
- `blender/scripts/lowpoly/`: the bake and export pipeline (`lp1.py`, `lp_export.py`, `embed.py`, `run*.sh`)
- `blender/scripts/weapons/`: infantry weapons (`weapons7.py` is current)
- `blender/scripts/vehicles/`: vehicle sources (`lt.py` light, `mt.py` medium, `ht.py` heavy) plus `vbake.py`, `vembed.py` and `vlib.py`
- `blender/scripts/heads/`: helmets and heads (`h13lib.py`)
- `blender/scripts/mange/`: Mange concepts
- `tools/`: the headless SIM harness (`load.js`, `duel.js` for balance, `long.js`, plus many browser test scripts)
- `web/live/index.html`: the latest published page. Textures, music and `skint.js`/`vtex.js` live on the artifact, not here.

## Working branches
Use one branch per family (`tanks`, `ground-support`, `aircraft`, `naval`, `buildings`, `mange`, `anim-bank`). Merge to `main` when a slice ships.
