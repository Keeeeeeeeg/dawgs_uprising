using System;

namespace DawgsUprising.Sim
{
    /// <summary>
    /// Value noise, bit-exact with the web SIM's makeNoise() and fbm(): a size x size table of seeded random
    /// values stored as 32-bit floats (the web uses a Float32Array), smoothly interpolated.
    /// </summary>
    public sealed class ValueNoise
    {
        readonly float[] _p;
        readonly int _n, _mask;

        public ValueNoise(long seed, int size)
        {
            _n = size;
            _mask = size - 1;
            _p = new float[size * size];
            var r = new Rng(seed);
            for (int i = 0; i < _p.Length; i++) _p[i] = (float)r.Next();
        }

        public double Sample(double x, double y)
        {
            double xf = Math.Floor(x), yf = Math.Floor(y);
            double fx = x - xf, fy = y - yf;
            double u = fx * fx * (3.0 - 2.0 * fx);
            double v = fy * fy * (3.0 - 2.0 * fy);
            int xi = (int)xf, yi = (int)yf;
            int x0 = (xi & _mask) * _n, x1 = ((xi + 1) & _mask) * _n;
            int y0 = yi & _mask, y1 = (yi + 1) & _mask;
            double a = _p[x0 + y0], b = _p[x1 + y0], c = _p[x0 + y1], d = _p[x1 + y1];
            return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
        }

        /// <summary>Fractal sum of `octaves` layers: amplitude starts at `gain` and is multiplied by it each layer,
        /// frequency is multiplied by `lacunarity`.</summary>
        public double Fbm(double x, double y, int octaves, double gain, double lacunarity)
        {
            double s = 0, a = gain, f = 1, t = 0;
            for (int i = 0; i < octaves; i++)
            {
                s += Sample(x * f, y * f) * a;
                t += a;
                a *= gain;
                f *= lacunarity;
            }
            return s / t;
        }
    }
}
