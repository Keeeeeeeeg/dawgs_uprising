// Dawgs Uprising -> Unity: realistic, weathered ground and building surfaces (DawgsRig/du_surfaces.py, du_ground.py).
//   Dawgs > Upgrade Ground and Buildings
// Ground: the terrain is repainted with four surfaces rendered in Blender - grass, rough meadow, bare earth and sand -
// each with a normal map and a height mask, blended by height (URP Terrain Lit), so grass tufts stand up through the
// earth instead of fading into it. Where each one goes comes from Data/ground_splat.raw: worn earth round the bases,
// along the road verges and at the foot of buildings, meadow on the drier ground and the top of the beach.
// Buildings: walls get cast concrete (formwork panels, tie holes, rain streaks, cracks), flat ground worn paving and
// roofs felt roofing - all multiplying the models' own colours, so every building keeps its paint - plus grime splashed
// up the foot of the walls; the city and house facades are redrawn sharp with real frames and sills, and their glass shines.
// The slice builder calls ApplyToOpenScene() too, so a full rebuild keeps the upgrade.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class DawgsSurfaceBuilder
{
    const string Root = "Assets/Dawgs";
    const string Tex = Root + "/Textures/Surface";
    const string Out = Root + "/Generated/Surface";
    static readonly string[] Scenes = { Root + "/Scenes/DawgsTestTown.unity", Root + "/Scenes/DawgsSkirmish.unity" };

    // terrain layers, in Data/ground_splat.raw order: name, tile size (m), normal strength
    static readonly (string name, float tile, float normal)[] Ground = { ("grass", 6f, 0.45f), ("meadow", 6f, 0.5f), ("dirt", 5f, 0.8f), ("sand", 5f, 0.6f) };

    // the baked world's materials (Generated/Materials/Mxxx.mat) that are buildings and paving:
    // id, wall detail strength, top (paving / roofing) strength, grime at the foot of the walls
    static readonly (int id, float wall, float top, float grime)[] Surfaces =
    {
        (9, 0.9f, 0.8f, 0.55f), (0, 0.9f, 0.8f, 0.55f),                          // most of the town and the bases, in vertex colours
        (82, 1f, 1f, 0.6f), (83, 1f, 1f, 0.6f), (38, 1f, 1f, 0.5f), (43, 1f, 1f, 0.5f),   // plain concrete and render
        (25, 0.9f, 1f, 0.4f), (26, 0.9f, 1f, 0.4f), (15, 0.8f, 0.8f, 0.4f), (23, 0.6f, 0.8f, 0.4f),
        (41, 0.6f, 0.9f, 0.5f),                                                    // already concrete-textured
        (17, 0.5f, 0.8f, 0.5f), (36, 0.5f, 0.8f, 0.5f), (30, 0.5f, 0.8f, 0.5f), (31, 0.5f, 0.8f, 0.5f), (27, 0.5f, 0.8f, 0.5f), (44, 0.5f, 0.8f, 0.5f),   // block walls
        (33, 0.6f, 0.8f, 0.5f),                                                    // olive paint
        (87, 0f, 0.7f, 0f), (37, 0f, 0.8f, 0f), (45, 0f, 0.8f, 0f),                // roads and hard standing
        (49, 0f, 0f, 0.4f), (53, 0f, 0f, 0.5f),                                    // the facades: grime only (glass below)
    };
    const int CityFacade = 49, HouseFacade = 53, DarkGlass = 34;

    [Serializable] class TerrainMeta { public float x0, z0, width, depth, hmin, hmax; }

    static string Abs(string p) => Path.Combine(Path.GetDirectoryName(Application.dataPath), p);
    static void Dir(string p) { if (!AssetDatabase.IsValidFolder(p)) { var parent = Path.GetDirectoryName(p).Replace('\\', '/'); Dir(parent); AssetDatabase.CreateFolder(parent, Path.GetFileName(p)); } }

    [MenuItem("Dawgs/Upgrade Ground and Buildings (weathered textures)")]
    public static void Menu()
    {
        if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
        Debug.Log("[Dawgs] " + UpgradeScenes());
    }

    /// upgrades both scenes (saved)
    public static string UpgradeScenes()
    {
        var log = new StringBuilder();
        try
        {
            foreach (var path in Scenes)
            {
                if (!File.Exists(Abs(path))) continue;
                var sc = EditorSceneManager.OpenScene(path, OpenSceneMode.Single);
                log.AppendLine("== " + path);
                ApplyToScene(log);
                EditorSceneManager.SaveScene(sc);
            }
            AssetDatabase.SaveAssets();
        }
        catch (Exception e) { log.AppendLine("FAILED: " + e); Debug.LogException(e); }
        return log.ToString();
    }

    /// for the slice builder: upgrade whatever scene is open (not saved here)
    public static void ApplyToOpenScene(StringBuilder log)
    {
        if (!File.Exists(Abs(Tex + "/grass_a.png"))) { log.AppendLine("surfaces: no Blender surface textures yet"); return; }
        ApplyToScene(log);
    }

    static void ApplyToScene(StringBuilder log)
    {
        Dir(Out);
        Import();
        var terrain = UnityEngine.Object.FindFirstObjectByType<Terrain>();
        var height = HeightMap(out var rect, out var range);
        if (terrain) log.AppendLine(Ground_(terrain));
        log.AppendLine(Buildings(height, rect, range));
        if (terrain) log.AppendLine(DawgsEnvBuilder.RefreshGrass(terrain));
        EditorSceneManager.MarkSceneDirty(UnityEngine.SceneManagement.SceneManager.GetActiveScene());
        AssetDatabase.SaveAssets();
    }

    // ------------------------------------------------------------------ texture import settings
    static void Import()
    {
        foreach (var guid in AssetDatabase.FindAssets("t:Texture2D", new[] { Tex }))
        {
            string p = AssetDatabase.GUIDToAssetPath(guid), n = Path.GetFileNameWithoutExtension(p);
            var ti = AssetImporter.GetAtPath(p) as TextureImporter; if (ti == null) continue;
            bool facade = p.Contains("/Facade/");
            bool normal = n.EndsWith("_n"), mask = n.EndsWith("_m");
            bool linearDetail = n == "wall_a" || n == "roof_a" || n == "pave_a";   // 0.5 = leave the colour alone, so read them raw
            bool alpha = mask || facade || n == "wall_a";                          // wall_a's alpha: the large-scale weathering
            var type = normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
            bool srgb = !(normal || mask || linearDetail);
            int max = facade && n != "t12" ? 2048 : 1024;
            var wrap = facade && n == "t12" ? TextureWrapMode.Clamp : TextureWrapMode.Repeat;
            if (ti.textureType == type && ti.sRGBTexture == srgb && ti.wrapMode == wrap && ti.anisoLevel >= 8 && ti.maxTextureSize == max && ti.mipmapEnabled
                && ti.textureCompression == TextureImporterCompression.CompressedHQ && !ti.alphaIsTransparency
                && ti.alphaSource == (alpha ? TextureImporterAlphaSource.FromInput : TextureImporterAlphaSource.None)) continue;
            ti.textureType = type; ti.sRGBTexture = srgb; ti.wrapMode = wrap; ti.anisoLevel = 8; ti.maxTextureSize = max; ti.mipmapEnabled = true;
            ti.alphaIsTransparency = false;                                         // facade alpha marks glass, mask alpha is smoothness
            ti.alphaSource = alpha ? TextureImporterAlphaSource.FromInput : TextureImporterAlphaSource.None;
            ti.textureCompression = TextureImporterCompression.CompressedHQ;
            ti.SaveAndReimport();
        }
    }

    static T Load<T>(string p) where T : UnityEngine.Object => AssetDatabase.LoadAssetAtPath<T>(p);

    /// mean of a texture's stored values (what the shader reads from a linear import), for dividing a detail map by
    static Color RawMean(string assetPath)
    {
        var t = new Texture2D(2, 2);
        t.LoadImage(File.ReadAllBytes(Abs(assetPath)));
        var px = t.GetPixels32(); double r = 0, g = 0, b = 0; int n = 0;
        for (int i = 0; i < px.Length; i += 5) { r += px[i].r; g += px[i].g; b += px[i].b; n++; }
        UnityEngine.Object.DestroyImmediate(t);
        return new Color((float)(r / n / 255.0), (float)(g / n / 255.0), (float)(b / n / 255.0), 1f);
    }

    // ------------------------------------------------------------------ the terrain's heights, for the building shader
    static Texture2D HeightMap(out Vector4 rect, out Vector4 range)
    {
        var meta = JsonUtility.FromJson<TerrainMeta>(File.ReadAllText(Abs(Root + "/Data/terrain.json")));
        rect = new Vector4(meta.x0, -(meta.z0 + meta.depth), 1f / meta.width, 1f / meta.depth);
        range = new Vector4(meta.hmin, meta.hmax - meta.hmin, 0f, 0f);
        string p = Out + "/GroundHeight.asset";
        var raw = File.ReadAllBytes(Abs(Root + "/Data/height1025.raw"));
        int res = (int)Math.Round(Math.Sqrt(raw.Length / 2));
        var t = Load<Texture2D>(p);
        if (t == null || t.width != res)
        {
            AssetDatabase.DeleteAsset(p);
            t = new Texture2D(res, res, TextureFormat.R16, false, true) { name = "GroundHeight", wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Bilinear };
            t.SetPixelData(raw, 0);
            t.Apply(false, false);
            AssetDatabase.CreateAsset(t, p);
        }
        return t;
    }

    // ------------------------------------------------------------------ ground
    static string Ground_(Terrain terrain)
    {
        string sp = Abs(Root + "/Data/ground_splat.raw");
        if (!File.Exists(sp)) return "ground: no ground_splat.raw";
        var td = terrain.terrainData;
        var layers = new TerrainLayer[Ground.Length];
        for (int i = 0; i < Ground.Length; i++)
        {
            var g = Ground[i];
            string lp = $"{Out}/{g.name}.terrainlayer";
            var tl = Load<TerrainLayer>(lp);
            if (tl == null) { tl = new TerrainLayer(); AssetDatabase.CreateAsset(tl, lp); }
            tl.diffuseTexture = Load<Texture2D>($"{Tex}/{g.name}_a.png");
            tl.normalMapTexture = Load<Texture2D>($"{Tex}/{g.name}_n.png");
            tl.maskMapTexture = Load<Texture2D>($"{Tex}/{g.name}_m.png");
            tl.normalScale = g.normal;
            tl.tileSize = new Vector2(g.tile, g.tile);
            tl.tileOffset = Vector2.zero;
            tl.diffuseRemapMin = Vector4.zero; tl.diffuseRemapMax = Vector4.one;   // the renders are already in the game's palette
            tl.maskMapRemapMin = Vector4.zero; tl.maskMapRemapMax = Vector4.one;
            tl.metallic = 0f; tl.smoothness = 0.12f;
            EditorUtility.SetDirty(tl);
            layers[i] = tl;
        }
        td.terrainLayers = layers;
        var bytes = File.ReadAllBytes(sp);
        int res = (int)Math.Round(Math.Sqrt(bytes.Length / 4));
        td.alphamapResolution = res;
        var a = new float[res, res, 4];
        for (int r = 0; r < res; r++) for (int c = 0; c < res; c++) for (int k = 0; k < 4; k++) a[r, c, k] = bytes[(r * res + c) * 4 + k] / 255f;
        td.SetAlphamaps(0, 0, a);
        EditorUtility.SetDirty(td);

        // URP Terrain Lit with height-based blending (four layers, so one pass), normal and mask maps
        string mp = Out + "/DawgsTerrain.mat";
        var sh = Shader.Find("Universal Render Pipeline/Terrain/Lit");
        if (sh == null) return "ground: URP Terrain/Lit shader not found";
        var m = Load<Material>(mp);
        if (m == null) { m = new Material(sh); AssetDatabase.CreateAsset(m, mp); }
        m.shader = sh;
        m.SetFloat("_EnableHeightBlend", 1f); m.EnableKeyword("_TERRAIN_BLEND_HEIGHT");
        m.SetFloat("_HeightTransition", 0.22f);
        m.SetFloat("_EnableInstancedPerPixelNormal", 1f); m.EnableKeyword("_TERRAIN_INSTANCED_PERPIXEL_NORMAL");
        m.EnableKeyword("_NORMALMAP"); m.EnableKeyword("_MASKMAP");
        m.enableInstancing = true;
        EditorUtility.SetDirty(m);
        terrain.materialTemplate = m;
        terrain.drawInstanced = true;
        terrain.basemapDistance = 2000f;
        EditorUtility.SetDirty(terrain);
        return $"ground: {layers.Length} layers ({string.Join(", ", Ground.Select(g => g.name))}), splat {res}x{res}, height blend on";
    }

    // ------------------------------------------------------------------ buildings
    static string Buildings(Texture2D height, Vector4 rect, Vector4 range)
    {
        var wall = Load<Texture2D>(Tex + "/wall_a.png"); var walln = Load<Texture2D>(Tex + "/wall_n.png");
        var pave = Load<Texture2D>(Tex + "/pave_a.png"); var paven = Load<Texture2D>(Tex + "/pave_n.png");
        var roof = Load<Texture2D>(Tex + "/roof_a.png"); var roofn = Load<Texture2D>(Tex + "/roof_n.png");
        if (!wall || !pave || !roof) return "buildings: surface textures missing";
        Color wm = RawMean(Tex + "/wall_a.png").gamma, pm = RawMean(Tex + "/pave_a.png").gamma, rm = RawMean(Tex + "/roof_a.png").gamma;   // colours are given in sRGB
        int done = 0;
        var missing = new List<int>();
        foreach (var s in Surfaces)
        {
            var m = Load<Material>($"{Root}/Generated/Materials/M{s.id:000}.mat");
            if (m == null || !m.HasProperty("_TopStrength")) { missing.Add(s.id); continue; }
            m.SetTexture("_DetailMap", wall); m.SetColor("_DetailMean", wm); m.SetFloat("_DetailScale", 8f);
            m.SetFloat("_DetailStrength", s.wall); m.SetFloat("_DetailMacro", s.wall > 0f ? Mathf.Min(1f, 0.35f + 0.55f * s.wall) : 0f);
            m.SetTexture("_DetailNormal", walln); m.SetFloat("_DetailNormalStrength", s.wall * 0.7f);
            m.SetTexture("_TopMap", pave); m.SetTexture("_TopNormal", paven); m.SetColor("_TopMean", pm); m.SetFloat("_TopScale", 5f);
            m.SetTexture("_RoofMap", roof); m.SetTexture("_RoofNormal", roofn); m.SetColor("_RoofMean", rm); m.SetFloat("_RoofScale", 6f);
            m.SetFloat("_RoofAbove", 2.2f);
            m.SetFloat("_TopStrength", s.top); m.SetFloat("_TopNormalStrength", s.top * 0.8f);
            m.SetFloat("_Grime", s.grime);
            m.SetTexture("_GroundHeight", height); m.SetVector("_GroundRect", rect); m.SetVector("_GroundRange", range);
            EditorUtility.SetDirty(m);
            done++;
        }
        // facades: the redrawn window layouts, glass from their alpha
        string glass = "";
        var city = Load<Material>($"{Root}/Generated/Materials/M{CityFacade:000}.mat");
        var t8 = Load<Texture2D>(Tex + "/Facade/t8.png"); var t9 = Load<Texture2D>(Tex + "/Facade/t9.png");
        if (city && t8)
        {
            city.SetTexture("_BaseMap", t8); if (t9) city.SetTexture("_EmissionMap", t9);
            city.SetFloat("_GlassFromAlpha", 1f); city.SetFloat("_GlassSmoothness", 0.84f); city.SetFloat("_Smoothness", 0.14f);
            EditorUtility.SetDirty(city); glass += " city";
        }
        var house = Load<Material>($"{Root}/Generated/Materials/M{HouseFacade:000}.mat");
        var t12 = Load<Texture2D>(Tex + "/Facade/t12.png");
        if (house && t12)
        {
            house.SetTexture("_BaseMap", t12);
            house.SetFloat("_GlassFromAlpha", 1f); house.SetFloat("_GlassSmoothness", 0.82f); house.SetFloat("_Smoothness", 0.1f);
            EditorUtility.SetDirty(house); glass += " houses";
        }
        var dark = Load<Material>($"{Root}/Generated/Materials/M{DarkGlass:000}.mat");
        if (dark) { dark.SetFloat("_Smoothness", 0.8f); EditorUtility.SetDirty(dark); glass += " windows";
        }
        return $"buildings: {done} materials weathered{(missing.Count > 0 ? " (missing: " + string.Join(",", missing) + ")" : "")}, glass:{glass}";
    }
}
