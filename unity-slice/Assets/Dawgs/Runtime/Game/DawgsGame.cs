// Dawgs Uprising -> Unity: a playable 1v1 skirmish on Test Town, on the browser game's own rules.
// Free Militia (you) start at Test HQ, the Crimson Legion at the far HQ; the five zones between are neutral.
// Hold ground units in a zone to take it (BALANCE.capture), zones pay funds and manpower (BALANCE.economy, zone types),
// recruit at your bases, and the Legion recruits from its own funds and sends waves at your zones (BALANCE.start.ai*).
// Take every zone, or wipe the other army out, to win. DawgsHud draws the browser game's HUD over it, DawgsCommand takes
// the mouse and keyboard.
using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using Random = UnityEngine.Random;

public class DawgsGame : MonoBehaviour
{
    [Serializable] public class UnitPrefab { public string key; public GameObject prefab; }
    [Serializable] public class Thumb { public string key; public Texture2D tex; }

    [Header("Data (set by Dawgs > Build Playable Skirmish)")]
    public TextAsset dataJson;
    public List<UnitPrefab> unitPrefabs = new List<UnitPrefab>();
    public List<DawgsFx.Sfx> sounds = new List<DawgsFx.Sfx>();
    public List<Thumb> thumbs = new List<Thumb>();
    public Material tracerMaterial, ringMaterial;
    public Texture2D minimap;

    [Header("Rules")]
    public int player = 0;
    public float incomeMul = 2.5f;      // no economy buildings in this slice yet: zones pay more to make up for markets and factories
    public float manpowerMul = 3f;
    public bool enemyAI = true;
    public float aiIncomeMul = 0.75f;   // the Legion's share of zone income (the browser's AI has its own over-extension rules)
    public int aiUnitCap = 40;

    // ---- runtime ----
    public DawgsRules R { get; private set; }
    public DawgsGrid Grid { get; private set; }
    public DawgsFx Fx { get; private set; }
    public readonly List<DawgsUnit> units = new List<DawgsUnit>();
    public readonly List<DawgsUnit> selection = new List<DawgsUnit>();
    public readonly List<Zone> zones = new List<Zone>();
    public readonly List<Army> armies = new List<Army>();
    public readonly List<Message> messages = new List<Message>();
    public float time;
    public bool over; public int winner = -1;
    public event Action<string, bool> OnToast;
    public Mesh RingMesh { get; private set; }

    public static readonly string[][] RecruitGroups =
    {
        new[] { "Barracks", "rifle", "mg", "at", "sniper", "flagb" },
        new[] { "Motor Pool", "tech", "ltank", "mtank", "htank", "qaa", "flak", "sam" },
        new[] { "Artillery Foundry", "spg", "how" },
    };
    static readonly Dictionary<string, float> AiComp = new Dictionary<string, float>
    { { "rifle", .28f }, { "mg", .16f }, { "at", .10f }, { "sniper", .054f }, { "tech", .04f }, { "ltank", .04f }, { "mtank", .08f }, { "htank", .14f }, { "spg", .04f } };

    public class Army
    {
        public int id; public string name, shortName; public Color color; public string css;
        public float money, manpower, incomeSec, mpMin; public int kills, losses; public bool alive = true;
    }
    public class Zone
    {
        public DGZone d; public int owner = -1; public int capF = -1; public float capP; public bool contested;
        public Vector3 pos; public float r; public string name;
        public readonly List<QItem> queue = new List<QItem>();
        public int[] count = new int[2];
        public LineRenderer ringLr;
    }
    public class QItem { public string type; public float left, total; }
    public class Message { public float t; public string text; public int army = -1; public bool alert; }

    readonly Dictionary<string, GameObject> prefabOf = new Dictionary<string, GameObject>();
    readonly Dictionary<string, Texture2D> thumbOf = new Dictionary<string, Texture2D>();
    readonly List<Impact> impacts = new List<Impact>();
    struct Impact { public float t; public DawgsUnit shooter; public DawgsUnit target; public Vector3 at; public string weapon; public float dmg, splash, hardK; public int army; public DGUnitDef shooterDef; }
    Terrain terrain; Transform unitsRoot;
    AudioSource music; float musicBase = 0.45f;
    readonly Dictionary<Zone, float> attackWarnT = new Dictionary<Zone, float>();
    int nextId = 1; float econT, zoneT, aiT, aiWaveT, winT;

    // ================================================================ setup
    void Awake()
    {
        R = new DawgsRules(dataJson.text);
        Grid = new DawgsGrid(R.D.grid, R.D.pass);
        terrain = Terrain.activeTerrain;
        foreach (var u in unitPrefabs) if (u.prefab) prefabOf[u.key] = u.prefab;
        foreach (var t in thumbs) if (t.tex) thumbOf[t.key] = t.tex;
        RingMesh = DawgsFx.MakeRing();
        Fx = new DawgsFx(transform, tracerMaterial, ringMaterial, RingMesh, sounds);
        unitsRoot = new GameObject("Units").transform; unitsRoot.SetParent(transform, false);
        var mg = GameObject.Find("Music"); music = mg ? mg.GetComponent<AudioSource>() : null;
        if (music) musicBase = music.volume;
        ApplyAudio(); DawgsAudio.Changed += ApplyAudio;
        NewGame();
    }

    void OnDestroy() { DawgsAudio.Changed -= ApplyAudio; }
    void ApplyAudio() { if (music) music.volume = Mathf.Clamp01(musicBase * DawgsAudio.MusicGain); }
    public string NowPlaying => music && music.clip ? music.clip.name : "";

    public Texture2D ThumbOf(string type) => thumbOf.TryGetValue(type, out var t) ? t : null;
    public float GroundY(Vector3 p) => terrain ? terrain.SampleHeight(p) + terrain.transform.position.y : 0f;

    public void NewGame()
    {
        foreach (var u in units) if (u) Destroy(u.gameObject);
        units.Clear(); selection.Clear(); impacts.Clear(); messages.Clear(); armies.Clear(); forms.Clear();
        foreach (var z in zones) if (z.ringLr) Destroy(z.ringLr.gameObject);
        zones.Clear();
        time = 0f; over = false; winner = -1; Time.timeScale = 1f;
        var S = R.D.start;
        for (int i = 0; i < 2; i++)
        {
            var f = R.D.factions[i];
            ColorUtility.TryParseHtmlString(f.css, out var col);
            armies.Add(new Army { id = i, name = f.name, shortName = f.@short, color = col, css = f.css, money = i == player ? S.money.player : S.money.ai, manpower = S.manpower });
        }
        Fx.armyColors = armies.Select(a => a.color).ToArray();
        // zones: the two HQs belong to their armies, everything between is up for grabs
        var hqs = R.D.zones.Where(z => z.type == "hq").OrderBy(z => z.x).ToList();
        foreach (var d in R.D.zones)
        {
            var z = new Zone { d = d, pos = new Vector3(d.x, 0f, -d.z), r = d.r, name = d.name };
            z.pos.y = GroundY(z.pos);
            if (hqs.Count >= 2 && d == hqs[0]) z.owner = player;
            else if (hqs.Count >= 2 && d == hqs[hqs.Count - 1]) { z.owner = 1 - player; if (z.name.StartsWith("Idle")) z.name = "Legion HQ"; }
            zones.Add(z);
            MakeZoneRing(z);
        }
        // the opening squads (BALANCE.start.squad, less the construction rover: no base building here yet)
        foreach (var z in zones.Where(z => z.owner >= 0))
        {
            var squad = S.squad.Where(t => t != "rover").ToList();
            var dirIn = (Vector3.zero - z.pos); dirIn.y = 0f; dirIn.Normalize();
            for (int i = 0; i < squad.Count; i++)
            {
                var p = z.pos + dirIn * (z.r + 6f) + Vector3.Cross(Vector3.up, dirIn) * ((i - (squad.Count - 1) * 0.5f) * 2.2f);
                Spawn(squad[i], z.owner, Grid.Snap(p), Mathf.Atan2(-dirIn.z, dirIn.x));
            }
            Msg($"{armies[z.owner].name} raises the flag over {z.name}.", z.owner);
        }
        Msg("Every army is your enemy. Take every zone.", -1, true);
        aiT = 3f; aiWaveT = S.aiWave + 10f;
        var cam = Camera.main ? Camera.main.GetComponent<DawgsRtsCamera>() : null;
        if (cam) { var home = Home(player); if (home != null) { cam.target = home.pos + new Vector3(35f, 0f, -10f); cam.distance = 120f; cam.pitch = 0.95f; cam.yaw = 0f; cam.Apply(); } }
    }

    void MakeZoneRing(Zone z)
    {
        var lr = new GameObject("zone " + z.name).AddComponent<LineRenderer>(); lr.transform.SetParent(transform, false);
        int n = 64; lr.positionCount = n; lr.loop = true; lr.useWorldSpace = true; lr.sharedMaterial = ringMaterial;
        lr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; lr.receiveShadows = false; lr.widthMultiplier = 0.45f;
        for (int i = 0; i < n; i++)
        {
            float a = i * Mathf.PI * 2f / n; var p = z.pos + new Vector3(Mathf.Cos(a), 0f, Mathf.Sin(a)) * z.r;
            p.y = GroundY(p) + 0.35f; lr.SetPosition(i, p);
        }
        z.ringLr = lr; TintZone(z);
    }
    void TintZone(Zone z)
    {
        var c = z.owner >= 0 ? armies[z.owner].color : new Color(0.85f, 0.82f, 0.7f);
        c.a = 0.55f; z.ringLr.startColor = c; z.ringLr.endColor = c;
    }

    public Zone Home(int army) => zones.FirstOrDefault(z => z.owner == army && z.d.type == "hq") ?? zones.FirstOrDefault(z => z.owner == army);

    public DawgsUnit Spawn(string type, int army, Vector3 pos, float heading)
    {
        if (!R.unit.TryGetValue(type, out var def)) return null;
        GameObject go;
        if (prefabOf.TryGetValue($"u_{type}_{army}", out var pf)) go = Instantiate(pf, unitsRoot);
        else { go = GameObject.CreatePrimitive(PrimitiveType.Cube); go.transform.SetParent(unitsRoot, false); Destroy(go.GetComponent<Collider>()); }
        int id = nextId++;
        go.name = $"{def.name} #{id} ({armies[army].shortName})";
        var u = go.AddComponent<DawgsUnit>();
        go.transform.position = pos;
        u.Init(this, id, army, def, heading);
        var ring = new GameObject("ring"); ring.transform.SetParent(go.transform, false);
        ring.transform.localPosition = Vector3.up * 0.2f; ring.transform.localScale = Vector3.one * (u.radius * 1.6f + 0.35f);
        ring.AddComponent<MeshFilter>().sharedMesh = RingMesh;
        var mr = ring.AddComponent<MeshRenderer>(); mr.sharedMaterial = ringMaterial; mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        var mpb = new MaterialPropertyBlock(); var rc = armies[army].color; rc.a = 0.9f; mpb.SetColor("_BaseColor", rc); mr.SetPropertyBlock(mpb);
        ring.SetActive(false); u.ring = ring;
        units.Add(u);
        return u;
    }

    public void Msg(string text, int army = -1, bool alert = false)
    {
        messages.Add(new Message { t = time, text = text, army = army, alert = alert });
        if (messages.Count > 60) messages.RemoveAt(0);
    }
    public void Toast(string text, bool bad = false) => OnToast?.Invoke(text, bad);

    // ================================================================ orders (the browser's A.order and its SIM order functions)
    static float Flat(Vector3 a, Vector3 b) { float dx = a.x - b.x, dz = a.z - b.z; return Mathf.Sqrt(dx * dx + dz * dz); }
    static Vector3 Centre(List<DawgsUnit> us) { Vector3 c = Vector3.zero; foreach (var u in us) c += u.Pos; return c / Mathf.Max(1, us.Count); }
    static readonly Color MoveCol = new Color(0.965f, 0.976f, 0.784f), FightCol = new Color(1f, 0.824f, 0.353f), AttackCol = new Color(1f, 0.29f, 0.196f), GuardCol = new Color(0.486f, 0.788f, 1f);
    List<DawgsUnit> Mine(List<DawgsUnit> us) => us.Where(u => u && u.alive && u.army == player && !u.def.isStatic).ToList();

    /// the player's move / fight-move to a point
    public void OrderMove(List<DawgsUnit> us, Vector3 point, bool fight)
    {
        IssueMove(Mine(us), point, fight);
        Fx.Marker(point, fight ? FightCol : MoveCol);
    }

    /// move a group to a point (the player's units or the AI's): any standing order ends, big groups going far march in formation
    public void IssueMove(List<DawgsUnit> us, Vector3 point, bool fight)
    {
        us = us.Where(u => u && u.alive && !u.def.isStatic).ToList();
        if (us.Count == 0) return;
        foreach (var u in us) u.Release();
        MoveGroup(us, point, fight);
    }

    /// one unit to a spot without ending what it is doing (an escort keeping station)
    public void MoveOne(DawgsUnit u, Vector3 point, bool fight) { MoveGroup(new List<DawgsUnit> { u }, point, fight); }

    /// the player drew a line with the right button: one unit to each point along it
    public void OrderSlots(List<DawgsUnit> us, List<Vector3> slots, bool fight)
    {
        var mine = Mine(us); if (mine.Count == 0 || slots.Count == 0) return;
        foreach (var u in mine) u.Release();
        SlotGroup(mine, slots, fight);
        Fx.Marker(slots[0], fight ? FightCol : MoveCol, 1.5f); Fx.Marker(slots[slots.Count - 1], fight ? FightCol : MoveCol, 1.5f);
    }

    public void OrderAttack(List<DawgsUnit> us, DawgsUnit t)
    {
        foreach (var u in Mine(us)) if (u.armed && R.Eff(u.def, t.def) > 0f) { u.Release(); u.OrderAttack(t); }
        Fx.Marker(t.Pos, AttackCol, t.radius * 2f + 1f);
    }

    /// attack everything in a circle, nearest first; returns how many targets are in it
    public int OrderArea(List<DawgsUnit> us, Vector3 c, float r)
    {
        r = Mathf.Clamp(r, 2f, 60f);
        foreach (var u in Mine(us))
        {
            if (!u.Military) continue;
            u.Release(); u.hasArea = true; u.areaC = c; u.areaR = r;
            var t = AreaPick(u);
            if (t != null) u.OrderAttack(t); else { u.hasArea = false; MoveGroup(new List<DawgsUnit> { u }, c, true); }
        }
        return units.Count(o => o.alive && o.army != player && Flat(o.Pos, c) <= r + o.rad);
    }

    /// the nearest enemy inside a unit's attack area that it can hurt
    public DawgsUnit AreaPick(DawgsUnit u)
    {
        DawgsUnit best = null; float bd = float.MaxValue;
        foreach (var o in units)
        {
            if (!o.alive || o.army == u.army) continue;
            if (Flat(o.Pos, u.areaC) > u.areaR + o.rad || R.Eff(u.def, o.def) <= 0f) continue;
            float d = Flat(o.Pos, u.Pos); if (d < bd) { bd = d; best = o; }
        }
        return best;
    }

    public void OrderHalt(List<DawgsUnit> us) { foreach (var u in Mine(us)) u.OrderHalt(); }

    /// guard: follow a friendly unit and protect it
    public bool OrderGuard(List<DawgsUnit> us, DawgsUnit t)
    {
        if (t == null || !t.alive || t.army != player) return false;
        var gs = Mine(us).Where(u => u != t && !u.def.builder).ToList(); if (gs.Count == 0) return false;
        t.guards.RemoveAll(g => g == null || !g.alive || g.guardOf != t || gs.Contains(g));
        foreach (var u in gs) u.OrderGuard(t);
        Fx.Marker(t.Pos, GuardCol, t.rad * 0.8f + 1f);
        return true;
    }
    public void SetStance(List<DawgsUnit> us, DStance s) { foreach (var u in us) if (u && u.alive && u.army == player) u.stance = s; }

    // ---- orderMove: a shared route to a block of slots, or a formation march ----
    void MoveGroup(List<DawgsUnit> us, Vector3 to, bool fight)
    {
        var O = R.D.orders;
        foreach (var u in us) { u.form = null; u.capV = 0f; }
        Vector3 c = Centre(us);
        if (us.Count >= O.formMin && Flat(c, to) > O.formDist) { MarchOrder(us, to, fight); return; }
        var shared = Grid.FindPath(c, to);
        bool veh = us.Any(u => u.def.isVeh);
        var slots = FormationSlots(us.Count, to, veh ? O.spacingVeh : O.spacingInf);
        // pair units and slots by sorting both across the direction of travel
        Vector3 dir = to - c; dir.y = 0f; float L = dir.magnitude; if (L < 1e-3f) { dir = Vector3.right; L = 1f; }
        Vector3 perp = new Vector3(-dir.z, 0f, dir.x) / L;
        var uo = us.OrderBy(u => Vector3.Dot(u.Pos, perp)).ToList();
        var so = slots.OrderBy(q => Vector3.Dot(q, perp)).ToList();
        for (int i = 0; i < uo.Count; i++)
        {
            var u = uo[i]; var q = so[i]; List<Vector3> path;
            // share the group's route only when this unit can walk straight onto it and straight off it to its slot
            if (shared == null || shared.Count == 0 || Flat(u.Pos, c) > O.sharePath || !Grid.LOS(u.Pos, shared[0]) ||
                (shared.Count > 1 && !Grid.LOS(shared[shared.Count - 2], q))) path = Grid.FindPath(u.Pos, q);
            else { path = shared.Take(shared.Count - 1).ToList(); path.Add(q); }
            u.OrderPath(path ?? new List<Vector3> { q }, q, fight);
        }
    }

    List<Vector3> FormationSlots(int n, Vector3 at, float spacing)
    {
        var res = new List<Vector3>(n); int cols = Mathf.CeilToInt(Mathf.Sqrt(n)); int rows = Mathf.CeilToInt(n / (float)cols);
        for (int k = 0; k < n; k++)
        {
            int r = k / cols, c = k % cols;
            res.Add(Grid.Snap(new Vector3(at.x + (c - (cols - 1) / 2f) * spacing, at.y, at.z + (r - (rows - 1) / 2f) * spacing)));
        }
        return res;
    }

    // ---- orderSlots: each unit to its own point (a line the player drew) ----
    void SlotGroup(List<DawgsUnit> us, List<Vector3> slots, bool fight)
    {
        var O = R.D.orders; int n = us.Count;
        Vector3 a = slots[0], b = slots[slots.Count - 1], d = b - a; d.y = 0f; d = d.sqrMagnitude > 1e-6f ? d.normalized : Vector3.right;
        var uo = us.OrderBy(u => Vector3.Dot(u.Pos - a, d)).ToList();
        Vector3 c = Centre(us), sc = Vector3.zero; foreach (var q in slots) sc += q; sc /= slots.Count;
        var shared = Grid.FindPath(c, sc);
        for (int i = 0; i < n; i++)
        {
            var u = uo[i]; Vector3 q = Grid.Snap(slots[Mathf.Min(i, slots.Count - 1)]); List<Vector3> path;
            if (shared != null && shared.Count > 0 && Flat(u.Pos, c) < O.sharePath)
            {
                path = shared.Take(shared.Count - 1).ToList();
                Vector3 last = path.Count > 0 ? path[path.Count - 1] : u.Pos;
                if (Grid.LOS(last, q)) path.Add(q); else path = Grid.FindPath(u.Pos, q) ?? new List<Vector3> { q };
            }
            else path = Grid.FindPath(u.Pos, q) ?? new List<Vector3> { q };
            u.OrderPath(path, q, fight);
        }
    }

    // ---- formation march: form up, then move off together at the slowest unit's pace (armour in columns at the
    //      front, infantry in ranks behind, artillery and anti-air at the rear) ----
    public class Formation
    {
        public List<DawgsUnit> units = new List<DawgsUnit>();
        public Dictionary<DawgsUnit, Vector2> slots = new Dictionary<DawgsUnit, Vector2>();   // x = forward of the middle, y = to the side
        public Vector3 to, at, h; public bool fight, marching; public float t, cap; public List<Vector3> route; public int seg;
    }
    public readonly List<Formation> forms = new List<Formation>();

    List<(DawgsUnit u, float f, float r)> FormLayout(List<DawgsUnit> us)
    {
        var O = R.D.orders; var by = new[] { new List<DawgsUnit>(), new List<DawgsUnit>(), new List<DawgsUnit>() };
        foreach (var u in us) by[DawgsRules.FormRole(u.def)].Add(u);
        foreach (var l in by) l.Sort((p, q) => q.def.hp != p.def.hp ? q.def.hp.CompareTo(p.def.hp) : p.id.CompareTo(q.id));   // toughest at the front of each block
        var res = new List<(DawgsUnit, float, float)>(); float f = 0f;
        void Block(List<DawgsUnit> list, int cols, float cg, float rg)
        {
            if (list.Count == 0) return; int rows = Mathf.CeilToInt(list.Count / (float)cols);
            for (int i = 0; i < list.Count; i++)
            {
                int row = i / cols, col = i % cols, inRow = Mathf.Min(cols, list.Count - row * cols);
                res.Add((list[i], f - row * rg, (col - (inRow - 1) / 2f) * cg));
            }
            f -= rows * rg + rg * 0.4f;
        }
        Block(by[0], Mathf.Min(O.armourFiles, Mathf.Max(1, by[0].Count)), O.fileGap, O.rowGap);
        Block(by[1], Mathf.Max(4, Mathf.CeilToInt(Mathf.Sqrt(by[1].Count * 2.2f))), O.rankGap, O.rankGap);
        Block(by[2], Mathf.Max(2, Mathf.CeilToInt(Mathf.Sqrt(by[2].Count * 1.5f))), O.rearGap, O.rearGap);
        float mid = f / 2f;
        return res.Select(x => (x.Item1, x.Item2 - mid, x.Item3)).ToList();
    }

    /// a unit's place in its formation right now
    public Vector3 FormPlace(Formation F, DawgsUnit u)
    {
        Vector2 s0 = F.slots[u]; Vector3 side = new Vector3(-F.h.z, 0f, F.h.x);
        Vector3 p = F.at + F.h * s0.x + side * s0.y;
        if (Grid.Passable(p)) return p;
        foreach (float k in new[] { 0.6f, 0.3f, 0f }) { Vector3 q = F.at + F.h * (s0.x * k) + side * (s0.y * k); if (Grid.Passable(q)) return q; }
        return Grid.Snap(p);
    }

    void MarchOrder(List<DawgsUnit> us, Vector3 to, bool fight)
    {
        Vector3 c = Centre(us), h = to - c; h.y = 0f; h = h.sqrMagnitude > 1e-6f ? h.normalized : Vector3.right;
        Vector3 a0 = Grid.Snap(c + h * 2f);
        var route = Grid.FindPath(a0, to) ?? new List<Vector3> { to };
        route.Insert(0, a0);
        var F = new Formation { to = to, at = a0, h = h, fight = fight, t = time, cap = us.Min(u => u.def.speed), route = route };
        foreach (var (u, f, r) in FormLayout(us)) { F.units.Add(u); F.slots[u] = new Vector2(f, r); }
        foreach (var u in F.units)
        {
            Vector3 p = FormPlace(F, u);
            u.OrderPath(Grid.FindPath(u.Pos, p) ?? new List<Vector3> { p }, p, fight);
            u.form = F; u.capV = 0f; u.march = to; u.hasMarch = true; u.formPathT = 0f;
        }
        forms.Add(F);
    }

    /// every frame: move each formation's point along its route and steer every unit at its place
    void FormTick(float dt)
    {
        var O = R.D.orders;
        for (int i = forms.Count - 1; i >= 0; i--)
        {
            var F = forms[i];
            var us = F.units.Where(u => u && u.alive && u.form == F).ToList();
            if (us.Count == 0) { forms.RemoveAt(i); continue; }
            int ready = 0; bool fighting = false; var lags = new List<float>();
            foreach (var u in us)
            {
                float d = Flat(u.Pos, FormPlace(F, u)); if (d < 2.5f) ready++; lags.Add(d);
                if (F.fight && u.target != null && u.target.alive && Flat(u.target.Pos, u.Pos) < u.def.range + 3f) fighting = true;
            }
            lags.Sort(); float lag = lags[Mathf.FloorToInt((lags.Count - 1) * 0.8f)];   // most of the column: one straggler stuck on a rock does not halt it
            if (!F.marching) { if (ready >= us.Count * O.formReady || time - F.t > O.formWait) { F.marching = true; F.t = time; } }
            else if (!fighting)
            {   // the point moves on at the column's pace, slower while units are out of place, turning gradually onto each new leg
                float k = lag <= O.lagSoft ? 1f : lag >= O.lagHard ? 0f : 1f - (lag - O.lagSoft) / (O.lagHard - O.lagSoft);
                float step = F.cap * O.pace * Mathf.Max(0.12f, k) * dt * (lag >= O.lagHard ? 0f : 1f);
                while (step > 0f && F.seg < F.route.Count - 1)
                {
                    Vector3 e = F.route[F.seg + 1] - F.at; e.y = 0f; float el = e.magnitude;
                    if (el < 1e-3f) { F.seg++; continue; }
                    float wa = Mathf.Atan2(e.z, e.x), ha = Mathf.Atan2(F.h.z, F.h.x), da = Mathf.DeltaAngle(ha * Mathf.Rad2Deg, wa * Mathf.Rad2Deg) * Mathf.Deg2Rad;
                    float na = ha + Mathf.Clamp(da, -O.turnRate * dt, O.turnRate * dt); F.h = new Vector3(Mathf.Cos(na), 0f, Mathf.Sin(na));
                    float go = Mathf.Min(step, el) * (Mathf.Abs(da) > 1.2f ? 0.35f : 1f); F.at += e / el * go; step = 0f; if (el - go < 0.3f) F.seg++;
                }
            }
            bool done = F.marching && F.seg >= F.route.Count - 1;
            foreach (var u in us)
            {
                Vector3 p = FormPlace(F, u);
                if (done)
                {   // arrived: everyone walks the last few metres to its place and stands
                    u.form = null; u.capV = 0f;
                    u.OrderPath(Grid.LOS(u.Pos, p) ? new List<Vector3> { p } : Grid.FindPath(u.Pos, p) ?? new List<Vector3> { p }, p, F.fight);
                    continue;
                }
                if (u.order != DOrder.Move && u.order != DOrder.Fight) u.order = F.fight ? DOrder.Fight : DOrder.Move;
                if (u.path == null || u.pi >= u.path.Count) { u.path = new List<Vector3> { p }; u.pi = 0; }
                float d = Flat(u.Pos, p);
                // keep pace: the column's speed when in place, faster when behind (up to catchUp x), slower when ahead
                float ahead = Vector3.Dot(p - u.Pos, F.h);
                u.capV = !F.marching ? 0f : F.cap * O.pace * Mathf.Clamp(1f + ahead * 0.18f, 0.45f, O.catchUp / O.pace);
                u.formPathT -= dt;
                if (u.formPathT <= 0f)
                {
                    u.formPathT = 0.5f;
                    if (Grid.LOS(u.Pos, p)) { u.path = new List<Vector3> { p }; u.pi = 0; }
                    else if (pathBudget > 0) { pathBudget--; u.path = Grid.FindPath(u.Pos, p) ?? new List<Vector3> { p }; u.pi = 0; u.formPathT = 1.2f; }
                }
                else if (u.path.Count == 1 && u.pi == 0) u.path[0] = p;                    // between checks just slide the target along
                if (F.marching && u.path.Count == 1 && d < 4f) u.path[0] = p + F.h * 4f;   // near its place: steer for a point ahead of it and keep rolling
                u.dest = p; u.hasDest = true; u.ClearStuck();
            }
            if (done) forms.RemoveAt(i);
        }
    }

    // ================================================================ recruiting
    public bool CanRecruit(int army, string type, out string why)
    {
        why = null;
        if (!R.unit.TryGetValue(type, out var d)) { why = "Unknown unit"; return false; }
        var A = armies[army];
        if (A.money < d.cost) { why = $"Needs ${d.cost:0}"; return false; }
        if (A.manpower < d.mp) { why = $"Needs {d.mp:0} manpower"; return false; }
        return true;
    }

    public bool Recruit(int army, string type, Zone at)
    {
        if (at == null || at.owner != army) return false;
        if (!CanRecruit(army, type, out var why)) { if (army == player) Toast(why, true); return false; }
        if (at.queue.Count >= 6) { if (army == player) Toast($"{at.name}: the queue is full", true); return false; }
        var d = R.unit[type]; var A = armies[army];
        A.money -= d.cost; A.manpower -= d.mp;
        at.queue.Add(new QItem { type = type, left = Mathf.Max(1f, d.build), total = Mathf.Max(1f, d.build) });
        return true;
    }

    void QueueTick(float dt)
    {
        foreach (var z in zones)
        {
            if (z.queue.Count == 0) continue;
            if (z.owner < 0) { z.queue.Clear(); continue; }
            var q = z.queue[0]; q.left -= dt;
            if (q.left > 0f) continue;
            z.queue.RemoveAt(0);
            Vector3 dirIn = (Vector3.zero - z.pos); dirIn.y = 0f; dirIn.Normalize();
            var at = Grid.Snap(z.pos + dirIn * (z.r * 0.6f) + Random.insideUnitSphere.WithY(0f) * 3f);
            var u = Spawn(q.type, z.owner, at, Mathf.Atan2(-dirIn.z, dirIn.x));
            if (u != null)
            {
                var rally = Grid.Snap(z.pos + dirIn * (z.r + 8f) + Random.insideUnitSphere.WithY(0f) * 5f);
                u.OrderMove(rally, true, Grid.FindPath(u.Pos, rally));
                if (z.owner == player) Msg($"{u.def.name} ready at {z.name}.", player);
            }
        }
    }

    // ================================================================ the battle
    public float lastUpdateMs;           // how long the last frame's simulation took (for tuning)
    public int pathBudget;               // route searches left this frame (chasing and re-planning wait their turn)
    readonly System.Diagnostics.Stopwatch watch = new System.Diagnostics.Stopwatch();

    void Update()
    {
        if (R == null || Fx == null)
        {   // the scripts were recompiled while playing: the battle can't carry on, so stop quietly instead of throwing every frame
            Debug.LogWarning("[Dawgs] Scripts were reloaded during Play mode. Stop and press Play again to restart the battle.");
            enabled = false; return;
        }
        watch.Restart();
        // the fallen: gone from the battlefield (and from every list) before anyone looks at them this frame
        for (int i = units.Count - 1; i >= 0; i--)
        {
            var u = units[i];
            if (u == null) { units.RemoveAt(i); continue; }
            if (u.gone) { units.RemoveAt(i); selection.Remove(u); Destroy(u.gameObject); }
        }
        float dt = Time.deltaTime;
        if (dt > 0f && !over)
        {
            time += dt;
            pathBudget = 8;
            FormTick(dt);
            for (int i = 0; i < units.Count; i++) units[i].Step(dt);
            Separate(dt);
            Impacts();
            zoneT += dt; if (zoneT >= 0.25f) { ZonesTick(zoneT); zoneT = 0f; }
            econT += dt; while (econT >= 1f) { econT -= 1f; Economy(); }
            QueueTick(dt);
            if (enemyAI) { aiT -= dt; if (aiT <= 0f) { aiT = R.D.start.aiThink; AiThink(); } }
            winT += dt; if (winT > 1f) { winT = 0f; CheckWin(); }
        }
        else if (over) { for (int i = 0; i < units.Count; i++) units[i].Step(dt); }
        selection.RemoveAll(u => u == null || !u.alive);
        Fx.Update();
        lastUpdateMs = (float)watch.Elapsed.TotalMilliseconds;
    }

    /// units push each other apart; infantry of one army keep infSpace apart, vehicles vehSpace beyond their hulls
    void Separate(float dt)
    {
        var O = R.D.orders; int n = units.Count;
        for (int i = 0; i < n; i++)
        {
            var u = units[i]; if (!u.alive || u.def.isStatic) continue;
            for (int j = i + 1; j < n; j++)
            {
                var o = units[j]; if (!o.alive || o.def.isStatic) continue;
                float rr = u.rad + o.rad;
                if (u.army == o.army) { if (u.infantry && o.infantry) rr = Mathf.Max(rr, O.infSpace); else rr += O.vehSpace * 0.5f; }
                float dx = u.Pos.x - o.Pos.x, dz = u.Pos.z - o.Pos.z, d2 = dx * dx + dz * dz; if (d2 >= rr * rr) continue;
                float d = Mathf.Max(0.01f, Mathf.Sqrt(d2)); dx /= d; dz /= d;
                if (d2 < 1e-4f) { dx = Mathf.Cos(u.id); dz = Mathf.Sin(u.id); }
                float push = Mathf.Min(0.5f, (rr - d) * 0.5f) * Mathf.Min(1f, dt * 12f);
                float wu = u.def.isVeh && !o.def.isVeh ? 0.3f : 1f, wo = o.def.isVeh && !u.def.isVeh ? 0.3f : 1f;
                var pu = u.Pos + new Vector3(dx, 0f, dz) * (push * wu); var po = o.Pos - new Vector3(dx, 0f, dz) * (push * wo);
                if (Grid.Passable(pu)) u.ApplyTransform(pu);
                if (Grid.Passable(po)) o.ApplyTransform(po);
            }
        }
    }

    // ---- shots: hit or miss on the game's odds, the round lands after its flight time ----
    public void Shoot(DawgsUnit u, DawgsUnit t)
    {
        var C = R.D.combat;
        Vector3 from = u.Muzzle(), tp = t.Pos + Vector3.up * t.AimHeight;
        float d = new Vector2(tp.x - from.x, tp.z - from.z).magnitude;
        float acc = u.def.acc * (R.IsSoft(t.def) ? 1f : C.vsVehicleAcc) * (d > u.def.range * C.longRange ? C.longRangeAcc : 1f);
        bool hit = Random.value < Mathf.Clamp01(acc);
        Vector3 at = tp;
        if (!hit) { var m = Random.insideUnitCircle * (C.missSpread + d * 0.05f); at = tp + new Vector3(m.x, 0f, m.y); at.y = GroundY(at) + 0.1f; }
        if (u.rig && u.rig.isActiveAndEnabled) { u.rig.Fire(tp); from = u.Muzzle(); }
        string w = u.def.weapon;
        R.weapon.TryGetValue(w, out var W);
        float flight = W != null && W.speed > 0f ? d / W.speed : 0.05f;
        impacts.Add(new Impact { t = time + flight, shooter = u, target = hit ? t : null, at = at, weapon = w, dmg = u.def.dmg, splash = u.def.splash, hardK = u.def.hardK, army = u.army, shooterDef = u.def });
        bool rocket = w == "rocket" || w == "hrocket" || w == "sam" || w == "aam";
        bool shell = w == "shell" || w == "apshell" || w == "artillery";
        if (rocket || shell) Fx.Projectile(from, at, flight, rocket);
        else Fx.Tracer(from, at, u.infantry ? 0.06f : 0.1f, 0.06f, u.army);
        Fx.Play(DawgsFx.SoundFor(u.type, w), from, rocket || shell ? 0.8f : 0.6f);
    }

    void Impacts()
    {
        for (int i = impacts.Count - 1; i >= 0; i--)
        {
            var im = impacts[i]; if (im.t > time) continue;
            impacts.RemoveAt(i);
            if (im.target != null && im.target.alive)
            {
                float dmg = R.Hit(im.weapon, im.dmg, im.target.def) * (R.IsSoft(im.target.def) ? 1f : im.hardK);
                Damage(im.target, dmg, im.shooter);
            }
            if (im.splash > 0f)
            {
                foreach (var o in units)
                {
                    if (!o.alive || o == im.target || o.army == im.army) continue;
                    float d = new Vector2(o.Pos.x - im.at.x, o.Pos.z - im.at.z).magnitude; if (d > im.splash + o.radius) continue;
                    float k = R.D.combat.splashFalloff * (1f - Mathf.Clamp01(d / (im.splash + o.radius)));
                    Damage(o, R.Hit(im.weapon, im.dmg, o.def) * k, im.shooter);
                }
                Fx.Blast(im.at, Mathf.Max(1.6f, im.splash * 1.4f), false);
            }
            else if (im.weapon == "rocket" || im.weapon == "shell" || im.weapon == "apshell") Fx.Blast(im.at, 1.4f, false);
        }
    }

    void Damage(DawgsUnit t, float dmg, DawgsUnit src)
    {
        if (dmg <= 0f || !t.alive) return;
        t.hp -= dmg; t.hitT = time; if (src && src.alive) t.attacker = src;
        t.Struck();
        if (t.hp > 0f) return;
        t.hp = 0f; t.Die();
        armies[t.army].losses++;
        if (src) armies[src.army].kills++;
        if (!t.infantry) { Fx.Blast(t.Pos + Vector3.up, 5f, true); Fx.Play("collapse", t.Pos, 0.8f); }
        if (t.army == player && !t.infantry) Msg($"{t.def.name} destroyed.", t.army, true);
    }

    // ---- zones: BALANCE.capture ----
    void ZonesTick(float dt)
    {
        var K = R.D.capture;
        foreach (var z in zones)
        {
            z.count[0] = z.count[1] = 0;
            foreach (var u in units)
                if (u.alive && u.Military && R.IsGround(u.def) && new Vector2(u.Pos.x - z.pos.x, u.Pos.z - z.pos.z).sqrMagnitude <= (z.r + 2f) * (z.r + 2f))
                    z.count[Mathf.Clamp(u.army, 0, 1)]++;
            int present = (z.count[0] > 0 ? 1 : 0) + (z.count[1] > 0 ? 1 : 0);
            z.contested = present > 1;
            if (present == 0) { z.capP = Mathf.Max(0f, z.capP - K.decay * dt); if (z.capP <= 0f) z.capF = -1; continue; }
            if (present > 1) continue;
            int a = z.count[0] > 0 ? 0 : 1;
            if (a == z.owner) { z.capP = Mathf.Max(0f, z.capP - K.rivalDrain * dt); if (z.capP <= 0f) z.capF = -1; continue; }
            if (z.capF >= 0 && z.capF != a) { z.capP -= K.rivalDrain * dt; if (z.capP <= 0f) { z.capP = 0f; z.capF = -1; } continue; }
            z.capF = a;
            if (z.owner == player && a != player && (!attackWarnT.TryGetValue(z, out var wt) || time - wt > 25f))
            {   // the game's alarm when one of your zones starts to fall
                attackWarnT[z] = time;
                Msg($"{z.name} is under attack!", player, true); Toast($"{z.name} is under attack", true);
                Fx.Alert("alarm", 0.7f, 6f);
            }
            z.capP += (K.@base + K.perUnit * Mathf.Min(z.count[a], K.maxUnits)) * dt;
            if (z.capP >= 100f)
            {
                int prev = z.owner; z.owner = a; z.capP = 0f; z.capF = -1; z.queue.Clear(); TintZone(z);
                Msg(prev >= 0 ? $"{armies[a].name} took {z.name} from {armies[prev].name}." : $"{armies[a].name} secured {z.name}.", a, prev == player);
                if (prev == player) { Toast($"{z.name} lost!", true); Fx.Alert("siren", 0.6f, 10f); }
                else if (a == player) Toast($"{z.name} secured");
            }
        }
    }

    void Economy()
    {
        var E = R.D.economy;
        foreach (var A in armies)
        {
            float inc = 0f, mp = 0f;
            foreach (var z in zones) if (z.owner == A.id && R.ztype.TryGetValue(z.d.type, out var T)) { inc += T.income; mp += T.mp; }
            float k = A.id == player ? 1f : aiIncomeMul;
            A.incomeSec = inc * incomeMul * k / E.incomeDiv; A.mpMin = mp * manpowerMul * k / E.manpowerDiv * 60f;
            A.money += A.incomeSec; A.manpower += A.mpMin / 60f;
        }
    }

    void CheckWin()
    {
        foreach (var A in armies)
        {
            bool hasZone = zones.Any(z => z.owner == A.id);
            bool hasUnits = units.Any(u => u.alive && u.army == A.id && u.Military);
            A.alive = hasZone || hasUnits;
        }
        int held = zones.Count(z => z.owner == player);
        if (!armies[1 - player].alive || held == zones.Count) End(player);
        else if (!armies[player].alive || zones.Count(z => z.owner == 1 - player) == zones.Count) End(1 - player);
    }
    void End(int w) { if (over) return; over = true; winner = w; Msg(w == player ? "Victory: the island is yours." : "Defeat: the Legion holds the island.", w, true); }

    // ---- the Legion: recruit by its army mix, send waves at the nearest zone it doesn't hold, defend what it has ----
    void AiThink()
    {
        int me = 1 - player; var A = armies[me];
        // recruit: two in hand at the HQ, one at each other base, up to the army cap
        int alive = units.Count(u => u.alive && u.army == me) + zones.Sum(z => z.owner == me ? z.queue.Count : 0);
        foreach (var z in zones.Where(z => z.owner == me))
        {
            if (alive >= aiUnitCap) break;
            if (z.queue.Count >= (z.d.type == "hq" ? 2 : 1)) continue;
            alive++;
            var opts = AiComp.Where(kv => prefabOf.ContainsKey($"u_{kv.Key}_{me}") && R.unit.ContainsKey(kv.Key) && R.unit[kv.Key].cost <= A.money && R.unit[kv.Key].mp <= A.manpower).ToList();
            if (opts.Count == 0) break;
            float tot = opts.Sum(o => o.Value), r = Random.value * tot; string pick = opts[0].Key;
            foreach (var o in opts) { r -= o.Value; if (r <= 0f) { pick = o.Key; break; } }
            Recruit(me, pick, z);
        }
        var mine = units.Where(u => u.alive && u.army == me && u.Military).ToList();
        // defend: zones with enemies in them pull in idle units nearby
        foreach (var z in zones.Where(z => z.owner == me && z.count[player] > 0))
        {
            var near = mine.Where(u => u.order == DOrder.Idle && (u.Pos - z.pos).magnitude < 140f).ToList();
            if (near.Count > 0) IssueMove(near, z.pos, true);
        }
        // waves
        aiWaveT -= R.D.start.aiThink;
        if (aiWaveT > 0f) return;
        aiWaveT = R.D.start.aiWave + Random.value * R.D.start.aiWaveStagger;
        var home = Home(me);
        var idle = mine.Where(u => u.order == DOrder.Idle).ToList();
        if (home != null && idle.Count > 4)
        {   // two stay home
            var keep = idle.OrderBy(u => (u.Pos - home.pos).sqrMagnitude).Take(2).ToList();
            idle = idle.Except(keep).ToList();
        }
        if (idle.Count < 3) return;
        Vector3 c = Vector3.zero; foreach (var u in idle) c += u.Pos; c /= idle.Count;
        Zone best = null; float bs = 1e9f;
        foreach (var z in zones.Where(z => z.owner != me))
        {
            float pref = z.d.type == "fortress" ? 1.8f : z.d.type == "hq" ? 1.3f : 1f;
            float s = (z.pos - c).magnitude / pref;
            if (s < bs) { bs = s; best = z; }
        }
        if (best != null) IssueMove(idle, best.pos, true);
    }
}

static class DawgsVecExt { public static Vector3 WithY(this Vector3 v, float y) { v.y = y; return v; } }
