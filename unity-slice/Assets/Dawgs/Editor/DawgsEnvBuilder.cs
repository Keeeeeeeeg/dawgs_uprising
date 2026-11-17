// Dawgs Uprising -> Unity: swaps in the environment models made in Blender (DawgsRig/du_env.py).
//   Dawgs > Upgrade Environment      trees + bushes (3 LODs, wind), grass / flowers on the terrain, the railway
// Reads Assets/Dawgs/Data/env_trees.bytes, env_grass.bytes, env_track.bytes, grass_cover.raw and
// Textures/Env/ballast*.png, builds everything under Assets/Dawgs/Generated/Env, then upgrades the Test Town and Skirmish
// scenes in place: every tree prop becomes a LOD tree (same spot, size, turn and tint), the old sleeper / rail props and the
// flat rail-bed ribbon give way to the modelled track, and the terrain gets grass detail layers.
// The slice builder calls ApplyToOpenScene() too, so a full rebuild keeps the upgrade.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

public static class DawgsEnvBuilder
{
    const string Root = "Assets/Dawgs";
    const string Out = Root + "/Generated/Env";
    static readonly string[] Scenes = { Root + "/Scenes/DawgsTestTown.unity", Root + "/Scenes/DawgsSkirmish.unity" };

    // tree props by prototype key (see DawgsRig/du_env.py TREES)
    static readonly string[] TreeKeys = { "pE2E60375_9", "p9F903079_9", "pCE1377AE_9", "p8A82B179_9", "p28E78046_9", "p45D5166C_9" };
    // the browser's track props (a sleeper quad and a rail quad, instanced) and its rail-bed ribbon material
    static readonly string[] OldTrackProps = { "p56080E87_90", "p68DA552E_91" };
    const int RailBedMat = 57;
    // LOD switch points (fraction of screen height); trees under 0.5% of the screen are culled
    static readonly float[] LodHeights = { 0.2f, 0.045f, 0.005f };

    // grass detail layers: instances per square metre at full cover
    static readonly (string kind, float perM2, float minS, float maxS)[] Grass =
    {
        ("tuft", 5.5f, 0.8f, 1.35f), ("tall", 3.2f, 0.8f, 1.3f), ("dry", 2.8f, 0.8f, 1.3f),
        ("daisy", 2.0f, 0.85f, 1.2f), ("buttercup", 2.0f, 0.85f, 1.2f), ("clover", 2.4f, 0.8f, 1.4f),
    };

    [Serializable] class Head { public string key; public int mat; public int tx; public int tz; public string proto; public int lod; public int nv; public int ni; }
    [Serializable] class Proto { public string key; public int n; public float[] data; }
    [Serializable] class ProtoList { public Proto[] protos; }
    [Serializable] class TerrainMeta { public float x0, z0, width, depth; }
    class Entry { public Head h; public Mesh mesh; }

    public class Assets
    {
        public Dictionary<string, GameObject> trees = new Dictionary<string, GameObject>();
        public List<GameObject> grass = new List<GameObject>();
        public GameObject railway;
        public Material foliage, grassMat, track_, steel, ballast;
    }

    static string Abs(string p) => Path.Combine(Path.GetDirectoryName(Application.dataPath), p);
    static void Dir(string p) { if (!AssetDatabase.IsValidFolder(p)) { var parent = Path.GetDirectoryName(p).Replace('\\', '/'); Dir(parent); AssetDatabase.CreateFolder(parent, Path.GetFileName(p)); } }

    [MenuItem("Dawgs/Upgrade Environment (Blender trees, grass, railway)")]
    public static void Menu()
    {
        if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
        Debug.Log("[Dawgs] " + UpgradeScenes());
    }

    /// builds the assets once and upgrades both scenes (saved)
    public static string UpgradeScenes()
    {
        var log = new StringBuilder();
        try
        {
            var a = BuildAssets(log);
            foreach (var path in Scenes)
            {
                if (!File.Exists(Abs(path))) continue;
                var sc = EditorSceneManager.OpenScene(path, OpenSceneMode.Single);
                log.AppendLine("== " + path);
                ApplyToScene(a, log);
                EditorSceneManager.SaveScene(sc);
            }
            AssetDatabase.SaveAssets();
        }
        catch (Exception e) { log.AppendLine("FAILED: " + e); Debug.LogException(e); }
        finally { EditorUtility.ClearProgressBar(); }
        return log.ToString();
    }

    /// for the slice builder: upgrade whatever scene is open (not saved here)
    public static void ApplyToOpenScene(StringBuilder log)
    {
        if (!File.Exists(Abs(Root + "/Data/env_trees.bytes"))) { log.AppendLine("env: no Blender environment data yet"); return; }
        ApplyToScene(BuildAssets(log), log);
    }

    // ------------------------------------------------------------------ assets
    public static Assets BuildAssets(StringBuilder log)
    {
        Dir(Out + "/Trees"); Dir(Out + "/Grass"); Dir(Out + "/Materials");
        FixTextures();
        var a = new Assets();
        a.foliage = Mat("Foliage", "Dawgs/Foliage", m =>
        {
            m.SetFloat("_WindStrength", 0.14f); m.SetFloat("_WindSpeed", 1.0f); m.SetFloat("_WindFlutter", 0.35f);
            m.SetFloat("_Translucency", 0.45f); m.SetFloat("_Smoothness", 0.12f); m.SetFloat("_Cull", (float)CullMode.Off);
        });
        a.grassMat = Mat("Grass", "Dawgs/Foliage", m =>
        {
            m.SetFloat("_WindStrength", 0.05f); m.SetFloat("_WindSpeed", 1.5f); m.SetFloat("_WindFlutter", 0.25f);
            m.SetFloat("_Translucency", 0.15f); m.SetFloat("_Smoothness", 0.1f); m.SetFloat("_Cull", (float)CullMode.Off);
        });
        a.track_ = Mat("Track", "Dawgs/Lit", m => { m.SetFloat("_VertexColor", 1); m.SetFloat("_Smoothness", 0.16f); m.SetFloat("_Metallic", 0f); });
        a.steel = Mat("TrackSteel", "Dawgs/Lit", m => { m.SetFloat("_VertexColor", 1); m.SetFloat("_Smoothness", 0.72f); m.SetFloat("_Metallic", 0.85f); });
        a.ballast = Mat("Ballast", "Dawgs/Lit", m =>
        {
            m.SetFloat("_VertexColor", 1); m.SetFloat("_Smoothness", 0.08f); m.SetFloat("_Metallic", 0f);
            var tex = AssetDatabase.LoadAssetAtPath<Texture2D>(Root + "/Textures/Env/ballast.png");
            var nrm = AssetDatabase.LoadAssetAtPath<Texture2D>(Root + "/Textures/Env/ballast_n.png");
            m.SetTexture("_DetailMap", tex); m.SetFloat("_DetailStrength", 0.85f); m.SetFloat("_DetailScale", 2.0f);
            m.SetColor("_DetailMean", MeanLinear(Root + "/Textures/Env/ballast.png").gamma);   // material colours are given in sRGB
            m.SetTexture("_DetailNormal", nrm); m.SetFloat("_DetailNormalStrength", 0.8f);
        });

        // trees: one LOD prefab per prototype
        var trees = ReadBank(Root + "/Data/env_trees.bytes", Out + "/TreeMeshes.asset", true);
        foreach (var g in trees.GroupBy(e => e.h.proto))
        {
            var go = new GameObject(g.Key);
            var lods = new List<LOD>();
            foreach (var e in g.OrderBy(e => e.h.lod))
            {
                var c = new GameObject("LOD" + e.h.lod); c.transform.SetParent(go.transform, false);
                c.AddComponent<MeshFilter>().sharedMesh = e.mesh;
                var r = c.AddComponent<MeshRenderer>(); r.sharedMaterial = a.foliage;
                r.shadowCastingMode = ShadowCastingMode.On; r.receiveShadows = true;
                lods.Add(new LOD(LodHeights[Mathf.Min(e.h.lod, LodHeights.Length - 1)], new Renderer[] { r }));
            }
            var lg = go.AddComponent<LODGroup>();
            lg.fadeMode = LODFadeMode.CrossFade; lg.animateCrossFading = true;
            lg.SetLODs(lods.ToArray()); lg.RecalculateBounds();
            a.trees[g.Key] = PrefabUtility.SaveAsPrefabAsset(go, $"{Out}/Trees/{g.Key}.prefab");
            UnityEngine.Object.DestroyImmediate(go);
        }
        // grass clumps: detail prefabs (no shadows: thousands of them)
        var grass = ReadBank(Root + "/Data/env_grass.bytes", Out + "/GrassMeshes.asset", true).ToDictionary(e => e.h.proto);
        foreach (var gd in Grass)
        {
            if (!grass.TryGetValue("grass_" + gd.kind, out var e)) continue;
            var go = new GameObject("grass_" + gd.kind);
            go.AddComponent<MeshFilter>().sharedMesh = e.mesh;
            var r = go.AddComponent<MeshRenderer>(); r.sharedMaterial = a.grassMat; r.shadowCastingMode = ShadowCastingMode.Off;
            a.grass.Add(PrefabUtility.SaveAsPrefabAsset(go, $"{Out}/Grass/grass_{gd.kind}.prefab"));
            UnityEngine.Object.DestroyImmediate(go);
        }
        // the railway: one prefab (scenes reference it, so rebuilding the meshes never leaves them dangling)
        var track = ReadBank(Root + "/Data/env_track.bytes", Out + "/TrackMeshes.asset", true);
        var rail = new GameObject("Railway");
        foreach (var g in track.GroupBy(e => e.h.proto))
        {
            var chunk = new GameObject(g.Key); chunk.transform.SetParent(rail.transform, false);
            foreach (var e in g)
            {
                var c = new GameObject(e.h.mat == 312 ? "ballast" : e.h.mat == 313 ? "railheads" : "sleepers_rails");
                c.transform.SetParent(chunk.transform, false);
                c.AddComponent<MeshFilter>().sharedMesh = e.mesh;
                var r = c.AddComponent<MeshRenderer>();
                r.sharedMaterial = e.h.mat == 312 ? a.ballast : e.h.mat == 313 ? a.steel : a.track_;
                r.shadowCastingMode = e.h.mat == 312 ? ShadowCastingMode.Off : ShadowCastingMode.On;
            }
        }
        foreach (var t in rail.GetComponentsInChildren<Transform>()) t.gameObject.isStatic = true;
        a.railway = PrefabUtility.SaveAsPrefabAsset(rail, Out + "/Railway.prefab");
        UnityEngine.Object.DestroyImmediate(rail);
        AssetDatabase.SaveAssets();
        log.AppendLine($"env assets: {a.trees.Count} trees, {a.grass.Count} grass clumps, {track.Count} track meshes");
        return a;
    }

    /// the already-built assets (no rebuild), for upgrading another scene
    public static Assets LoadAssets()
    {
        var a = new Assets();
        foreach (var key in TreeKeys) { var pf = AssetDatabase.LoadAssetAtPath<GameObject>($"{Out}/Trees/{key}.prefab"); if (pf) a.trees[key] = pf; }
        foreach (var gd in Grass) { var pf = AssetDatabase.LoadAssetAtPath<GameObject>($"{Out}/Grass/grass_{gd.kind}.prefab"); if (pf) a.grass.Add(pf); }
        a.railway = AssetDatabase.LoadAssetAtPath<GameObject>(Out + "/Railway.prefab");
        a.foliage = AssetDatabase.LoadAssetAtPath<Material>(Out + "/Materials/Foliage.mat");
        a.grassMat = AssetDatabase.LoadAssetAtPath<Material>(Out + "/Materials/Grass.mat");
        return a;
    }

    /// open a scene, upgrade it with the built assets, save it
    public static string UpgradeScene(string path)
    {
        var log = new StringBuilder();
        var sc = EditorSceneManager.OpenScene(path, OpenSceneMode.Single);
        ApplyToScene(LoadAssets(), log);
        EditorSceneManager.SaveScene(sc);
        return log.ToString();
    }

    static Material Mat(string name, string shader, Action<Material> set)
    {
        string p = $"{Out}/Materials/{name}.mat";
        var sh = Shader.Find(shader);
        if (sh == null) throw new Exception(shader + " did not compile (check the Console)");
        var m = AssetDatabase.LoadAssetAtPath<Material>(p);
        if (m == null) { m = new Material(sh); AssetDatabase.CreateAsset(m, p); }
        m.shader = sh;
        m.SetColor("_BaseColor", Color.white);
        set(m);
        m.enableInstancing = true;
        EditorUtility.SetDirty(m);
        return m;
    }

    static Color MeanLinear(string assetPath)
    {
        var t = new Texture2D(2, 2);
        t.LoadImage(File.ReadAllBytes(Abs(assetPath)));
        var px = t.GetPixels32(); double r = 0, g = 0, b = 0;
        for (int i = 0; i < px.Length; i += 7) { r += Mathf.GammaToLinearSpace(px[i].r / 255f); g += Mathf.GammaToLinearSpace(px[i].g / 255f); b += Mathf.GammaToLinearSpace(px[i].b / 255f); }
        int n = (px.Length + 6) / 7;
        UnityEngine.Object.DestroyImmediate(t);
        return new Color((float)(r / n), (float)(g / n), (float)(b / n), 1f);
    }

    static void FixTextures()
    {
        foreach (var (p, normal) in new[] { (Root + "/Textures/Env/ballast.png", false), (Root + "/Textures/Env/ballast_n.png", true) })
        {
            var ti = AssetImporter.GetAtPath(p) as TextureImporter; if (ti == null) continue;
            bool ch = false;
            if (normal && ti.textureType != TextureImporterType.NormalMap) { ti.textureType = TextureImporterType.NormalMap; ch = true; }
            if (ti.wrapMode != TextureWrapMode.Repeat) { ti.wrapMode = TextureWrapMode.Repeat; ch = true; }
            if (ti.anisoLevel < 8) { ti.anisoLevel = 8; ch = true; }
            if (ch) ti.SaveAndReimport();
        }
    }

    /// DWG1 bank -> meshes (sub-assets of one file). Colours: sRGB -> linear; alpha kept raw (the wind weight).
    static List<Entry> ReadBank(string dataPath, string container, bool keepAlpha)
    {
        AssetDatabase.DeleteAsset(container);
        var holder = ScriptableObject.CreateInstance<DawgsMeshBank>();
        AssetDatabase.CreateAsset(holder, container);
        var list = new List<Entry>();
        var bytes = File.ReadAllBytes(Abs(dataPath));
        if (bytes[0] != 'D' || bytes[1] != 'W' || bytes[2] != 'G' || bytes[3] != '1') throw new Exception(dataPath + ": bad header");
        int o = 4, count = BitConverter.ToInt32(bytes, o); o += 4;
        for (int e = 0; e < count; e++)
        {
            int hl = BitConverter.ToInt32(bytes, o); o += 4;
            var h = JsonUtility.FromJson<Head>(Encoding.UTF8.GetString(bytes, o, hl)); o += hl;
            int bl = BitConverter.ToInt32(bytes, o); o += 4; int b = o; o += bl;
            int nv = h.nv, ni = h.ni;
            var pos = new Vector3[nv]; var nor = new Vector3[nv]; var col = new Color[nv]; var uv = new Vector2[nv]; var idx = new int[ni];
            for (int i = 0; i < nv; i++) pos[i] = new Vector3(BitConverter.ToSingle(bytes, b + i * 12), BitConverter.ToSingle(bytes, b + i * 12 + 4), BitConverter.ToSingle(bytes, b + i * 12 + 8));
            b += nv * 12;
            for (int i = 0; i < nv; i++) nor[i] = new Vector3((sbyte)bytes[b + i * 4] / 127f, (sbyte)bytes[b + i * 4 + 1] / 127f, (sbyte)bytes[b + i * 4 + 2] / 127f).normalized;
            b += nv * 4;
            for (int i = 0; i < nv; i++)
                col[i] = new Color(Mathf.GammaToLinearSpace(bytes[b + i * 4] / 255f), Mathf.GammaToLinearSpace(bytes[b + i * 4 + 1] / 255f),
                                   Mathf.GammaToLinearSpace(bytes[b + i * 4 + 2] / 255f), keepAlpha ? bytes[b + i * 4 + 3] / 255f : 1f);
            b += nv * 4;
            for (int i = 0; i < nv; i++) uv[i] = new Vector2(BitConverter.ToSingle(bytes, b + i * 8), BitConverter.ToSingle(bytes, b + i * 8 + 4));
            b += nv * 8;
            Buffer.BlockCopy(bytes, b, idx, 0, ni * 4);
            var mesh = new Mesh { name = h.key.Replace('|', '_') };
            mesh.indexFormat = nv > 65000 ? IndexFormat.UInt32 : IndexFormat.UInt16;
            mesh.SetVertices(pos); mesh.SetNormals(nor); mesh.SetColors(col); mesh.SetUVs(0, uv);
            mesh.SetTriangles(idx, 0, true);
            mesh.UploadMeshData(false);
            AssetDatabase.AddObjectToAsset(mesh, holder);
            list.Add(new Entry { h = h, mesh = mesh });
        }
        holder.count = list.Count;
        EditorUtility.SetDirty(holder);
        return list;
    }

    // ------------------------------------------------------------------ scene
    public static void ApplyToScene(Assets a, StringBuilder log)
    {
        var props = GameObject.Find("Props");
        var pl = JsonUtility.FromJson<ProtoList>(File.ReadAllText(Abs(Root + "/Data/instances.json")));
        var protos = pl.protos.ToDictionary(p => p.key);
        var variants = new Dictionary<string, Material>();
        int trees = 0;
        if (props)
        {
            foreach (var key in TreeKeys)
            {
                var grp = props.transform.Find(key);
                if (!grp || !a.trees.TryGetValue(key, out var pf) || !protos.TryGetValue(key, out var proto)) continue;
                var old = new List<Transform>(); foreach (Transform t in grp) old.Add(t);
                for (int i = 0; i < proto.n; i++)
                {
                    int k = i * 13; var d = proto.data;
                    var go = (GameObject)PrefabUtility.InstantiatePrefab(pf, grp);
                    go.transform.SetLocalPositionAndRotation(new Vector3(d[k], d[k + 1], d[k + 2]), new Quaternion(d[k + 3], d[k + 4], d[k + 5], d[k + 6]));
                    go.transform.localScale = new Vector3(d[k + 7], d[k + 8], d[k + 9]);
                    go.isStatic = true;
                    float tr = Mathf.Round(d[k + 10] * 20) / 20, tg = Mathf.Round(d[k + 11] * 20) / 20, tb = Mathf.Round(d[k + 12] * 20) / 20;
                    if (Mathf.Abs(tr - 1) + Mathf.Abs(tg - 1) + Mathf.Abs(tb - 1) > 0.03f)
                    {
                        string vk = $"Foliage_t{tr:0.00}_{tg:0.00}_{tb:0.00}";
                        if (!variants.TryGetValue(vk, out var vm))
                        {
                            string vp = $"{Out}/Materials/{vk}.mat";
                            vm = AssetDatabase.LoadAssetAtPath<Material>(vp);
                            if (vm == null) { vm = new Material(a.foliage); AssetDatabase.CreateAsset(vm, vp); }
                            vm.CopyPropertiesFromMaterial(a.foliage);
                            vm.SetColor("_BaseColor", new Color(tr, tg, tb, 1));
                            EditorUtility.SetDirty(vm);
                            variants[vk] = vm;
                        }
                        foreach (var r in go.GetComponentsInChildren<MeshRenderer>()) r.sharedMaterial = vm;
                    }
                    trees++;
                }
                foreach (var t in old) UnityEngine.Object.DestroyImmediate(t.gameObject);
            }
            foreach (var key in OldTrackProps) { var g = props.transform.Find(key); if (g) UnityEngine.Object.DestroyImmediate(g.gameObject); }
        }
        log.AppendLine($"trees: {trees} upgraded, {variants.Count} tint variants");

        // railway: hide the flat bed ribbon, lay the modelled track
        int bed = 0;
        var world = GameObject.Find("World");
        if (world) foreach (var mr in world.GetComponentsInChildren<MeshRenderer>(true))
                if (mr.gameObject.name == "m" + RailBedMat) { mr.gameObject.SetActive(false); bed++; }
        var oldRail = GameObject.Find("Railway"); if (oldRail) UnityEngine.Object.DestroyImmediate(oldRail);
        var rail = (GameObject)PrefabUtility.InstantiatePrefab(a.railway);
        log.AppendLine($"railway: {rail.transform.childCount} chunks, rail-bed ribbons hidden: {bed}");

        // grass on the terrain
        var terrain = UnityEngine.Object.FindFirstObjectByType<Terrain>();
        if (terrain && a.grass.Count > 0) log.AppendLine(ApplyGrass(terrain, a));
        EditorSceneManager.MarkSceneDirty(UnityEngine.SceneManagement.SceneManager.GetActiveScene());
    }

    /// re-plants the terrain's grass from Data/grass_cover.raw (the ground upgrade changes where grass grows)
    public static string RefreshGrass(Terrain terrain)
    {
        var a = LoadAssets();
        if (!terrain || a.grass.Count == 0) return "grass: run Dawgs > Upgrade Environment first";
        return ApplyGrass(terrain, a);
    }

    static string ApplyGrass(Terrain terrain, Assets a)
    {
        var td = terrain.terrainData;
        string coverPath = Abs(Root + "/Data/grass_cover.raw");
        if (!File.Exists(coverPath)) return "grass: no grass_cover.raw";
        var cover = File.ReadAllBytes(coverPath);
        int layers = Grass.Length, res = (int)Math.Round(Math.Sqrt(cover.Length / layers));
        var protos = new List<DetailPrototype>();
        for (int i = 0; i < layers && i < a.grass.Count; i++)
        {
            var gd = Grass[i];
            protos.Add(new DetailPrototype
            {
                usePrototypeMesh = true, prototype = a.grass[i], renderMode = DetailRenderMode.VertexLit, useInstancing = true,
                minWidth = gd.minS, maxWidth = gd.maxS, minHeight = gd.minS, maxHeight = gd.maxS * 1.05f, noiseSpread = 0.4f,
                healthyColor = Color.white, dryColor = Color.white,
            });
        }
        td.SetDetailScatterMode(DetailScatterMode.InstanceCountMode);
        td.SetDetailResolution(res, 32);
        td.detailPrototypes = protos.ToArray();
        float cellArea = (td.size.x / res) * (td.size.z / res);
        var rng = new System.Random(11);
        long total = 0;
        for (int l = 0; l < protos.Count; l++)
        {
            var map = new int[res, res];
            float k = Grass[l].perM2 * cellArea / 255f;
            for (int y = 0; y < res; y++)
                for (int x = 0; x < res; x++)
                {
                    float want = cover[(y * res + x) * layers + l] * k;
                    int n = (int)want; if (rng.NextDouble() < want - n) n++;
                    map[y, x] = n; total += n;
                }
            td.SetDetailLayer(0, 0, l, map);
        }
        EditorUtility.SetDirty(td);
        terrain.detailObjectDistance = 140f;
        terrain.detailObjectDensity = 1f;
        terrain.drawTreesAndFoliage = true;
        EditorUtility.SetDirty(terrain);
        return $"grass: {protos.Count} layers at {res}x{res}, {total} clumps";
    }
}
