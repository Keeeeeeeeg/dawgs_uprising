using System;
using System.Collections.Generic;

namespace DawgsUprising.Sim
{
    public sealed class Circle { public double X, Z, R; }

    /// <summary>A terrain feature that blocks movement: rocks, ruins, wrecks... and, outside a walled Town, its
    /// workshops and yards (W x D footprint, Ht tall, Town = the town's zone id).</summary>
    public sealed class Prop
    {
        public string Type;
        public double X, Z, Rot, V, H;
        public double W, D, Ht;
        public int? Town;
        public List<Circle> Circles = new List<Circle>();
    }

    /// <summary>An inlet cut from the sea toward a coastal base: from A to B along (Ux, Uz), R wide.</summary>
    public sealed class Cove
    {
        public int Zone;
        public double Ax, Az, Bx, Bz, Ux, Uz, R;
    }

    /// <summary>
    /// Terrain: heights, passability and props for one battle, ported from the web SIM's buildMap() and its
    /// terrain queries (heightAt, cellOf, passable). Bit-exact with the web game: heights are 32-bit floats like
    /// the web's Float32Array, all maths goes through DMath, and every number comes from mapgen.json ("terrain").
    /// </summary>
    public sealed class Terrain
    {
        public double W, H, X0, Z0, Cell;
        public int GW, GH, VW, VH;
        public float[] Hv;            // (GW+1) x (GH+1) vertex heights
        public byte[] LandGrid;       // GW x GH: 1 = ground units can stand here
        public byte[] WaterGrid;      // GW x GH: 1 = deep enough for boats
        public List<Prop> Props = new List<Prop>();
        public List<Cove> Coves = new List<Cove>();

        // ---------- queries (web heightAt, cellOf, passable) ----------

        public double HeightAt(double x, double z)
        {
            double fx = (x - X0) / Cell, fz = (z - Z0) / Cell;
            fx = Math.Max(0.0, Math.Min(GW - 0.001, fx));
            fz = Math.Max(0.0, Math.Min(GH - 0.001, fz));
            int i = (int)Math.Floor(fx), j = (int)Math.Floor(fz);
            double u = fx - i, v = fz - j;
            double a = Hv[j * VW + i], b = Hv[j * VW + i + 1], c = Hv[(j + 1) * VW + i], d = Hv[(j + 1) * VW + i + 1];
            return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
        }

        public int CellOf(double x, double z)
        {
            int i = (int)Math.Floor((x - X0) / Cell), j = (int)Math.Floor((z - Z0) / Cell);
            if (i < 0 || j < 0 || i >= GW || j >= GH) return -1;
            return j * GW + i;
        }

        public bool Passable(double x, double z, byte[] grid = null)
        {
            int c = CellOf(x, z);
            if (c < 0) return false;
            return (grid ?? LandGrid)[c] == 1;
        }

        /// <summary>Vertex height nearest a point (web hvAt / hAt inside buildMap).</summary>
        double HvAt(double x, double z)
        {
            int i = (int)Math.Max(0.0, Math.Min(GW, DMath.RoundJs((x - X0) / Cell)));
            int j = (int)Math.Max(0.0, Math.Min(GH, DMath.RoundJs((z - Z0) / Cell)));
            return Hv[j * VW + i];
        }

        // ---------- building (web buildMap) ----------

        /// <summary>m: the map with ZonesFinal (after start slots). seed: the battle seed.</summary>
        public static Terrain Build(MapDef m, long seed, JObj balance, JObj gen)
        {
            var t = new Terrain();
            t.BuildAll(m, seed, balance, gen);
            return t;
        }

        void BuildAll(MapDef m, long seed, JObj balance, JObj gen)
        {
            var T = gen.Obj("terrain");
            var BZ = balance.Obj("zones");
            var CV = gen.Obj("convert");
            Cell = T.Num("cell");
            W = m.W;
            H = m.H;
            GW = (int)(W / Cell);
            GH = (int)(H / Cell);
            X0 = -W / 2.0;
            Z0 = -H / 2.0;
            VW = GW + 1;
            VH = GH + 1;
            var ns = T.Nums("noiseSeeds");
            int size = T.Int("noiseSize");
            var n1 = new ValueNoise(seed + (long)ns[0], size);
            var n2 = new ValueNoise(seed + (long)ns[1], size);
            var n3 = new ValueNoise(seed + (long)ns[2], size);
            int oct = T.Int("octaves");
            double gain = T.Num("octaveGain"), lac = T.Num("octaveLacunarity");
            var zones = m.ZonesFinal;
            double SX = m.Ns[0], SZ = m.Ns[1];
            double pad = T.Num("zoneBlobPad");
            var zbr = zones.ConvertAll(z => BZ.Obj(z.Type).Num("r") + pad);

            double landStart = T.Num("landStart"), zw = T.Num("zoneBlobWeight"), lf = T.Num("landNoiseFreq");
            double lox = T.Num("landNoiseOffX"), loz = T.Num("landNoiseOffZ"), lmid = T.Num("landNoiseMid"), lamp = T.Num("landNoiseAmp");
            double cdep = CV.Num("carveDepth"), cflo = CV.Num("carveFloor"), nland = CV.Num("neckLand"), efade = CV.Num("edgeFade");
            double seaFloor = T.Num("seaFloor"), seaSlope = T.Num("seaSlope"), seaDrop = T.Num("seaDrop"), rise = T.Num("hillRise");
            double baseH = T.Num("baseHeight"), cap = T.Num("landCap"), lift = T.Num("landLift"), hf = T.Num("hillNoiseFreq");
            double hmid = T.Num("hillNoiseMid"), hamp = T.Num("hillAmp"), rexp = T.Num("ridgeExp"), rbase = T.Num("ridgeBase");
            double rvar = T.Num("ridgeVar"), rf = T.Num("ridgeNoiseFreq");

            double Land(double x, double z)
            {
                double L = landStart;
                foreach (var b in m.Blobs)
                {
                    double v = 1.0 - DMath.Hypot((x - b.X) / b.Rx, (z - b.Z) / b.Rz);
                    if (v > L) L = v;
                }
                for (int k = 0; k < zones.Count; k++)
                {
                    double r = zbr[k];
                    double v = (1.0 - DMath.Hypot((x - zones[k].X) / r, (z - zones[k].Z) / r)) * zw;
                    if (v > L) L = v;
                }
                L += (n1.Fbm(x / SX * lf + lox, z / SZ * lf + loz, oct, gain, lac) - lmid) * lamp;
                foreach (var c in m.Carves)
                {
                    double d = DMath.Hypot(x - c.X, z - c.Z);
                    if (d < c.R) L = Math.Min(L, -(1.0 - d / c.R) * cdep - cflo);
                }
                foreach (var n in m.Necks)
                {
                    double nv = 1.0 - Maps.SegDist(x, z, n.A[0], n.A[1], n.B[0], n.B[1]) / n.W;
                    if (nv * nland > L) L = nv * nland;
                }
                double ex = Math.Min(Math.Min(x - X0, X0 + W - x), Math.Min(z - Z0, Z0 + H - z));
                L -= Math.Max(0.0, (efade - ex) / efade);
                return L;
            }

            double Height(double x, double z)
            {
                double L = Land(x, z);
                if (L < 0.0) return Math.Max(seaFloor, L * seaSlope - seaDrop);
                double kk = Math.Min(1.0, L * rise);
                double h = baseH + Math.Min(L, cap) * lift + (n2.Fbm(x * hf, z * hf, oct, gain, lac) - hmid) * hamp * kk;
                foreach (var r in m.Ridges)
                {
                    double d = Maps.SegDist(x, z, r.A[0], r.A[1], r.B[0], r.B[1]);
                    if (d < r.W)
                        h += r.H * DMath.Pow(1.0 - d / r.W, rexp) * (rbase + rvar * n3.Fbm(x * rf, z * rf, oct, gain, lac)) * kk;
                }
                return h;
            }

            Hv = new float[VW * VH];
            for (int j = 0; j < VH; j++)
                for (int i = 0; i < VW; i++)
                    Hv[j * VW + i] = (float)Height(X0 + i * Cell, Z0 + j * Cell);

            // flatten zone pads
            double tpad = T.Num("townPadExtra"), bin = T.Num("padBlendIn"), bout = T.Num("padBlendOut");
            foreach (var zd in zones)
            {
                double r = BZ.Obj(zd.Type).Num("r") + (zd.Type == "town" ? tpad : 0.0);
                double cx = zd.X, cz = zd.Z;
                double bse = Math.Max(T.Num("padMin"), Math.Min(T.Num("padMax"), Height(cx, cz)));
                double reach = r + bout;
                for (int j = 0; j < VH; j++)
                    for (int i = 0; i < VW; i++)
                    {
                        double x = X0 + i * Cell, z = Z0 + j * Cell;
                        double d = DMath.Hypot(x - cx, z - cz);
                        if (d < reach)
                        {
                            double t = 1.0 - Maps.Smooth(r - bin, r + bout, d);
                            int k = j * VW + i;
                            Hv[k] = (float)(Hv[k] * (1.0 - t) + bse * t);
                        }
                    }
            }

            CutCoves(m, zones, BZ, T);
            Grids(m, T);
            PlaceProps(m, zones, BZ, T, seed);
        }

        /// <summary>Coastal bases sit on a cove: an inlet cut from the sea toward the base (web buildMap).</summary>
        void CutCoves(MapDef m, List<MapZone> zones, JObj BZ, JObj T)
        {
            Coves = new List<Cove>();
            if (m.NoWater) return;
            var skipAll = T.Obj("coveSkip");
            var skip = m.Id != null && skipAll.Has(m.Id) ? skipAll.Nums(m.Id) : new double[0];
            double water = T.Num("coveWater"), R = T.Num("coveR"), step = T.Num("coveStep");
            int rays = T.Int("coveRays");
            for (int zi = 0; zi < zones.Count; zi++)
            {
                var zd = zones[zi];
                if (zd.Port != true || zd.Type == "airbase" || Array.IndexOf(skip, (double)zi) >= 0) continue;
                double r = BZ.Obj(zd.Type).Num("r");
                double cx = zd.X, cz = zd.Z;
                double bestA = 0, bestD = double.PositiveInfinity;
                bool found = false;
                for (int k = 0; k < rays; k++)
                {
                    double a = (double)k / T.Num("coveRays") * T.Num("coveTurn");
                    for (double d = r + T.Num("coveSearchFrom"); d < r + T.Num("coveSearchTo"); d += step)
                        if (HvAt(cx + DMath.Cos(a) * d, cz + DMath.Sin(a) * d) < water)
                        {
                            if (!found || d < bestD) { found = true; bestA = a; bestD = d; }
                            break;
                        }
                }
                if (!found) continue;
                double ux = DMath.Cos(bestA), uz = DMath.Sin(bestA);
                double ax = 0, az = 0, bx = 0, bz = 0, bestLand = -1e9;
                double side = r + T.Num("coveSide"), back = T.Num("coveBack"), maxLen = T.Num("coveMaxLen");
                var tries = new[] { new[] { side, back }, new[] { -side, back }, new[] { side, r * T.Num("coveMidK") },
                    new[] { -side, r * T.Num("coveMidK") }, new[] { 0.0, r + T.Num("coveHeadOut") } };
                foreach (var tri in tries)
                {
                    double lat = tri[0], ax0 = tri[1];
                    double hx = cx - uz * lat + ux * ax0, hz = cz + ux * lat + uz * ax0;
                    double d = 0.0;
                    while (d < maxLen && HvAt(hx + ux * d, hz + uz * d) > water) d += step;
                    if (d >= maxLen) continue;
                    double l = 0.0;
                    for (double t = 0.0; t <= d; t += step) l += Math.Max(0.0, HvAt(hx + ux * t, hz + uz * t));
                    if (l > bestLand)
                    {
                        bestLand = l;
                        ax = hx; az = hz;
                        bx = hx + ux * (d + T.Num("coveTail"));
                        bz = hz + uz * (d + T.Num("coveTail"));
                    }
                }
                if (bestLand < 0.0) continue;
                bool blocked = false;
                foreach (var o in zones)
                    if (!ReferenceEquals(o, zd) && Maps.SegDist(o.X, o.Z, ax, az, bx, bz) < BZ.Obj(o.Type).Num("r") + R + T.Num("coveZoneClear")) { blocked = true; break; }
                if (blocked) continue;
                double nc = R + T.Num("coveNeckClear");
                foreach (var n in m.Necks)
                    if (Maps.SegDist(n.A[0], n.A[1], ax, az, bx, bz) < nc || Maps.SegDist(n.B[0], n.B[1], ax, az, bx, bz) < nc) { blocked = true; break; }
                if (blocked) continue;
                double mg = T.Num("coveMargin"), eOut = T.Num("coveEdgeOut"), eIn = T.Num("coveEdgeIn"), depth = T.Num("coveDepth");
                int j0 = Math.Max(0, (int)Math.Floor((Math.Min(az, bz) - R - mg - Z0) / Cell));
                int j1 = Math.Min(GH, (int)Math.Ceiling((Math.Max(az, bz) + R + mg - Z0) / Cell));
                int i0 = Math.Max(0, (int)Math.Floor((Math.Min(ax, bx) - R - mg - X0) / Cell));
                int i1 = Math.Min(GW, (int)Math.Ceiling((Math.Max(ax, bx) + R + mg - X0) / Cell));
                for (int j = j0; j <= j1; j++)
                    for (int i = i0; i <= i1; i++)
                    {
                        double d = Maps.SegDist(X0 + i * Cell, Z0 + j * Cell, ax, az, bx, bz);
                        if (d > R + eOut) continue;
                        double t = Maps.Smooth(R - eIn, R + eOut, d);
                        int k = j * VW + i;
                        Hv[k] = (float)Math.Min(Hv[k], Hv[k] * t - depth * (1.0 - t));
                    }
                Coves.Add(new Cove { Zone = zi, Ax = ax, Az = az, Bx = bx, Bz = bz, Ux = ux, Uz = uz, R = R });
            }
        }

        void Grids(MapDef m, JObj T)
        {
            LandGrid = new byte[GW * GH];
            WaterGrid = new byte[GW * GH];
            bool noWater = m.NoWater;
            double minH = T.Num("passMinH"), maxAvg = T.Num("passMaxAvg"), maxSlope = T.Num("passMaxSlope"), wmax = T.Num("waterMaxH");
            int we = T.Int("waterEdge");
            for (int j = 0; j < GH; j++)
                for (int i = 0; i < GW; i++)
                {
                    double a = Hv[j * VW + i], b = Hv[j * VW + i + 1], c = Hv[(j + 1) * VW + i], d = Hv[(j + 1) * VW + i + 1];
                    double mx = Math.Max(Math.Max(a, b), Math.Max(c, d)), mn = Math.Min(Math.Min(a, b), Math.Min(c, d));
                    double av = (a + b + c + d) / 4.0;
                    LandGrid[j * GW + i] = (byte)(mn > minH && av < maxAvg && mx - mn < maxSlope ? 1 : 0);
                    WaterGrid[j * GW + i] = (byte)(!noWater && mx < wmax && i > we - 1 && j > we - 1 && i < GW - we && j < GH - we ? 1 : 0);
                }
        }

        /// <summary>Terrain features scattered across the island (web buildMap props). They block movement.</summary>
        void PlaceProps(MapDef m, List<MapZone> zones, JObj BZ, JObj T, long seed)
        {
            Props = new List<Prop>();
            var pr = new Rng(seed ^ (long)T.Num("propSeedXor"));
            var types = m.Palette == "moon" ? T.Strs("propTypesMoon") : T.Strs("propTypes");
            int count = (int)DMath.RoundJs(T.Num("propBase") * W * H / (T.Num("propRefW") * T.Num("propRefH")));
            double edge = T.Num("propEdge"), ringR = T.Num("propRingR");
            var PR = T.Obj("propR");
            int k = 0;
            while (k < count * T.Num("propTriesPer") && Props.Count < count)
            {
                k++;
                double x = X0 + edge + pr.Next() * (W - 2.0 * edge);
                double z = Z0 + edge + pr.Next() * (H - 2.0 * edge);
                double h = HvAt(x, z);
                if (h < T.Num("propMinH") || h > T.Num("propMaxH")) continue;
                bool bad = false;
                foreach (var d in zones)
                    if (DMath.Hypot(d.X - x, d.Z - z) < BZ.Obj(d.Type).Num("r") + T.Num("propZoneClear")) { bad = true; break; }
                if (bad) continue;
                foreach (var p in Props)
                    if (DMath.Hypot(p.X - x, p.Z - z) < T.Num("propSpacing")) { bad = true; break; }
                if (bad) continue;
                foreach (var n in m.Necks)
                    if (Maps.SegDist(x, z, n.A[0], n.A[1], n.B[0], n.B[1]) < T.Num("propNeckClear")) { bad = true; break; }
                if (bad) continue;
                for (double a = 0.0; a < T.Num("propRingEnd"); a += T.Num("propRingStep"))
                    if (HvAt(x + DMath.Cos(a) * ringR, z + DMath.Sin(a) * ringR) < T.Num("propRingMinH")) bad = true;
                if (bad) continue;
                string type = types[Props.Count % types.Length];
                double rot = pr.Next() * T.Num("propTurn");
                double v = pr.Next();
                var prop = new Prop { Type = type, X = x, Z = z, Rot = rot, V = v, H = h };
                if (type == "wreck")
                {
                    double span = T.Num("wreckSpan");
                    for (double t = -span; t <= span; t += span)
                        prop.Circles.Add(new Circle { X = x + DMath.Cos(rot) * t, Z = z + DMath.Sin(rot) * t, R = T.Num("wreckR") });
                }
                else prop.Circles.Add(new Circle { X = x, Z = z, R = PR.Num(type, PR.Num("other")) });
                foreach (var c in prop.Circles) BlockCircle(c.X, c.Z, c.R, T.Num("propCellPad"));
                Props.Add(prop);
            }
        }

        void BlockCircle(double x, double z, double r, double padr)
        {
            int j0 = (int)Math.Floor((z - r - Z0) / Cell), j1 = (int)Math.Floor((z + r - Z0) / Cell);
            int i0 = (int)Math.Floor((x - r - X0) / Cell), i1 = (int)Math.Floor((x + r - X0) / Cell);
            for (int j = j0; j <= j1; j++)
                for (int i = i0; i <= i1; i++)
                {
                    if (i < 0 || j < 0 || i >= GW || j >= GH) continue;
                    double cx = X0 + (i + 0.5) * Cell, cz = Z0 + (j + 0.5) * Cell;
                    if (DMath.Hypot(cx - x, cz - z) <= r + padr) LandGrid[j * GW + i] = 0;
                }
        }
    }
}
