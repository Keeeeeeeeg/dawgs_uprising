# Dawgs Uprising: team production playbook (read this first)

Dawgs Uprising is a browser RTS: a single HTML page plus supporting files, published as one shared claude.ai artifact. Keegan is the art director and signs off every design. This doc tells a teammate (and their Claude) how we build content, so several groups can move at once without stepping on each other.

## Where things live
- **The game:** artifact https://claude.ai/code/artifact/f19e611d-226f-4d81-b847-d27ca14a589b. It holds the page plus `music/`, `sfx/`, `tex/marine/*` (including `skint.js`), `tex/veh/*` (including `vtex.js`), `env/*` (skies, terrain, water, foliage, rocks).
- **Docs (this folder, also in Keegan's claude.ai project "RTS Game" under `claude/`):**
  - `handoff.md`: current state and what's next (start here).
  - `roadmap.md`: decisions, status, and what's next for every group.
  - `ventora-conventions.md`: engine conventions, the INFANTRY STANDARD, and pitfalls. Required reading.
  - `grand-strategy.md`: the Grand Strategy mode.
- **Blender sources:** Keegan's `~/3D Objects/DawgsUprising/` folders (`body/`, `lowpoly/`, `weapons/`, `vehicles/`, `heads/`, `mange/`, `work/`). Ask Keegan for a copy.

## How we roll content out (agreed 2026-11-20)
1. **Design a whole family together** (tanks; ground support; aircraft; naval; buildings; the Mange): question round with Keegan, then a side-by-side concept sheet; Keegan signs the family off as a set.
2. **Build each unit as a complete vertical slice, then ship it:** bake, textures, rig, in-game animation, sounds and effects, balance check, publish as its own version.
3. **Build shared systems once**, before the first slice that needs them.
4. **Only one Blender bake runs at a time on a machine.**

## Claiming a group
- Pick one family, post it in the team channel, and add a line under "In progress" in the roadmap with your name and the date. One person per family at a time.

## The art standard (every unit)
- **Original designs only.** References set design language, never one-to-one copies.
- **Faction look:** grounded, gritty Halo Wars style; army colour only through the mask (stripes, pauldrons, visor lenses).
- **Quality gate before showing renders:** QA 0 issues (nothing floating, no clipping, nothing below the floor); Cycles stills; Keegan approves before any bake; in-game close-up after the bake.
- **All on-screen numbers are whole numbers.**
- Scenery is PROCEDURAL (rules + seed place rocks, plants, trees, ground materials); only the gameplay layout is hand-made.

## Shipping to the shared game
- **Always start from the live published version.** If a publish is refused because someone published in between, merge onto theirs and bump past their version.
- **Every publish:** bump `GAME_VERSION`; newest-first `CHANGELOG` entry with `by:'<your name>'`; keep a copy of what you published; include every changed supporting file in `files`.
- **Code safety:** `node --check` every `<script>` block; never put a `//` comment mid-line with code after it (this has broken the game many times); every gameplay number in `BALANCE`; test the SIM headless (`G.update(.25)` steps). Game code lives inside the battle boot function, so the menu (`MenuBG`) can't call `vkMesh`/`RIMU` etc.
- **Afterwards,** update `roadmap.md` and `handoff.md` (here and in the project).

## Working with Keegan
- He likes question rounds before work and high-quality stills before anything goes in the game.
- Keep updates short: what changed, what he should look at, what's next.
