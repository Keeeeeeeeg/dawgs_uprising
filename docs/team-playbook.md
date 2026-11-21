# Dawgs Uprising: team production playbook (read this first)

Dawgs Uprising is a browser RTS: a single HTML page plus supporting files, published as one shared claude.ai artifact. Keegan is the art director and signs off every design. This doc tells a teammate (and their Claude) how we build content, so several groups can move at once without stepping on each other.

## Where things live
- **The game:** artifact https://claude.ai/code/artifact/f19e611d-226f-4d81-b847-d27ca14a589b. It holds the page plus `music/`, `sfx/`, `tex/marine/*` (including `skint.js`) and `tex/veh/*` (including `vtex.js`).
- **Project docs in the "RTS Game" Claude project.** Read them before working:
  - `claude/roadmap.md`: decisions, status, and what's next for every group.
  - `claude/ventora-conventions.md`: engine conventions, the INFANTRY STANDARD, and pitfalls. Required reading.
  - `claude/grand-strategy.md`: the Grand Strategy mode.
- **Blender sources:** Keegan's `~/3D Objects/DawgsUprising/` folders:
  - `body/`: marines
  - `lowpoly/`: the bake and export pipeline
  - `weapons/`
  - `vehicles/`
  - `heads/`
  - `mange/`
  
  Ask Keegan for a copy, or for access to the shared repo once we set one up.
- **Skill:** `dawgs-infantry-standard` (infantry rules). A vehicle standard follows the same pattern.

## How we roll content out (agreed 2026-11-20)
1. **Design a whole family together.** Families: tanks; ground support (technical, AA trio, SPG and howitzer, rover, trains); aircraft; naval; buildings; the Mange.
   - Start with a question round (AskUserQuestion) with Keegan.
   - Then a side-by-side concept sheet of the whole family.
   - Keegan signs the family off as a set, so the design language stays consistent.
2. **Build each unit as a complete vertical slice, then ship it:** bake → textures → rig → in-game animation → sounds and effects → balance check (`tools/duel.js`) → publish as its own version.
3. **Build shared systems once, before the first slice that needs them.** Examples: the vehicle rig template (pods, turret, recoil, damage, wreck) and the infantry animation bank (one skeleton for every kit).
4. **Only one Blender bake runs at a time on a machine.** While it runs, work on the next concept or on engine work.

## Claiming a group
- Pick one family. Post it in the team channel, and add a line under "In progress" in `claude/roadmap.md` with your name and the date.
- One person per family at a time. Nobody touches another family's source scripts.
- Status as of 2026-11-20:
  - **Keegan:** the tank family (light and medium move to pods; the heavy gets touch-ups), then ground support.
  - **Open:** aircraft, naval, buildings and bases, the Mange restyle, and the infantry animation bank (deaths and hit reactions).

## The art standard (every unit)
- **Original designs only.** References set design language, never one-to-one copies. Real historical hardware may be interpreted directly.
- **Faction look.**
  - Grounded, gritty Halo Wars style: weathered paint, chamfered hard surfaces, bolts and seams baked into the normal maps.
  - Army colour appears only through the mask (team stripes, pauldrons, visor lenses).
  - Boarding Marines use hazard orange.
- **Quality gate before showing renders.**
  - `qa` reports 0 issues: nothing floating, no clipping, nothing below the floor.
  - Look closely at the joints.
  - Cycles stills: lineup; front and side orthographic; close-ups of details, weapons, feet and head.
- **Keegan approves the stills before any bake.** After the bake, take an in-game close-up to check muzzle origins, clipping and texture stretch.
- **All on-screen numbers are whole numbers.**

## Shipping to the shared game (important with several people)
- **Always start from the live published version, never from an old local copy.** If a publish is refused because someone published in between, merge your changes onto theirs and bump past their version number.
- **Every publish:**
  - Bump `GAME_VERSION`.
  - Add a newest-first `CHANGELOG` entry with `by:'<your name>'`.
  - Keep a copy of what you published, to use as the base for the next merge.
  - Include every changed supporting file in `files` (texture maps, `skint.js`, `vtex.js`).
- **Code safety.**
  - Run `node --check` on every `<script>` block before publishing.
  - Never put a `//` comment in the middle of a line that has more code after it. This has broken the game several times.
  - Every gameplay number goes in `BALANCE`.
  - Test the SIM headless in Node (`G.update(.25)` steps).
- **Afterwards,** update `claude/roadmap.md`, and `claude/ventora-conventions.md` too if you learned something. Add anything reusable to the team skills.

## Working with Keegan
- He likes question rounds before work and high-quality stills before anything goes in the game.
- Keep updates short: what changed, what he should look at, what's next.
