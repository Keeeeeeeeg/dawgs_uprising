using System;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;

namespace DawgsUprising.Sim
{
    /// <summary>A class that reads itself from a JSON array row, like a map's zone ["name", "type", x, z, port].</summary>
    public interface IJsonRow
    {
        void ReadRow(List<object> row);
    }

    /// <summary>
    /// Fills typed data classes from parsed JSON (Json.Parse): each key goes to the public field with the same
    /// name, ignoring case ("garrisonHp" -> GarrisonHp). Keys starting with "_" are notes and skipped. Any other
    /// key with no matching field is an error, so a typo in a
    /// data file is caught when it loads instead of silently reading 0. Runs at load time only (reflection).
    /// Supported field types: numbers, bool, string, nullable numbers, arrays and List of those or of classes,
    /// Dictionary&lt;string, T&gt;, nested classes, IJsonRow, and object / JObj (kept as parsed).
    /// </summary>
    public static class Bind
    {
        static readonly Dictionary<Type, Dictionary<string, FieldInfo>> _fields = new Dictionary<Type, Dictionary<string, FieldInfo>>();

        public static T To<T>(object json) where T : new() => (T)Value(typeof(T), json, typeof(T).Name);

        /// <summary>Copies every key of `o` into the matching fields of an existing object.</summary>
        public static void Into(object target, JObj o, string where)
        {
            var fields = Fields(target.GetType());
            foreach (var k in o.Keys)
            {
                if (k.StartsWith("_")) continue;   // notes for people, like "_about"
                if (!fields.TryGetValue(k.ToLowerInvariant(), out var f))
                    throw new FormatException($"{where}: unknown key '{k}' (no field {target.GetType().Name}.{k})");
                f.SetValue(target, Value(f.FieldType, o[k], where + "." + k));
            }
        }

        static Dictionary<string, FieldInfo> Fields(Type t)
        {
            if (_fields.TryGetValue(t, out var d)) return d;
            d = new Dictionary<string, FieldInfo>();
            foreach (var f in t.GetFields(BindingFlags.Public | BindingFlags.Instance)) d[f.Name.ToLowerInvariant()] = f;
            _fields[t] = d;
            return d;
        }

        static object Value(Type t, object v, string where)
        {
            if (t == typeof(object)) return v;
            if (t == typeof(JObj)) return v as JObj ?? throw Bad(where, "an object", v);
            var under = Nullable.GetUnderlyingType(t);
            if (under != null) return v == null ? null : Value(under, v, where);
            if (v == null)
            {
                if (t.IsValueType) throw Bad(where, t.Name, v);
                return null;
            }
            if (t == typeof(double)) return v is double d ? d : throw Bad(where, "a number", v);
            if (t == typeof(float)) return v is double f ? (float)f : throw Bad(where, "a number", v);
            if (t == typeof(int) || t == typeof(long))
            {
                if (!(v is double n) || Math.Floor(n) != n) throw Bad(where, "a whole number", v);
                return t == typeof(int) ? (object)checked((int)n) : checked((long)n);
            }
            if (t == typeof(bool)) return v is bool b ? b : throw Bad(where, "true or false", v);
            if (t == typeof(string)) return v as string ?? throw Bad(where, "a string", v);
            if (typeof(IJsonRow).IsAssignableFrom(t))
            {
                var row = (IJsonRow)Activator.CreateInstance(t);
                row.ReadRow(v as List<object> ?? throw Bad(where, "an array", v));
                return row;
            }
            if (t.IsArray)
            {
                var src = v as List<object> ?? throw Bad(where, "an array", v);
                var et = t.GetElementType();
                var arr = Array.CreateInstance(et, src.Count);
                for (int i = 0; i < src.Count; i++) arr.SetValue(Value(et, src[i], $"{where}[{i}]"), i);
                return arr;
            }
            if (t.IsGenericType && t.GetGenericTypeDefinition() == typeof(List<>))
            {
                var src = v as List<object> ?? throw Bad(where, "an array", v);
                var et = t.GetGenericArguments()[0];
                var list = (IList)Activator.CreateInstance(t);
                for (int i = 0; i < src.Count; i++) list.Add(Value(et, src[i], $"{where}[{i}]"));
                return list;
            }
            if (t.IsGenericType && t.GetGenericTypeDefinition() == typeof(Dictionary<,>))
            {
                var src = v as JObj ?? throw Bad(where, "an object", v);
                var vt = t.GetGenericArguments()[1];
                var dict = (IDictionary)Activator.CreateInstance(t);
                foreach (var k in src.Keys) dict[k] = Value(vt, src[k], where + "." + k);
                return dict;
            }
            if (t.IsClass)
            {
                var o = v as JObj ?? throw Bad(where, "an object", v);
                var target = Activator.CreateInstance(t);
                Into(target, o, where);
                return target;
            }
            throw new FormatException($"{where}: can't read into a {t.Name}");
        }

        static FormatException Bad(string where, string want, object got) =>
            new FormatException($"{where}: expected {want}, found {(got == null ? "null" : got is string s ? $"\"{s}\"" : got.ToString())}");
    }
}
