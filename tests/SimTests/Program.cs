using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;

namespace DawgsUprising.Sim.Tests
{
    /// <summary>
    /// The SIM's checks against recordings of the web game (v22.5), run outside Unity:
    ///   cd tests/SimTests && dotnet run -c Release
    /// Prints one line per check, then "TESTS PASSED n/n" or "TESTS FAILED"; exit code 0 or 1.
    /// A check that throws counts as a failure.
    /// </summary>
    static class Program
    {
        static int _passed, _failed;
        public static string Root;     // repo root
        public static string Golden => Path.Combine(Root, "godot", "tests", "golden");
        public static string Data => Path.Combine(Root, "godot", "data");
        public static string SimSource => Path.Combine(Root, "packages", "com.dawgs.sim", "Runtime");

        static GameData _game;
        public static GameData Game => _game ?? (_game = GameData.FromJson(Read(Data, "balance.json"), Read(Data, "maps.json"),
            Read(Data, "mapgen.json"), Read(Data, "factions.json")));

        static int Main(string[] args)
        {
            Root = FindRoot();
            var sw = Stopwatch.StartNew();
            Run("balance", Checks.Balance);
            Run("sim steps", Checks.SimSteps);
            Run("sim is pure", Checks.SimIsPure);
            Run("rng matches web", Checks.Rng);
            Run("dmath matches V8", Checks.MathFns);
            Run("maps", Checks.Maps);
            Run("terrain", Checks.Terrain);
            Run("pathing", Checks.Pathing);
            Run("spatial", Checks.Spatial);
            Run("tables", Checks.Tables);
            Run("setup", Checks.Setup);
            Console.WriteLine(_failed == 0 ? $"TESTS PASSED {_passed}/{_passed}" : $"TESTS FAILED {_failed} of {_passed + _failed}");
            Console.WriteLine($"({sw.Elapsed.TotalSeconds:F1} s)");
            return _failed == 0 ? 0 : 1;
        }

        static string FindRoot()
        {
            var d = new DirectoryInfo(AppContext.BaseDirectory);
            while (d != null && !Directory.Exists(Path.Combine(d.FullName, "web"))) d = d.Parent;
            if (d == null) throw new DirectoryNotFoundException("repo root (with web/) not found above " + AppContext.BaseDirectory);
            return d.FullName;
        }

        static void Run(string name, Action check)
        {
            try { check(); }
            catch (Exception e)
            {
                string at = e.StackTrace?.Split('\n').FirstOrDefault()?.Trim() ?? "";
                Ok(false, $"check '{name}' crashed: {e.GetType().Name}: {e.Message} ({at})");
            }
        }

        public static void Ok(bool cond, string what)
        {
            if (cond) { _passed++; Console.WriteLine("  ok   " + what); }
            else { _failed++; Console.WriteLine("  FAIL " + what); }
        }

        public static string Read(string dir, string file) => File.ReadAllText(Path.Combine(dir, file));
        public static object Load(string path) => Json.Parse(File.ReadAllText(path));
        public static long HexBits(string h) => unchecked((long)ulong.Parse(h, NumberStyles.HexNumber, CultureInfo.InvariantCulture));
        public static double HexFloat(string h) => DMath.FromBits(HexBits(h));
    }

    static class Checks
    {
        static readonly string[] UnitFields = { "name", "cost", "hp", "speed", "range", "dmg", "rof", "acc", "weapon", "armor" };

        public static void Balance()
        {
            var b = Program.Game.Balance;
            Program.Ok(b.Count > 0, "balance.json loads");
            foreach (var key in new[] { "engine", "units", "weapons", "walls", "zones", "economy", "combat", "ai", "campaign", "carrier", "manning" })
                Program.Ok(b.Has(key), $"balance has '{key}'");
            var units = b.Obj("units");
            Program.Ok(units.Count > 10, $"balance has {units.Count} unit types");
            var missing = new List<string>();
            foreach (var k in units.Keys)
                foreach (var f in UnitFields)
                    if (!units.Obj(k).Has(f)) missing.Add($"{k}.{f}");
            Program.Ok(missing.Count == 0, "every unit has the core stats " + string.Join(", ", missing));
            Program.Ok(units.Obj("rifle").Num("hp") == 45.0, "units.rifle.hp = 45 (web v22.5)");
        }

        const double Chunk = 0.25;   // matches the web harness: G.update() is stepped in 0.25 s chunks
        const double Seconds = 30.0;

        static Battle RunSim()
        {
            var sim = new Battle(GameData.BalanceOnly(Program.Read(Program.Data, "balance.json")), new BattleOptions { Seed = 7 });
            for (double t = 0; t < Seconds; t += Chunk) sim.Update(Chunk);
            return sim;
        }

        public static void SimSteps()
        {
            var a = RunSim();
            var b = RunSim();
            var engine = Program.Game.Balance.Obj("engine");
            double step = engine.Num("step");
            Program.Ok(!a.Over, "sim starts and runs");
            Program.Ok(Math.Abs(a.Ticks - Seconds / step) <= 1.0, $"{Seconds:F0} s of play = {a.Ticks} ticks at {step:F4} s");
            Program.Ok(a.StateHash() == b.StateHash(), "two runs, same seed, same state hash");
            var capped = new Battle(GameData.BalanceOnly(Program.Read(Program.Data, "balance.json")), new BattleOptions { Seed = 7 });
            capped.Update(10.0);
            double maxFrame = engine.Num("maxFrame");
            Program.Ok(capped.Time <= maxFrame + 1e-9, $"one long frame is capped at maxFrame ({capped.Time:F2} s)");
        }

        /// <summary>The SIM must stay deterministic and engine-free: no Unity, no clocks or files, no unseeded
        /// randomness, and no platform maths that can differ in the last bit (DMath has the exact versions).</summary>
        public static void SimIsPure()
        {
            var banned = new[] { "UnityEngine", "System.Random", "new Random(", "DateTime", "Stopwatch", "Environment.TickCount", "System.IO",
                "Math.Sin(", "Math.Cos(", "Math.Tan(", "Math.Atan", "Math.Asin(", "Math.Acos(", "Math.Pow(", "Math.Exp(", "Math.Log", "Math.Round(" };
            var asmdef = Program.Read(Program.SimSource, "DawgsUprising.Sim.asmdef");
            Program.Ok(asmdef.Contains("\"noEngineReferences\": true"), "the SIM assembly has no engine references (asmdef)");
            foreach (var path in Directory.GetFiles(Program.SimSource, "*.cs"))
            {
                string file = Path.GetFileName(path);
                var code = string.Join("\n", File.ReadAllLines(path).Where(l => !l.TrimStart().StartsWith("//")));
                // "Math.Sin(" but not "DMath.Sin(": System.Math only
                var found = banned.Where(s => s.StartsWith("Math.")
                    ? file != "DMath.cs" && Regex.IsMatch(code, @"(?<!\w)" + Regex.Escape(s))
                    : code.Contains(s)).ToList();
                Program.Ok(found.Count == 0, $"{file} uses no engine, clock, file or platform-maths calls {string.Join(", ", found)}");
            }
        }

        public static void Rng()
        {
            var g = (JObj)Program.Load(Path.Combine(Program.Golden, "rng.json"));
            var seqs = g.Obj("mulberry32");
            Program.Ok(seqs != null && seqs.Count > 0, $"golden rng.json loads (web v{g.Str("web")})");
            foreach (var key in seqs.Keys)
            {
                var r = new Sim.Rng(long.Parse(key, CultureInfo.InvariantCulture));
                var want = seqs.Arr(key);
                int bad = -1;
                for (int i = 0; i < want.Count; i++)
                    if (r.NextU32() != (uint)Math.Round((double)want[i] * 4294967296.0)) { bad = i; break; }
                Program.Ok(bad == -1, $"rng seed {key} matches web for {want.Count} values{(bad == -1 ? "" : $" (differs at {bad})")}");
            }
        }

        public static void MathFns()
        {
            var g = (JObj)Program.Load(Path.Combine(Program.Golden, "math.json"));
            var cases = g.Obj("cases");
            Program.Ok(cases != null, $"golden math.json loads (V8 {g.Str("v8")})");
            var fns = new Dictionary<string, Func<double[], double>> {
                ["sin"] = a => DMath.Sin(a[0]), ["cos"] = a => DMath.Cos(a[0]), ["atan2"] = a => DMath.Atan2(a[0], a[1]),
                ["pow"] = a => DMath.Pow(a[0], a[1]), ["hypot"] = a => DMath.Hypot(a[0], a[1]),
                ["hypot3"] = a => DMath.Hypot3(a[0], a[1], a[2]), ["round"] = a => DMath.RoundJs(a[0]) };
            foreach (var kv in fns)
            {
                var rows = cases.Arr(kv.Key);
                int bad = 0; string first = "";
                foreach (List<object> row in rows)
                {
                    var args = new double[row.Count - 1];
                    for (int i = 0; i < args.Length; i++) args[i] = Program.HexFloat((string)row[i]);
                    long want = Program.HexBits((string)row[row.Count - 1]);
                    double got = kv.Value(args);
                    if (DMath.Bits(got) != want && !(double.IsNaN(got) && double.IsNaN(DMath.FromBits(want))))
                    {
                        bad++;
                        if (first == "") first = $" first: {kv.Key}({string.Join(", ", args)}) = {got:R}, V8 {DMath.FromBits(want):R}";
                    }
                }
                Program.Ok(rows.Count > 0 && bad == 0, $"dmath {kv.Key} matches V8 bit for bit on {rows.Count} inputs{(bad == 0 ? "" : $" ({bad} differ;{first})")}");
            }
        }

        /// <summary>Every number in a parsed JSON value, keys sorted, as 64-bit patterns (same order as tools/export_maps.js).</summary>
        static void Fingerprint(object v, List<long> o)
        {
            if (v is double d) o.Add(DMath.Bits(d));
            else if (v is List<object> l) foreach (var x in l) Fingerprint(x, o);
            else if (v is JObj j)
            {
                var keys = new List<string>(j.Keys);
                keys.Sort(StringComparer.Ordinal);
                foreach (var k in keys) Fingerprint(j[k], o);
            }
        }

        /// <summary>maps.json must hold every map number exactly as the web game has it, maps load into the typed
        /// MapDef, and Chaos Isles must roll the same map as the web game for the same seed.</summary>
        public static void Maps()
        {
            var file = (JObj)Program.Load(Path.Combine(Program.Data, "maps.json"));
            var raw = file.Obj("maps");
            var golden = (JObj)Program.Load(Path.Combine(Program.Golden, "maps.json"));
            var gm = golden.Obj("maps");
            Program.Ok(raw.Count == gm.Count && raw.Count > 0, $"maps.json has {raw.Count} maps (web v{golden.Str("web")} has {gm.Count})");
            var bad = new List<string>();
            foreach (var id in gm.Keys)
            {
                var want = gm.Arr(id);
                var got = new List<long>();
                Fingerprint(raw[id], got);
                if (got.Count != want.Count) { bad.Add($"{id}: {got.Count} numbers, web {want.Count}"); continue; }
                for (int i = 0; i < want.Count; i++)
                    if (got[i] != Program.HexBits(((string)want[i]).TrimStart('#'))) { bad.Add($"{id}: number {i} differs"); break; }
            }
            Program.Ok(bad.Count == 0, $"every number on all {gm.Count} maps matches the web game exactly {string.Join("; ", bad)}");
            var diffs = new List<string>();
            foreach (var id in raw.Keys)
            {
                string d = Compare.FirstDiff(raw[id], Program.Game.Maps[id], id);
                if (d != "") diffs.Add(d);
            }
            Program.Ok(diffs.Count == 0, $"all {raw.Count} maps load into MapDef unchanged {string.Join("; ", diffs)}");
            var gen = Program.Game.Mapgen;
            var chaos = golden.Obj("chaos");
            foreach (var seed in chaos.Keys)
            {
                var want = chaos.Obj(seed).Obj("map");
                var got = Sim.Maps.MakeChaos(double.Parse(seed, CultureInfo.InvariantCulture), gen, Program.Game.Balance);
                string diff = Compare.FirstDiff(want, got, "");
                Program.Ok(diff == "", $"Chaos Isles seed {seed} matches the web game ({got.Zones.Count} bases, {want.Arr("blobs").Count} islands) {diff}");
            }
        }

        static BattleOptions Opts(JObj o) => Bind.To<BattleOptions>(o);

        /// <summary>Terrain must match the web game's buildMap (terrain0.json): start slots, every height (as 32-bit
        /// floats), the passability and water grids, props and coves. Every recorded map runs.</summary>
        public static void Terrain()
        {
            var golden = (JObj)Program.Load(Path.Combine(Program.Golden, "terrain0.json"));
            var runs = golden.Obj("runs");
            Program.Ok(runs.Count > 0, $"golden terrain0.json loads (web v{golden.Str("web")})");
            var game = Program.Game;
            foreach (var name in runs.Keys)
            {
                var g = runs.Obj(name);
                var opts = Opts(g.Obj("opts"));
                long seed = opts.Seed;
                var m = opts.Map == "chaos" ? Sim.Maps.MakeChaos(seed, game.Mapgen, game.Balance) : game.Maps[opts.Map].Copy();
                var rnd = new Sim.Rng(seed ^ 0x9e3779b9L);
                var bz = Sim.Maps.BattleZonesFor(m, opts, rnd, game.Mapgen);
                m.ZonesFinal = bz.ZonesFinal;
                var problems = new List<string>();
                string diff = Compare.FirstDiff(g["zonesFinal"], bz.ZonesFinal, "zonesFinal");
                if (diff == "") diff = Compare.FirstDiff(g["slotOf"], bz.SlotOf, "slotOf");
                if (diff != "") problems.Add("start slots " + diff);
                var sw = Stopwatch.StartNew();
                var t = Sim.Terrain.Build(m, seed, game.Balance, game.Mapgen);
                double secs = sw.Elapsed.TotalSeconds;
                if (Compare.Sha(t.Hv) != g.Str("hv"))
                {
                    string first = "";
                    foreach (List<object> s in g.Arr("samples"))
                    {
                        int v = (int)(double)s[0];
                        if (DMath.Bits(t.Hv[v]) != Program.HexBits((string)s[1])) { first = $" (first sampled difference at vertex {v}: web {Program.HexFloat((string)s[1]):R}, port {(double)t.Hv[v]:R})"; break; }
                    }
                    problems.Add("heights differ" + first);
                }
                if (Compare.Sha(t.LandGrid) != g.Str("pass")) problems.Add($"passability differs ({Compare.Count(t.LandGrid)} land cells, web {g.Num("passCount")})");
                if (Compare.Sha(t.WaterGrid) != g.Str("wpass")) problems.Add("water grid differs");
                string pd = Compare.FirstDiff(g["props"], t.Props, "props");
                if (pd != "") problems.Add(pd);
                string cd = Compare.FirstDiff(g["coves"], t.Coves, "coves");
                if (cd != "") problems.Add(cd);
                Program.Ok(problems.Count == 0, $"terrain {name} identical to web ({t.GW}x{t.GH} cells, {t.Props.Count} props, {t.Coves.Count} coves, built in {secs:F2} s) {string.Join("; ", problems)}");
            }
        }

        /// <summary>Pathing must find the same paths as the web game's findPath, waypoint for waypoint, on the same
        /// ground grid (paths.json, from tools/web_paths.js).</summary>
        public static void Pathing()
        {
            var golden = (JObj)Program.Load(Path.Combine(Program.Golden, "paths.json"));
            var runs = golden.Obj("runs");
            Program.Ok(runs.Count > 0, $"golden paths.json loads (web v{golden.Str("web")})");
            foreach (var name in runs.Keys)
            {
                var g = runs.Obj(name);
                var p = new Sim.Pathing(g.Num("X0"), g.Num("Z0"), g.Num("CELL"), g.Int("GW"), g.Int("GH"), Program.Game.Balance.Obj("engine"));
                var grid = Convert.FromBase64String(g.Str("pass"));
                var queries = g.Arr("queries");
                int bad = 0, found = 0;
                string first = "";
                for (int qi = 0; qi < queries.Count; qi++)
                {
                    var q = (List<object>)queries[qi];
                    var got = p.FindPath(Program.HexFloat((string)q[0]), Program.HexFloat((string)q[1]), Program.HexFloat((string)q[2]), Program.HexFloat((string)q[3]), grid);
                    var want = q[4] as List<object>;
                    bool same = (got == null) == (want == null);
                    if (same && want != null)
                    {
                        found++;
                        same = got.Count == want.Count;
                        for (int k = 0; same && k < want.Count; k++)
                        {
                            var w = (List<object>)want[k];
                            same = DMath.Bits(got[k][0]) == Program.HexBits((string)w[0]) && DMath.Bits(got[k][1]) == Program.HexBits((string)w[1]);
                        }
                    }
                    if (!same)
                    {
                        bad++;
                        if (first == "") first = $" first: query {qi}, web {(want == null ? "none" : want.Count.ToString())} waypoints, port {(got == null ? "none" : got.Count.ToString())}";
                    }
                }
                Program.Ok(bad == 0, $"pathing {name}: {queries.Count - bad} paths identical to web ({found} found){(bad == 0 ? "" : $" - {bad} differ;{first}")}");
            }
        }

        sealed class Dot : ISpatialItem
        {
            public double X { get; set; }
            public double Z { get; set; }
            public bool Alive { get; set; }
        }

        /// <summary>The spatial hash must find exactly the live units within range, in the web game's visit order.</summary>
        public static void Spatial()
        {
            var rng = new Sim.Rng(99);
            double W = 790, H = 450;
            var units = new List<Dot>();
            for (int k = 0; k < 600; k++)
                units.Add(new Dot { X = -W / 2 + rng.Next() * W, Z = -H / 2 + rng.Next() * H, Alive = rng.Next() > 0.1 });
            var hash = new Spatial<Dot>(W, H, -W / 2, -H / 2, Program.Game.Balance.Obj("engine").Num("hashBucket"));
            hash.Rebuild(units);
            int bad = 0;
            for (int q = 0; q < 200; q++)
            {
                double x = -W / 2 + rng.Next() * W, z = -H / 2 + rng.Next() * H, r = 5 + rng.Next() * 60;
                var got = new List<Dot>();
                hash.Query(x, z, r, (u, d2) => got.Add(u));
                // expected: bucket rows, then columns, then insertion order (the web visit order)
                var want = new List<Dot>();
                for (int j = 0; j < hash.BH; j++)
                    for (int i = 0; i < hash.BW; i++)
                        foreach (var u in units)
                        {
                            if (!u.Alive) continue;
                            int ui = Math.Max(0, Math.Min(hash.BW - 1, (int)Math.Floor((u.X - hash.X0) / hash.Size)));
                            int uj = Math.Max(0, Math.Min(hash.BH - 1, (int)Math.Floor((u.Z - hash.Z0) / hash.Size)));
                            if (ui == i && uj == j && (u.X - x) * (u.X - x) + (u.Z - z) * (u.Z - z) <= r * r) want.Add(u);
                        }
                if (!got.SequenceEqual(want)) bad++;
            }
            Program.Ok(bad == 0, $"spatial hash: 200 range queries over 600 units match a full scan, in web order{(bad == 0 ? "" : $" ({bad} differ)")}");
        }

        /// <summary>Tables must build the same unit, zone and facility tables as the web game.</summary>
        public static void Tables()
        {
            var golden = (JObj)Program.Load(Path.Combine(Program.Golden, "tables.json"));
            var t = new Sim.Tables(Program.Game.Balance);
            foreach (var (name, got, count) in new (string, object, int)[] { ("UTYPES", t.UTypes, t.UTypes.Count), ("ZTYPES", t.ZTypes, t.ZTypes.Count), ("FACILITIES", t.Facilities, t.Facilities.Count) })
            {
                var want = golden.Obj(name);
                string diff = Compare.FirstDiff(want, got, name);
                Program.Ok(want.Count > 0 && diff == "" && want.Count == count, $"{name}: {want.Count} entries identical to web {diff}");
            }
            Program.Ok(Program.Game.Factions.Player != null && Program.Game.Factions.Ai.Count == 15, $"factions.json has the player and {Program.Game.Factions.Ai.Count} AI armies");
        }

        /// <summary>Battle setup (the web createGame) must match the web game at each recorded checkpoint, including
        /// how many random numbers have been drawn (setup.json, tools/web_setup.js).</summary>
        public static void Setup()
        {
            var golden = (JObj)Program.Load(Path.Combine(Program.Golden, "setup.json"));
            var runs = golden.Obj("runs");
            Program.Ok(runs.Count > 0, $"golden setup.json loads (web v{golden.Str("web")})");
            foreach (var name in runs.Keys)
            {
                var g = runs.Obj(name);
                var cps = g.Obj("checkpoints");
                var sw = Stopwatch.StartNew();
                Battle sim = null;
                var problems = new List<string>();
                var p2 = new List<string>();
                int spots = 0;
                sim = new Battle(Program.Game, Opts(g.Obj("opts")), (cp, s) =>
                {
                    if (cp == "zones")
                    {
                        var c = cps.Obj("zones");
                        if (s.Rnd.Draws != c.Int("rc")) problems.Add($"random draws {s.Rnd.Draws}, web {c.Int("rc")}");
                        foreach (var (key, got) in new (string, object)[] { ("factions", s.Factions), ("zones", s.Zones), ("home", s.Home), ("homes", s.Homes) })
                        {
                            string d = Compare.FirstDiff(c[key], got, key);
                            if (d != "") problems.Add(d);
                        }
                    }
                    else if (cp == "plots" && cps.Has("plots"))
                    {
                        // checkpoint 2: build plots (streets, runways, plots, levelled ground)
                        var c = cps.Obj("plots");
                        string d = Compare.FirstDiff(c["zones"], s.Zones, "zones");
                        if (d != "") p2.Add(d);
                        d = Compare.FirstDiff(c["streets"], s.Streets, "streets");
                        if (d != "") p2.Add(d);
                        if (Compare.Sha(s.Terrain.Hv) != c.Str("hv")) p2.Add("levelled heights differ");
                        if (Compare.Sha(s.Terrain.LandGrid) != c.Str("pass")) p2.Add($"walkable grid differs ({Compare.Count(s.Terrain.LandGrid)} cells)");
                        foreach (var z in s.Zones) spots += z.Spots?.Count ?? 0;
                    }
                });
                double secs = sw.Elapsed.TotalSeconds;
                Program.Ok(problems.Count == 0, $"setup {name}: {sim.Factions.Count} armies, {sim.Zones.Count} bases identical to web after {cps.Obj("zones").Int("rc")} draws ({secs:F2} s) {string.Join("; ", problems)}");
                if (cps.Has("plots"))
                    Program.Ok(p2.Count == 0, $"setup {name} plots: {sim.Streets.Count} streets, {spots} plots identical to web {string.Join("; ", p2)}");
            }
        }
    }
}
