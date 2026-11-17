// Dawgs Uprising -> Unity: the browser game's mouse and keyboard, for the playable skirmish.
//   left-drag box select · click select (Shift adds / drops, double-click picks every one of that type on screen)
//   right-click: move, attack the enemy under the cursor, or escort the friendly unit under it
//   right-drag: spread the selection along the line you draw · started on an enemy: a circle, attack everything in it
//   F fight-move · H halt · G guard (click a unit to follow and protect) · Esc menu / cancel · Ctrl+A all military
//   P pause · Space jump home · Home reset the camera view · middle drag orbit (Shift: pan) · mouse at a screen edge pans
//   Tab scoreboard · M full-screen map · Shift+1-9 save a control group, 1-9 recall it (twice: jump to it) · Shift+M mute
//   unit hotkeys (Z rifleman, X machine gunner, C rocketeer, Shift+Z sniper ...) train at the base shown on the card
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.InputSystem;

public class DawgsCommand : MonoBehaviour
{
    public DawgsGame game;
    public DawgsHud hud;
    public enum Armed { None, Fight, Guard, Ping }
    public Armed armed;

    Camera cam;
    Vector2 dragStart; bool dragging, boxing;
    // right-button drag: a line to spread along, or (started on an enemy) a circle to attack
    bool rdrag, rLine, rCircle, rFight; float rLen, rRadius; Vector3 rCentre;
    readonly List<Vector2> rPts = new List<Vector2>(); readonly List<Vector3> rGround = new List<Vector3>();
    LineRenderer lineLr, ringLr; float ringFade;
    DawgsRtsCamera rts;
    float lastClickT; string lastClickType;
    readonly Dictionary<int, List<DawgsUnit>> groups = new Dictionary<int, List<DawgsUnit>>();
    readonly float[] groupT = new float[10];
    List<DawgsUnit> Sel => game.selection;

    void Start()
    {
        cam = Camera.main; rts = cam ? cam.GetComponent<DawgsRtsCamera>() : null;
        lineLr = Preview("order line", 0.22f); ringLr = Preview("attack area", 0.3f); ringLr.loop = true;
    }

    LineRenderer Preview(string name, float width)
    {
        var lr = new GameObject(name).AddComponent<LineRenderer>(); lr.transform.SetParent(transform, false);
        lr.useWorldSpace = true; lr.sharedMaterial = game.ringMaterial; lr.widthMultiplier = width; lr.numCornerVertices = 2;
        lr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; lr.receiveShadows = false; lr.enabled = false;
        return lr;
    }

    public bool OwnSelection => Sel.Count > 0 && Sel[0].army == game.player;

    void Update()
    {
        var m = Mouse.current; var kb = Keyboard.current;
        if (m == null || kb == null || game == null) return;
        if (!cam) cam = Camera.main;
        Vector2 mp = m.position.ReadValue();
        bool overUI = hud && hud.OverUI(mp);
        bool shift = kb.leftShiftKey.isPressed || kb.rightShiftKey.isPressed;
        bool ctrl = kb.leftCtrlKey.isPressed || kb.rightCtrlKey.isPressed;
        bool modal = hud && hud.ModalOpen;

        // ---- mouse ----
        if (!modal)
        {
            if (m.leftButton.wasPressedThisFrame && !overUI) { dragStart = mp; dragging = true; boxing = false; }
            if (dragging && m.leftButton.isPressed && armed == Armed.None && (mp - dragStart).magnitude > 6f) { boxing = true; hud?.ShowBox(dragStart, mp); }
            if (dragging && m.leftButton.wasReleasedThisFrame)
            {
                dragging = false; hud?.HideBox();
                if (boxing) BoxSelect(dragStart, mp, shift);
                else LeftClick(mp, shift);
                boxing = false;
            }
            if (m.rightButton.wasPressedThisFrame && !overUI) RightDown(mp);
            if (rdrag && m.rightButton.isPressed) RightDrag(mp);
            if (rdrag && m.rightButton.wasReleasedThisFrame) RightUp(mp, shift);
        }
        else if (rdrag) CancelRightDrag();
        if (ringFade > 0f && !rdrag) { ringFade -= Time.unscaledDeltaTime; if (ringFade <= 0f) ringLr.enabled = false; }
        // the mouse at a screen edge pans, unless something is being dragged
        if (rts) rts.edgePan = !modal && !dragging && !rdrag && !rts.MiddleDragging && !(hud && hud.OverlayOpen);

        // ---- keys ----
        if (kb.mKey.wasPressedThisFrame && shift) hud?.SetMute(!DawgsAudio.MusicMuted);   // Shift+M, as in the browser game
        if (kb.tabKey.wasPressedThisFrame && !modal) hud?.ToggleScore();
        if (kb.mKey.wasPressedThisFrame && !shift && !modal) hud?.ToggleBigMap();
        if (kb.escapeKey.wasPressedThisFrame)
        {
            if (hud && hud.OverlayOpen) hud.CloseOverlays();
            else if (rdrag) CancelRightDrag();
            else if (armed != Armed.None) SetArmed(Armed.None);
            else hud?.TogglePause();
        }
        if (kb.aKey.wasPressedThisFrame && ctrl && !modal) SelectAllMilitary();
        if (modal) return;
        if (kb.homeKey.wasPressedThisFrame) hud?.Toast("Camera view reset");   // DawgsRtsCamera resets it
        if (kb.pKey.wasPressedThisFrame) hud?.TogglePauseSpeed();
        if (kb.spaceKey.wasPressedThisFrame) JumpHome();
        if (kb.fKey.wasPressedThisFrame && OwnSelection) SetArmed(armed == Armed.Fight ? Armed.None : Armed.Fight);
        if (kb.hKey.wasPressedThisFrame && OwnSelection) { game.OrderHalt(Sel); SetArmed(Armed.None); hud?.Toast("Halt"); }
        if (kb.gKey.wasPressedThisFrame && OwnSelection) SetArmed(armed == Armed.Guard ? Armed.None : Armed.Guard);
        if (kb.iKey.wasPressedThisFrame) SetArmed(armed == Armed.Ping ? Armed.None : Armed.Ping);
        for (int d = 1; d <= 9; d++)
        {
            var key = kb[(Key)((int)Key.Digit1 + d - 1)];
            if (!key.wasPressedThisFrame) continue;
            if (shift || ctrl) SaveGroup(d); else RecallGroup(d);
        }
        // unit hotkeys (the browser's: "Z", "⇧Z" ...)
        foreach (var grp in DawgsGame.RecruitGroups)
            for (int i = 1; i < grp.Length; i++)
            {
                if (!game.R.unit.TryGetValue(grp[i], out var def) || string.IsNullOrEmpty(def.hot)) continue;
                bool needShift = def.hot.StartsWith("⇧");
                string k = needShift ? def.hot.Substring(1) : def.hot;
                if (k.Length != 1 || needShift != shift) continue;
                Key key = KeyOf(k[0]); if (key == Key.None || !kb[key].wasPressedThisFrame) continue;
                if (key == Key.F || key == Key.H || key == Key.G || key == Key.P || key == Key.I) continue;
                hud?.TrainHere(def.key);
            }
    }

    static Key KeyOf(char c)
    {
        c = char.ToUpperInvariant(c);
        if (c >= 'A' && c <= 'Z') return (Key)((int)Key.A + (c - 'A'));
        return Key.None;
    }

    public void SetArmed(Armed a)
    {
        armed = a;
        if (a == Armed.Fight) hud?.Toast("Fight-move: right- or left-click where to go");
        else if (a == Armed.Guard) hud?.Toast("Guard: click one of your units to follow and protect it");
        else if (a == Armed.Ping) hud?.Toast("Ping: click the map");
    }

    // ---- picking ----
    public bool GroundAt(Vector2 sp, out Vector3 p)
    {
        var ray = cam.ScreenPointToRay(sp);
        if (Physics.Raycast(ray, out var hit, 6000f)) { p = hit.point; return true; }
        var pl = new Plane(Vector3.up, Vector3.zero);
        if (pl.Raycast(ray, out float t)) { p = ray.GetPoint(t); return true; }
        p = Vector3.zero; return false;
    }

    DawgsUnit UnitAt(Vector2 sp, System.Func<DawgsUnit, bool> ok = null)
    {
        DawgsUnit best = null; float bd = 1e9f;
        foreach (var u in game.units)
        {
            if (!u.alive || (ok != null && !ok(u))) continue;
            Vector3 c = u.Pos + Vector3.up * u.AimHeight;
            Vector3 s = cam.WorldToScreenPoint(c); if (s.z <= 0f) continue;
            Vector3 e = cam.WorldToScreenPoint(c + cam.transform.right * (u.radius + 0.6f));
            float pr = Mathf.Max(9f, (e - s).magnitude * 1.3f);
            float d = ((Vector2)s - sp).magnitude;
            if (d < pr && d < bd) { bd = d; best = u; }
        }
        return best;
    }

    void LeftClick(Vector2 sp, bool shift)
    {
        if (armed == Armed.Guard) { GuardAt(sp); return; }
        if (armed != Armed.None && GroundAt(sp, out var gp))
        {
            if (armed == Armed.Fight) IssueAt(sp, true);
            else if (armed == Armed.Ping) hud?.Ping(gp);
            if (!shift) SetArmed(Armed.None);
            return;
        }
        var u = UnitAt(sp);
        if (u == null) { if (!shift) Select(new List<DawgsUnit>()); return; }
        bool dbl = Time.unscaledTime - lastClickT < 0.35f && lastClickType == u.type;
        lastClickT = Time.unscaledTime; lastClickType = u.type;
        if (u.army != game.player) { Select(new List<DawgsUnit> { u }); return; }
        if (dbl)
        {
            var same = game.units.Where(o => o.alive && o.army == game.player && o.type == u.type && OnScreen(o)).ToList();
            Select(same); hud?.Toast($"{same.Count} {u.def.name}{(same.Count == 1 ? "" : "s")} selected");
            return;
        }
        if (shift && OwnSelection)
        {
            var s = Sel.ToList(); if (s.Contains(u)) s.Remove(u); else s.Add(u); Select(s);
        }
        else Select(new List<DawgsUnit> { u });
    }

    bool OnScreen(DawgsUnit u)
    {
        var s = cam.WorldToScreenPoint(u.Pos); return s.z > 0 && s.x >= 0 && s.y >= 0 && s.x <= Screen.width && s.y <= Screen.height;
    }

    void BoxSelect(Vector2 a, Vector2 b, bool shift)
    {
        var r = Rect.MinMaxRect(Mathf.Min(a.x, b.x), Mathf.Min(a.y, b.y), Mathf.Max(a.x, b.x), Mathf.Max(a.y, b.y));
        var hits = game.units.Where(u => u.alive && u.army == game.player && !u.def.isStatic && r.Contains((Vector2)cam.WorldToScreenPoint(u.Pos + Vector3.up * u.AimHeight)) && cam.WorldToScreenPoint(u.Pos).z > 0f).ToList();
        if (shift && OwnSelection) hits = Sel.Union(hits).ToList();
        Select(hits);
        if (hits.Count > 1) hud?.Toast($"{hits.Count} military units selected");
    }

    public void Select(List<DawgsUnit> us)
    {
        foreach (var u in Sel) if (u) { u.selected = false; if (u.ring) u.ring.SetActive(false); }
        Sel.Clear(); Sel.AddRange(us.Where(u => u && u.alive));
        foreach (var u in Sel) { u.selected = true; if (u.ring) u.ring.SetActive(true); }
        if (!OwnSelection && armed != Armed.Ping) armed = Armed.None;
        hud?.SelectionChanged();
    }

    // ---- the right button: click, line or circle (the browser's rdrag / rightRelease / issueAt) ----
    void RightDown(Vector2 sp)
    {
        rdrag = true; rLine = false; rCircle = false; rLen = 0f; rRadius = 0f; rFight = armed == Armed.Fight;
        rPts.Clear(); rGround.Clear(); rPts.Add(sp);
        bool ground = GroundAt(sp, out var g); if (ground) rGround.Add(g);
        // pressed on an enemy with fighting units selected: dragging draws a circle to attack everything inside
        if (ground && armed != Armed.Guard && armed != Armed.Ping && OwnSelection && Sel.Any(u => u.Military))
        {
            var foe = UnitAt(sp, u => u.army != game.player);
            if (foe != null) { rCircle = true; rCentre = g; }
        }
    }

    void RightDrag(Vector2 sp)
    {
        if (rCircle)
        {
            if (GroundAt(sp, out var g))
            {
                rRadius = Mathf.Min(60f, new Vector2(g.x - rCentre.x, g.z - rCentre.z).magnitude);
                if (rRadius > 2.5f) DrapeRing(rCentre, rRadius, new Color(1f, 0.35f, 0.25f, 0.9f)); else ringLr.enabled = false;
            }
            return;
        }
        float dd = (sp - rPts[rPts.Count - 1]).magnitude;
        if (dd > 6f && GroundAt(sp, out var gp)) { rPts.Add(sp); rGround.Add(gp); rLen += dd; }
        if (rLen > 14f && Sel.Count > 1 && OwnSelection) rLine = true;
        if (rLine) DrapeLine(rGround, rFight ? new Color(1f, 0.82f, 0.35f, 0.95f) : new Color(0.96f, 0.98f, 0.78f, 0.95f));
    }

    void RightUp(Vector2 sp, bool shift)
    {
        bool circle = rCircle && rRadius > 2.5f, line = rLine && rGround.Count > 1; bool fight = rFight || armed == Armed.Fight;
        rdrag = false; lineLr.enabled = false;
        if (armed == Armed.Guard) { GuardAt(sp); return; }
        if (armed == Armed.Ping) { SetArmed(Armed.None); return; }
        if (!OwnSelection) { SetArmed(Armed.None); ringLr.enabled = false; return; }
        if (circle)
        {
            int n = game.OrderArea(Sel, rCentre, rRadius);
            ringFade = 1.4f;
            hud?.Toast($"Attack area: {n} target{(n == 1 ? "" : "s")} in the circle");
        }
        else
        {
            ringLr.enabled = false;
            if (line) game.OrderSlots(Sel, LineSlots(rGround, Sel.Count(u => u.alive && !u.def.isStatic)), fight);
            else IssueAt(sp, fight);
        }
        if (armed == Armed.Fight && !shift) SetArmed(Armed.None);
    }

    void CancelRightDrag() { rdrag = false; lineLr.enabled = false; ringLr.enabled = false; }

    /// a plain right-click: attack the enemy under the cursor, escort the friendly unit under it, else go there
    void IssueAt(Vector2 sp, bool fight)
    {
        if (!OwnSelection) return;
        var hit = UnitAt(sp, u => !u.selected);
        if (hit != null && hit.army != game.player) { game.OrderAttack(Sel, hit); return; }
        if (hit != null && Sel.Any(u => u != hit && !u.def.builder))
        {   // right on a friendly unit: guard it
            Vector3 s = cam.WorldToScreenPoint(hit.Pos + Vector3.up * 0.8f);
            float tight = (hit.def.isVeh ? 12f : 8f) * Mathf.Min(1.6f, 95f / Mathf.Max(1f, rts ? rts.distance : 110f) + 0.4f) * Screen.height / 900f;
            if (s.z > 0f && ((Vector2)s - sp).magnitude < tight * 2.2f) { GuardOrder(hit); return; }
        }
        if (GroundAt(sp, out var gp)) game.OrderMove(Sel, gp, fight);
    }

    void GuardAt(Vector2 sp)
    {
        SetArmed(Armed.None);
        if (!OwnSelection) return;
        var t = UnitAt(sp, u => u.army == game.player && !u.selected);
        if (t != null) GuardOrder(t); else hud?.Toast("Click one of your units to guard it.");
    }

    void GuardOrder(DawgsUnit t)
    {
        int n = Sel.Count(u => u != t && u.alive);
        if (game.OrderGuard(Sel, t)) hud?.Toast($"{n} unit{(n == 1 ? "" : "s")} guarding the {t.def.name}");
    }

    /// n points evenly along the line the player drew
    static List<Vector3> LineSlots(List<Vector3> g, int n)
    {
        var res = new List<Vector3>(); if (g.Count == 0 || n <= 0) return res;
        var seg = new float[g.Count];
        for (int i = 1; i < g.Count; i++) seg[i] = seg[i - 1] + new Vector2(g[i].x - g[i - 1].x, g[i].z - g[i - 1].z).magnitude;
        float L = seg[g.Count - 1];
        for (int k = 0; k < n; k++)
        {
            float t = n == 1 ? L / 2f : L * k / (n - 1); int i = 1; while (i < g.Count - 1 && seg[i] < t) i++;
            Vector3 a = g[Mathf.Max(0, i - 1)], b = g[Mathf.Min(g.Count - 1, i)]; float sl = i < g.Count ? seg[i] - seg[i - 1] : 0f; if (sl <= 0f) sl = 1f;
            res.Add(Vector3.Lerp(a, b, Mathf.Clamp01((t - seg[Mathf.Max(0, i - 1)]) / sl)));
        }
        return res;
    }

    void DrapeLine(List<Vector3> pts, Color col)
    {
        lineLr.positionCount = pts.Count;
        for (int i = 0; i < pts.Count; i++) { var p = pts[i]; p.y = game.GroundY(p) + 0.3f; lineLr.SetPosition(i, p); }
        lineLr.startColor = lineLr.endColor = col; lineLr.enabled = true;
    }

    void DrapeRing(Vector3 c, float r, Color col)
    {
        int n = 72; ringLr.positionCount = n;
        for (int i = 0; i < n; i++)
        {
            float a = i * Mathf.PI * 2f / n; var p = c + new Vector3(Mathf.Cos(a), 0f, Mathf.Sin(a)) * r;
            p.y = game.GroundY(p) + 0.35f; ringLr.SetPosition(i, p);
        }
        ringLr.startColor = ringLr.endColor = col; ringLr.enabled = true; ringFade = 0f;
    }

    public void SelectAllMilitary()
    {
        var all = game.units.Where(u => u.alive && u.army == game.player && u.Military).ToList();
        Select(all); hud?.Toast($"{all.Count} military units selected");
    }

    void SaveGroup(int d)
    {
        if (!OwnSelection) return;
        groups[d] = Sel.ToList(); foreach (var u in Sel) u.group = d;
        hud?.Toast($"Group {d} saved ({Sel.Count})");
    }

    void RecallGroup(int d)
    {
        if (!groups.TryGetValue(d, out var g)) return;
        g.RemoveAll(u => u == null || !u.alive);
        if (g.Count == 0) return;
        Select(g);
        if (Time.unscaledTime - groupT[d] < 0.4f) JumpTo(g.Aggregate(Vector3.zero, (s, u) => s + u.Pos) / g.Count);
        groupT[d] = Time.unscaledTime;
    }

    public void JumpHome() { var h = game.Home(game.player); if (h != null) JumpTo(h.pos); }
    public void JumpTo(Vector3 p)
    {
        var rc = cam ? cam.GetComponent<DawgsRtsCamera>() : null;
        if (rc) { rc.target = new Vector3(p.x, 0f, p.z); rc.Apply(); }
    }
}
