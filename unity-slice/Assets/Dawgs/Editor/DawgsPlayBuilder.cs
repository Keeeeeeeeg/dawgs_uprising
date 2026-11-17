// Dawgs Uprising -> Unity: turns the Test Town slice into a playable 1v1 skirmish scene.
//   Dawgs > Build Playable Skirmish   ->  Assets/Dawgs/Scenes/DawgsSkirmish.unity
// Copies the slice scene, swaps the battle replay for the game (DawgsGame + DawgsCommand), adds the UI Toolkit HUD
// (PanelSettings, theme, DawgsHud.uss), an EventSystem for the Input System, renders a thumbnail of every unit for the
// HUD's cards (the game's look: the model over a blue-grey radial backdrop) and a top-down picture of the map for
// the minimap.
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.UIElements;

public static class DawgsPlayBuilder
{
    const string Root = "Assets/Dawgs";
    const string Gen = Root + "/Generated";
    const string SlicePath = Root + "/Scenes/DawgsTestTown.unity";
    const string ScenePath = Root + "/Scenes/DawgsSkirmish.unity";

    static void Dir(string p) { if (!AssetDatabase.IsValidFolder(p)) { var parent = Path.GetDirectoryName(p).Replace('\\', '/'); Dir(parent); AssetDatabase.CreateFolder(parent, Path.GetFileName(p)); } }
    static string Abs(string assetPath) => Path.Combine(Path.GetDirectoryName(Application.dataPath), assetPath);

    [MenuItem("Dawgs/Build Playable Skirmish")]
    public static void BuildMenu() { Debug.Log("[Dawgs] " + Build()); }

    public static string Build(bool rebuildSlice = false)
    {
        var log = new System.Text.StringBuilder();
        if (rebuildSlice || !File.Exists(Abs(SlicePath))) log.AppendLine(DawgsSliceBuilder.Build());
        Dir(Gen + "/Thumbs"); Dir(Root + "/UI");
        var scene = EditorSceneManager.OpenScene(SlicePath, OpenSceneMode.Single);

        // the replay's assets carry over; the replay itself goes
        var rep = Object.FindFirstObjectByType<DawgsReplay>();
        var prefabs = new Dictionary<string, GameObject>(); var sounds = new List<DawgsFx.Sfx>(); Material tracer = null;
        if (rep)
        {
            foreach (var u in rep.unitPrefabs) if (u.prefab) prefabs[u.key] = u.prefab;
            foreach (var s in rep.sounds) sounds.Add(new DawgsFx.Sfx { key = s.key, clip = s.clip, volume = s.volume, pitch = s.pitch });
            tracer = rep.tracerMaterial;
            Object.DestroyImmediate(rep.gameObject);
        }
        log.AppendLine($"unit models {prefabs.Count}, sounds {sounds.Count}");

        // ring material: alpha-blended unlit, tinted per unit
        string rp = Gen + "/Materials/Ring.mat";
        var ring = AssetDatabase.LoadAssetAtPath<Material>(rp);
        if (ring == null) { ring = new Material(Shader.Find("Dawgs/Unlit")); AssetDatabase.CreateAsset(ring, rp); }
        ring.SetOverrideTag("RenderType", "Transparent");
        ring.SetFloat("_SrcBlend", (float)BlendMode.SrcAlpha); ring.SetFloat("_DstBlend", (float)BlendMode.OneMinusSrcAlpha); ring.SetFloat("_ZWrite", 0);
        ring.SetFloat("_VertexColor", 1); ring.SetFloat("_Intensity", 1.3f); ring.SetFloat("_Cull", (float)CullMode.Off);
        ring.renderQueue = (int)RenderQueue.Transparent + 5; EditorUtility.SetDirty(ring);

        // thumbnails and the minimap picture, before the game objects exist
        bool fog = RenderSettings.fog; RenderSettings.fog = false;
        var thumbs = RenderThumbs(prefabs);
        string mp = Gen + "/minimap.png";
        File.WriteAllBytes(Abs(mp), RenderMinimap(1032, 384).EncodeToPNG());
        RenderSettings.fog = fog;
        AssetDatabase.Refresh();
        foreach (var th in thumbs) { string tp = $"{Gen}/Thumbs/{th.key}.png"; UiTexture(tp); th.tex = AssetDatabase.LoadAssetAtPath<Texture2D>(tp); }
        UiTexture(mp);
        log.AppendLine($"thumbnails {thumbs.Count}");

        // UI Toolkit: a theme that pulls in the HUD stylesheet, and panel settings scaled to a 1600 x 900 layout
        string ussPath = Root + "/UI/DawgsHud.uss", tssPath = Root + "/UI/DawgsTheme.tss", psPath = Root + "/UI/DawgsPanelSettings.asset";
        File.WriteAllText(Abs(tssPath), "@import url(\"project://database/Assets/Dawgs/UI/DawgsHud.uss\");\n");
        AssetDatabase.ImportAsset(tssPath);
        var theme = AssetDatabase.LoadAssetAtPath<ThemeStyleSheet>(tssPath);
        var ps = AssetDatabase.LoadAssetAtPath<PanelSettings>(psPath);
        if (ps == null) { ps = ScriptableObject.CreateInstance<PanelSettings>(); AssetDatabase.CreateAsset(ps, psPath); }
        ps.themeStyleSheet = theme; ps.scaleMode = PanelScaleMode.ScaleWithScreenSize; ps.referenceResolution = new Vector2Int(1600, 900);
        ps.screenMatchMode = PanelScreenMatchMode.MatchWidthOrHeight; ps.match = 1f; ps.clearColor = false; EditorUtility.SetDirty(ps);

        // the game
        var gameGo = new GameObject("Dawgs Game");
        var game = gameGo.AddComponent<DawgsGame>();
        game.dataJson = AssetDatabase.LoadAssetAtPath<TextAsset>(Root + "/Data/game_data.json");
        game.unitPrefabs = prefabs.Select(kv => new DawgsGame.UnitPrefab { key = kv.Key, prefab = kv.Value }).ToList();
        game.sounds = sounds; game.thumbs = thumbs; game.tracerMaterial = tracer; game.ringMaterial = ring;
        game.minimap = AssetDatabase.LoadAssetAtPath<Texture2D>(mp);
        var cmd = gameGo.AddComponent<DawgsCommand>(); cmd.game = game;
        var hudGo = new GameObject("HUD");
        var docu = hudGo.AddComponent<UIDocument>(); docu.panelSettings = ps;
        var hud = hudGo.AddComponent<DawgsHud>(); hud.game = game; hud.cmd = cmd; hud.style = AssetDatabase.LoadAssetAtPath<StyleSheet>(ussPath);
        cmd.hud = hud;
        var es = new GameObject("EventSystem");
        es.AddComponent<UnityEngine.EventSystems.EventSystem>();
        es.AddComponent<UnityEngine.InputSystem.UI.InputSystemUIInputModule>();

        // the camera: no Q/E turning (missile key) and no right-drag tilt (orders)
        var rts = Object.FindFirstObjectByType<DawgsRtsCamera>();
        if (rts) { rts.keyTurn = false; rts.dragTilt = false; rts.minDistance = 14f; EditorUtility.SetDirty(rts); }

        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene, ScenePath);
        var list = EditorBuildSettings.scenes.Where(s => s.path != ScenePath).ToList();
        list.Insert(0, new EditorBuildSettingsScene(ScenePath, true));
        EditorBuildSettings.scenes = list.ToArray();
        AssetDatabase.SaveAssets();
        log.AppendLine("done: " + ScenePath);
        return log.ToString();
    }

    static void UiTexture(string path)
    {
        var ti = AssetImporter.GetAtPath(path) as TextureImporter; if (ti == null) return;
        ti.textureType = TextureImporterType.Default; ti.mipmapEnabled = false; ti.wrapMode = TextureWrapMode.Clamp;
        ti.npotScale = TextureImporterNPOTScale.None; ti.textureCompression = TextureImporterCompression.Uncompressed; ti.alphaIsTransparency = true;
        ti.SaveAndReimport();
    }

    static Texture2D Grab(Camera c, int w, int h, Color bg)
    {
        c.backgroundColor = bg;
        var rt = new RenderTexture(w, h, 24, RenderTextureFormat.ARGB32) { antiAliasing = 8 };
        c.targetTexture = rt; c.Render();
        var prev = RenderTexture.active; RenderTexture.active = rt;
        var t = new Texture2D(w, h, TextureFormat.RGBA32, false); t.ReadPixels(new Rect(0, 0, w, h), 0, 0); t.Apply();
        RenderTexture.active = prev; c.targetTexture = null; Object.DestroyImmediate(rt);
        return t;
    }

    static Camera TempCamera(string name)
    {
        var go = new GameObject(name); var c = go.AddComponent<Camera>();
        c.clearFlags = CameraClearFlags.SolidColor; c.allowHDR = false; c.allowMSAA = true;
        var ucd = c.GetUniversalAdditionalCameraData(); ucd.renderPostProcessing = false; ucd.renderShadows = false; ucd.antialiasing = AntialiasingMode.None;
        return c;
    }

    // every recruitable unit's picture for the HUD, twice the tile's usual size so it stays sharp on the bigger tiles a
    // roomy command card gets (Generated/Thumbs/<type>.png)
    static List<DawgsGame.Thumb> RenderThumbs(Dictionary<string, GameObject> prefabs)
    {
        var thumbs = new List<DawgsGame.Thumb>();
        var types = new HashSet<string>(DawgsGame.RecruitGroups.SelectMany(g => g.Skip(1)));
        foreach (var t in new[] { "rifle", "mg", "at", "sniper", "rover" }) types.Add(t);
        foreach (var t in types)
        {
            if (!prefabs.TryGetValue($"u_{t}_0", out var pf)) continue;
            string tp = $"{Gen}/Thumbs/{t}.png";
            File.WriteAllBytes(Abs(tp), RenderThumb(pf, 416, 264).EncodeToPNG());
            thumbs.Add(new DawgsGame.Thumb { key = t, tex = null });
        }
        return thumbs;
    }

    /// re-renders the unit pictures in place (same files, so the skirmish scene keeps pointing at them), without
    /// rebuilding the scene
    [MenuItem("Dawgs/Rebuild Unit Thumbnails")]
    public static void ThumbsMenu() { if (EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) Debug.Log("[Dawgs] " + RebuildThumbnails()); }

    public static string RebuildThumbnails()
    {
        string back = EditorSceneManager.GetActiveScene().path;
        Dir(Gen + "/Thumbs");
        EditorSceneManager.OpenScene(SlicePath, OpenSceneMode.Single);
        var rep = Object.FindFirstObjectByType<DawgsReplay>();
        var prefabs = new Dictionary<string, GameObject>();
        if (rep) foreach (var u in rep.unitPrefabs) if (u.prefab) prefabs[u.key] = u.prefab;
        bool fog = RenderSettings.fog; RenderSettings.fog = false;
        var thumbs = RenderThumbs(prefabs);
        RenderSettings.fog = fog;
        AssetDatabase.Refresh();
        foreach (var th in thumbs) UiTexture($"{Gen}/Thumbs/{th.key}.png");
        if (!string.IsNullOrEmpty(back) && back != SlicePath) EditorSceneManager.OpenScene(back, OpenSceneMode.Single);
        return $"thumbnails {thumbs.Count} at 416x264";
    }

    // the model from the front right, over the game's thumbnail backdrop (radial #4a6278 -> #24313c -> #141b21)
    static Texture2D RenderThumb(GameObject prefab, int w, int h)
    {
        var inst = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
        inst.transform.position = new Vector3(0f, 2500f, 0f);
        // the model's real vertices (skinned meshes baked in their pose), so the frame fits it tightly
        var pts = new List<Vector3>();
        foreach (var smr in inst.GetComponentsInChildren<SkinnedMeshRenderer>())
        { var m = new Mesh(); smr.BakeMesh(m, true); foreach (var v in m.vertices) pts.Add(smr.transform.TransformPoint(v)); Object.DestroyImmediate(m); }
        foreach (var mf in inst.GetComponentsInChildren<MeshFilter>())
            if (mf.sharedMesh && mf.GetComponent<MeshRenderer>()) foreach (var v in mf.sharedMesh.vertices) pts.Add(mf.transform.TransformPoint(v));
        var b = new Bounds(pts[0], Vector3.zero); foreach (var p in pts) b.Encapsulate(p);
        var c = TempCamera("thumbCam"); c.orthographic = true;
        var dir = new Vector3(0.78f, 0.5f, -0.62f).normalized;
        c.transform.position = b.center + dir * 60f; c.transform.LookAt(b.center); c.nearClipPlane = 1f; c.farClipPlane = 200f;
        float aspect = w / (float)h;
        float x0 = 1e9f, x1 = -1e9f, y0 = 1e9f, y1 = -1e9f;
        foreach (var p in pts) { var lp = c.transform.InverseTransformPoint(p); x0 = Mathf.Min(x0, lp.x); x1 = Mathf.Max(x1, lp.x); y0 = Mathf.Min(y0, lp.y); y1 = Mathf.Max(y1, lp.y); }
        // centre on the projected box, a little low like the game's thumbnails
        c.transform.position += c.transform.right * ((x0 + x1) / 2f) + c.transform.up * ((y0 + y1) / 2f + (y1 - y0) * 0.04f);
        c.orthographicSize = Mathf.Max((y1 - y0) / 2f, (x1 - x0) / 2f / aspect) * 1.1f; c.aspect = aspect;
        Grab(c, 16, 16, Color.black);   // the first render after opening a scene comes out unlit
        var black = Grab(c, w, h, new Color(0, 0, 0, 0)); var white = Grab(c, w, h, new Color(1, 1, 1, 0));
        Object.DestroyImmediate(c.gameObject); Object.DestroyImmediate(inst);
        var outT = new Texture2D(w, h, TextureFormat.RGBA32, false);
        var A = black.GetPixels(); var B = white.GetPixels(); var o = new Color[A.Length];
        Color c0 = new Color(0x4a / 255f, 0x62 / 255f, 0x78 / 255f), c1 = new Color(0x24 / 255f, 0x31 / 255f, 0x3c / 255f), c2 = new Color(0x14 / 255f, 0x1b / 255f, 0x21 / 255f);
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++)
            {
                int i = y * w + x;
                float alpha = Mathf.Clamp01(1f - ((B[i].r - A[i].r) + (B[i].g - A[i].g) + (B[i].b - A[i].b)) / 3f);
                Color fg = alpha > 0.004f ? new Color(A[i].r / alpha, A[i].g / alpha, A[i].b / alpha) : Color.black;
                float dx = (x / (float)w - 0.5f) / 0.5f, dy = ((h - 1 - y) / (float)h - 0.46f) / 0.5f;
                float r = Mathf.Sqrt(dx * dx + dy * dy);
                Color bg = r < 0.55f ? Color.Lerp(c0, c1, r / 0.55f) : Color.Lerp(c1, c2, Mathf.Clamp01((r - 0.55f) / 0.45f));
                o[i] = Color.Lerp(bg, fg, alpha); o[i].a = 1f;
            }
        outT.SetPixels(o); outT.Apply();
        return outT;
    }

    // the whole map from straight above (image top = Unity +z = the game's -z, as the browser's minimap)
    static Texture2D RenderMinimap(int w, int h)
    {
        var meta = JsonUtility.FromJson<DGData>(File.ReadAllText(Abs(Root + "/Data/game_data.json"))).grid;
        var c = TempCamera("miniCam"); c.orthographic = true; c.orthographicSize = meta.H / 2f; c.aspect = w / (float)h;
        c.transform.SetPositionAndRotation(new Vector3(meta.X0 + meta.W / 2f, 700f, -(meta.Z0 + meta.H / 2f)), Quaternion.Euler(90f, 0f, 0f));
        c.nearClipPlane = 1f; c.farClipPlane = 1500f;
        Grab(c, 16, 16, Color.black);
        var t = Grab(c, w, h, new Color(0x1d / 255f, 0x4b / 255f, 0x5c / 255f, 1f));
        Object.DestroyImmediate(c.gameObject);
        // the sea: the water surface doesn't draw for a camera this far up, so paint it in from the terrain's heights
        var terr = Terrain.activeTerrain; var water = GameObject.Find("Water");
        if (terr && water)
        {
            float wy = water.transform.position.y; var px = t.GetPixels();
            Color deep = new Color(0x16 / 255f, 0x3b / 255f, 0x4a / 255f), shallow = new Color(0x2c / 255f, 0x6e / 255f, 0x7c / 255f);
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++)
                {
                    var wp = new Vector3(meta.X0 + (x + 0.5f) / w * meta.W, 0f, -(meta.Z0 + meta.H) + (y + 0.5f) / h * meta.H);
                    float d = wy - (terr.SampleHeight(wp) + terr.transform.position.y);
                    if (d <= 0.02f) continue;
                    var wc = Color.Lerp(shallow, deep, Mathf.Clamp01(d / 2.5f));
                    int i = y * w + x; px[i] = Color.Lerp(px[i], wc, Mathf.Clamp01(d / 0.35f) * 0.92f); px[i].a = 1f;
                }
            t.SetPixels(px); t.Apply();
        }
        return t;
    }
}
