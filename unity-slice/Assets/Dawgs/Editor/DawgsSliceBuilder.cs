// Dawgs Uprising -> Unity: builds the Devtest "Test Town" slice from the data exported out of the browser game.
//   Dawgs > Build Test Town Slice      materials, meshes, prop prefabs, terrain, lighting, camera, music -> new scene
// Everything lands under Assets/Dawgs/Generated and Assets/Dawgs/Scenes/DawgsTestTown.unity. Re-running rebuilds it.
// Axes: the game's (x, y, z) is Unity's (x, y, -z); the exporter already converted every mesh and transform.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

public static class DawgsSliceBuilder
{
    const string Root = "Assets/Dawgs";
    const string Gen = Root + "/Generated";
    const string ScenePath = Root + "/Scenes/DawgsTestTown.unity";

    // ---------- data shapes (JsonUtility) ----------
    [Serializable] class MatDef { public int id; public bool unlit; public string color; public float[] col; public float[] emi; public int tex; public int emap = -1; public bool vc; public bool transparent; public float opacity; public string emissive; public float emissiveIntensity; public bool doubleSided; public float alphaTest; public float shininess; public bool additive; public string type; }
    [Serializable] class MatList { public MatDef[] mats; }
    [Serializable] class TexDef { public int i; public string name; public bool wrap; public string file; }
    [Serializable] class TexList { public TexDef[] texs; }
    [Serializable] class Proto { public string key; public int n; public float[] data; }
    [Serializable] class ProtoList { public Proto[] protos; }
    [Serializable] class Layer { public string name; public float[] tint; public float tile; }
    [Serializable] class LightDef { public string type; public string color; public float intensity; public float[] dir; public string sky; public string ground; }
    [Serializable] class FogDef { public string color; public float near; public float far; }
    [Serializable] class CamDef { public float x, z, d, yaw, pitch; }
    [Serializable] class ZoneDef { public string name; public string type; public float x, z, r; public int owner; public bool mega; public float gate; }
    [Serializable] class TerrainMeta { public float x0, z0, width, depth, hmin, hmax; public int res, alphaRes; public float water; public Layer[] layers; public LightDef[] lights; public FogDef fog; public string bg; public CamDef cam; public ZoneDef[] zones; }
    [Serializable] class EntryHead { public string key; public int mat; public int tx; public int tz; public string proto; public int nv; public int ni; }

    static string Abs(string assetPath) => Path.Combine(Path.GetDirectoryName(Application.dataPath), assetPath);
    static T Json<T>(string assetPath) => JsonUtility.FromJson<T>(File.ReadAllText(Abs(assetPath)));
    static Color Hex(string h, float a = 1f) { ColorUtility.TryParseHtmlString("#" + h, out var c); c.a = a; return c; }
    static void Dir(string p) { if (!AssetDatabase.IsValidFolder(p)) { var parent = Path.GetDirectoryName(p).Replace('\\', '/'); Dir(parent); AssetDatabase.CreateFolder(parent, Path.GetFileName(p)); } }
    static void Progress(string what, float t) { EditorUtility.DisplayProgressBar("Dawgs: building Test Town", what, t); }

    [MenuItem("Dawgs/Build Test Town Slice")]
    public static void BuildMenu() { Build(); }

    public static string Build()
    {
        var log = new System.Text.StringBuilder();
        try
        {
            Dir(Gen + "/Materials"); Dir(Gen + "/Props"); Dir(Gen + "/Terrain"); Dir(Root + "/Scenes");
            Progress("textures", 0.02f);
            FixTextureImports();
            Progress("materials", 0.08f);
            var mats = BuildMaterials(log);
            Progress("meshes", 0.2f);
            var meshes = BuildMeshes(log);
            Progress("prop prefabs", 0.45f);
            var prefabs = BuildPrefabs(meshes, mats, log);
            Progress("units", 0.5f);
            var units = BuildUnits(log);
            Progress("terrain", 0.55f);
            var meta = Json<TerrainMeta>(Root + "/Data/terrain.json");
            var tdata = BuildTerrainData(meta, log);
            Progress("scene", 0.7f);
            BuildScene(meta, tdata, meshes, mats, prefabs, log);
            AddReplay(units, log);
            Progress("environment (Blender trees, grass, railway)", 0.9f);
            DawgsEnvBuilder.ApplyToOpenScene(log);
            DawgsSurfaceBuilder.ApplyToOpenScene(log);
            EditorSceneManager.SaveScene(EditorSceneManager.GetActiveScene(), ScenePath);
            AssetDatabase.SaveAssets();
            log.AppendLine("done: " + ScenePath);
        }
        catch (Exception e) { log.AppendLine("FAILED: " + e); Debug.LogException(e); }
        finally { EditorUtility.ClearProgressBar(); }
        Debug.Log("[Dawgs] " + log);
        return log.ToString();
    }

    // ---------- textures ----------
    static void FixTextureImports()
    {
        foreach (var guid in AssetDatabase.FindAssets("t:Texture2D", new[] { Root + "/Textures" }))
        {
            var p = AssetDatabase.GUIDToAssetPath(guid);
            var ti = AssetImporter.GetAtPath(p) as TextureImporter; if (ti == null) continue;
            bool changed = false;
            bool normal = p.EndsWith("water_n.jpg") || p.Contains("_n.") || p.Contains("_normal");
            if (normal && ti.textureType != TextureImporterType.NormalMap) { ti.textureType = TextureImporterType.NormalMap; changed = true; }
            if (ti.wrapMode != TextureWrapMode.Repeat) { ti.wrapMode = TextureWrapMode.Repeat; changed = true; }
            if (ti.anisoLevel < 8) { ti.anisoLevel = 8; changed = true; }
            if (p.Contains("/Baked/") && ti.filterMode != FilterMode.Bilinear) { ti.filterMode = FilterMode.Bilinear; changed = true; }
            if (changed) ti.SaveAndReimport();
        }
    }

    // ---------- materials: one per distinct game material ----------
    static Dictionary<int, Material> BuildMaterials(System.Text.StringBuilder log)
    {
        var defs = Json<MatList>(Root + "/Data/materials.json").mats;
        var texs = Json<TexList>(Root + "/Data/textures.json").texs.ToDictionary(t => t.i);
        Shader lit = Shader.Find("Dawgs/Lit"), unlit = Shader.Find("Dawgs/Unlit");
        if (lit == null || unlit == null) throw new Exception("Dawgs shaders did not compile (check the Console)");
        var res = new Dictionary<int, Material>();
        foreach (var d in defs)
        {
            string path = $"{Gen}/Materials/M{d.id:000}.mat";
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (m == null) { m = new Material(d.unlit ? unlit : lit); AssetDatabase.CreateAsset(m, path); }
            m.shader = d.unlit ? unlit : lit;
            // exact float colours (some of the game's are brighter than 1, which its hex form can't hold)
            var bc = d.col != null && d.col.Length == 3 ? new Color(d.col[0], d.col[1], d.col[2]) : Hex(d.color);
            bc.a = d.transparent ? d.opacity : 1f;
            m.SetColor("_BaseColor", bc);
            m.SetFloat("_VertexColor", d.vc ? 1 : 0);
            Texture2D tex = null;
            if (d.tex >= 0 && texs.TryGetValue(d.tex, out var td) && !string.IsNullOrEmpty(td.file))
                tex = AssetDatabase.LoadAssetAtPath<Texture2D>($"{Root}/Textures/Baked/{td.file}");
            m.SetTexture("_BaseMap", tex);
            Texture2D etex = null;
            if (d.emap >= 0 && texs.TryGetValue(d.emap, out var ed) && !string.IsNullOrEmpty(ed.file))
                etex = AssetDatabase.LoadAssetAtPath<Texture2D>($"{Root}/Textures/Baked/{ed.file}");
            if (!d.unlit) m.SetTexture("_EmissionMap", etex);
            m.SetFloat("_Cull", d.doubleSided ? (float)CullMode.Off : (float)CullMode.Back);
            m.SetFloat("_Cutoff", d.alphaTest);
            if (!d.unlit)
            {
                // Lambert -> rough; Phong shininess -> smoothness
                float sm = d.shininess > 0 ? Mathf.Clamp01(Mathf.Log(d.shininess + 1f, 2f) / 9f) : 0.12f;
                m.SetFloat("_Smoothness", sm);
                m.SetFloat("_Metallic", 0f);
                var em = (d.emi != null && d.emi.Length == 3 ? new Color(d.emi[0], d.emi[1], d.emi[2]) : Hex(d.emissive)) * d.emissiveIntensity;
                m.SetColor("_EmissionColor", em);
                if (em.maxColorComponent > 0.001f) { m.EnableKeyword("_EMISSION"); m.globalIlluminationFlags = MaterialGlobalIlluminationFlags.None; }
            }
            else m.SetFloat("_Intensity", 1f);
            if (d.transparent || d.additive)
            {
                m.SetOverrideTag("RenderType", "Transparent");
                m.SetFloat("_SrcBlend", d.additive ? (float)BlendMode.One : (float)BlendMode.SrcAlpha);
                m.SetFloat("_DstBlend", d.additive ? (float)BlendMode.One : (float)BlendMode.OneMinusSrcAlpha);
                m.SetFloat("_ZWrite", 0);
                m.renderQueue = (int)RenderQueue.Transparent;
            }
            else
            {
                m.SetOverrideTag("RenderType", d.alphaTest > 0 ? "TransparentCutout" : "Opaque");
                m.SetFloat("_SrcBlend", (float)BlendMode.One); m.SetFloat("_DstBlend", (float)BlendMode.Zero); m.SetFloat("_ZWrite", 1);
                m.renderQueue = d.alphaTest > 0 ? (int)RenderQueue.AlphaTest : (int)RenderQueue.Geometry;
            }
            m.enableInstancing = true;
            EditorUtility.SetDirty(m);
            res[d.id] = m;
        }
        log.AppendLine($"materials {res.Count}");
        return res;
    }

    // ---------- meshes: world.bytes -> one mesh per (96 m tile, material), one per (prop prototype, material) ----------
    class MeshEntry { public EntryHead h; public Mesh mesh; }
    static List<MeshEntry> BuildMeshes(System.Text.StringBuilder log) => ReadBank(Root + "/Data/world.bytes", Gen + "/WorldMeshes.asset", log);
    static List<MeshEntry> ReadBank(string dataPath, string container, System.Text.StringBuilder log)
    {
        AssetDatabase.DeleteAsset(container);
        var holder = ScriptableObject.CreateInstance<DawgsMeshBank>();
        AssetDatabase.CreateAsset(holder, container);
        var list = new List<MeshEntry>();
        var bytes = File.ReadAllBytes(Abs(dataPath));
        int o = 0;
        if (bytes[0] != 'D' || bytes[1] != 'W' || bytes[2] != 'G' || bytes[3] != '1') throw new Exception(dataPath + ": bad header");
        o = 4; int count = BitConverter.ToInt32(bytes, o); o += 4;
        long tris = 0;
        for (int e = 0; e < count; e++)
        {
            int hl = BitConverter.ToInt32(bytes, o); o += 4;
            var h = JsonUtility.FromJson<EntryHead>(System.Text.Encoding.UTF8.GetString(bytes, o, hl)); o += hl;
            int bl = BitConverter.ToInt32(bytes, o); o += 4; int b = o; o += bl;
            int nv = h.nv, ni = h.ni;
            var pos = new Vector3[nv]; var nor = new Vector3[nv]; var col = new Color[nv]; var uv = new Vector2[nv]; var idx = new int[ni];
            for (int i = 0; i < nv; i++) { pos[i] = new Vector3(BitConverter.ToSingle(bytes, b + i * 12), BitConverter.ToSingle(bytes, b + i * 12 + 4), BitConverter.ToSingle(bytes, b + i * 12 + 8)); }
            b += nv * 12;
            for (int i = 0; i < nv; i++) { nor[i] = new Vector3((sbyte)bytes[b + i * 4] / 127f, (sbyte)bytes[b + i * 4 + 1] / 127f, (sbyte)bytes[b + i * 4 + 2] / 127f).normalized; }
            b += nv * 4;
            for (int i = 0; i < nv; i++)   // the game's colours are display values: linearise them like material colours
                col[i] = new Color(Mathf.GammaToLinearSpace(bytes[b + i * 4] / 255f), Mathf.GammaToLinearSpace(bytes[b + i * 4 + 1] / 255f), Mathf.GammaToLinearSpace(bytes[b + i * 4 + 2] / 255f), 1f);
            b += nv * 4;
            for (int i = 0; i < nv; i++) uv[i] = new Vector2(BitConverter.ToSingle(bytes, b + i * 8), BitConverter.ToSingle(bytes, b + i * 8 + 4));
            b += nv * 8;
            Buffer.BlockCopy(bytes, b, idx, 0, ni * 4);
            var mesh = new Mesh { name = !string.IsNullOrEmpty(h.proto) ? $"{h.proto}_m{h.mat}" : $"W_{h.tx}_{h.tz}_m{h.mat}" };
            mesh.indexFormat = nv > 65000 ? IndexFormat.UInt32 : IndexFormat.UInt16;
            mesh.SetVertices(pos); mesh.SetNormals(nor); mesh.SetColors(col); mesh.SetUVs(0, uv);
            mesh.SetTriangles(idx, 0, true);
            AssetDatabase.AddObjectToAsset(mesh, holder);
            list.Add(new MeshEntry { h = h, mesh = mesh });
            tris += ni / 3;
            if ((e & 31) == 0) Progress($"meshes {e}/{count}", 0.2f + 0.25f * e / count);
        }
        holder.count = list.Count;
        EditorUtility.SetDirty(holder);
        AssetDatabase.SaveAssets();
        log.AppendLine($"{Path.GetFileName(dataPath)}: {list.Count} meshes, {tris} triangles");
        return list;
    }

    // ---------- prop prefabs (trees, rocks, sheds...): one per prototype, replaceable with upgraded models ----------
    static Dictionary<string, GameObject> BuildPrefabs(List<MeshEntry> meshes, Dictionary<int, Material> mats, System.Text.StringBuilder log)
    {
        var res = new Dictionary<string, GameObject>();
        foreach (var g in meshes.Where(m => !string.IsNullOrEmpty(m.h.proto)).GroupBy(m => m.h.proto))
        {
            var go = new GameObject(g.Key);
            foreach (var me in g)
            {
                var c = new GameObject("m" + me.h.mat); c.transform.SetParent(go.transform, false);
                c.AddComponent<MeshFilter>().sharedMesh = me.mesh;
                c.AddComponent<MeshRenderer>().sharedMaterial = mats[me.h.mat];
            }
            string path = $"{Gen}/Props/{g.Key}.prefab";
            var pf = PrefabUtility.SaveAsPrefabAsset(go, path);
            UnityEngine.Object.DestroyImmediate(go);
            res[g.Key] = pf;
        }
        log.AppendLine($"prop prefabs {res.Count}");
        return res;
    }

    // ---------- units: every unit model for both armies, as prefabs (swap in upgraded models here) ----------
    static Dictionary<string, GameObject> BuildUnits(System.Text.StringBuilder log)
    {
        Dir(Gen + "/Units");
        var res = new Dictionary<string, GameObject>();
        if (!File.Exists(Abs(Root + "/Data/units.bytes"))) return res;
        var mp = Gen + "/Materials/Unit.mat";
        var um = AssetDatabase.LoadAssetAtPath<Material>(mp);
        if (um == null) { um = new Material(Shader.Find("Dawgs/Lit")); AssetDatabase.CreateAsset(um, mp); }
        um.SetFloat("_VertexColor", 1); um.SetFloat("_Smoothness", 0.32f); um.SetFloat("_Metallic", 0.08f); um.enableInstancing = true; EditorUtility.SetDirty(um);
        foreach (var me in ReadBank(Root + "/Data/units.bytes", Gen + "/UnitMeshes.asset", log))
        {
            var go = new GameObject(me.h.proto);
            var body = new GameObject("body"); body.transform.SetParent(go.transform, false);
            body.AddComponent<MeshFilter>().sharedMesh = me.mesh;
            body.AddComponent<MeshRenderer>().sharedMaterial = um;
            res[me.h.proto] = PrefabUtility.SaveAsPrefabAsset(go, $"{Gen}/Units/{me.h.proto}.prefab");
            UnityEngine.Object.DestroyImmediate(go);
        }
        log.AppendLine($"unit prefabs {res.Count}");
        return res;
    }

    // ---------- the recorded 1v1: units, tracers, blasts and the game's own weapon sounds ----------
    static void AddReplay(Dictionary<string, GameObject> units, System.Text.StringBuilder log)
    {
        var rb = AssetDatabase.LoadAssetAtPath<TextAsset>(Root + "/Data/replay.bytes");
        var rm = AssetDatabase.LoadAssetAtPath<TextAsset>(Root + "/Data/replay_meta.json");
        if (rb == null || rm == null) { log.AppendLine("no replay data"); return; }
        string tp = Gen + "/Materials/Tracer.mat";
        var tm = AssetDatabase.LoadAssetAtPath<Material>(tp);
        if (tm == null) { tm = new Material(Shader.Find("Dawgs/Unlit")); AssetDatabase.CreateAsset(tm, tp); }
        tm.SetOverrideTag("RenderType", "Transparent");
        tm.SetFloat("_SrcBlend", (float)BlendMode.One); tm.SetFloat("_DstBlend", (float)BlendMode.One); tm.SetFloat("_ZWrite", 0);
        tm.SetFloat("_VertexColor", 1); tm.SetFloat("_Intensity", 2.2f); tm.SetFloat("_Cull", (float)CullMode.Off);
        tm.renderQueue = (int)RenderQueue.Transparent + 10; EditorUtility.SetDirty(tm);

        var go = new GameObject("Battle Replay");
        var rp = go.AddComponent<DawgsReplay>();
        rp.replayBytes = rb; rp.replayMeta = rm; rp.tracerMaterial = tm;
        // units rigged in Blender (Dawgs/Rigged) replace the static models where there is one
        var rigged = DawgsRigBuilder.BuildAll();
        foreach (var kv in rigged) units[kv.Key] = kv.Value;
        foreach (var kv in units) rp.unitPrefabs.Add(new DawgsReplay.UnitPrefab { key = kv.Key, prefab = kv.Value });
        log.AppendLine($"rigged units: {rigged.Count}");
        foreach (var guid in AssetDatabase.FindAssets("t:AudioClip", new[] { Root + "/Audio/Sfx" }))
        {
            var p = AssetDatabase.GUIDToAssetPath(guid); var clip = AssetDatabase.LoadAssetAtPath<AudioClip>(p);
            string key = Path.GetFileNameWithoutExtension(p);
            float vol = key == "rifle" ? 0.55f : key == "mg_burst" ? 0.5f : key == "collapse" ? 0.8f : key == "mac_fire" ? 0.6f : 0.7f;
            rp.sounds.Add(new DawgsReplay.Sfx { key = key, clip = clip, volume = vol, pitch = key == "mac_fire" ? 0.8f : 1f });
        }
        log.AppendLine($"replay: {rp.unitPrefabs.Count} unit models, {rp.sounds.Count} sounds");
    }

    // ---------- terrain: the game's heights and its grass / sand / rock / soil splat ----------
    static TerrainData BuildTerrainData(TerrainMeta meta, System.Text.StringBuilder log)
    {
        string path = Gen + "/Terrain/TestTownTerrain.asset";
        AssetDatabase.DeleteAsset(path);
        var td = new TerrainData();
        int res = meta.res;
        td.heightmapResolution = res;
        td.size = new Vector3(meta.width, meta.hmax - meta.hmin, meta.depth);
        var raw = File.ReadAllBytes(Abs(Root + "/Data/height1025.raw"));
        var h = new float[res, res];
        for (int r = 0; r < res; r++) for (int c = 0; c < res; c++) h[r, c] = BitConverter.ToUInt16(raw, (r * res + c) * 2) / 65535f;
        td.SetHeights(0, 0, h);

        var layers = new List<TerrainLayer>();
        foreach (var L in meta.layers)
        {
            string lp = $"{Gen}/Terrain/{L.name}.terrainlayer";
            var tl = AssetDatabase.LoadAssetAtPath<TerrainLayer>(lp);
            if (tl == null) { tl = new TerrainLayer(); AssetDatabase.CreateAsset(tl, lp); }
            tl.diffuseTexture = AssetDatabase.LoadAssetAtPath<Texture2D>($"{Root}/Textures/Ground/{L.name}.jpg");
            tl.tileSize = new Vector2(L.tile, L.tile);
            tl.diffuseRemapMin = Vector4.zero;
            var tint = new Vector3(L.tint[0], L.tint[1], L.tint[2]);
            if (L.name == "grass") tint = Vector3.Scale(tint, new Vector3(0.86f, 1.04f, 1.0f));   // the game's grass reads greener
            tl.diffuseRemapMax = new Vector4(tint.x, tint.y, tint.z, 1f);   // keeps the game's palette
            tl.smoothness = L.name == "sand" ? 0.18f : 0.06f;
            tl.metallic = 0f;
            EditorUtility.SetDirty(tl);
            layers.Add(tl);
        }
        td.terrainLayers = layers.ToArray();
        int ar = meta.alphaRes;
        td.alphamapResolution = ar;
        var sp = File.ReadAllBytes(Abs(Root + "/Data/splat1024.raw"));
        var a = new float[ar, ar, 4];
        for (int r = 0; r < ar; r++) for (int c = 0; c < ar; c++) for (int k = 0; k < 4; k++) a[r, c, k] = sp[(r * ar + c) * 4 + k] / 255f;
        td.SetAlphamaps(0, 0, a);
        AssetDatabase.CreateAsset(td, path);
        log.AppendLine($"terrain {meta.width}x{meta.depth} m, heights {meta.hmin:0.0}..{meta.hmax:0.0}");
        return td;
    }

    // ---------- the scene ----------
    static void BuildScene(TerrainMeta meta, TerrainData td, List<MeshEntry> meshes, Dictionary<int, Material> mats, Dictionary<string, GameObject> prefabs, System.Text.StringBuilder log)
    {
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        // terrain (game z flipped: Unity z runs from -(z0 + depth) to -z0)
        var tgo = Terrain.CreateTerrainGameObject(td);
        tgo.name = "Terrain";
        tgo.transform.position = new Vector3(meta.x0, meta.hmin, -(meta.z0 + meta.depth));
        var terrain = tgo.GetComponent<Terrain>();
        var rp = GraphicsSettings.currentRenderPipeline;
        if (rp != null && rp.defaultTerrainMaterial != null) terrain.materialTemplate = rp.defaultTerrainMaterial;
        terrain.heightmapPixelError = 2f; terrain.basemapDistance = 2000f; terrain.drawInstanced = true;
        terrain.shadowCastingMode = ShadowCastingMode.On;

        // water
        var water = new GameObject("Water");
        water.transform.position = new Vector3(0, meta.water, 0);
        var wm = new Mesh { name = "WaterQuad" };
        float WX = Mathf.Max(1600f, meta.width * 4.5f) / 2f, WZ = Mathf.Max(1100f, meta.depth * 6f) / 2f;
        wm.vertices = new[] { new Vector3(-WX, 0, -WZ), new Vector3(-WX, 0, WZ), new Vector3(WX, 0, WZ), new Vector3(WX, 0, -WZ) };
        wm.uv = new[] { new Vector2(0, 0), new Vector2(0, WZ / 12f), new Vector2(WX / 12f, WZ / 12f), new Vector2(WX / 12f, 0) };
        wm.triangles = new[] { 0, 1, 2, 0, 2, 3 }; wm.RecalculateNormals(); wm.RecalculateTangents(); wm.RecalculateBounds();
        AssetDatabase.DeleteAsset(Gen + "/WaterQuad.asset"); AssetDatabase.CreateAsset(wm, Gen + "/WaterQuad.asset");
        water.AddComponent<MeshFilter>().sharedMesh = wm;
        water.AddComponent<MeshRenderer>().sharedMaterial = WaterMaterial();

        // world: baked static geometry by 96 m tile
        var world = new GameObject("World");
        var tiles = new Dictionary<string, Transform>();
        foreach (var me in meshes.Where(m => string.IsNullOrEmpty(m.h.proto)))
        {
            string tk = $"Tile_{me.h.tx}_{me.h.tz}";
            if (!tiles.TryGetValue(tk, out var tt)) { tt = new GameObject(tk).transform; tt.SetParent(world.transform, false); tiles[tk] = tt; }
            var g = new GameObject($"m{me.h.mat}"); g.transform.SetParent(tt, false);
            g.AddComponent<MeshFilter>().sharedMesh = me.mesh;
            var mr = g.AddComponent<MeshRenderer>(); mr.sharedMaterial = mats[me.h.mat];
            if (mats[me.h.mat].renderQueue >= (int)RenderQueue.Transparent) mr.shadowCastingMode = ShadowCastingMode.Off;
        }

        // props: prefab instances with the game's per-instance tint (tints share a handful of material variants)
        var props = new GameObject("Props");
        var pl = Json<ProtoList>(Root + "/Data/instances.json");
        var variants = new Dictionary<string, Material>();
        int placed = 0;
        foreach (var p in pl.protos)
        {
            if (!prefabs.TryGetValue(p.key, out var pf)) continue;
            var parent = new GameObject(p.key).transform; parent.SetParent(props.transform, false);
            for (int i = 0; i < p.n; i++)
            {
                int k = i * 13; var d = p.data;
                var go = (GameObject)PrefabUtility.InstantiatePrefab(pf, parent);
                go.transform.SetLocalPositionAndRotation(new Vector3(d[k], d[k + 1], d[k + 2]), new Quaternion(d[k + 3], d[k + 4], d[k + 5], d[k + 6]));
                go.transform.localScale = new Vector3(d[k + 7], d[k + 8], d[k + 9]);
                float tr = d[k + 10], tg = d[k + 11], tb = d[k + 12];
                if (Mathf.Abs(tr - 1) + Mathf.Abs(tg - 1) + Mathf.Abs(tb - 1) > 0.03f)
                {
                    tr = Mathf.Round(tr * 20) / 20; tg = Mathf.Round(tg * 20) / 20; tb = Mathf.Round(tb * 20) / 20;
                    foreach (var r in go.GetComponentsInChildren<MeshRenderer>())
                    {
                        var bm = r.sharedMaterial; string vk = $"{bm.name}_t{tr:0.00}_{tg:0.00}_{tb:0.00}";
                        if (!variants.TryGetValue(vk, out var vm))
                        {
                            string vp = $"{Gen}/Materials/{vk}.mat";
                            vm = AssetDatabase.LoadAssetAtPath<Material>(vp);
                            if (vm == null) { vm = new Material(bm); AssetDatabase.CreateAsset(vm, vp); }
                            vm.CopyPropertiesFromMaterial(bm);
                            var bc = bm.GetColor("_BaseColor"); vm.SetColor("_BaseColor", new Color(bc.r * tr, bc.g * tg, bc.b * tb, bc.a));
                            variants[vk] = vm;
                        }
                        r.sharedMaterial = vm;
                    }
                }
                placed++;
            }
        }

        // sun, sky light, fog
        var sunDef = meta.lights.FirstOrDefault(l => l.type == "dir");
        var sun = new GameObject("Sun").AddComponent<Light>();
        sun.type = LightType.Directional;
        sun.color = sunDef != null ? Hex(sunDef.color) : new Color(1f, .86f, .7f);
        sun.intensity = sunDef != null ? sunDef.intensity * 1.2f : 1.4f;
        sun.shadows = LightShadows.Soft; sun.shadowStrength = 0.85f;
        var dir = sunDef != null ? new Vector3(sunDef.dir[0], sunDef.dir[1], -sunDef.dir[2]) : new Vector3(.5f, -.75f, .35f);
        sun.transform.rotation = Quaternion.LookRotation(dir.normalized);
        RenderSettings.sun = sun;
        var hemi = meta.lights.FirstOrDefault(l => l.type == "hemi");
        RenderSettings.ambientMode = AmbientMode.Trilight;
        if (hemi != null)
        {
            var sky = Hex(hemi.sky) * hemi.intensity * 1.7f; var gnd = Hex(hemi.ground) * hemi.intensity * 1.9f;   // three.js skips colour management, so its shade reads lighter: lift the fill
            RenderSettings.ambientSkyColor = sky; RenderSettings.ambientEquatorColor = Color.Lerp(sky, gnd, .45f); RenderSettings.ambientGroundColor = gnd;
        }
        RenderSettings.skybox = null;
        if (meta.fog != null && !string.IsNullOrEmpty(meta.fog.color))
        {
            RenderSettings.fog = true; RenderSettings.fogMode = FogMode.Linear; RenderSettings.fogColor = Hex(meta.fog.color);
            RenderSettings.fogStartDistance = meta.fog.near; RenderSettings.fogEndDistance = meta.fog.far;
        }

        // camera, starting over Test Town the way the game frames it
        var camGo = new GameObject("RTS Camera"); camGo.tag = "MainCamera";
        var cam = camGo.AddComponent<Camera>(); cam.fieldOfView = 34f; cam.nearClipPlane = 0.5f; cam.farClipPlane = 3000f;
        cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = meta.fog != null ? Hex(meta.fog.color) : Hex(meta.bg ?? "1b4a5c");
        camGo.AddComponent<AudioListener>();
        var ucd = cam.GetUniversalAdditionalCameraData(); ucd.renderPostProcessing = true; ucd.antialiasing = AntialiasingMode.SubpixelMorphologicalAntiAliasing; ucd.antialiasingQuality = AntialiasingQuality.High;
        var rts = camGo.AddComponent<DawgsRtsCamera>();
        var town = meta.zones.FirstOrDefault(z => z.name == "Test Town") ?? meta.zones[0];
        rts.target = new Vector3(town.x + 8f, 0f, -(town.z - 14f)); rts.distance = 150f; rts.pitch = 0.9f; rts.yaw = 0.35f;
        rts.boundsMin = new Vector2(meta.x0, -(meta.z0 + meta.depth)); rts.boundsMax = new Vector2(meta.x0 + meta.width, -meta.z0);
        rts.Apply();

        // post-processing: the game's ACES look plus a little bloom on the lit windows
        var vol = new GameObject("Post Processing").AddComponent<Volume>(); vol.isGlobal = true;
        string pp = Gen + "/TestTownPost.asset"; AssetDatabase.DeleteAsset(pp);
        var prof = ScriptableObject.CreateInstance<VolumeProfile>(); AssetDatabase.CreateAsset(prof, pp);
        var tm = prof.Add<Tonemapping>(true); tm.mode.Override(TonemappingMode.Neutral);   // ACES' toe crushes the game's linear-space colours; Neutral matches the browser look
        var bl = prof.Add<Bloom>(true); bl.threshold.Override(1.0f); bl.intensity.Override(0.35f); bl.scatter.Override(0.6f);
        var ca = prof.Add<ColorAdjustments>(true); ca.postExposure.Override(0.35f); ca.contrast.Override(0f); ca.saturation.Override(-6f);
        var vg = prof.Add<Vignette>(true); vg.intensity.Override(0.2f);
        foreach (var c in prof.components) AssetDatabase.AddObjectToAsset(c, prof);
        vol.sharedProfile = prof;

        // an RTS camera sits 100-300 m up: shadows have to reach that far (the URP template stops them at 50 m)
        if (GraphicsSettings.currentRenderPipeline is UniversalRenderPipelineAsset urp && urp.shadowDistance < 400f)
        { urp.shadowDistance = 420f; urp.cascade4Split = new Vector3(0.06f, 0.18f, 0.45f); EditorUtility.SetDirty(urp); }

        // the game's battle music
        var music = new GameObject("Music").AddComponent<AudioSource>();
        music.clip = AssetDatabase.LoadAssetAtPath<AudioClip>(Root + "/Audio/Music/battle3.mp3");
        music.loop = true; music.playOnAwake = true; music.volume = 0.45f; music.spatialBlend = 0f;

        EditorSceneManager.SaveScene(scene, ScenePath);
        log.AppendLine($"scene: {tiles.Count} tiles, {placed} props, {variants.Count} tint variants");
    }

    static Material WaterMaterial()
    {
        string p = Gen + "/Materials/Water.mat";
        var m = AssetDatabase.LoadAssetAtPath<Material>(p);
        var sh = Shader.Find("Universal Render Pipeline/Lit");
        if (m == null) { m = new Material(sh); AssetDatabase.CreateAsset(m, p); }
        m.shader = sh;
        m.SetFloat("_Surface", 1f); m.SetFloat("_Blend", 0f);
        m.SetOverrideTag("RenderType", "Transparent");
        m.SetFloat("_SrcBlend", (float)BlendMode.SrcAlpha); m.SetFloat("_DstBlend", (float)BlendMode.OneMinusSrcAlpha);
        m.SetFloat("_SrcBlendAlpha", (float)BlendMode.One); m.SetFloat("_DstBlendAlpha", (float)BlendMode.OneMinusSrcAlpha);
        m.SetFloat("_ZWrite", 0f);
        m.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
        m.renderQueue = (int)RenderQueue.Transparent;
        m.SetColor("_BaseColor", new Color(0x2f / 255f, 0x6f / 255f, 0x7e / 255f, 0.8f));
        m.SetFloat("_Smoothness", 0.93f); m.SetFloat("_Metallic", 0f);
        var n = AssetDatabase.LoadAssetAtPath<Texture2D>(Root + "/Textures/Ground/water_n.jpg");
        if (n != null) { m.SetTexture("_BumpMap", n); m.SetFloat("_BumpScale", 0.45f); m.EnableKeyword("_NORMALMAP"); }
        m.SetFloat("_ReceiveShadows", 1f);
        EditorUtility.SetDirty(m);
        return m;
    }
}
