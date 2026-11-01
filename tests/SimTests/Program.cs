using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;

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

        static int Main(string[] args)
        {
            Root = FindRoot();
            var sw = Stopwatch.StartNew();
            Run("rng matches web", Checks.Rng);
            Run("dmath matches V8", Checks.MathFns);
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
            catch (Exception e) { Ok(false, $"check '{name}' crashed: {e.GetType().Name}: {e.Message}"); }
        }

        public static void Ok(bool cond, string what)
        {
            if (cond) { _passed++; Console.WriteLine("  ok   " + what); }
            else { _failed++; Console.WriteLine("  FAIL " + what); }
        }

        public static object Load(string path) => Json.Parse(File.ReadAllText(path));
        public static long HexBits(string h) => unchecked((long)ulong.Parse(h, NumberStyles.HexNumber, CultureInfo.InvariantCulture));
    }

    static class Checks
    {
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
                    for (int i = 0; i < args.Length; i++) args[i] = DMath.FromBits(Program.HexBits((string)row[i]));
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
    }
}
