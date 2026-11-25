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
- NEXT: tank treads (scrolling tread texture + spinning wheels) + 4096 rebake of light/medium/heavy on Keegan's desktop Blender (needs his PC linked and Blender open).
