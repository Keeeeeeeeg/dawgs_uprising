// Dawgs Uprising -> Unity: the browser game's battle HUD in UI Toolkit, laid out and styled after its HTML / CSS
// (UI/DawgsHud.uss holds the CSS port; the panels' cut corners are drawn by DawgsPanel).
//   top bar: brand, funds, manpower, zones held, clock, menu, speed · right: armies · left: messages
//   bottom bar: ping/draw/erase + minimap | the selection | the command card (orders or recruit) + the footer strip
//   over the battlefield: health bars, zone banners, the drag box, toasts; Esc opens the pause menu
using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.TextCore.Text;
using UnityEngine.UIElements;

[RequireComponent(typeof(UIDocument))]
public class DawgsHud : MonoBehaviour
{
    public DawgsGame game;
    public DawgsCommand cmd;
    public StyleSheet style;

    UIDocument doc; VisualElement root; Camera cam;
    FontDefinition fBody, fDisplay, fMono;
    bool built;

    // top bar
    Label funds, fundsEm, manp, manpEm, zonesN, zonesSub, clock; readonly List<VisualElement> speedBtns = new List<VisualElement>();
    static readonly float[] Speeds = { 0f, 1f, 2f, 3f };
    int speedIdx = 1, lastSpeedIdx = 1;
    // armies / messages
    VisualElement facList, logBody; readonly List<(VisualElement row, Label ct, Label sub)> facRows = new List<(VisualElement, Label, Label)>();
    int logShown = -1;
    // bottom bar
    DawgsMinimap mini; VisualElement selHead, selBody, cardTabs, cardTop, cardGrid, gstrip, pingBtn; Label cardHint;
    string selSig = "", cardSig = ""; string cardMode = "";   // "orders" / "recruit"
    bool cardForced;
    int deployIdx, recruitFac;
    readonly List<(string type, VisualElement tile, Label q, VisualElement pb)> recruitTiles = new List<(string, VisualElement, Label, VisualElement)>();
    readonly List<(DawgsIcon ic, VisualElement btn, Func<bool> on)> orderBtns = new List<(DawgsIcon, VisualElement, Func<bool>)>();
    VisualElement ucHpFill; Label ucHpText, ucStatus;
    readonly List<(VisualElement fill, string type)> tileHp = new List<(VisualElement, string)>();
    // overlays
    VisualElement hpLayer, zoneLayer, selRect; Label toast; float toastUntil;
    readonly List<VisualElement> hpPool = new List<VisualElement>();
    readonly Dictionary<DawgsGame.Zone, (VisualElement box, Label kick, VisualElement sq, Label nm, VisualElement capF, Label sub, VisualElement nbox)> zoneTags = new Dictionary<DawgsGame.Zone, (VisualElement, Label, VisualElement, Label, VisualElement, Label, VisualElement)>();
    // menus
    VisualElement modalBg; bool modalOpen, endShown;
    // overlays that don't pause the battle: the scoreboard (Tab) and the full-screen map (M)
    VisualElement overlayBg, scoreBody; string overlay = ""; DawgsMinimap bigMap; Label scoreStats;
    public bool OverlayOpen => overlay != "";
    public bool ModalOpen => modalOpen;
    float refreshT, miniT;

    static Color Hex(string h) { ColorUtility.TryParseHtmlString(h, out var c); return c; }
    static readonly Color Militia = Hex("#7cc94f"), Dim = Hex("#a39c84"), Text = Hex("#ece6d2"), Bad = Hex("#ff5a40"), Warn = Hex("#ffd25a"), Ink = Hex("#12150e");

    void Start()
    {
        doc = GetComponent<UIDocument>(); cam = Camera.main;
        if (!game) game = FindFirstObjectByType<DawgsGame>();
        if (!cmd) cmd = FindFirstObjectByType<DawgsCommand>();
        LoadFonts();
        Build();
        game.OnToast += Toast;
        DawgsRtsCamera.PointerBlocked = OverUI;   // the wheel over the HUD doesn't zoom the map
    }

    void OnDestroy() { if (DawgsRtsCamera.PointerBlocked == (Func<Vector2, bool>)OverUI) DawgsRtsCamera.PointerBlocked = null; }

    void LoadFonts()
    {
        FontAsset Sys(string fam, string st) { try { return FontAsset.CreateFontAsset(fam, st, 90); } catch { return null; } }
        var legacy = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        var bahn = Sys("Bahnschrift", "Regular"); var cons = Sys("Consolas", "Regular");
        var sym = Sys("Segoe UI Symbol", "Regular");   // glyphs the game's fonts lack (⇧, ▾, ‹ ›)
        if (sym != null)
        {
            if (bahn != null) bahn.fallbackFontAssetTable = new List<FontAsset> { sym };
            if (cons != null) cons.fallbackFontAssetTable = new List<FontAsset> { sym };
        }
        fDisplay = bahn ? FontDefinition.FromSDFFont(bahn) : FontDefinition.FromFont(legacy);
        fBody = fDisplay;
        fMono = cons ? FontDefinition.FromSDFFont(cons) : fDisplay;
    }

    // ---------------------------------------------------------------- building blocks
    enum F { Body, Display, Mono }
    Label L(string text, string cls, VisualElement parent = null, F font = F.Body)
    {
        var l = new Label(text);
        if (!string.IsNullOrEmpty(cls)) foreach (var c in cls.Split(' ')) l.AddToClassList(c);
        if (font == F.Display) l.style.unityFontDefinition = fDisplay; else if (font == F.Mono) l.style.unityFontDefinition = fMono;
        parent?.Add(l); return l;
    }
    static VisualElement E(string cls = null, VisualElement parent = null, string name = null)
    {
        var e = new VisualElement(); if (name != null) e.name = name;
        if (!string.IsNullOrEmpty(cls)) foreach (var c in cls.Split(' ')) e.AddToClassList(c);
        parent?.Add(e); return e;
    }
    static VisualElement Btn(VisualElement el, Action<bool> click)
    {
        el.pickingMode = PickingMode.Position;
        el.RegisterCallback<ClickEvent>(e => { click(e.shiftKey); e.StopPropagation(); });
        return el;
    }
    static void Show(VisualElement e, bool on) { e.style.display = on ? DisplayStyle.Flex : DisplayStyle.None; }

    // ---------------------------------------------------------------- the HUD
    void Build()
    {
        speedBtns.Clear(); facRows.Clear(); hpPool.Clear(); zoneTags.Clear(); recruitTiles.Clear(); orderBtns.Clear(); tileHp.Clear();
        selSig = ""; cardSig = ""; logShown = -1; cardTop = null;
        root = doc.rootVisualElement; root.Clear();
        if (style) root.styleSheets.Add(style);
        root.AddToClassList("hud-root"); root.pickingMode = PickingMode.Ignore;
        root.style.unityFontDefinition = fBody;

        zoneLayer = E("layer", root); zoneLayer.pickingMode = PickingMode.Ignore;
        hpLayer = E("layer", root); hpLayer.pickingMode = PickingMode.Ignore;

        BuildTop(); BuildArmies(); BuildLog(); BuildBottom();

        selRect = E(null, root, "selRect"); selRect.pickingMode = PickingMode.Ignore; Show(selRect, false);
        toast = L("", null, root, F.Display); toast.name = "toast"; toast.pickingMode = PickingMode.Ignore;

        overlayBg = E("overlay-bg", root); Show(overlayBg, false); overlay = "";
        modalBg = E("modal-bg", root); Show(modalBg, false);
        foreach (var z in game.zones) MakeZoneTag(z);
        built = true; refreshT = 0f;
    }

    void BuildTop()
    {
        var top = new DawgsPanel { name = "top" }; root.Add(top);
        var c0 = E("cell", top); L("DAWGS", "brand", c0, F.Display); L("UPRISING", "brand-small", c0, F.Display);
        VisualElement Stat(string head, out Label v, out Label em)
        {
            var c = E("cell", top); L(head, "cell-head", c, F.Display);
            var r = E("stat-row", c); v = L("", "stat", r, F.Mono); em = L("", "stat-em", r, F.Mono); return c;
        }
        Stat("FUNDS", out funds, out fundsEm);
        Stat("MANPOWER", out manp, out manpEm);
        Stat("ZONES HELD", out zonesN, out zonesSub); zonesSub.RemoveFromClassList("stat-em"); zonesSub.AddToClassList("stat-dim");
        Stat("CLOCK", out clock, out var _);
        var cm = E("cell", top);
        var mb = Btn(E("btn-outline", cm), _ => TogglePause()); L("MENU", "btn-label", mb, F.Display); L("ESC", "kbd", mb, F.Mono);
        var cs = E("cell cell-last", top); L("SPEED", "cell-head", cs, F.Display);
        var row = E("ctl-row", cs);
        string[] lab = { "II", "1×", "2×", "3×" };
        for (int i = 0; i < 4; i++) { int k = i; var b = Btn(L(lab[i], "ctl-btn", row, F.Mono), _ => SetSpeed(k)); speedBtns.Add(b); }
    }

    void BuildArmies()
    {
        var right = new DawgsPanel { name = "right" }; root.Add(right);
        var head = Btn(E("panel-head", right), _ => Show(facList, facList.resolvedStyle.display == DisplayStyle.None));
        L("ARMIES", "panel-title", head, F.Display); L("▾", "fold", head);
        facList = E(null, right);
        for (int i = 0; i < game.armies.Count; i++)
        {
            var A = game.armies[i];
            var row = E(i == 0 ? "fac fac-first" : "fac", facList);
            var sw = new DawgsFlag(A.color); sw.AddToClassList("fac-sw"); row.Add(sw);
            var main = E("fac-main", row);
            var r1 = E("fac-row", main); var nm = L(A.name, "fac-nm", r1, F.Display); nm.style.color = A.color; var ct = L("", "fac-ct", r1, F.Mono);
            var r2 = E("fac-row", main); var sub = L("", "fac-sub", r2);
            if (i != game.player) L("vs you", "fac-vs", r2);
            facRows.Add((row, ct, sub));
        }
    }

    void BuildLog()
    {
        var log = new DawgsPanel { name = "log" }; root.Add(log);
        var head = Btn(E("panel-head", log), _ => Show(logBody, logBody.resolvedStyle.display == DisplayStyle.None));
        L("MESSAGES", "panel-title", head, F.Display); L("▾", "fold", head);
        logBody = E(null, log);
    }

    void BuildBottom()
    {
        var bar = new DawgsPanel { name = "cmd" }; root.Add(bar);
        // minimap and the map tools
        var mapBox = E(null, bar, "mapBox");
        var mbtn = E("map-btns", mapBox);
        pingBtn = Btn(E("tool-btn tool-ping", mbtn), _ => cmd.SetArmed(cmd.armed == DawgsCommand.Armed.Ping ? DawgsCommand.Armed.None : DawgsCommand.Armed.Ping));
        L("PING", null, pingBtn, F.Display); L(" I", null, pingBtn, F.Mono); pingBtn.style.flexDirection = FlexDirection.Row;
        var draw = E("tool-btn tool-draw off", mbtn); draw.style.flexDirection = FlexDirection.Row; L("DRAW", null, draw, F.Display); L(" `", null, draw, F.Mono);
        var erase = E("tool-btn tool-erase off", mbtn); L("ERASE", null, erase, F.Display);
        var wrap = E("mini-wrap", mapBox);
        mini = new DawgsMinimap(game) { cam = cam }; mini.style.overflow = Overflow.Hidden;
        mini.onJump = w => { cmd.JumpTo(w); return true; };
        wrap.Add(mini);
        // selection
        var selBox = E(null, bar, "selBox");
        selHead = E("sel-head", selBox); selBody = E(null, selBox);
        // command card
        var card = E(null, bar, "card");
        cardTabs = E(null, card, "cardTabs");
        cardGrid = E(null, card, "cardGrid");
        cardGrid.RegisterCallback<GeometryChangedEvent>(_ => FitCardGrid());   // a resized window or panel refits the tiles
        cardHint = L("", null, card); cardHint.name = "cardHint";
        gstrip = E("gstrip", card);
        var ms = E("gs-btn off", gstrip); L("MISSILE", null, ms, F.Display); L("0", "gs-b", ms, F.Mono); L("NO SILO", "gs-b", ms, F.Display); L("Q", "gs-b", ms, F.Mono);
        var auto = E("gs-auto", gstrip); E("gs-chk", auto); L("Auto", "sel-dim", auto);
        E("gs-btn off", gstrip).Add(L("RALLY ALL", null, null, F.Display));
        Btn(E("gs-btn", gstrip), _ => cmd.SelectAllMilitary()).Add(L("ALL MILITARY", null, null, F.Display));
        E("gs-btn off", gstrip).Add(L("ALL BUILDERS", null, null, F.Display));
        E("gs-btn off", gstrip).Add(L("ALL AIRCRAFT", null, null, F.Display));
    }

    void MakeZoneTag(DawgsGame.Zone z)
    {
        var box = E("zl", zoneLayer); box.pickingMode = PickingMode.Ignore;
        var kick = L("", "zl-k", box, F.Display);
        var nbox = E("zl-n", box); var sq = E("zl-sq", nbox); var nm = L(z.name.ToUpperInvariant(), "zl-nt", nbox, F.Display);
        var cap = E("zl-cap", box); var capF = E("zl-capf", cap);
        var sub = L("", "zl-sub", box, F.Display);
        foreach (var e in box.Query<VisualElement>().ToList()) e.pickingMode = PickingMode.Ignore;
        zoneTags[z] = (box, kick, sq, nm, capF, sub, nbox);
    }

    // ---------------------------------------------------------------- per frame
    void Update()
    {
        if (!built || !game || game.R == null) return;                     // (after a script reload in Play mode the battle has stopped)
        if (doc.rootVisualElement != root) { built = false; Build(); }
        if (!cam) { cam = Camera.main; mini.cam = cam; }
        UpdateHpBars();
        UpdateZoneTags();
        if (Time.unscaledTime > toastUntil && toast.ClassListContains("on")) toast.RemoveFromClassList("on");
        miniT -= Time.unscaledDeltaTime; if (miniT <= 0f) { miniT = 0.1f; mini.MarkDirtyRepaint(); if (bigMap != null) { bigMap.cam = cam; bigMap.MarkDirtyRepaint(); } }
        refreshT -= Time.unscaledDeltaTime;
        if (refreshT <= 0f)
        {
            refreshT = 0.15f;
            RefreshTop(); RefreshArmies(); RefreshLog(); RefreshSelection(); RefreshCard();
            if (overlay == "score") FillScore();
            pingBtn.EnableInClassList("on", cmd.armed == DawgsCommand.Armed.Ping);
        }
        if (game.over && !endShown) ShowEnd();
    }

    static string Clock(float t) { int s = Mathf.FloorToInt(t); return $"{s / 60:00}:{s % 60:00}"; }

    void RefreshTop()
    {
        var A = game.armies[game.player];
        funds.text = $"${Mathf.FloorToInt(A.money)}"; fundsEm.text = $"+{A.incomeSec:0.0}/s";
        manp.text = $"{Mathf.FloorToInt(A.manpower)}"; manpEm.text = $"+{A.mpMin:0}/min";
        zonesN.text = game.zones.Count(z => z.owner == game.player).ToString(); zonesSub.text = $"/ {game.zones.Count} to win";
        clock.text = Clock(game.time);
        for (int i = 0; i < speedBtns.Count; i++) speedBtns[i].EnableInClassList("on", i == speedIdx);
    }

    void RefreshArmies()
    {
        for (int i = 0; i < facRows.Count; i++)
        {
            var A = game.armies[i]; var (row, ct, sub) = facRows[i];
            int zn = game.zones.Count(z => z.owner == i), un = game.units.Count(u => u.alive && u.army == i);
            ct.text = $"{zn}z · {un}u"; sub.text = $"{A.kills} kills · {A.losses} lost";
            row.EnableInClassList("dead", !A.alive);
        }
    }

    void RefreshLog()
    {
        if (logShown == game.messages.Count && game.messages.Count > 0) return;
        logShown = game.messages.Count; logBody.Clear();
        foreach (var m in game.messages.Skip(Math.Max(0, game.messages.Count - 7)))
        {
            var row = E("log-line", logBody);
            L(Clock(m.t), "log-t", row, F.Mono);
            var x = L(m.text, m.alert ? "log-x log-alert" : "log-x", row);
            if (!m.alert && m.army >= 0) x.style.color = game.armies[m.army].color;
        }
    }

    // ---------------------------------------------------------------- the selection box
    public void SelectionChanged() { selSig = ""; cardSig = ""; if (!cardForced) cardMode = ""; }

    void RefreshSelection()
    {
        var sel = game.selection;
        string sig = sel.Count + ":" + string.Join(",", sel.Take(40).Select(u => u.id));
        if (sig == selSig) { UpdateSelectionLive(); return; }
        selSig = sig; selHead.Clear(); selBody.Clear(); tileHp.Clear(); ucHpFill = null;
        if (sel.Count == 0)
        {
            L("Command", "sel-b", selHead, F.Display); L("Nothing selected", "sel-dim", selHead);
            L("Drag a box around your units, or click one. Recruit at your bases on the right.", "hint", selBody);
            void Tip(string k, string v) { var r = E("tip-row", selBody); L(k, "tip-k", r, F.Mono); L(v, "tip-v", r); }
            Tip("Right-click", "move / attack · right-drag to spread along a line");
            Tip("F", "fight-move"); Tip("H", "halt"); Tip("G", "guard one of your units");
            Tip("Shift+1–9", "save a control group, 1–9 to recall it");
            Tip("Space", "jump home");
            Tip("Middle drag", DawgsPrefs.MidPan ? "pan the camera (Shift: orbit)" : "orbit the camera (Shift: pan)");
            Tip("Tab", "scoreboard"); Tip("M", "full-screen map"); Tip("Ctrl+A", "all military units");
            return;
        }
        if (sel.Count == 1)
        {
            var u = sel[0]; var A = game.armies[u.army];
            var nm = L(u.def.name, "sel-b", selHead, F.Display); nm.style.color = A.color;
            L(u.army == game.player ? "" : A.name, "sel-dim", selHead);
            L(ClassName(u.def).ToUpperInvariant(), "uc-cls", selBody, F.Display);
            var hp = E("uc-hp", selBody); ucHpFill = E("uc-hpf", hp); ucHpText = L("", "uc-hpt", hp, F.Mono);
            var sx = E("sx-row", selBody);
            void Sx(string v, string s) { var b = E("sx", sx); L(v, "sx-b", b, F.Mono); L(s, "sx-s", b, F.Display); }
            Sx($"{u.def.dmg:0.#}", "DAMAGE"); Sx($"{u.def.range:0}", "RANGE"); Sx($"{u.def.speed:0.#}", "SPEED"); Sx($"{game.R.ArmorOf(u.def):0}", "ARMOUR");
            ucStatus = L("", "hint", selBody);
            UpdateSelectionLive();
            return;
        }
        L($"× {sel.Count}", "sel-b", selHead, F.Display); L("units selected", "sel-txt", selHead);
        L("Click a type to keep only those · Shift-click to drop them", "hint", selBody);
        var tiles = E("tiles", selBody);
        foreach (var g in sel.GroupBy(u => u.type).OrderByDescending(g => g.Count()))
        {
            string type = g.Key;
            var t = Btn(E("utile", tiles), shift =>
            {
                var keep = shift ? game.selection.Where(u => u.type != type).ToList() : game.selection.Where(u => u.type == type).ToList();
                cmd.Select(keep);
            });
            var th = game.ThumbOf(type); if (th) t.style.backgroundImage = new StyleBackground(th);
            L(g.First().def.name, "utile-n", t, F.Display); L($"× {g.Count()}", "utile-c", t, F.Mono);
            var hpb = E("utile-hp", t); var f = E("utile-hpf", hpb); tileHp.Add((f, type));
            foreach (var c in t.Children()) c.pickingMode = PickingMode.Ignore;
        }
        UpdateSelectionLive();
    }

    static string ClassName(DGUnitDef d) => d.armor == "inf" ? "Infantry" : d.armor == "hvy" ? "Heavy armour" : d.armor == "veh" ? "Vehicle" : d.armor;

    void UpdateSelectionLive()
    {
        var sel = game.selection;
        if (ucHpFill != null && sel.Count == 1)
        {
            var u = sel[0]; float k = Mathf.Clamp01(u.hp / u.maxHp);
            ucHpFill.style.width = Length.Percent(k * 100f); ucHpText.text = $"{Mathf.CeilToInt(u.hp)} / {u.maxHp:0}";
            ucHpFill.style.backgroundColor = k > 0.5f ? new Color(0.31f, 0.54f, 0.2f) : k > 0.25f ? new Color(0.6f, 0.5f, 0.15f) : new Color(0.6f, 0.2f, 0.12f);
            if (ucStatus != null)
            {
                string o = u.Guarding ? $"Guarding the {u.guardOf.def.name}" : u.hasArea ? "Attacking the area" : u.form != null ? (u.form.marching ? "Marching in formation" : "Forming up")
                    : u.order == DOrder.Move ? "Moving" : u.order == DOrder.Fight ? "Fight-moving" : u.order == DOrder.Attack ? "Attacking" : u.target ? "Engaging" : "Idle";
                string s = u.stance == DStance.Aggressive ? "Aggressive" : u.stance == DStance.Hold ? "Hold ground" : "Return fire";
                ucStatus.text = u.army == game.player ? $"{o} · {s}" : "Enemy unit";
            }
        }
        foreach (var (fill, type) in tileHp)
        {
            var us = sel.Where(u => u.type == type).ToList(); if (us.Count == 0) continue;
            float k = us.Sum(u => u.hp) / us.Sum(u => u.maxHp);
            fill.style.width = Length.Percent(k * 100f);
        }
    }

    // ---------------------------------------------------------------- the command card
    DawgsGame.Zone DeployZone()
    {
        var own = game.zones.Where(z => z.owner == game.player).ToList();
        if (own.Count == 0) return null;
        deployIdx = ((deployIdx % own.Count) + own.Count) % own.Count;
        return own[deployIdx];
    }

    void RefreshCard()
    {
        bool own = cmd.OwnSelection;
        string mode = cardMode != "" ? cardMode : own ? "orders" : "recruit";
        if (!own && mode == "orders") mode = "recruit";
        var dz = DeployZone();
        string sig = mode + "|" + selSig + "|" + (dz != null ? dz.name : "-") + "|" + cmd.armed;
        if (sig != cardSig)
        {
            cardSig = sig; cardTabs.Clear(); cardGrid.Clear(); recruitTiles.Clear(); orderBtns.Clear();
            if (own) Btn(L("ORDERS", mode == "orders" ? "tab on" : "tab", cardTabs, F.Display), _ => { cardMode = "orders"; cardForced = true; });
            Btn(L("RECRUIT", mode == "recruit" ? "tab on" : "tab", cardTabs, F.Display), _ => { cardMode = "recruit"; cardForced = own; });
            if (mode == "orders") BuildOrders(); else BuildRecruit(dz);
            cardGrid.schedule.Execute(FitCardGrid);                          // once the new tiles have been laid out
        }
        // live state
        foreach (var (ic, btn, on) in orderBtns) { bool o = on(); btn.EnableInClassList("on", o); ic.SetColor(o ? Ink : Militia); }
        if (mode == "recruit") UpdateRecruit(dz);
        else
        {
            int n = game.selection.Count(u => u.alive && u.army == game.player && u.Military);
            cardHint.text = cmd.armed == DawgsCommand.Armed.Fight ? "Fight-move: click where to go. Units stop for anything they meet on the way."
                : cmd.armed == DawgsCommand.Armed.Guard ? "Guard: click one of your units. The selection follows it and fights off whatever threatens it."
                : $"Stance applies to {n} ground unit{(n == 1 ? "" : "s")}. Right-click to move or attack.";
        }
    }

    // ---------------------------------------------------------------- tiles that fill the card
    // like the browser's fitCardGrid: when the card has room to spare (a few units or orders on a wide screen) its tiles
    // grow to fill it, pictures, icons and text with them; with many tiles they keep their usual size
    const float CbGap = 4f, CbMaxH = 230f, CbMinAspect = 0.95f, CbMaxAspect = 2.3f;
    static readonly Dictionary<string, float> CbFont = new Dictionary<string, float>
    { { "rt-n", 9.5f }, { "rt-k", 10.5f }, { "rt-c", 10f }, { "rt-q", 11f }, { "cb-n", 13f }, { "cb-k", 9.5f } };

    void FitCardGrid()
    {
        var g = cardGrid; if (g == null || g.panel == null) return;
        var tiles = g.Children().Where(e => e.ClassListContains("rt") || e.ClassListContains("cb")).ToList();
        foreach (var t in tiles) SizeTile(t, -1f, -1f, 1f, 1f);
        float W = g.contentRect.width, H = g.contentRect.height;
        if (tiles.Count == 0 || float.IsNaN(W) || float.IsNaN(H) || W < 60f || H < 40f) return;
        bool rt = tiles[0].ClassListContains("rt");
        float bw = 104f, bh = rt ? 66f : 70f;
        float fixedH = 0f;
        foreach (var e in g.Children()) if (!tiles.Contains(e)) fixedH += e.layout.height + e.resolvedStyle.marginTop + e.resolvedStyle.marginBottom;
        int n = tiles.Count; float Ha = H - fixedH, bestW = 0f, bestH = 0f, bestA = 0f;
        for (int cols = 1; cols <= n; cols++)
        {
            int rows = Mathf.CeilToInt(n / (float)cols);
            float colW = (W - cols * CbGap) / cols - 0.5f; if (colW < bw) break;
            float h = Mathf.Min((Ha - rows * CbGap) / rows, colW / CbMinAspect, CbMaxH); if (h < bh) continue;
            float w = Mathf.Min(colW, h * (rt ? 1.9f : CbMaxAspect)), a = w * h;   // unit pictures fill their tile, so don't let it get too wide
            if (a > bestA + 1f) { bestA = a; bestW = w; bestH = h; }
        }
        if (bestA <= 0f || (bestH < bh * 1.08f && bestW < bw * 1.25f)) return;
        float k = Mathf.Min(2.6f, bestH / bh), f = 1f + (k - 1f) * 0.45f;
        foreach (var t in tiles) SizeTile(t, Mathf.Floor(bestW), Mathf.Floor(bestH), k, f);
    }

    /// w < 0: back to the stylesheet's size
    static void SizeTile(VisualElement t, float w, float h, float k, float f)
    {
        t.style.width = w < 0f ? new StyleLength(StyleKeyword.Null) : new StyleLength(w);
        t.style.height = h < 0f ? new StyleLength(StyleKeyword.Null) : new StyleLength(h);
        foreach (var c in t.Children())
        {
            if (c is DawgsIcon)
            {
                c.style.width = w < 0f ? new StyleLength(StyleKeyword.Null) : new StyleLength(30f * k);
                c.style.height = w < 0f ? new StyleLength(StyleKeyword.Null) : new StyleLength(20f * k);
                c.MarkDirtyRepaint();
                continue;
            }
            foreach (var kv in CbFont)
                if (c.ClassListContains(kv.Key)) { c.style.fontSize = w < 0f ? new StyleLength(StyleKeyword.Null) : new StyleLength(kv.Value * f); break; }
            if (c.ClassListContains("rt-pb")) c.style.height = w < 0f ? new StyleLength(StyleKeyword.Null) : new StyleLength(4f * f);
        }
    }

    void OrderButton(string name, string key, DawgsIcon.Kind kind, Func<bool> on, Action click, bool enabled = true)
    {
        var b = E(enabled ? "cb" : "cb off", cardGrid);
        var ic = new DawgsIcon(kind); b.Add(ic);
        L(name, "cb-n", b, F.Display);
        if (!string.IsNullOrEmpty(key)) L(key, "cb-k", b, F.Mono);
        foreach (var c in b.Children()) c.pickingMode = PickingMode.Ignore;
        if (enabled) { Btn(b, _ => click()); orderBtns.Add((ic, b, on)); }
        else ic.SetColor(Dim);
    }

    void BuildOrders()
    {
        var sel = game.selection;
        bool All(DStance s) => sel.Count > 0 && sel.All(u => u.stance == s);
        OrderButton("Fight", "F", DawgsIcon.Kind.Fight, () => cmd.armed == DawgsCommand.Armed.Fight, () => cmd.SetArmed(cmd.armed == DawgsCommand.Armed.Fight ? DawgsCommand.Armed.None : DawgsCommand.Armed.Fight));
        OrderButton("Halt", "H", DawgsIcon.Kind.Halt, () => false, () => { game.OrderHalt(game.selection); Toast("Halt"); });
        OrderButton("Guard", "G", DawgsIcon.Kind.Guard, () => cmd.armed == DawgsCommand.Armed.Guard, () => cmd.SetArmed(cmd.armed == DawgsCommand.Armed.Guard ? DawgsCommand.Armed.None : DawgsCommand.Armed.Guard));
        OrderButton("Aggressive", "", DawgsIcon.Kind.Aggressive, () => All(DStance.Aggressive), () => game.SetStance(game.selection, DStance.Aggressive));
        OrderButton("Hold ground", "", DawgsIcon.Kind.Hold, () => All(DStance.Hold), () => game.SetStance(game.selection, DStance.Hold));
        OrderButton("Return fire", "", DawgsIcon.Kind.ReturnFire, () => All(DStance.ReturnFire), () => game.SetStance(game.selection, DStance.ReturnFire));
        OrderButton("Wave the flag", "Y", DawgsIcon.Kind.Flag, () => false, null, false);
        OrderButton("Unload", "", DawgsIcon.Kind.Unload, () => false, null, false);
        OrderButton("Man walls", "", DawgsIcon.Kind.Walls, () => false, null, false);
    }

    void BuildRecruit(DawgsGame.Zone dz)
    {
        if (cardTop != null) cardTop.RemoveFromHierarchy();
        cardTop = E("card-top", cardTabs);
        L("DEPLOY AT", "card-top-l", cardTop, F.Display);
        Btn(L("‹", "arrow-btn", cardTop, F.Display), _ => { deployIdx--; cardSig = ""; });
        L(dz != null ? dz.name : "No base", "card-top-b", cardTop, F.Display);
        Btn(L("›", "arrow-btn", cardTop, F.Display), _ => { deployIdx++; cardSig = ""; });
        // the browser lists units by the building that trains them: one building's units at a time
        var tabs = E("fac-tabs", cardGrid);
        for (int fi = 0; fi < DawgsGame.RecruitGroups.Length; fi++)
        {
            int k = fi; var g = DawgsGame.RecruitGroups[fi];
            var tb = Btn(E(fi == recruitFac ? "fac-tab on" : "fac-tab", tabs), _ => { recruitFac = k; cardSig = ""; });
            L(g[0].ToUpperInvariant(), null, tb, F.Display); L($"{g.Length - 1} units", "fac-tab-n", tb);
            foreach (var c in tb.Children()) c.pickingMode = PickingMode.Ignore;
        }
        {
            var grp = DawgsGame.RecruitGroups[Mathf.Clamp(recruitFac, 0, DawgsGame.RecruitGroups.Length - 1)];
            for (int i = 1; i < grp.Length; i++)
            {
                string type = grp[i]; if (!game.R.unit.TryGetValue(type, out var d)) continue;
                var t = Btn(E("rt", cardGrid), _ => TrainHere(type));
                var th = game.ThumbOf(type); if (th) t.style.backgroundImage = new StyleBackground(th);
                L(d.hot, "rt-k", t, F.Mono); L(d.name, "rt-n", t, F.Display); L($"${d.cost:0}·{d.mp:0}", "rt-c", t, F.Mono);
                var q = L("", "rt-q", t, F.Mono); var pb = E("rt-pb", t);
                foreach (var c in t.Children()) c.pickingMode = PickingMode.Ignore;
                recruitTiles.Add((type, t, q, pb));
            }
        }
    }

    void UpdateRecruit(DawgsGame.Zone dz)
    {
        foreach (var (type, tile, q, pb) in recruitTiles)
        {
            tile.EnableInClassList("off", !game.CanRecruit(game.player, type, out _));
            int n = dz != null ? dz.queue.Count(x => x.type == type) : 0;
            q.text = n > 0 ? $"×{n}" : "";
            var head = dz != null && dz.queue.Count > 0 && dz.queue[0].type == type ? dz.queue[0] : null;
            pb.style.width = Length.Percent(head != null ? (1f - head.left / head.total) * 100f : 0f);
        }
        if (dz == null) { cardHint.text = "You hold no bases to recruit at."; return; }
        cardHint.text = dz.queue.Count == 0
            ? $"Units train at {dz.name} and walk out to the front. Hotkeys train from anywhere."
            : $"Training at {dz.name}: " + string.Join(", ", dz.queue.Select((x, i) => i == 0 ? $"{game.R.unit[x.type].name} {Mathf.CeilToInt(x.left)}s" : game.R.unit[x.type].name));
    }

    public void TrainHere(string type)
    {
        var dz = DeployZone();
        if (dz == null) { Toast("You hold no bases to recruit at", true); return; }
        if (game.Recruit(game.player, type, dz)) Toast($"{game.R.unit[type].name} queued at {dz.name}");
    }

    // ---------------------------------------------------------------- overlays
    // Health bars, as the browser draws them: over every unit (Settings: "Always show unit health bars"), or only over
    // selected and damaged ones. They grow as you zoom in (1x at the default view, up to 2.6x up close). Enemy bars are
    // red; yours go green, amber, red as they take damage. A small square in the army's colour sits to the left.
    static readonly Color HpBack = new Color(0, 0, 0, 0.65f), SqBack = new Color(0, 0, 0, 0.75f), HpFoe = Hex("#ff3b2e"),
        HpGood = Hex("#5fe08a"), HpMid = Hex("#ffb22e"), HpLow = Hex("#ff4b3a");
    readonly Dictionary<string, float> modelTop = new Dictionary<string, float>();

    VisualElement HpBar()
    {
        var w = E(null, hpLayer); w.pickingMode = PickingMode.Ignore;
        w.style.position = Position.Absolute; w.style.width = 0; w.style.height = 0;
        for (int i = 0; i < 4; i++) { var c = E(null, w); c.pickingMode = PickingMode.Ignore; c.style.position = Position.Absolute; }
        w[0].style.backgroundColor = HpBack; w[2].style.backgroundColor = SqBack;   // [0] bar back, [1] fill, [2] square back, [3] square
        hpPool.Add(w); return w;
    }

    static void Rect(VisualElement e, float x, float y, float w, float h) { e.style.left = x; e.style.top = y; e.style.width = w; e.style.height = h; }

    // height of a unit type's model above its feet (from its renderers, once), so bars sit just over the model
    float TopOf(DawgsUnit u)
    {
        if (modelTop.TryGetValue(u.type, out float t)) return t;
        float top = 0f; bool any = false;
        foreach (var r in u.GetComponentsInChildren<Renderer>())
        {
            if (u.ring && r.transform.IsChildOf(u.ring.transform)) continue;
            top = Mathf.Max(top, r.bounds.max.y - u.transform.position.y); any = true;
        }
        if (!any) return u.infantry ? 0.9f : 1.6f;
        return modelTop[u.type] = top;
    }

    void UpdateHpBars()
    {
        int k = 0;
        var rc = cam ? cam.GetComponent<DawgsRtsCamera>() : null;
        float HS = Mathf.Clamp(110f / Mathf.Max(1f, rc ? rc.distance : 110f), 0.85f, 2.6f);
        bool always = DawgsPrefs.HpAlways;
        if (cam && root.panel != null)
            foreach (var u in game.units)
            {
                if (!u.alive) continue;
                bool hurt = u.hp < u.maxHp - 0.01f;
                if (!(u.selected || hurt || (always && !u.def.isStatic))) continue;
                // the browser's heights over the feet (infantry 1.65, vehicles 2, buildings 3.6), never inside a taller model
                float over = u.def.@struct ? 3.6f : u.def.builder || u.def.naval ? 2.8f : u.def.air ? 2f : u.infantry ? 1.65f : 2f;
                over = Mathf.Max(over, TopOf(u) + (u.infantry ? 0.45f : 0.35f));
                Vector3 sp = cam.WorldToScreenPoint(u.Pos + Vector3.up * over);
                if (sp.z <= 0f || sp.x < -40 || sp.x > cam.pixelWidth + 40 || sp.y < -20 || sp.y > cam.pixelHeight + 20) continue;
                var p = ToPanel(sp);
                var bar = k < hpPool.Count ? hpPool[k] : HpBar(); k++; Show(bar, true);
                bar.style.left = p.x; bar.style.top = p.y;
                float w = (u.def.@struct ? 46f : !u.infantry ? 26f : 16f) * HS, kk = Mathf.Clamp01(u.hp / u.maxHp);
                float bh = Mathf.Max(2f, Mathf.Round(2f * HS)), sq = Mathf.Round(5f * Mathf.Min(1.8f, HS));
                Rect(bar[0], -w / 2f - 1f, -1f, w + 2f, bh + 2f);
                Rect(bar[1], -w / 2f, 0f, w * kk, bh);
                bool foe = u.army != game.player;
                bar[1].style.backgroundColor = foe ? HpFoe : kk > 0.6f ? HpGood : kk > 0.3f ? HpMid : HpLow;
                Rect(bar[2], -w / 2f - sq - 3f, bh / 2f - sq / 2f - 1f, sq + 2f, sq + 2f);
                Rect(bar[3], -w / 2f - sq - 2f, bh / 2f - sq / 2f, sq, sq);
                bar[3].style.backgroundColor = game.armies[u.army].color;
            }
        for (int i = k; i < hpPool.Count; i++) Show(hpPool[i], false);
    }

    void UpdateZoneTags()
    {
        if (!cam || root.panel == null) return;
        var rc = cam.GetComponent<DawgsRtsCamera>(); bool far = rc && rc.distance > 420f;
        foreach (var kv in zoneTags)
        {
            var z = kv.Key; var t = kv.Value;
            Vector3 w = z.pos + Vector3.up * 14f; Vector3 sp = cam.WorldToScreenPoint(w);
            bool vis = !far && sp.z > 0f && sp.x > -100 && sp.x < cam.pixelWidth + 100 && sp.y > 0 && sp.y < cam.pixelHeight;
            Show(t.box, vis); if (!vis) continue;
            var pp = ToPanel(sp);
            t.box.style.left = pp.x; t.box.style.top = pp.y;
            var col = z.owner >= 0 ? game.armies[z.owner].color : Text;
            string kind = z.d.type == "hq" ? "HQ" : z.d.type.ToUpperInvariant();
            t.kick.text = $"{kind} · {(z.owner >= 0 ? game.armies[z.owner].shortName.ToUpperInvariant() : "NEUTRAL")}";
            t.kick.style.color = col; t.sq.style.backgroundColor = col; t.nbox.style.borderTopColor = t.nbox.style.borderBottomColor = t.nbox.style.borderLeftColor = t.nbox.style.borderRightColor = col;
            bool cap = z.capF >= 0 && z.capP > 0f;
            Show(t.capF.parent, cap);
            if (cap) { t.capF.style.width = Length.Percent(z.capP); t.capF.style.backgroundColor = game.armies[z.capF].color; }
            t.sub.text = z.contested ? "CONTESTED" : cap ? $"{game.armies[z.capF].shortName.ToUpperInvariant()} TAKING IT · {z.capP:0}%" : z.queue.Count > 0 && z.owner == game.player ? $"TRAINING {z.queue.Count}" : "";
            Show(t.sub, t.sub.text.Length > 0);
        }
    }

    // a camera pixel (origin bottom-left) to panel coordinates
    Vector2 ToPanel(Vector3 sp) => RuntimePanelUtils.ScreenToPanel(root.panel, new Vector2(sp.x, cam.pixelHeight - sp.y));

    public bool OverUI(Vector2 screenPos)
    {
        if (root == null || root.panel == null) return false;
        if (modalOpen) return true;
        var pp = RuntimePanelUtils.ScreenToPanel(root.panel, new Vector2(screenPos.x, Screen.height - screenPos.y));
        return root.panel.Pick(pp) != null;
    }

    public void ShowBox(Vector2 a, Vector2 b)
    {
        var pa = RuntimePanelUtils.ScreenToPanel(root.panel, new Vector2(a.x, Screen.height - a.y));
        var pb = RuntimePanelUtils.ScreenToPanel(root.panel, new Vector2(b.x, Screen.height - b.y));
        selRect.style.left = Mathf.Min(pa.x, pb.x); selRect.style.top = Mathf.Min(pa.y, pb.y);
        selRect.style.width = Mathf.Abs(pa.x - pb.x); selRect.style.height = Mathf.Abs(pa.y - pb.y);
        Show(selRect, true);
    }
    public void HideBox() { if (selRect != null) Show(selRect, false); }

    public void Toast(string text) => Toast(text, false);
    public void Toast(string text, bool bad)
    {
        if (toast == null) return;
        toast.text = text; toast.EnableInClassList("bad", bad); toast.AddToClassList("on");
        toastUntil = Time.unscaledTime + (bad ? 2.4f : 1.6f);
    }

    public void Ping(Vector3 at)
    {
        mini.pings.Add((at, Time.unscaledTime));
        game.Fx.Marker(at, Warn, 7f, 2.5f);
        game.Fx.Alert("ping", 0.8f);
        game.Msg("You pinged the map.", game.player);
    }

    // ---------------------------------------------------------------- scoreboard (Tab) and full-screen map (M)
    public void CloseOverlays() { overlay = ""; if (overlayBg != null) { overlayBg.Clear(); Show(overlayBg, false); } bigMap = null; scoreBody = null; }
    public void ToggleScore() { if (overlay == "score") CloseOverlays(); else OpenOverlay("score"); }
    public void ToggleBigMap() { if (overlay == "map") CloseOverlays(); else OpenOverlay("map"); }

    void OpenOverlay(string which)
    {
        if (modalOpen || endShown) return;
        CloseOverlays(); overlay = which; Show(overlayBg, true);
        var box = new DawgsPanel(); box.AddToClassList(which == "score" ? "score" : "bigmap"); overlayBg.Add(box);
        var head = E("ov-head", box); var hl = E(null, head);
        L(which == "score" ? "SCOREBOARD" : "MAP", "modal-kick", hl, F.Display);
        L(which == "score" ? "Armies" : game.zones.Count > 0 ? "Test Town island" : "Map", "ov-title", hl, F.Display);
        if (which == "score")
        {
            scoreStats = L("", "ov-stats", head, F.Mono);
            scoreBody = E(null, box);
            FillScore();
            L("Tab or Esc closes", "ov-foot", box);
        }
        else
        {
            L("Click or drag to move the camera · M or Esc closes", "ov-stats", head);
            bigMap = new DawgsMinimap(game) { cam = cam, name = "bigMini" };
            bigMap.onJump = w => { cmd.JumpTo(w); return true; };
            box.Add(bigMap);
        }
    }

    void FillScore()
    {
        if (scoreBody == null) return;
        var me = game.armies[game.player];
        scoreStats.text = $"Your funds ${Mathf.FloorToInt(me.money)}   ·   Your zones {game.zones.Count(z => z.owner == game.player)} / {game.zones.Count}   ·   Time {Clock(game.time)}";
        scoreBody.Clear();
        foreach (bool mine in new[] { true, false })
        {
            L(mine ? "YOU" : "ENEMY", mine ? "sc-team sc-me" : "sc-team", scoreBody, F.Display);
            var hd = E("sc-row sc-hd", scoreBody);
            foreach (var h in new[] { "Army", "Zones", "Units", "Kills", "Lost", "Income", "Funds" }) L(h, h == "Army" ? "sc-c sc-name" : "sc-c", hd, F.Display);
            foreach (var A in game.armies.Where(a => (a.id == game.player) == mine))
            {
                var row = E(A.alive ? "sc-row" : "sc-row dead", scoreBody);
                var nm = E("sc-c sc-name", row); nm.style.flexDirection = FlexDirection.Row; nm.style.alignItems = Align.Center;
                var sw = new DawgsFlag(A.color); sw.AddToClassList("sc-flag"); nm.Add(sw);
                var nl = L(A.name, "sc-army", nm, F.Display); nl.style.color = A.color;
                L(game.zones.Count(z => z.owner == A.id).ToString(), "sc-c", row, F.Mono);
                L(game.units.Count(u => u.alive && u.army == A.id).ToString(), "sc-c", row, F.Mono);
                L(A.kills.ToString(), "sc-c", row, F.Mono); L(A.losses.ToString(), "sc-c", row, F.Mono);
                L($"+${A.incomeSec:0.0}/s", "sc-c", row, F.Mono);
                L(mine ? $"${Mathf.FloorToInt(A.money)}" : "—", "sc-c", row, F.Mono);
            }
        }
    }

    // ---------------------------------------------------------------- speed, pause and the menus
    public void SetSpeed(int i)
    {
        if (game.over) return;
        speedIdx = Mathf.Clamp(i, 0, Speeds.Length - 1); if (speedIdx > 0) lastSpeedIdx = speedIdx;
        if (!modalOpen) Time.timeScale = Speeds[speedIdx];
    }
    public void TogglePauseSpeed() => SetSpeed(speedIdx == 0 ? lastSpeedIdx : 0);

    public void TogglePause()
    {
        if (endShown) return;
        if (modalOpen) { CloseModal(); return; }
        CloseOverlays();
        OpenModal("PAUSED", "Battle paused", "", new (string, Action, bool)[]
        {
            ("RESUME", (Action)CloseModal, true), ("RESTART", (Action)(() => { CloseModal(); Restart(); }), false), ("QUIT", (Action)Quit, false)
        }, true, true);
    }

    // the browser's pause screen: sound settings, then the buttons, then the controls
    void OpenModal(string kick, string title, string sub, (string label, Action act, bool main)[] buttons, bool keys, bool audio = false)
    {
        modalBg.Clear();
        var m = new DawgsPanel(); m.AddToClassList("modal"); modalBg.Add(m);
        L(kick, "modal-kick", m, F.Display); L(title, "modal-title", m, F.Display);
        if (!string.IsNullOrEmpty(sub)) L(sub, "modal-sub", m);
        if (audio) { BuildAudio(m); BuildInterface(m); }
        foreach (var (label, act, main) in buttons) Btn(L(label, main ? "mbtn mbtn-main" : "mbtn", m, F.Display), _ => act());
        if (keys)
        {
            var k = E("keys", m);
            void Tip(string a, string b) { var r = E("tip-row", k); L(a, "tip-k", r, F.Mono); L(b, "tip-v", r); }
            Tip("WASD / arrows", "pan the map"); Tip("Mouse wheel", "zoom in and out (+ / - too)");
            Tip("Middle drag", DawgsPrefs.MidPan ? "pan the camera (Shift: orbit)" : "orbit the camera (Shift: pan)"); Tip("Home", "reset the camera view");
            Tip("Right-drag", "spread along a line · on an enemy: attack an area");
            Tip("Tab / M", "scoreboard / full-screen map"); Tip("P", "pause · speed on the top bar"); Tip("Shift+M", "mute the music");
        }
        Show(modalBg, true); modalOpen = true; Time.timeScale = 0f;
    }
    // Music volume (+ Mute music), Alerts volume, Unit sounds: the game's sliders, its wording and its defaults
    Label muteBox;
    void BuildAudio(VisualElement m)
    {
        var box = E("volrow", m);
        L("SOUND", "modal-sec", box, F.Display);
        void Row(string name, string small, Func<float> get, Action<float> set)
        {
            var r = E("set-row", box);
            var left = E("set-left", r); L(name, "set-name", left); L(small, "set-small", left);
            var outL = L($"{Mathf.RoundToInt(get() * 100f)}%", "set-out", r, F.Mono);
            var s = new DawgsSlider(get(), v => { set(v); outL.text = $"{Mathf.RoundToInt(v * 100f)}%"; });
            box.Add(s);
        }
        string now = game.NowPlaying;
        Row("Music volume", string.IsNullOrEmpty(now) ? "" : TrackName(now), () => DawgsAudio.Music, v => DawgsAudio.Music = v);
        var tog = Btn(E("tog", box), _ => SetMute(!DawgsAudio.MusicMuted));
        muteBox = L("", DawgsAudio.MusicMuted ? "tog-box on" : "tog-box", tog, F.Mono); L("Mute music", "tog-l", tog); L("Shift+M", "kbd", tog, F.Mono);
        foreach (var c in tog.Children()) c.pickingMode = PickingMode.Ignore;
        Row("Alerts volume", "missile sirens, air raid alarm, pings", () => DawgsAudio.Alerts, v => { DawgsAudio.Alerts = v; game.Fx.Alert("ping", 0.8f, 0.4f); });
        Row("Unit sounds", "gunfire, rockets, explosions", () => DawgsAudio.Units, v => DawgsAudio.Units = v);
    }

    // Interface: the browser's "Always show unit health bars" and "Middle mouse drag" settings
    void BuildInterface(VisualElement m)
    {
        var box = E("volrow", m);
        L("INTERFACE", "modal-sec", box, F.Display);
        Label hpBox = null;
        var tog = Btn(E("tog", box), _ =>
        {
            DawgsPrefs.HpAlways = !DawgsPrefs.HpAlways; hpBox.EnableInClassList("on", DawgsPrefs.HpAlways);
            Toast(DawgsPrefs.HpAlways ? "Health bars on every unit" : "Health bars on selected and damaged units only");
        });
        hpBox = L("", DawgsPrefs.HpAlways ? "tog-box on" : "tog-box", tog, F.Mono);
        L("Always show unit health bars", "tog-l", tog); L("otherwise only selected or damaged units", "set-small", tog);
        foreach (var c in tog.Children()) c.pickingMode = PickingMode.Ignore;

        var r = E("set-row", box); var left = E("set-left", r);
        L("Middle mouse drag", "set-name", left); L("hold Shift while dragging for the other one", "set-small", left);
        var seg = E("seg", box);
        Label a = null, b = null;
        void Paint() { a.EnableInClassList("on", !DawgsPrefs.MidPan); b.EnableInClassList("on", DawgsPrefs.MidPan); }
        a = (Label)Btn(L("ORBIT · SHIFT PANS", "seg-btn", seg, F.Display), _ => { DawgsPrefs.MidPan = false; Paint(); selSig = ""; });
        b = (Label)Btn(L("PAN · SHIFT ORBITS", "seg-btn seg-btn-r", seg, F.Display), _ => { DawgsPrefs.MidPan = true; Paint(); selSig = ""; });
        Paint();
    }

    static string TrackName(string clip) => clip.StartsWith("battle") ? "Battle theme" : clip == "purity" ? "Purity" : clip;

    public void SetMute(bool on)
    {
        DawgsAudio.MusicMuted = on;
        if (muteBox != null) muteBox.EnableInClassList("on", on);
        Toast(on ? "Music muted" : "Music on");
    }

    void CloseModal() { Show(modalBg, false); modalOpen = false; Time.timeScale = game.over ? 1f : Speeds[speedIdx]; }

    void ShowEnd()
    {
        CloseOverlays(); endShown = true;
        bool won = game.winner == game.player; var A = game.armies[game.player];
        OpenModal($"TEST TOWN · {Clock(game.time)}", won ? "VICTORY" : "DEFEAT",
            $"{(won ? "Every zone flies your flag." : "The Legion holds the island.")} {A.kills} kills, {A.losses} lost.",
            new (string, Action, bool)[] { ("PLAY AGAIN", (Action)(() => { endShown = false; CloseModal(); Restart(); }), true), ("QUIT", (Action)Quit, false) }, false);
        Time.timeScale = 1f;
    }

    void Restart()
    {
        game.NewGame(); cmd.Select(new List<DawgsUnit>());
        foreach (var kv in zoneTags) kv.Value.box.RemoveFromHierarchy();
        zoneTags.Clear(); foreach (var z in game.zones) MakeZoneTag(z);
        logShown = -1; SetSpeed(1);
    }

    void Quit()
    {
#if UNITY_EDITOR
        UnityEditor.EditorApplication.isPlaying = false;
#else
        Application.Quit();
#endif
    }
}
