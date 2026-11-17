// Dawgs Uprising -> Unity: plays back a battle recorded from the browser game's own simulation (an AI-vs-AI 1v1 on the
// Devtest map). Every unit's position, heading and health 4x a second, every shot and every death, so the real battle
// can be watched here with Unity's lighting and sound while the game logic stays in the browser.
// Controls: Space pause, [ / ] slower / faster, , / . skip 15 s back / forward, R restart, F follow the fighting.
using System;
using System.Collections.Generic;
using UnityEngine;
using Object = UnityEngine.Object;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

public class DawgsReplay : MonoBehaviour
{
    [Serializable] public class Meta
    {
        public float dt; public int frames; public float firstShot;
        public int[] unitId; public string[] unitType; public int[] unitF;
        public float[] shotT; public int[] shotId; public float[] shotX; public float[] shotZ; public string[] shotW;
        public float[] deathT; public int[] deathId; public float[] deathX; public float[] deathZ;
    }
    [Serializable] public class UnitPrefab { public string key; public GameObject prefab; }
    [Serializable] public class Sfx { public string key; public AudioClip clip; public float volume = 1f; public float pitch = 1f; }

    public TextAsset replayBytes, replayMeta;
    public List<UnitPrefab> unitPrefabs = new List<UnitPrefab>();
    public List<Sfx> sounds = new List<Sfx>();
    public Material tracerMaterial;
    public Color[] armyColors = { new Color(0.49f, 0.79f, 0.31f), new Color(0.91f, 0.44f, 0.37f) };
    public float startAt = -1f;     // seconds into the battle; -1 = a little before the first shot
    public float speed = 1f;
    public bool paused;
    public bool showHud = true;

    // ---- decoded data ----
    struct Snap { public int id; public Vector3 p; public float ang, hp; public bool air; }
    float[] frameT; Snap[][] frames; Meta meta;
    readonly Dictionary<int, string> typeOf = new Dictionary<int, string>();
    readonly Dictionary<int, int> armyOf = new Dictionary<int, int>();
    readonly Dictionary<string, GameObject> prefabOf = new Dictionary<string, GameObject>();
    readonly Dictionary<string, Sfx> sfxOf = new Dictionary<string, Sfx>();
    readonly Dictionary<int, Transform> live = new Dictionary<int, Transform>();
    readonly Dictionary<int, DawgsUnitRig> rigs = new Dictionary<int, DawgsUnitRig>();
    readonly Dictionary<int, Vector3> lastPos = new Dictionary<int, Vector3>();
    float t; int nextShot, nextDeath; Terrain terrain;
    readonly List<AudioSource> voices = new List<AudioSource>();
    readonly List<(LineRenderer lr, float until)> tracers = new List<(LineRenderer, float)>();
    readonly List<(Transform tr, float t0, float size, Color col, MeshRenderer mr)> blasts = new List<(Transform, float, float, Color, MeshRenderer)>();
    MaterialPropertyBlock mpb;
    Transform unitsRoot, fxRoot;

    void Awake() { Init(); }
    static void Kill(Object o) { if (Application.isPlaying) Destroy(o); else DestroyImmediate(o); }

    // also callable from an editor script, to preview a moment of the battle without entering Play mode
    public void Init()
    {
        if (frames != null) return;
        mpb = new MaterialPropertyBlock();
        terrain = Terrain.activeTerrain;
        meta = JsonUtility.FromJson<Meta>(replayMeta.text);
        for (int i = 0; i < meta.unitId.Length; i++) { typeOf[meta.unitId[i]] = meta.unitType[i]; armyOf[meta.unitId[i]] = meta.unitF[i]; }
        foreach (var u in unitPrefabs) if (u.prefab) prefabOf[u.key] = u.prefab;
        foreach (var s in sounds) if (s.clip) sfxOf[s.key] = s;
        Decode(replayBytes.bytes);
        unitsRoot = new GameObject("Units").transform; unitsRoot.SetParent(transform, false);
        fxRoot = new GameObject("Effects").transform; fxRoot.SetParent(transform, false);
        for (int i = 0; i < 24; i++)
        {
            var a = new GameObject("voice" + i).AddComponent<AudioSource>(); a.transform.SetParent(fxRoot, false);
            a.playOnAwake = false; a.spatialBlend = 0.85f; a.rolloffMode = AudioRolloffMode.Linear; a.minDistance = 30f; a.maxDistance = 600f; a.dopplerLevel = 0f;
            voices.Add(a);
        }
        Seek(startAt >= 0 ? startAt : Mathf.Max(0f, meta.firstShot - 8f));
    }

    void Decode(byte[] b)
    {
        int o = 4, n = BitConverter.ToInt32(b, o); o += 4;
        frameT = new float[n]; frames = new Snap[n][];
        for (int f = 0; f < n; f++)
        {
            frameT[f] = BitConverter.ToSingle(b, o); o += 4; int c = BitConverter.ToUInt16(b, o); o += 2;
            var arr = new Snap[c];
            for (int i = 0; i < c; i++)
            {
                int id = (int)BitConverter.ToUInt32(b, o);
                float x = BitConverter.ToInt16(b, o + 4) / 10f, z = BitConverter.ToInt16(b, o + 6) / 10f, y = BitConverter.ToInt16(b, o + 8) / 10f;
                float ang = BitConverter.ToUInt16(b, o + 10) / 65535f * Mathf.PI * 2f, hp = b[o + 12] / 255f;
                arr[i] = new Snap { id = id, p = new Vector3(x, y, -z), ang = ang, hp = hp, air = y > -3000f };   // the game's z is Unity's -z
                o += 16;
            }
            frames[f] = arr;
        }
    }

    public void Seek(float time)
    {
        t = Mathf.Clamp(time, frameT[0], frameT[frameT.Length - 1]);
        nextShot = LowerBound(meta.shotT, t); nextDeath = LowerBound(meta.deathT, t);
    }
    static int LowerBound(float[] a, float v) { int lo = 0, hi = a.Length; while (lo < hi) { int m = (lo + hi) >> 1; if (a[m] < v) lo = m + 1; else hi = m; } return lo; }

    void Update()
    {
        HandleKeys();
        Advance(paused ? 0f : Time.deltaTime * speed);
    }

    public float Now => t;
    public Vector3 FightCentre(float window = 20f)
    {
        int i0 = LowerBound(meta.shotT, t), i1 = LowerBound(meta.shotT, t + window); if (i1 <= i0) return Vector3.zero;
        Vector3 c = Vector3.zero; for (int i = i0; i < i1; i++) c += new Vector3(meta.shotX[i], 0, meta.shotZ[i]);
        return c / (i1 - i0);
    }

    public void Advance(float dt)
    {
        if (t + dt >= frameT[frameT.Length - 1]) { t = frameT[frameT.Length - 1]; paused = true; dt = 0f; }
        float t0 = t; t += dt;

        // where everyone is: interpolate between the two recorded frames around t
        int f = Mathf.Clamp(LowerBound(frameT, t) - 1, 0, frameT.Length - 2);
        float k = Mathf.Clamp01((t - frameT[f]) / Mathf.Max(1e-4f, frameT[f + 1] - frameT[f]));
        var next = new Dictionary<int, Snap>(frames[f + 1].Length); foreach (var s in frames[f + 1]) next[s.id] = s;
        var seen = new HashSet<int>();
        foreach (var a in frames[f])
        {
            if (!next.TryGetValue(a.id, out var bb)) bb = a;
            seen.Add(a.id);
            var tr = UnitTransform(a.id); if (tr == null) continue;
            Vector3 p = Vector3.Lerp(a.p, bb.p, k);
            float ang = Mathf.LerpAngle(a.ang * Mathf.Rad2Deg, bb.ang * Mathf.Rad2Deg, k);
            if (!a.air && terrain) p.y = terrain.SampleHeight(p) + terrain.transform.position.y;
            else if (!a.air) p.y = 0f;
            tr.SetPositionAndRotation(p, Quaternion.Euler(0f, ang, 0f));   // the game's heading: model +x toward (cos a, sin a); z mirrored
            if (rigs.TryGetValue(a.id, out var rg) && rg)
            {   // walk / drive at the recorded ground speed
                float span = Mathf.Max(1e-3f, frameT[f + 1] - frameT[f]);
                rg.SetMotion(new Vector2(bb.p.x - a.p.x, bb.p.z - a.p.z).magnitude / span);
            }
            if (!tr.gameObject.activeSelf) tr.gameObject.SetActive(true);
            lastPos[a.id] = p;
        }
        foreach (var kv in live) if (!seen.Contains(kv.Key) && kv.Value.gameObject.activeSelf) kv.Value.gameObject.SetActive(false);

        if (dt > 0f)
        {
            while (nextShot < meta.shotT.Length && meta.shotT[nextShot] <= t) { if (meta.shotT[nextShot] >= t0) Shot(nextShot); nextShot++; }
            while (nextDeath < meta.deathT.Length && meta.deathT[nextDeath] <= t) { if (meta.deathT[nextDeath] >= t0) Death(nextDeath); nextDeath++; }
        }
        UpdateFx();
    }

    Transform UnitTransform(int id)
    {
        if (live.TryGetValue(id, out var tr)) return tr;
        if (!typeOf.TryGetValue(id, out var type)) return null;
        int f = armyOf.TryGetValue(id, out var ff) ? Mathf.Clamp(ff, 0, 1) : 0;
        GameObject go;
        if (prefabOf.TryGetValue($"u_{type}_{f}", out var pf)) go = Instantiate(pf, unitsRoot);
        else { go = GameObject.CreatePrimitive(PrimitiveType.Cube); go.transform.SetParent(unitsRoot, false); go.transform.localScale = new Vector3(2f, 1f, 1.2f); Kill(go.GetComponent<Collider>()); }
        go.name = $"{type} #{id} (army {f})";
        var rig = go.GetComponent<DawgsUnitRig>(); if (rig) rigs[id] = rig;
        live[id] = go.transform; return go.transform;
    }

    // ---- shots: a tracer from the shooter to where the round lands, and the game's own sound for that weapon ----
    void Shot(int i)
    {
        int id = meta.shotId[i]; string w = meta.shotW[i];
        if (!lastPos.TryGetValue(id, out var from)) return;
        typeOf.TryGetValue(id, out var type);
        Vector3 to = new Vector3(meta.shotX[i], 0f, meta.shotZ[i]);
        to.y = terrain ? terrain.SampleHeight(to) + terrain.transform.position.y + 0.6f : 0.6f;
        from.y += type == "rifle" || type == "mg" || type == "at" || type == "sniper" ? 1.0f : 1.6f;
        if (rigs.TryGetValue(id, out var rig) && rig && rig.isActiveAndEnabled) { rig.Fire(to); from = rig.MuzzlePosition; }   // the turret / soldier turns onto it
        bool heavy = w == "shell" || w == "bomb" || w == "rocket" || w == "cas";
        Tracer(from, to, heavy ? 0.22f : 0.08f, heavy ? 0.18f : 0.07f, armyOf.TryGetValue(id, out var f) ? f : 0);
        if (heavy) Blast(to, w == "bomb" ? 5f : w == "shell" ? 2.4f : 1.8f, false);
        Play(SoundFor(type, w), from, w == "bomb" ? 1f : 0.7f);
    }

    string SoundFor(string type, string w)
    {
        if (type == "sniper") return "sniper";
        if (type == "mg") return "mg_burst";
        if (type == "cas" || w == "cas") return "cas_brrt";
        if (w == "bomb") return "collapse";
        if (w == "shell") return "mac_fire";
        if (type == "flak" || type == "qaa" || type == "sam" || type == "heli" || type == "intc" || w == "rocket") return "zep_autocannon";
        return "rifle";
    }

    void Death(int i)
    {
        int id = meta.deathId[i];
        var p = new Vector3(meta.deathX[i], 0f, meta.deathZ[i]);
        p.y = terrain ? terrain.SampleHeight(p) + terrain.transform.position.y : 0f;
        typeOf.TryGetValue(id, out var type);
        bool inf = type == "rifle" || type == "mg" || type == "at" || type == "sniper" || type == "rover";
        if (!inf) { Blast(p, 4f, true); Play("collapse", p, 0.8f); }
        if (live.TryGetValue(id, out var tr)) tr.gameObject.SetActive(false);
    }

    void Play(string key, Vector3 at, float vol)
    {
        if (!sfxOf.TryGetValue(key, out var s)) return;
        AudioSource best = null; foreach (var v in voices) if (!v.isPlaying) { best = v; break; }
        if (best == null) return;   // like the game: a cap on how many shots sound at once
        best.transform.position = at; best.clip = s.clip; best.volume = vol * s.volume; best.pitch = s.pitch * UnityEngine.Random.Range(0.94f, 1.06f) * Mathf.Clamp(speed, 0.5f, 1.4f);
        best.Play();
    }

    void Tracer(Vector3 a, Vector3 b, float width, float life, int army)
    {
        LineRenderer lr = null;
        for (int i = 0; i < tracers.Count; i++) if (tracers[i].until < Time.time) { lr = tracers[i].lr; tracers.RemoveAt(i); break; }
        if (lr == null)
        {
            lr = new GameObject("tracer").AddComponent<LineRenderer>(); lr.transform.SetParent(fxRoot, false);
            lr.positionCount = 2; lr.useWorldSpace = true; lr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; lr.receiveShadows = false;
            lr.sharedMaterial = tracerMaterial;
        }
        var c = Color.Lerp(new Color(1f, 0.85f, 0.45f), armyColors[Mathf.Clamp(army, 0, armyColors.Length - 1)], 0.25f);
        lr.startColor = c; lr.endColor = new Color(c.r, c.g, c.b, 0.15f);
        lr.startWidth = width; lr.endWidth = width * 0.4f;
        lr.SetPosition(0, a); lr.SetPosition(1, b); lr.enabled = true;
        tracers.Add((lr, Time.time + life / Mathf.Max(0.25f, speed)));
    }

    void Blast(Vector3 at, float size, bool big)
    {
        var s = GameObject.CreatePrimitive(PrimitiveType.Sphere); Kill(s.GetComponent<Collider>());
        s.name = "blast"; s.transform.SetParent(fxRoot, false); s.transform.position = at; s.transform.localScale = Vector3.one * size * 0.3f;
        var r = s.GetComponent<MeshRenderer>(); r.sharedMaterial = tracerMaterial; r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        var col = big ? new Color(1f, 0.5f, 0.18f, 1f) : new Color(1f, 0.78f, 0.42f, 1f);
        blasts.Add((s.transform, Time.time, size, col, r));
    }

    void UpdateFx()
    {
        foreach (var tr in tracers) if (tr.until < Time.time && tr.lr.enabled) tr.lr.enabled = false;
        for (int i = blasts.Count - 1; i >= 0; i--)
        {
            var (tr, t0, size, col, mr) = blasts[i]; float a = (Time.time - t0) * Mathf.Max(0.5f, speed) / 0.6f;   // 0..1 over its life
            if (a >= 1f) { Kill(tr.gameObject); blasts.RemoveAt(i); continue; }
            tr.localScale = Vector3.one * size * (0.3f + 0.9f * Mathf.Sqrt(a));
            mpb.SetColor("_BaseColor", col * (1f - a) * 2.2f); mpb.SetFloat("_VertexColor", 0f); mr.SetPropertyBlock(mpb);
        }
    }

    void HandleKeys()
    {
#if ENABLE_INPUT_SYSTEM
        var kb = Keyboard.current; if (kb == null) return;
        if (kb.spaceKey.wasPressedThisFrame) paused = !paused;
        if (kb.rightBracketKey.wasPressedThisFrame) speed = Mathf.Min(8f, speed * 2f);
        if (kb.leftBracketKey.wasPressedThisFrame) speed = Mathf.Max(0.125f, speed * 0.5f);
        if (kb.periodKey.wasPressedThisFrame) Seek(t + 15f);
        if (kb.commaKey.wasPressedThisFrame) Seek(t - 15f);
        if (kb.rKey.wasPressedThisFrame) { Seek(Mathf.Max(0f, meta.firstShot - 8f)); paused = false; }
        if (kb.fKey.wasPressedThisFrame) FollowFight();
        if (kb.hKey.wasPressedThisFrame) showHud = !showHud;
#else
        if (Input.GetKeyDown(KeyCode.Space)) paused = !paused;
        if (Input.GetKeyDown(KeyCode.RightBracket)) speed = Mathf.Min(8f, speed * 2f);
        if (Input.GetKeyDown(KeyCode.LeftBracket)) speed = Mathf.Max(0.125f, speed * 0.5f);
        if (Input.GetKeyDown(KeyCode.Period)) Seek(t + 15f);
        if (Input.GetKeyDown(KeyCode.Comma)) Seek(t - 15f);
        if (Input.GetKeyDown(KeyCode.R)) { Seek(Mathf.Max(0f, meta.firstShot - 8f)); paused = false; }
        if (Input.GetKeyDown(KeyCode.F)) FollowFight();
        if (Input.GetKeyDown(KeyCode.H)) showHud = !showHud;
#endif
    }

    // point the camera at where the most shots are being fired in the next 20 s
    void FollowFight()
    {
        var c = FightCentre(); if (c == Vector3.zero) return;
        var cam = Camera.main ? Camera.main.GetComponent<DawgsRtsCamera>() : null;
        if (cam) { cam.target = c; cam.distance = Mathf.Min(cam.distance, 90f); }
    }

    void OnGUI()
    {
        if (!showHud) return;
        int a0 = 0, a1 = 0; foreach (var kv in live) if (kv.Value.gameObject.activeSelf) { if (armyOf.TryGetValue(kv.Key, out var f) && f == 1) a1++; else a0++; }
        var r = new Rect(12, 12, 460, 64);
        GUI.color = new Color(0, 0, 0, 0.55f); GUI.DrawTexture(r, Texture2D.whiteTexture); GUI.color = Color.white;
        int m = (int)(t / 60f), s = (int)(t % 60f);
        GUI.Label(new Rect(22, 18, 440, 22), $"Battle replay  {m}:{s:00}   x{speed:0.##}{(paused ? "  (paused)" : "")}   green {a0}  vs  red {a1}");
        GUI.Label(new Rect(22, 40, 440, 22), "Space pause · [ ] speed · , . skip 15 s · F follow the fighting · R restart · H hide");
    }
}
