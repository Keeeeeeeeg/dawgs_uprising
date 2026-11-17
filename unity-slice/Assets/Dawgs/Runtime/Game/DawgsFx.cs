// Dawgs Uprising -> Unity: shot effects for the playable skirmish. Bullet tracers, rockets and shells that fly at the
// weapon's own speed, blasts, the game's weapon sounds (24 voices, like the browser's cap) and the little rings that
// mark where an order was given.
using System;
using System.Collections.Generic;
using UnityEngine;

public class DawgsFx
{
    [Serializable] public class Sfx { public string key; public AudioClip clip; public float volume = 1f; public float pitch = 1f; }

    readonly Transform root;
    readonly Material additive, ringMat;
    readonly Mesh ringMesh;
    readonly Dictionary<string, Sfx> sfx = new Dictionary<string, Sfx>();
    readonly List<AudioSource> voices = new List<AudioSource>();
    readonly AudioSource alertVoice;   // alerts play flat (not in the world), on their own volume
    readonly Dictionary<string, float> alertT = new Dictionary<string, float>();
    readonly List<(LineRenderer lr, float until)> tracers = new List<(LineRenderer, float)>();
    readonly List<Shell> shells = new List<Shell>();
    readonly List<(Transform tr, float t0, float size, Color col, MeshRenderer mr)> blasts = new List<(Transform, float, float, Color, MeshRenderer)>();
    readonly List<(Transform tr, float t0, float life, float size, Color col, MeshRenderer mr)> marks = new List<(Transform, float, float, float, Color, MeshRenderer)>();
    readonly MaterialPropertyBlock mpb = new MaterialPropertyBlock();
    public Color[] armyColors = { new Color(0.49f, 0.79f, 0.31f), new Color(0.91f, 0.44f, 0.37f) };

    class Shell { public LineRenderer lr; public Vector3 a, b; public float t0, t1; public float arc; public bool smoke; }

    public DawgsFx(Transform parent, Material additive, Material ringMat, Mesh ringMesh, IEnumerable<Sfx> sounds)
    {
        root = new GameObject("Effects").transform; root.SetParent(parent, false);
        this.additive = additive; this.ringMat = ringMat; this.ringMesh = ringMesh;
        foreach (var s in sounds) if (s != null && s.clip) sfx[s.key] = s;
        for (int i = 0; i < 24; i++)
        {
            var a = new GameObject("voice" + i).AddComponent<AudioSource>(); a.transform.SetParent(root, false);
            a.playOnAwake = false; a.spatialBlend = 0.85f; a.rolloffMode = AudioRolloffMode.Linear; a.minDistance = 30f; a.maxDistance = 600f; a.dopplerLevel = 0f;
            voices.Add(a);
        }
        alertVoice = new GameObject("alerts").AddComponent<AudioSource>(); alertVoice.transform.SetParent(root, false);
        alertVoice.playOnAwake = false; alertVoice.spatialBlend = 0f;
    }

    /// a siren, alarm or ping: heard wherever the camera is, at the Alerts volume; the same alert at most every `gap` s
    public void Alert(string key, float vol, float gap = 0f)
    {
        if (!sfx.TryGetValue(key, out var s)) return;
        if (gap > 0f && alertT.TryGetValue(key, out var t) && Time.unscaledTime - t < gap) return;
        alertT[key] = Time.unscaledTime;
        alertVoice.PlayOneShot(s.clip, Mathf.Clamp01(vol * s.volume * DawgsAudio.AlertGain));
    }

    LineRenderer NewLine(string name)
    {
        var lr = new GameObject(name).AddComponent<LineRenderer>(); lr.transform.SetParent(root, false);
        lr.positionCount = 2; lr.useWorldSpace = true; lr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; lr.receiveShadows = false;
        lr.sharedMaterial = additive; return lr;
    }

    public void Tracer(Vector3 a, Vector3 b, float width, float life, int army)
    {
        LineRenderer lr = null;
        for (int i = 0; i < tracers.Count; i++) if (tracers[i].until < Time.time) { lr = tracers[i].lr; tracers.RemoveAt(i); break; }
        if (lr == null) lr = NewLine("tracer");
        var c = Color.Lerp(new Color(1f, 0.85f, 0.45f), armyColors[Mathf.Clamp(army, 0, armyColors.Length - 1)], 0.25f);
        lr.startColor = c; lr.endColor = new Color(c.r, c.g, c.b, 0.15f);
        lr.startWidth = width; lr.endWidth = width * 0.4f;
        lr.SetPosition(0, a); lr.SetPosition(1, b); lr.enabled = true;
        tracers.Add((lr, Time.time + life));
    }

    /// a rocket or shell in flight from a to b, landing after `flight` seconds (game time)
    public void Projectile(Vector3 a, Vector3 b, float flight, bool rocket)
    {
        Shell s = null;
        foreach (var x in shells) if (x.t1 < 0f) { s = x; break; }
        if (s == null) { s = new Shell { lr = NewLine(rocket ? "rocket" : "shell") }; shells.Add(s); }
        s.a = a; s.b = b; s.t0 = Time.time; s.t1 = Time.time + Mathf.Max(0.05f, flight); s.smoke = rocket;
        s.arc = rocket ? 0.3f : Mathf.Min(8f, (b - a).magnitude * 0.08f);
        s.lr.startWidth = rocket ? 0.16f : 0.12f; s.lr.endWidth = 0.02f;
        s.lr.startColor = rocket ? new Color(1f, 0.75f, 0.4f) : new Color(1f, 0.9f, 0.6f);
        s.lr.endColor = rocket ? new Color(0.6f, 0.6f, 0.6f, 0.2f) : new Color(1f, 0.7f, 0.3f, 0.1f);
        s.lr.enabled = true;
    }

    public void Blast(Vector3 at, float size, bool big)
    {
        var s = GameObject.CreatePrimitive(PrimitiveType.Sphere); UnityEngine.Object.Destroy(s.GetComponent<Collider>());
        s.name = "blast"; s.transform.SetParent(root, false); s.transform.position = at; s.transform.localScale = Vector3.one * size * 0.3f;
        var r = s.GetComponent<MeshRenderer>(); r.sharedMaterial = additive; r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        var col = big ? new Color(1f, 0.42f, 0.12f, 1f) : new Color(1f, 0.66f, 0.3f, 1f);
        blasts.Add((s.transform, Time.time, size, col, r));
    }

    /// a ring that grows and fades where an order was given (green move, orange fight, red attack)
    public void Marker(Vector3 at, Color col, float size = 2.2f, float life = 0.7f)
    {
        var g = new GameObject("marker"); g.transform.SetParent(root, false); g.transform.position = at + Vector3.up * 0.25f;
        g.AddComponent<MeshFilter>().sharedMesh = ringMesh;
        var mr = g.AddComponent<MeshRenderer>(); mr.sharedMaterial = ringMat; mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        marks.Add((g.transform, Time.unscaledTime, life, size, col, mr));
    }

    public void Play(string key, Vector3 at, float vol)
    {
        if (!sfx.TryGetValue(key, out var s)) return;
        AudioSource best = null; foreach (var v in voices) if (!v.isPlaying) { best = v; break; }
        if (best == null) return;
        best.transform.position = at; best.clip = s.clip; best.volume = vol * s.volume * DawgsAudio.UnitGain; best.pitch = s.pitch * UnityEngine.Random.Range(0.94f, 1.06f) * Mathf.Clamp(Time.timeScale, 0.5f, 1.4f);
        best.Play();
    }

    public static string SoundFor(string type, string w)
    {
        if (type == "sniper") return "sniper";
        if (type == "mg") return "mg_burst";
        if (w == "cas") return "cas_brrt";
        if (w == "bomb") return "collapse";
        if (w == "shell" || w == "apshell" || w == "artillery") return "mac_fire";
        if (w == "autocannon" || w == "flak" || w == "aa" || w == "rocket" || w == "hrocket" || w == "sam") return "zep_autocannon";
        return "rifle";
    }

    public void Update()
    {
        foreach (var tr in tracers) if (tr.until < Time.time && tr.lr.enabled) tr.lr.enabled = false;
        foreach (var s in shells)
        {
            if (s.t1 < 0f) continue;
            float k = (Time.time - s.t0) / (s.t1 - s.t0);
            if (k >= 1f) { s.t1 = -1f; s.lr.enabled = false; continue; }
            Vector3 p = Vector3.Lerp(s.a, s.b, k) + Vector3.up * (s.arc * 4f * k * (1f - k));
            Vector3 q = Vector3.Lerp(s.a, s.b, Mathf.Max(0f, k - (s.smoke ? 0.12f : 0.05f))) + Vector3.up * (s.arc * 4f * Mathf.Max(0f, k - 0.05f) * (1f - Mathf.Max(0f, k - 0.05f)));
            s.lr.SetPosition(0, p); s.lr.SetPosition(1, q);
        }
        for (int i = blasts.Count - 1; i >= 0; i--)
        {
            var (tr, t0, size, col, mr) = blasts[i]; float a = (Time.time - t0) / 0.6f;
            if (a >= 1f) { UnityEngine.Object.Destroy(tr.gameObject); blasts.RemoveAt(i); continue; }
            tr.localScale = Vector3.one * size * (0.3f + 0.75f * Mathf.Sqrt(a));
            mpb.Clear(); mpb.SetColor("_BaseColor", col * (1f - a) * (1f - a) * 0.9f); mpb.SetFloat("_VertexColor", 0f); mpb.SetFloat("_Intensity", 1f); mr.SetPropertyBlock(mpb);
        }
        for (int i = marks.Count - 1; i >= 0; i--)
        {
            var (tr, t0, life, size, col, mr) = marks[i]; float a = (Time.unscaledTime - t0) / life;
            if (a >= 1f) { UnityEngine.Object.Destroy(tr.gameObject); marks.RemoveAt(i); continue; }
            tr.localScale = Vector3.one * size * (0.5f + 0.7f * a);
            mpb.Clear(); var c = col; c.a = 1f - a; mpb.SetColor("_BaseColor", c); mr.SetPropertyBlock(mpb);
        }
    }

    /// a flat ring (inner radius 0.82, outer 1), vertex alpha 1; scaled per unit
    public static Mesh MakeRing(int seg = 48, float inner = 0.82f)
    {
        var m = new Mesh { name = "DawgsRing" };
        var v = new Vector3[seg * 2]; var c = new Color[seg * 2]; var t = new int[seg * 6];
        for (int i = 0; i < seg; i++)
        {
            float a = i * Mathf.PI * 2f / seg; var d = new Vector3(Mathf.Cos(a), 0f, Mathf.Sin(a));
            v[i * 2] = d * inner; v[i * 2 + 1] = d; c[i * 2] = Color.white; c[i * 2 + 1] = Color.white;
            int n = (i + 1) % seg, k = i * 6;
            t[k] = i * 2; t[k + 1] = n * 2; t[k + 2] = i * 2 + 1; t[k + 3] = i * 2 + 1; t[k + 4] = n * 2; t[k + 5] = n * 2 + 1;
        }
        m.vertices = v; m.colors = c; m.triangles = t; m.RecalculateBounds();
        return m;
    }
}
