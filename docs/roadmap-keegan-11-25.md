# Roadmap addendum (Keegan, 11-25) - merge into roadmap.md on the next edit

(The claude.ai "RTS Game" project is at 100% capacity, so this lives here.)

- KEEGAN NOTE on the AA vehicles: the remodelled Light/Medium/Heavy AA (25.82/25.99) are a fair bit off from the concept art he provided. Revisit them against his concept sheets (question round, concept sheet, his sign-off before any bake), the same way the tanks were done.
- SHIPPED 26.0 'Timber' (Keegan, built on Andrew's 25.99): textured trees. `TT` module right after `treeMat` in the renderer.
  - Crowns = leaf-cluster cards cut from Poly Haven CC0 tree scans (jacaranda, island tree, small tree, fir) -> `env/trees/leaves.webp` (4x2 cells: broad 0,1 | olive 2,3 | light 4,5 | conifer 6,7; colour dilated into the transparent texels).
  - Bark = Poly Haven CC0 tileable bark: `env/trees/bark_oak.jpg` (bark_brown_02), `bark_pine.jpg` (pine_bark), `bark_olive.jpg` (bark_willow_02).
  - Spherical crown normals (+ up bias) and vertex AO so each crown is lit as one rounded mass; leaf colour x1.55, bark x1.25; both faces of a card lit by the crown normal.
  - One geometry per species with groups (0 bark, 1 leaves) so each tree is still ONE instance: `TREE_INST` / rover felling unchanged. `customDepthMaterial` cuts leaf alpha (attribute `lf`) for dappled shadows. Same wind sway as `treeMat` (`window.__TW`).
  - Species: oak, olive, umbrella, cypress, larch, bush, snowpine (snow on upward cards); two shapes each (`TTP` splits the list by index). Desert plants unchanged.
  - Sources (Keegan's cloud session): trees/clusters.py (Blender card renders), trees/pack.py, trees/texTree.js.
- (Andrew shipped 26.1 'Dashes': Zeppelin health bar dashes.)
- SHIPPED 26.2 'Rolling Stock' (Keegan, merged onto Andrew's 26.1):
  - TREADS: vbake.py builds every TRACKS_LP loop twice: the old band (group `trkband`, baked, only kept in the far-LOD hull) and a tread part `trk<i>` with its own UVs (u = distance along the loop / loop length, v = a row of a strip atlas; outer face 0-.6 of the row, sides and inner face the rest). The strips are baked from the HIGH model's real links into `tex/veh/<type>_t_c.jpg` / `_t_n.jpg` (4096 x 128 per loop). VTEX[type].trk = [[part, group (pod name or 'hull'), loop length]].
  - Engine: vkMesh adds each tread part to its pod group (or the hull) with `vkTrkMat` (Phong, map + normal map, RepeatWrapping in u, per-mesh uniform uS added to vUv.x). vkFrame scrolls uS by kb * (forward distance + side * half-width * yaw change) / scale, where kb = the strip's direction along the bottom run (voted from the bottom triangles' du/dx) / L. Wrecks get dark treads.
  - All three tanks rebaked at RES 4096 on Keegan's desktop Blender (RTX 2070 SUPER, OptiX; ~10 min for all three via a bpy.app.timers job in the 'claude_work' scene; vbake runs as `vbake_t.py` on the PC because device file commits can lag behind). Env per tank: ltank KEEP=cage, mtank HULLT=6500, htank defaults; CDEV=GPU. Old bakes kept in veh/<type>_backup_2574 (cloud). Tank textures now ~25 MB for the three.
  - Not done: road wheels/sprockets spinning (wheels are baked into their stations / pods, would need their own groups).
- NEXT (Keegan's order): more scenery (shorelines, desert/arctic checks, colour grading, contact shade under buildings) and the main-menu attract mode; audio once the Sonniss files are in DawgsUprising/sfx_refs.
