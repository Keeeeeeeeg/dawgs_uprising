using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace DawgsUprising.Sim
{
    /// <summary>A JSON object that keeps its keys in file order (the web game iterates objects in order).</summary>
    public sealed class JObj
    {
        readonly Dictionary<string, object> _map = new Dictionary<string, object>();
        public readonly List<string> Keys = new List<string>();
        public int Count => Keys.Count;
        public bool Has(string k) => _map.ContainsKey(k);
        public object this[string k]
        {
            get => _map.TryGetValue(k, out var v) ? v : null;
            set { if (!_map.ContainsKey(k)) Keys.Add(k); _map[k] = value; }
        }
        public object Get(string k, object fallback) => _map.TryGetValue(k, out var v) ? v : fallback;
        public double Num(string k) => Convert.ToDouble(_map[k], CultureInfo.InvariantCulture);
        public double Num(string k, double fallback) => _map.TryGetValue(k, out var v) && v != null ? Convert.ToDouble(v, CultureInfo.InvariantCulture) : fallback;
        public string Str(string k) => _map.TryGetValue(k, out var v) ? v as string : null;
        public bool Bool(string k) => _map.TryGetValue(k, out var v) && v is bool b && b;
        public JObj Obj(string k) => _map.TryGetValue(k, out var v) ? v as JObj : null;
        public List<object> Arr(string k) => _map.TryGetValue(k, out var v) ? v as List<object> : null;
        public int Int(string k) => (int)Num(k);
        public double[] Nums(string k)
        {
            var a = Arr(k);
            var r = new double[a.Count];
            for (int i = 0; i < r.Length; i++) r[i] = Convert.ToDouble(a[i], CultureInfo.InvariantCulture);
            return r;
        }
        public string[] Strs(string k)
        {
            var a = Arr(k);
            var r = new string[a.Count];
            for (int i = 0; i < r.Length; i++) r[i] = (string)a[i];
            return r;
        }
    }

    /// <summary>
    /// Small JSON reader for the SIM's data files: objects (JObj, ordered), arrays (List&lt;object&gt;), numbers
    /// (double), strings, booleans, null. A string "#" + 16 hex digits is an exact 64-bit double (the data
    /// files store long numbers and -0 that way, because JSON tools round or lose them). No engine dependency.
    /// </summary>
    public static class Json
    {
        public static object Parse(string text)
        {
            int i = 0;
            object v = Value(text, ref i);
            Ws(text, ref i);
            if (i != text.Length) throw new FormatException($"Json: unexpected text at {i}");
            return v;
        }

        static void Ws(string s, ref int i) { while (i < s.Length && (s[i] == ' ' || s[i] == '\t' || s[i] == '\n' || s[i] == '\r')) i++; }

        static object Value(string s, ref int i)
        {
            Ws(s, ref i);
            if (i >= s.Length) throw new FormatException("Json: unexpected end");
            char c = s[i];
            if (c == '{')
            {
                var o = new JObj(); i++; Ws(s, ref i);
                if (s[i] == '}') { i++; return o; }
                while (true)
                {
                    Ws(s, ref i); string k = Str(s, ref i); Ws(s, ref i);
                    if (s[i] != ':') throw new FormatException($"Json: ':' expected at {i}");
                    i++; o[k] = Value(s, ref i); Ws(s, ref i);
                    if (s[i] == ',') { i++; continue; }
                    if (s[i] == '}') { i++; return o; }
                    throw new FormatException($"Json: ',' or '}}' expected at {i}");
                }
            }
            if (c == '[')
            {
                var a = new List<object>(); i++; Ws(s, ref i);
                if (s[i] == ']') { i++; return a; }
                while (true)
                {
                    a.Add(Value(s, ref i)); Ws(s, ref i);
                    if (s[i] == ',') { i++; continue; }
                    if (s[i] == ']') { i++; return a; }
                    throw new FormatException($"Json: ',' or ']' expected at {i}");
                }
            }
            if (c == '"')
            {
                string str = Str(s, ref i);
                if (str.Length == 17 && str[0] == '#' && IsHex(str, 1)) return DMath.FromBits(unchecked((long)ulong.Parse(str.Substring(1), NumberStyles.HexNumber, CultureInfo.InvariantCulture)));
                return str;
            }
            if (s.Length - i >= 4 && string.CompareOrdinal(s, i, "true", 0, 4) == 0) { i += 4; return true; }
            if (s.Length - i >= 5 && string.CompareOrdinal(s, i, "false", 0, 5) == 0) { i += 5; return false; }
            if (s.Length - i >= 4 && string.CompareOrdinal(s, i, "null", 0, 4) == 0) { i += 4; return null; }
            int st = i;
            while (i < s.Length && "+-0123456789.eE".IndexOf(s[i]) >= 0) i++;
            if (st == i) throw new FormatException($"Json: unexpected '{c}' at {i}");
            return double.Parse(s.Substring(st, i - st), NumberStyles.Float, CultureInfo.InvariantCulture);
        }

        static bool IsHex(string s, int from)
        {
            for (int k = from; k < s.Length; k++) if (Uri.IsHexDigit(s[k]) == false) return false;
            return true;
        }

        static string Str(string s, ref int i)
        {
            if (s[i] != '"') throw new FormatException($"Json: string expected at {i}");
            i++;
            var sb = new StringBuilder();
            while (s[i] != '"')
            {
                char c = s[i++];
                if (c != '\\') { sb.Append(c); continue; }
                char e = s[i++];
                switch (e)
                {
                    case '"': sb.Append('"'); break;
                    case '\\': sb.Append('\\'); break;
                    case '/': sb.Append('/'); break;
                    case 'b': sb.Append('\b'); break;
                    case 'f': sb.Append('\f'); break;
                    case 'n': sb.Append('\n'); break;
                    case 'r': sb.Append('\r'); break;
                    case 't': sb.Append('\t'); break;
                    case 'u': sb.Append((char)int.Parse(s.Substring(i, 4), NumberStyles.HexNumber, CultureInfo.InvariantCulture)); i += 4; break;
                    default: throw new FormatException($"Json: bad escape at {i}");
                }
            }
            i++;
            return sb.ToString();
        }
    }
}
