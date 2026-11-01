using System;
using System.Collections.Generic;

namespace DawgsUprising.Sim
{
    /// <summary>Anything the spatial hash can hold.</summary>
    public interface ISpatialItem
    {
        double X { get; }
        double Z { get; }
        bool Alive { get; }
    }

    /// <summary>
    /// Spatial hash: units sorted into square buckets so "who is near this point?" only looks at nearby buckets
    /// (web SIM rebuildHash/query). Visit order matches the web game exactly (bucket rows, then columns, then the
    /// order units were added), because combat picks targets in that order.
    /// </summary>
    public sealed class Spatial<T> where T : class, ISpatialItem
    {
        public readonly double X0, Z0, Size;   // Size: bucket edge, balance.engine.hashBucket
        public readonly int BW, BH;
        readonly List<T>[] _buckets;

        public Spatial(double worldW, double worldH, double x0, double z0, double bucket)
        {
            X0 = x0;
            Z0 = z0;
            Size = bucket;
            BW = (int)Math.Ceiling(worldW / bucket);
            BH = (int)Math.Ceiling(worldH / bucket);
            _buckets = new List<T>[BW * BH];
            for (int k = 0; k < _buckets.Length; k++) _buckets[k] = new List<T>();
        }

        public void Rebuild(IEnumerable<T> units)
        {
            foreach (var b in _buckets) b.Clear();
            foreach (var u in units)
            {
                if (!u.Alive) continue;
                int i = Clamp((int)Math.Floor((u.X - X0) / Size), 0, BW - 1);
                int j = Clamp((int)Math.Floor((u.Z - Z0) / Size), 0, BH - 1);
                _buckets[j * BW + i].Add(u);
            }
        }

        /// <summary>Calls fn(unit, squared distance) for every live unit within r of (x, z).</summary>
        public void Query(double x, double z, double r, Action<T, double> fn)
        {
            int i0 = Math.Max(0, (int)Math.Floor((x - r - X0) / Size));
            int i1 = Math.Min(BW - 1, (int)Math.Floor((x + r - X0) / Size));
            int j0 = Math.Max(0, (int)Math.Floor((z - r - Z0) / Size));
            int j1 = Math.Min(BH - 1, (int)Math.Floor((z + r - Z0) / Size));
            double r2 = r * r;
            for (int j = j0; j <= j1; j++)
                for (int i = i0; i <= i1; i++)
                    foreach (var u in _buckets[j * BW + i])
                    {
                        double dx = u.X - x, dz = u.Z - z, d2 = dx * dx + dz * dz;
                        if (d2 <= r2 && u.Alive) fn(u, d2);
                    }
        }

        static int Clamp(int v, int lo, int hi) => v < lo ? lo : v > hi ? hi : v;
    }
}
