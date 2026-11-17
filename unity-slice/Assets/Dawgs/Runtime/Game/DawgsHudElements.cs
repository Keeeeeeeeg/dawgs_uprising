// Dawgs Uprising -> Unity: custom UI Toolkit elements for the HUD, drawn with Painter2D where USS can't reach:
//   DawgsPanel    the game's chamfered instrument panel (clip-path corners cut top-left and bottom-right)
//   DawgsIcon     the order glyphs on the command card (fight, halt, guard, stances ...)
//   DawgsFlag     an army's swatch in the Armies list
//   DawgsMinimap  the map picture with zones, units, pings and the camera's view, click / drag to jump
//   DawgsSlider   the settings sliders (the game's range inputs in its militia green)
using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UIElements;

public class DawgsPanel : VisualElement
{
    public Color fill = new Color(22 / 255f, 26 / 255f, 17 / 255f, 0.9f);
    public Color line = new Color(0x38 / 255f, 0x42 / 255f, 0x2c / 255f, 1f);
    public float cut = 8f;

    public DawgsPanel() { generateVisualContent += Draw; pickingMode = PickingMode.Position; }

    void Draw(MeshGenerationContext ctx)
    {
        float w = layout.width, h = layout.height; if (w < 2f || h < 2f) return;
        var p = ctx.painter2D;
        p.BeginPath();
        p.MoveTo(new Vector2(cut, 0f)); p.LineTo(new Vector2(w, 0f)); p.LineTo(new Vector2(w, h - cut));
        p.LineTo(new Vector2(w - cut, h)); p.LineTo(new Vector2(0f, h)); p.LineTo(new Vector2(0f, cut)); p.ClosePath();
        p.fillColor = fill; p.Fill();
        p.lineWidth = 1f; p.strokeColor = line; p.Stroke();
    }
}

public class DawgsFlag : VisualElement
{
    public Color color = Color.green;
    public DawgsFlag(Color c) { color = c; generateVisualContent += Draw; pickingMode = PickingMode.Ignore; }
    void Draw(MeshGenerationContext ctx)
    {
        float w = layout.width, h = layout.height; if (w < 2f) return;
        var p = ctx.painter2D;
        // a slanted chip with a dark band, like the game's .chips
        p.BeginPath(); p.MoveTo(new Vector2(4f, 0f)); p.LineTo(new Vector2(w, 0f)); p.LineTo(new Vector2(w - 4f, h)); p.LineTo(new Vector2(0f, h)); p.ClosePath();
        p.fillColor = color; p.Fill();
        p.BeginPath(); p.MoveTo(new Vector2(2.6f, h * 0.38f)); p.LineTo(new Vector2(w - 1.6f, h * 0.38f)); p.LineTo(new Vector2(w - 2.6f, h * 0.62f)); p.LineTo(new Vector2(1.6f, h * 0.62f)); p.ClosePath();
        p.fillColor = new Color(0f, 0f, 0f, 0.3f); p.Fill();
    }
}

public class DawgsIcon : VisualElement
{
    public enum Kind { Fight, Halt, Guard, Aggressive, Hold, ReturnFire, Flag, Unload, Walls }
    public Kind kind;
    public Color color = new Color(0x7c / 255f, 0xc9 / 255f, 0x4f / 255f);
    public DawgsIcon(Kind k) { kind = k; generateVisualContent += Draw; pickingMode = PickingMode.Ignore; AddToClassList("cb-ic"); }
    public void SetColor(Color c) { if (c != color) { color = c; MarkDirtyRepaint(); } }

    void Draw(MeshGenerationContext ctx)
    {
        float w = layout.width, h = layout.height; if (w < 2f) return;
        var p = ctx.painter2D; p.fillColor = color; p.strokeColor = color; p.lineWidth = 2f; p.lineJoin = LineJoin.Miter;
        float cx = w * 0.5f, cy = h * 0.5f, s = Mathf.Min(w, h) * 0.5f;
        Vector2 V(float x, float y) => new Vector2(cx + x * s, cy + y * s);
        switch (kind)
        {
            case Kind.Fight:   // ▶>
                p.BeginPath(); p.MoveTo(V(-1.3f, -0.8f)); p.LineTo(V(-0.2f, 0f)); p.LineTo(V(-1.3f, 0.8f)); p.ClosePath(); p.Fill();
                p.BeginPath(); p.MoveTo(V(0.2f, -0.8f)); p.LineTo(V(1.2f, 0f)); p.LineTo(V(0.2f, 0.8f)); p.Stroke();
                break;
            case Kind.Halt:
                p.BeginPath(); p.MoveTo(V(-0.7f, -0.7f)); p.LineTo(V(0.7f, -0.7f)); p.LineTo(V(0.7f, 0.7f)); p.LineTo(V(-0.7f, 0.7f)); p.ClosePath(); p.Fill();
                break;
            case Kind.Guard:
            case Kind.Hold:
                p.BeginPath(); p.MoveTo(V(-0.85f, -0.85f)); p.LineTo(V(0.85f, -0.85f)); p.LineTo(V(0.85f, 0.05f));
                p.BezierCurveTo(V(0.85f, 0.55f), V(0.3f, 0.8f), V(0f, 0.95f)); p.BezierCurveTo(V(-0.3f, 0.8f), V(-0.85f, 0.55f), V(-0.85f, 0.05f)); p.ClosePath(); p.Fill();
                if (kind == Kind.Guard)
                {   // a light check through the shield
                    p.strokeColor = new Color(0.08f, 0.1f, 0.06f, 0.85f); p.lineWidth = 1.6f;
                    p.BeginPath(); p.MoveTo(V(-0.4f, 0f)); p.LineTo(V(-0.05f, 0.35f)); p.LineTo(V(0.45f, -0.35f)); p.Stroke();
                }
                break;
            case Kind.Aggressive:
                p.BeginPath(); p.MoveTo(V(0f, -0.95f)); p.LineTo(V(1.25f, 0f)); p.LineTo(V(0f, 0.95f)); p.LineTo(V(-1.25f, 0f)); p.ClosePath(); p.Stroke();
                p.BeginPath(); p.MoveTo(V(0f, -0.35f)); p.LineTo(V(0.5f, 0f)); p.LineTo(V(0f, 0.35f)); p.LineTo(V(-0.5f, 0f)); p.ClosePath(); p.Fill();
                break;
            case Kind.ReturnFire:
                p.BeginPath(); p.Arc(V(0f, 0.1f), s * 0.75f, Angle.Degrees(200f), Angle.Degrees(-20f), ArcDirection.Clockwise); p.Stroke();
                p.BeginPath(); p.MoveTo(V(-1.25f, -0.1f)); p.LineTo(V(-0.75f, 0.45f)); p.LineTo(V(-0.25f, -0.1f)); p.ClosePath(); p.Fill();
                break;
            case Kind.Flag:
            case Kind.Unload:
                p.BeginPath(); p.MoveTo(V(-0.7f, -0.95f)); p.LineTo(V(-0.55f, -0.95f)); p.LineTo(V(-0.55f, 0.95f)); p.LineTo(V(-0.7f, 0.95f)); p.ClosePath(); p.Fill();
                p.BeginPath(); p.MoveTo(V(-0.55f, -0.9f)); p.LineTo(V(0.9f, -0.9f)); p.LineTo(V(0.45f, -0.5f)); p.LineTo(V(0.9f, -0.1f)); p.LineTo(V(-0.55f, -0.1f)); p.ClosePath(); p.Fill();
                break;
            case Kind.Walls:
                p.BeginPath();
                p.MoveTo(V(-1.2f, 0.9f)); p.LineTo(V(-1.2f, -0.7f)); p.LineTo(V(-0.85f, -0.7f)); p.LineTo(V(-0.85f, -0.35f)); p.LineTo(V(-0.45f, -0.35f)); p.LineTo(V(-0.45f, -0.7f));
                p.LineTo(V(-0.1f, -0.7f)); p.LineTo(V(-0.1f, -0.35f)); p.LineTo(V(0.3f, -0.35f)); p.LineTo(V(0.3f, -0.7f)); p.LineTo(V(0.65f, -0.7f)); p.LineTo(V(0.65f, -0.35f));
                p.LineTo(V(1.0f, -0.35f)); p.LineTo(V(1.0f, -0.7f)); p.LineTo(V(1.2f, -0.7f)); p.LineTo(V(1.2f, 0.9f)); p.ClosePath(); p.Fill();
                break;
        }
    }
}

/// the minimap: the pre-rendered map picture plus zones, units, pings and the camera's footprint
public class DawgsMinimap : VisualElement
{
    public DawgsGame game;
    public Camera cam;
    public Func<Vector3, bool> onJump;
    public readonly List<(Vector3 at, float t0)> pings = new List<(Vector3, float)>();
    float x0, zTop, W, H;
    bool dragging;

    public DawgsMinimap(DawgsGame g)
    {
        game = g; name = "mini";
        var gd = g.R.D.grid; x0 = gd.X0; W = gd.W; H = gd.H; zTop = -gd.Z0;   // Unity z at the top edge (the game's -z)
        if (g.minimap) style.backgroundImage = new StyleBackground(g.minimap);
        generateVisualContent += Draw;
        RegisterCallback<PointerDownEvent>(e => { if (e.button == 0) { dragging = true; this.CapturePointer(e.pointerId); Jump(e.localPosition); e.StopPropagation(); } });
        RegisterCallback<PointerMoveEvent>(e => { if (dragging) Jump(e.localPosition); });
        RegisterCallback<PointerUpEvent>(e => { if (dragging) { dragging = false; this.ReleasePointer(e.pointerId); } });
    }

    Vector2 ToMap(Vector3 w) => new Vector2((w.x - x0) / W * layout.width, (zTop - w.z) / H * layout.height);
    Vector3 ToWorld(Vector2 m) => new Vector3(x0 + m.x / layout.width * W, 0f, zTop - m.y / layout.height * H);
    void Jump(Vector2 local) { onJump?.Invoke(ToWorld(local)); }

    void Draw(MeshGenerationContext ctx)
    {
        if (game == null || layout.width < 4f) return;
        var p = ctx.painter2D;
        // zones: a square in the owner's colour, a ring while it's being taken
        foreach (var z in game.zones)
        {
            var c = ToMap(z.pos); var col = z.owner >= 0 ? game.armies[z.owner].color : new Color(0.85f, 0.82f, 0.7f);
            float s = z.d.type == "hq" ? 4.5f : 3.5f;
            p.fillColor = col; p.BeginPath(); p.MoveTo(c + new Vector2(-s, -s)); p.LineTo(c + new Vector2(s, -s)); p.LineTo(c + new Vector2(s, s)); p.LineTo(c + new Vector2(-s, s)); p.ClosePath(); p.Fill();
            p.strokeColor = new Color(0f, 0f, 0f, 0.7f); p.lineWidth = 1f; p.Stroke();
            if (z.capF >= 0 && z.capP > 0f)
            {
                p.strokeColor = game.armies[z.capF].color; p.lineWidth = 1.5f;
                p.BeginPath(); p.Arc(c, s + 3f, Angle.Degrees(-90f), Angle.Degrees(-90f + 360f * z.capP / 100f), ArcDirection.Clockwise); p.Stroke();
            }
        }
        // units
        foreach (var u in game.units)
        {
            if (!u.alive) continue;
            var c = ToMap(u.Pos); var col = game.armies[u.army].color; if (u.selected) col = Color.white;
            float s = u.infantry ? 1.1f : 1.7f;
            p.fillColor = col; p.BeginPath(); p.MoveTo(c + new Vector2(-s, -s)); p.LineTo(c + new Vector2(s, -s)); p.LineTo(c + new Vector2(s, s)); p.LineTo(c + new Vector2(-s, s)); p.ClosePath(); p.Fill();
        }
        // pings
        for (int i = pings.Count - 1; i >= 0; i--)
        {
            float a = (Time.unscaledTime - pings[i].t0) / 4f; if (a >= 1f) { pings.RemoveAt(i); continue; }
            var c = ToMap(pings[i].at);
            p.strokeColor = new Color(1f, 0.82f, 0.35f, 1f - a); p.lineWidth = 1.5f;
            p.BeginPath(); p.Arc(c, 3f + 9f * ((a * 3f) % 1f), Angle.Degrees(0f), Angle.Degrees(360f)); p.Stroke();
        }
        // what the camera sees: the screen's corners on the ground
        if (cam)
        {
            var pts = new List<Vector2>();
            foreach (var sp in new[] { new Vector2(0, 0), new Vector2(Screen.width, 0), new Vector2(Screen.width, Screen.height), new Vector2(0, Screen.height) })
            {
                var ray = cam.ScreenPointToRay(sp); var pl = new Plane(Vector3.up, Vector3.zero);
                if (!pl.Raycast(ray, out float t) || t > 6000f) t = 6000f;
                pts.Add(ToMap(ray.GetPoint(t)));
            }
            p.strokeColor = new Color(1f, 1f, 1f, 0.9f); p.lineWidth = 1.2f;
            p.BeginPath(); p.MoveTo(pts[0]); for (int i = 1; i < 4; i++) p.LineTo(pts[i]); p.ClosePath(); p.Stroke();
        }
    }
}

/// a 0..1 slider: a track, the filled part and a knob; click or drag anywhere on it
public class DawgsSlider : VisualElement
{
    public float value;
    readonly Action<float> onChange;
    readonly VisualElement fill, knob;
    bool dragging;

    public DawgsSlider(float v, Action<float> changed)
    {
        onChange = changed; AddToClassList("vol-slider"); pickingMode = PickingMode.Position;
        var track = new VisualElement(); track.AddToClassList("vol-track"); track.pickingMode = PickingMode.Ignore; Add(track);
        fill = new VisualElement(); fill.AddToClassList("vol-fill"); fill.pickingMode = PickingMode.Ignore; track.Add(fill);
        knob = new VisualElement(); knob.AddToClassList("vol-knob"); knob.pickingMode = PickingMode.Ignore; Add(knob);
        Show(v);
        RegisterCallback<PointerDownEvent>(e => { dragging = true; this.CapturePointer(e.pointerId); Pick(e.localPosition.x); e.StopPropagation(); });
        RegisterCallback<PointerMoveEvent>(e => { if (dragging) Pick(e.localPosition.x); });
        RegisterCallback<PointerUpEvent>(e => { if (dragging) { dragging = false; this.ReleasePointer(e.pointerId); } });
    }

    void Pick(float x)
    {
        float w = layout.width; if (w < 2f) return;
        float v = Mathf.Round(Mathf.Clamp01(x / w) * 100f) / 100f;
        if (Mathf.Approximately(v, value)) return;
        Show(v); onChange?.Invoke(v);
    }

    void Show(float v)
    {
        value = Mathf.Clamp01(v);
        fill.style.width = Length.Percent(value * 100f);
        knob.style.left = Length.Percent(value * 100f);
    }
}
