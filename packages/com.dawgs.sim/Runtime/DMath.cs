using System;

namespace DawgsUprising.Sim
{
    /// <summary>
    /// Deterministic maths for the SIM: the exact results the web game gets from V8 (Node 22 / V8 12.4, which
    /// the golden recordings come from), on every OS and runtime. System.Math.Sin/Cos/Atan2/Pow and
    /// UnityEngine.Mathf go through platform libraries that can differ in the last bit between Windows, macOS,
    /// Linux, Mono and IL2CPP, and from V8: enough to make two lockstep machines drift apart.
    ///
    /// Ported from V8 12.4.254.21 src/base/ieee754.cc (fdlibm sin, cos, atan, atan2, pow) and
    /// src/builtins/math.tq (Math.hypot, Math.round).
    /// Use these in the SIM instead of Math.Sin, Cos, Atan2, Pow, Round and vector lengths.
    /// Floor, Ceiling, Abs, Min, Max, Sqrt and + - * / are exact everywhere.
    /// </summary>
    public static class DMath
    {
        // ---------- bit access (fdlibm's GET_HIGH_WORD and friends) ----------
        public static long Bits(double x) => BitConverter.DoubleToInt64Bits(x);
        public static double FromBits(long b) => BitConverter.Int64BitsToDouble(b);
        static int Hi(double x) => (int)(Bits(x) >> 32);
        static uint Lo(double x) => unchecked((uint)Bits(x));
        static double Words(int hi, uint lo) => FromBits(((long)hi << 32) | lo);
        static double SetLo(double x, uint lo) => Words(Hi(x), lo);
        static double SetHi(double x, int hi) => Words(hi, Lo(x));

        // ---------- JS Math.round / Math.hypot ----------

        /// <summary>JS Math.round: halves go up (-2.5 -> -2), unlike Math.Round's banker's rounding.</summary>
        public static double RoundJs(double x)
        {
            double c = Math.Ceiling(x);
            return c - 0.5 > x ? c - 1.0 : c;
        }

        /// <summary>JS Math.hypot(a, b), V8's exact algorithm (normalised Kahan sum).</summary>
        public static double Hypot(double a, double b)
        {
            if (double.IsNaN(a) || double.IsNaN(b))
                return double.IsInfinity(a) || double.IsInfinity(b) ? double.PositiveInfinity : double.NaN;
            a = Math.Abs(a); b = Math.Abs(b);
            double mx = a > b ? a : b;
            if (double.IsInfinity(mx)) return double.PositiveInfinity;
            if (mx == 0) return 0;
            double s = 0, comp = 0;
            double n = a / mx, summand = n * n - comp, pre = s + summand;
            comp = (pre - s) - summand; s = pre;
            n = b / mx; summand = n * n - comp; pre = s + summand;
            s = pre;
            return Math.Sqrt(s) * mx;
        }

        /// <summary>JS Math.hypot with three arguments.</summary>
        public static double Hypot3(double a, double b, double c)
        {
            if (double.IsNaN(a) || double.IsNaN(b) || double.IsNaN(c))
                return double.IsInfinity(a) || double.IsInfinity(b) || double.IsInfinity(c) ? double.PositiveInfinity : double.NaN;
            a = Math.Abs(a); b = Math.Abs(b); c = Math.Abs(c);
            double mx = Math.Max(a, Math.Max(b, c));
            if (double.IsInfinity(mx)) return double.PositiveInfinity;
            if (mx == 0) return 0;
            double s = 0, comp = 0;
            foreach (double v in new[] { a, b, c })
            {
                double n = v / mx, summand = n * n - comp, pre = s + summand;
                comp = (pre - s) - summand; s = pre;
            }
            return Math.Sqrt(s) * mx;
        }

        // ---------- sin / cos ----------

        static readonly int[] NPIO2_HW = {
            0x3FF921FB, 0x400921FB, 0x4012D97C, 0x401921FB, 0x401F6A7A, 0x4022D97C,
            0x4025FDBB, 0x402921FB, 0x402C463A, 0x402F6A7A, 0x4031475C, 0x4032D97C,
            0x40346B9C, 0x4035FDBB, 0x40378FDB, 0x403921FB, 0x403AB41B, 0x403C463A,
            0x403DD85A, 0x403F6A7A, 0x40407E4C, 0x4041475C, 0x4042106C, 0x4042D97C,
            0x4043A28C, 0x40446B9C, 0x404534AC, 0x4045FDBB, 0x4046C6CB, 0x40478FDB,
            0x404858EB, 0x404921FB };

        const double invpio2 = 6.36619772367581382433e-01, pio2_1 = 1.57079632673412561417e+00,
            pio2_1t = 6.07710050650619224932e-11, pio2_2 = 6.07710050630396597660e-11,
            pio2_2t = 2.02226624879595063154e-21, pio2_3 = 2.02226624871116645580e-21,
            pio2_3t = 8.47842766036889956997e-32;

        /// <summary>x = n*pi/2 + (y0 + y1). Handles |x| up to about 1.6e6 (more is never used by the game).</summary>
        static int RemPio2(double x, out double y0, out double y1)
        {
            int hx = Hi(x), ix = hx & 0x7FFFFFFF;
            double z;
            if (ix <= 0x3FE921FB) { y0 = x; y1 = 0; return 0; }
            if (ix < 0x4002D97C)
            {
                if (hx > 0)
                {
                    z = x - pio2_1;
                    if (ix != 0x3FF921FB) { y0 = z - pio2_1t; y1 = (z - y0) - pio2_1t; }
                    else { z -= pio2_2; y0 = z - pio2_2t; y1 = (z - y0) - pio2_2t; }
                    return 1;
                }
                z = x + pio2_1;
                if (ix != 0x3FF921FB) { y0 = z + pio2_1t; y1 = (z - y0) + pio2_1t; }
                else { z += pio2_2; y0 = z + pio2_2t; y1 = (z - y0) + pio2_2t; }
                return -1;
            }
            if (ix <= 0x413921FB)
            {
                double t = Math.Abs(x);
                int n = (int)(t * invpio2 + 0.5);
                double fn = n, r = t - fn * pio2_1, w = fn * pio2_1t;
                if (n < 32 && ix != NPIO2_HW[n - 1]) y0 = r - w;
                else
                {
                    int j = ix >> 20;
                    y0 = r - w;
                    int i = j - ((Hi(y0) >> 20) & 0x7FF);
                    if (i > 16)
                    {
                        t = r; w = fn * pio2_2; r = t - w; w = fn * pio2_2t - ((t - r) - w); y0 = r - w;
                        i = j - ((Hi(y0) >> 20) & 0x7FF);
                        if (i > 49) { t = r; w = fn * pio2_3; r = t - w; w = fn * pio2_3t - ((t - r) - w); y0 = r - w; }
                    }
                }
                y1 = (r - y0) - w;
                if (hx < 0) { y0 = -y0; y1 = -y1; return -n; }
                return n;
            }
            if (ix >= 0x7FF00000) { y0 = y1 = x - x; return 0; }
            throw new ArgumentOutOfRangeException(nameof(x), "DMath: argument too large for sin/cos");
        }

        static double KCos(double x, double y)
        {
            const double C1 = 4.16666666666666019037e-02, C2 = -1.38888888888741095749e-03,
                C3 = 2.48015872894767294178e-05, C4 = -2.75573143513906633035e-07,
                C5 = 2.08757232129817482790e-09, C6 = -1.13596475577881948265e-11;
            int ix = Hi(x) & 0x7FFFFFFF;
            if (ix < 0x3E400000 && (int)x == 0) return 1.0;
            double z = x * x, r = z * (C1 + z * (C2 + z * (C3 + z * (C4 + z * (C5 + z * C6)))));
            if (ix < 0x3FD33333) return 1.0 - (0.5 * z - (z * r - x * y));
            double qx = ix > 0x3FE90000 ? 0.28125 : Words(ix - 0x00200000, 0);
            double iz = 0.5 * z - qx, a = 1.0 - qx;
            return a - (iz - (z * r - x * y));
        }

        static double KSin(double x, double y, int iy)
        {
            const double S1 = -1.66666666666666324348e-01, S2 = 8.33333333332248946124e-03,
                S3 = -1.98412698298579493134e-04, S4 = 2.75573137070700676789e-06,
                S5 = -2.50507602534068634195e-08, S6 = 1.58969099521155010221e-10;
            int ix = Hi(x) & 0x7FFFFFFF;
            if (ix < 0x3E400000 && (int)x == 0) return x;
            double z = x * x, v = z * x, r = S2 + z * (S3 + z * (S4 + z * (S5 + z * S6)));
            if (iy == 0) return x + v * (S1 + z * r);
            return x - ((z * (0.5 * y - v * r) - y) - v * S1);
        }

        public static double Sin(double x)
        {
            int ix = Hi(x) & 0x7FFFFFFF;
            if (ix <= 0x3FE921FB) return KSin(x, 0, 0);
            if (ix >= 0x7FF00000) return x - x;
            int n = RemPio2(x, out double y0, out double y1);
            switch (n & 3)
            {
                case 0: return KSin(y0, y1, 1);
                case 1: return KCos(y0, y1);
                case 2: return -KSin(y0, y1, 1);
                default: return -KCos(y0, y1);
            }
        }

        public static double Cos(double x)
        {
            int ix = Hi(x) & 0x7FFFFFFF;
            if (ix <= 0x3FE921FB) return KCos(x, 0);
            if (ix >= 0x7FF00000) return x - x;
            int n = RemPio2(x, out double y0, out double y1);
            switch (n & 3)
            {
                case 0: return KCos(y0, y1);
                case 1: return -KSin(y0, y1, 1);
                case 2: return -KCos(y0, y1);
                default: return KSin(y0, y1, 1);
            }
        }

        // ---------- atan / atan2 ----------

        static readonly double[] atanhi = { 4.63647609000806093515e-01, 7.85398163397448278999e-01, 9.82793723247329054082e-01, 1.57079632679489655800e+00 };
        static readonly double[] atanlo = { 2.26987774529616870924e-17, 3.06161699786838301793e-17, 1.39033110312309984516e-17, 6.12323399573676603587e-17 };
        static readonly double[] aT = {
            3.33333333333329318027e-01, -1.99999999998764832476e-01, 1.42857142725034663711e-01,
            -1.11111104054623557880e-01, 9.09088713343650656196e-02, -7.69187620504482999495e-02,
            6.66107313738753120669e-02, -5.83357013379057348645e-02, 4.97687799461593236017e-02,
            -3.65315727442169155270e-02, 1.62858201153657823623e-02 };

        public static double Atan(double x)
        {
            int hx = Hi(x), ix = hx & 0x7FFFFFFF, id;
            if (ix >= 0x44100000)
            {
                if (ix > 0x7FF00000 || (ix == 0x7FF00000 && Lo(x) != 0)) return x + x;
                return hx > 0 ? atanhi[3] + atanlo[3] : -atanhi[3] - atanlo[3];
            }
            if (ix < 0x3FDC0000)
            {
                if (ix < 0x3E400000 && 1.0e300 + x > 1.0) return x;
                id = -1;
            }
            else
            {
                x = Math.Abs(x);
                if (ix < 0x3FF30000)
                {
                    if (ix < 0x3FE60000) { id = 0; x = (2.0 * x - 1.0) / (2.0 + x); }
                    else { id = 1; x = (x - 1.0) / (x + 1.0); }
                }
                else
                {
                    if (ix < 0x40038000) { id = 2; x = (x - 1.5) / (1.0 + 1.5 * x); }
                    else { id = 3; x = -1.0 / x; }
                }
            }
            double z = x * x, w = z * z;
            double s1 = z * (aT[0] + w * (aT[2] + w * (aT[4] + w * (aT[6] + w * (aT[8] + w * aT[10])))));
            double s2 = w * (aT[1] + w * (aT[3] + w * (aT[5] + w * (aT[7] + w * aT[9]))));
            if (id < 0) return x - x * (s1 + s2);
            z = atanhi[id] - ((x * (s1 + s2) - atanlo[id]) - x);
            return hx < 0 ? -z : z;
        }

        public static double Atan2(double y, double x)
        {
            const double tiny = 1.0e-300, pi_o_4 = 7.8539816339744827900E-01, pi_o_2 = 1.5707963267948965580E+00,
                pi = 3.1415926535897931160E+00, pi_lo = 1.2246467991473531772E-16;
            int hx = Hi(x), ix = hx & 0x7FFFFFFF, hy = Hi(y), iy = hy & 0x7FFFFFFF;
            uint lx = Lo(x), ly = Lo(y);
            if ((ix | (lx != 0 ? 1 : 0)) > 0x7FF00000 || (iy | (ly != 0 ? 1 : 0)) > 0x7FF00000) return x + y;
            if (hx == 0x3FF00000 && lx == 0) return Atan(y);
            int m = ((hy >> 31) & 1) | ((hx >> 30) & 2);
            if ((iy | (int)ly) == 0)
            {
                switch (m) { case 0: case 1: return y; case 2: return pi + tiny; default: return -pi - tiny; }
            }
            if ((ix | (int)lx) == 0) return hy < 0 ? -pi_o_2 - tiny : pi_o_2 + tiny;
            if (ix == 0x7FF00000)
            {
                if (iy == 0x7FF00000)
                {
                    switch (m) { case 0: return pi_o_4 + tiny; case 1: return -pi_o_4 - tiny; case 2: return 3.0 * pi_o_4 + tiny; default: return -3.0 * pi_o_4 - tiny; }
                }
                switch (m) { case 0: return 0.0; case 1: return -0.0; case 2: return pi + tiny; default: return -pi - tiny; }
            }
            if (iy == 0x7FF00000) return hy < 0 ? -pi_o_2 - tiny : pi_o_2 + tiny;
            int k = (iy - ix) >> 20;
            double z;
            if (k > 60) { z = pi_o_2 + 0.5 * pi_lo; m &= 1; }
            else if (hx < 0 && k < -60) z = 0.0;
            else z = Atan(Math.Abs(y / x));
            switch (m)
            {
                case 0: return z;
                case 1: return -z;
                case 2: return pi - (z - pi_lo);
                default: return (z - pi_lo) - pi;
            }
        }

        // ---------- pow ----------

        public static double Pow(double x, double y)
        {
            const double two53 = 9007199254740992.0, huge = 1.0e300, tiny = 1.0e-300,
                L1 = 5.99999999999994648725e-01, L2 = 4.28571428578550184252e-01, L3 = 3.33333329818377432918e-01,
                L4 = 2.72728123808534006489e-01, L5 = 2.30660745775561754067e-01, L6 = 2.06975017800338417784e-01,
                P1 = 1.66666666666666019037e-01, P2 = -2.77777777770155933842e-03, P3 = 6.61375632143793436117e-05,
                P4 = -1.65339022054652515390e-06, P5 = 4.13813679705723846039e-08,
                lg2 = 6.93147180559945286227e-01, lg2_h = 6.93147182464599609375e-01, lg2_l = -1.90465429995776804525e-09,
                ovt = 8.0085662595372944372e-0017, cp = 9.61796693925975554329e-01, cp_h = 9.61796700954437255859e-01,
                cp_l = -7.02846165095275826516e-09, ivln2 = 1.44269504088896338700e+00,
                ivln2_h = 1.44269502162933349609e+00, ivln2_l = 1.92596299112661746887e-08;
            double[] bp = { 1.0, 1.5 }, dp_h = { 0.0, 5.84962487220764160156e-01 }, dp_l = { 0.0, 1.35003920212974897128e-08 };
            unchecked
            {
                double z, ax, z_h, z_l, p_h, p_l, y1, t1, t2, r, s, t, u, v, w;
                int i, j, k, yisint, n;
                int hx = Hi(x), hy = Hi(y);
                uint lx = Lo(x), ly = Lo(y);
                int ix = hx & 0x7fffffff, iy = hy & 0x7fffffff;
                if ((iy | (int)ly) == 0) return 1.0;
                if (ix > 0x7ff00000 || (ix == 0x7ff00000 && lx != 0) || iy > 0x7ff00000 || (iy == 0x7ff00000 && ly != 0)) return x + y;
                yisint = 0;
                if (hx < 0)
                {
                    if (iy >= 0x43400000) yisint = 2;
                    else if (iy >= 0x3ff00000)
                    {
                        k = (iy >> 20) - 0x3ff;
                        if (k > 20) { j = (int)(ly >> (52 - k)); if ((j << (52 - k)) == (int)ly) yisint = 2 - (j & 1); }
                        else if (ly == 0) { j = iy >> (20 - k); if ((j << (20 - k)) == iy) yisint = 2 - (j & 1); }
                    }
                }
                if (ly == 0)
                {
                    if (iy == 0x7ff00000)
                    {
                        if (((ix - 0x3ff00000) | (int)lx) == 0) return y - y;
                        else if (ix >= 0x3ff00000) return hy >= 0 ? y : 0.0;
                        else return hy < 0 ? -y : 0.0;
                    }
                    if (iy == 0x3ff00000) return hy < 0 ? 1.0 / x : x;
                    if (hy == 0x40000000) return x * x;
                    if (hy == 0x3fe00000 && hx >= 0) return Math.Sqrt(x);
                }
                ax = Math.Abs(x);
                if (lx == 0 && (ix == 0x7ff00000 || ix == 0 || ix == 0x3ff00000))
                {
                    z = ax;
                    if (hy < 0) z = 1.0 / z;
                    if (hx < 0)
                    {
                        if (((ix - 0x3ff00000) | yisint) == 0) z = double.NaN;
                        else if (yisint == 1) z = -z;
                    }
                    return z;
                }
                n = (hx >> 31) + 1;
                if ((n | yisint) == 0) return double.NaN;
                s = 1.0;
                if ((n | (yisint - 1)) == 0) s = -1.0;
                if (iy > 0x41e00000)
                {
                    if (iy > 0x43f00000)
                    {
                        if (ix <= 0x3fefffff) return hy < 0 ? huge * huge : tiny * tiny;
                        if (ix >= 0x3ff00000) return hy > 0 ? huge * huge : tiny * tiny;
                    }
                    if (ix < 0x3fefffff) return hy < 0 ? s * huge * huge : s * tiny * tiny;
                    if (ix > 0x3ff00000) return hy > 0 ? s * huge * huge : s * tiny * tiny;
                    t = ax - 1.0;
                    w = (t * t) * (0.5 - t * (0.3333333333333333333333 - t * 0.25));
                    u = ivln2_h * t;
                    v = t * ivln2_l - w * ivln2;
                    t1 = SetLo(u + v, 0);
                    t2 = v - (t1 - u);
                }
                else
                {
                    double ss, s2, s_h, s_l, t_h, t_l;
                    n = 0;
                    if (ix < 0x00100000) { ax *= two53; n -= 53; ix = Hi(ax); }
                    n += (ix >> 20) - 0x3ff;
                    j = ix & 0x000fffff;
                    ix = j | 0x3ff00000;
                    if (j <= 0x3988E) k = 0;
                    else if (j < 0xBB67A) k = 1;
                    else { k = 0; n += 1; ix -= 0x00100000; }
                    ax = SetHi(ax, ix);
                    u = ax - bp[k];
                    v = 1.0 / (ax + bp[k]);
                    ss = u * v;
                    s_h = SetLo(ss, 0);
                    t_h = Words(((ix >> 1) | 0x20000000) + 0x00080000 + (k << 18), 0);
                    t_l = ax - (t_h - bp[k]);
                    s_l = v * ((u - s_h * t_h) - s_h * t_l);
                    s2 = ss * ss;
                    r = s2 * s2 * (L1 + s2 * (L2 + s2 * (L3 + s2 * (L4 + s2 * (L5 + s2 * L6)))));
                    r += s_l * (s_h + ss);
                    s2 = s_h * s_h;
                    t_h = SetLo(3.0 + s2 + r, 0);
                    t_l = r - ((t_h - 3.0) - s2);
                    u = s_h * t_h;
                    v = s_l * t_h + t_l * ss;
                    p_h = SetLo(u + v, 0);
                    p_l = v - (p_h - u);
                    z_h = cp_h * p_h;
                    z_l = cp_l * p_h + p_l * cp + dp_l[k];
                    t = n;
                    t1 = SetLo(((z_h + z_l) + dp_h[k]) + t, 0);
                    t2 = z_l - (((t1 - t) - dp_h[k]) - z_h);
                }
                y1 = SetLo(y, 0);
                p_l = (y - y1) * t1 + y * t2;
                p_h = y1 * t1;
                z = p_l + p_h;
                j = Hi(z); i = (int)Lo(z);
                if (j >= 0x40900000)
                {
                    if (((j - 0x40900000) | i) != 0) return s * huge * huge;
                    if (p_l + ovt > z - p_h) return s * huge * huge;
                }
                else if ((j & 0x7fffffff) >= 0x4090cc00)
                {
                    if (((j - unchecked((int)0xc090cc00)) | i) != 0) return s * tiny * tiny;
                    if (p_l <= z - p_h) return s * tiny * tiny;
                }
                i = j & 0x7fffffff;
                k = (i >> 20) - 0x3ff;
                n = 0;
                if (i > 0x3fe00000)
                {
                    n = j + (0x00100000 >> (k + 1));
                    k = ((n & 0x7fffffff) >> 20) - 0x3ff;
                    t = Words(n & ~(0x000fffff >> k), 0);
                    n = ((n & 0x000fffff) | 0x00100000) >> (20 - k);
                    if (j < 0) n = -n;
                    p_h -= t;
                }
                t = SetLo(p_l + p_h, 0);
                u = t * lg2_h;
                v = (p_l - (t - p_h)) * lg2 + t * lg2_l;
                z = u + v;
                w = v - (z - u);
                t = z * z;
                t1 = z - t * (P1 + t * (P2 + t * (P3 + t * (P4 + t * P5))));
                r = (z * t1) / ((t1 - 2.0) - (w + z * w));
                z = 1.0 - (r - z);
                j = Hi(z);
                j += (int)((uint)n << 20);
                if ((j >> 20) <= 0) z = ScaleB(z, n);
                else z = SetHi(z, Hi(z) + (int)((uint)n << 20));
                return s * z;
            }
        }

        /// <summary>z * 2^n exactly (only reached for results near the bottom of the double range).</summary>
        static double ScaleB(double z, int n)
        {
            while (n < -1000) { z *= FromBits(0x0170000000000000); n += 1000; }
            while (n > 1000) { z *= FromBits(0x7E70000000000000); n -= 1000; }
            return z * FromBits((long)(n + 1023) << 52);
        }
    }
}
