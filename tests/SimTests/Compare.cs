using System;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
using System.Security.Cryptography;
using DawgsUprising.Sim;

namespace DawgsUprising.Sim.Tests
{
    /// <summary>Compares a recording of the web game (parsed JSON) with the port's typed objects.</summary>
    static class Compare
    {
        /// <summary>"" if `got` has everything `want` has (numbers compared bit for bit), else where it first differs.
        /// JSON keys match fields ignoring case; a `false` the port doesn't have counts as the same.</summary>
        public static string FirstDiff(object want, object got, string at)
        {
            if (got is MapZone mz) got = new List<object>(mz.Row());
            if (want is double wd)
            {
                if (!IsNumber(got)) return $"at {at}: web {wd:R}, port {Show(got)}";
                double gd = Convert.ToDouble(got);
                return DMath.Bits(wd) == DMath.Bits(gd) ? "" : $"at {at}: web {wd:R}, port {gd:R}";
            }
            if (want is List<object> wl)
            {
                if (!(got is IList gl) || got is string) return $"at {at}: web a list, port {Show(got)}";
                if (wl.Count != gl.Count) return $"at {at}: web {wl.Count} items, port {gl.Count}";
                for (int i = 0; i < wl.Count; i++)
                {
                    string d = FirstDiff(wl[i], gl[i], $"{at}[{i}]");
                    if (d != "") return d;
                }
                return "";
            }
            if (want is JObj wo)
            {
                if (got == null) return $"at {at}: web an object, port null";
                foreach (var k in wo.Keys)
                {
                    if (!TryGet(got, k, out var gv))
                    {
                        if (wo[k] is bool b && !b) continue;
                        return $"at {at}.{k}: missing";
                    }
                    string d = FirstDiff(wo[k], gv, at + "." + k);
                    if (d != "") return d;
                }
                return "";
            }
            if (want == null) return got == null ? "" : $"at {at}: web null, port {Show(got)}";
            return Equals(want, got) ? "" : $"at {at}: web {Show(want)}, port {Show(got)}";
        }

        static bool IsNumber(object o) => o is double || o is float || o is int || o is long || o is uint || o is byte;

        static string Show(object o) => o == null ? "null" : o is double d ? d.ToString("R") : o.ToString();

        public static bool TryGet(object o, string key, out object value)
        {
            value = null;
            if (o is IDictionary d)
            {
                if (!d.Contains(key)) return false;
                value = d[key];
                return true;
            }
            var f = o.GetType().GetField(key, BindingFlags.Public | BindingFlags.Instance | BindingFlags.IgnoreCase);
            if (f == null) return false;
            value = f.GetValue(o);
            return true;
        }

        public static string Sha(byte[] b)
        {
            using (var h = SHA256.Create()) return BitConverter.ToString(h.ComputeHash(b)).Replace("-", "").ToLowerInvariant();
        }

        /// <summary>SHA-256 of an array's bytes (little-endian, like the web game's typed arrays).</summary>
        public static string Sha(Array a)
        {
            var b = new byte[Buffer.ByteLength(a)];
            Buffer.BlockCopy(a, 0, b, 0, b.Length);
            return Sha(b);
        }

        public static int Count(byte[] b)
        {
            int n = 0;
            foreach (var x in b) n += x;
            return n;
        }
    }
}
