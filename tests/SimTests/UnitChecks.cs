using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;

namespace DawgsUprising.Sim.Tests
{
    /// <summary>
    /// Units, orders, movement and combat against the web game's unit scenarios (units.json, tools/web_units.js):
    /// the same spawns and orders at the same ticks, then every tick's fingerprint of all units and, every second,
    /// the full state of every unit, projectile and army must match exactly.
    /// </summary>
    static class UnitChecks
    {
        static string Hex(double x) => ((ulong)DMath.Bits(x)).ToString("x16");

        /// <summary>FNV-1a over the 32-bit halves of each number, as tools/web_units.js computes it.</summary>
        static string Fingerprint(Battle b)
        {
            uint h = 2166136261;
            void Mix(double x)
            {
                ulong bits = (ulong)DMath.Bits(x);
                unchecked
                {
                    h = (h ^ (uint)(bits >> 32)) * 16777619u;
                    h = (h ^ (uint)bits) * 16777619u;
                }
            }
            foreach (var u in b.Units) { Mix(u.Id); Mix(u.Alive ? 1 : 0); Mix(u.X); Mix(u.Z); Mix(u.Ang); Mix(u.Hp); Mix(u.Cd); }
            Mix(b.Projectiles.Count);
            return h.ToString("x8");
        }

        static int IdOf(Unit u) => u == null ? -1 : u.Id;

        static List<object> UnitRow(Unit u) => new List<object> { (double)u.Id, u.Type, (double)u.F, u.Alive, u.Mode, Hex(u.X), Hex(u.Z), Hex(u.Ang), Hex(u.Hp),
            Hex(u.MaxHp), Hex(u.Cd), Hex(u.AcqT), (double)IdOf(u.Target), (double)IdOf(u.Forced), (double)(u.Path == null ? -1 : u.Path.Count), (double)u.Pi,
            u.Deployed, Hex(u.DeployT), (double)IdOf(u.LastHitBy), u.Stance, (double)(u.Guard == null ? -1 : IdOf(u.Guard.T)) };

        static List<object> ProjRow(Projectile p) => new List<object> { (double)IdOf(p.Src), (double)IdOf(p.Tgt), p.Wpn, Hex(p.Ex), Hex(p.Ez), Hex(p.T), Hex(p.Dur) };

        static readonly string[] UnitFields = { "id", "type", "f", "alive", "mode", "x", "z", "ang", "hp", "maxHp", "cd", "acqT", "target", "forced",
            "path", "pi", "deployed", "deployT", "lastHitBy", "stance", "guarding" };

        /// <summary>"" if two rows are the same, else which field differs.</summary>
        static string RowDiff(List<object> want, List<object> got, string[] names)
        {
            if (want.Count != got.Count) return $"{want.Count} fields, port {got.Count}";
            for (int i = 0; i < want.Count; i++)
                if (!Equals(want[i], got[i])) return $"{(names != null ? names[i] : "field " + i)}: web {Show(want[i])}, port {Show(got[i])}";
            return "";
        }

        static string Show(object o)
        {
            if (o is string s && s.Length == 16 && s.All(Uri.IsHexDigit)) return DMath.FromBits(Program.HexBits(s)).ToString("R", CultureInfo.InvariantCulture);
            return o == null ? "null" : o.ToString();
        }

        static string SnapDiff(JObj want, Battle b)
        {
            var wu = want.Arr("units");
            if (wu.Count != b.Units.Count) return $"{wu.Count} units, port {b.Units.Count}";
            for (int i = 0; i < wu.Count; i++)
            {
                string d = RowDiff((List<object>)wu[i], UnitRow(b.Units[i]), UnitFields);
                if (d != "") return $"unit {((List<object>)wu[i])[0]} ({((List<object>)wu[i])[1]}) {d}";
            }
            var wp = want.Arr("projectiles");
            if (wp.Count != b.Projectiles.Count) return $"{wp.Count} projectiles, port {b.Projectiles.Count}";
            for (int i = 0; i < wp.Count; i++)
            {
                string d = RowDiff((List<object>)wp[i], ProjRow(b.Projectiles[i]), new[] { "src", "tgt", "wpn", "ex", "ez", "t", "T" });
                if (d != "") return $"projectile {i} {d}";
            }
            var wf = want.Arr("factions");
            for (int i = 0; i < wf.Count; i++)
            {
                var row = (List<object>)wf[i];
                var f = b.Factions[i];
                var got = new List<object> { (double)f.Kills, (double)f.Losses, f.Aggro.Select(a => (object)Hex(a)).ToList() };
                if ((double)row[0] != f.Kills || (double)row[1] != f.Losses || !((List<object>)row[2]).Cast<string>().SequenceEqual(f.Aggro.Select(Hex)))
                    return $"army {i} kills/losses/grudges: web {row[0]}/{row[1]}, port {f.Kills}/{f.Losses}";
            }
            return "";
        }

        static object OrderArg(object a, Battle b)
        {
            if (a is JObj o && o.Has("uid")) return b.Units.Find(u => u.Id == (int)o.Num("uid"));
            if (a is List<object> l) return l.Select(p => new[] { ((JObj)p).Num("x"), ((JObj)p).Num("z") }).ToList();
            return a;
        }

        public static void Units()
        {
            var golden = (JObj)Program.Load(Path.Combine(Program.Golden, "units.json"));
            var runs = golden.Obj("runs");
            Program.Ok(runs.Count > 0, $"golden units.json loads (web v{golden.Str("web")})");
            foreach (var name in runs.Keys)
            {
                var g = runs.Obj(name);
                var b = new Battle(Program.Game, new BattleOptions { Map = g.Str("map"), Seed = (long)g.Num("seed") });
                b.Rnd = new Sim.Rng((long)g.Num("rseed"));
                if (b.NextId != g.Int("id0")) { Program.Ok(false, $"units {name}: first unit id {b.NextId}, web {g.Int("id0")}"); continue; }
                var events = new Dictionary<string, int>();
                b.Event += (ev, x, y) => events[ev] = events.TryGetValue(ev, out int n) ? n + 1 : 1;
                var actions = g.Arr("actions").Cast<JObj>().ToList();
                var fps = g.Arr("tickFp");
                var snaps = g.Arr("snaps").Cast<JObj>().ToDictionary(s => s.Int("tick"));
                int ticks = g.Int("ticks");
                string problem = "";
                for (int k = 0; k <= ticks && problem == ""; k++)
                {
                    foreach (var a in actions.Where(a => a.Int("at") == k))
                    {
                        if (a.Has("spawn"))
                            foreach (List<object> s in a.Arr("spawn")) b.SpawnUnit((string)s[0], (int)(double)s[1], (double)s[2], (double)s[3]);
                        if (a.Has("order"))
                        {
                            var o = a.Arr("order");
                            var ids = ((List<object>)o[2]).Select(x => (int)(double)x).ToList();
                            b.OrderAs((int)(double)o[0], (string)o[1], ids, o.Count > 3 ? OrderArg(o[3], b) : null, o.Count > 4 ? OrderArg(o[4], b) : null);
                        }
                    }
                    if (snaps.TryGetValue(k, out var snap))
                    {
                        string d = SnapDiff(snap, b);
                        if (d != "") { problem = $"at {k / 30.0:F1} s (tick {k}): {d}"; break; }
                    }
                    if (k == ticks) break;
                    b.StepTicks(1);
                    string fp = Fingerprint(b);
                    if (fp != (string)fps[k])
                    {
                        // show what differs at the next full snapshot
                        int next = snaps.Keys.Where(t => t > k).DefaultIfEmpty(-1).Min();
                        problem = $"tick {k + 1} ({(k + 1) / 30.0:F2} s) fingerprint differs";
                        if (next > 0)
                        {
                            for (int j = k + 1; j < next; j++) b.StepTicks(1);
                            problem += $"; at tick {next}: {SnapDiff(snaps[next], b)}";
                        }
                        break;
                    }
                }
                var last = (JObj)g.Arr("snaps").Last();
                var we = last.Obj("events");
                string evs = string.Join(", ", we.Keys.Select(k => $"{we.Num(k)} {k}"));
                if (problem == "")
                    foreach (var k in we.Keys)
                        if (!events.TryGetValue(k, out int n) || n != (int)we.Num(k)) { problem = $"events: web {we.Num(k)} {k}, port {(events.TryGetValue(k, out int m) ? m : 0)}"; break; }
                Program.Ok(problem == "", $"units {name}: {ticks} ticks identical to web ({evs}) {problem}");
            }
        }
    }
}
