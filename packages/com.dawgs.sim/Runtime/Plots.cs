using System;
using System.Collections.Generic;

namespace DawgsUprising.Sim
{
    /// <summary>
    /// Build plots: each base grows like a small settlement that follows the ground (web createGame, "build plots").
    /// Airbases get a runway on the flattest open line, a taxiway, an apron and terminal stands; Towns and HQs run
    /// streets out through their gates; Fortresses get a gate road and a ring of bastions; Ports add quays along
    /// their cove or waterfront. Every plot is levelled into the ground. No randomness here, but the order things
    /// happen in matters (streets block later plots), so it follows the web code step by step.
    /// Numbers: mapgen.json "plots".
    /// </summary>
    public sealed class Plots
    {
        public readonly List<Street> Streets = new List<Street>();    // web G.streets
        public readonly List<AirField> AirCorr = new List<AirField>(); // web G.airCorr: each airbase's runway frame

        readonly Battle _sim;
        readonly Terrain _t;
        readonly JObj P;
        readonly List<Plot> _allPlots = new List<Plot>();
        readonly List<int> _touched = new List<int>();       // cells to recheck after levelling, in order
        readonly HashSet<int> _touchedSet = new HashSet<int>();
        readonly Dictionary<string, double> _walkCache = new Dictionary<string, double>();
        readonly double _turn, _quarter, _far, _worst;

        static bool IsPortType(string t) => t == "hq" || t == "fortress" || t == "town";

        public Plots(Battle sim)
        {
            _sim = sim;
            _t = sim.Terrain;
            P = sim.Data.Mapgen.Obj("plots");
            _turn = P.Num("turn");
            _quarter = P.Num("quarterTurn");
            _far = P.Num("far");
            _worst = P.Num("worst");
        }

        static double AngD(double a, double b) => Math.Abs(DMath.Atan2(DMath.Sin(a - b), DMath.Cos(a - b)));

        public void Run()
        {
            foreach (var c in _t.Coves) _sim.Zones[c.Zone].Cove = c;
            Airbases();
            Repass();
            foreach (var z in _sim.Zones) PlotsFor(z, _sim.Tables.ZTypes[z.Type]);
            // level the ground under every plot (a flat yard a little wider than the plate)
            double probe = P.Num("plotLevelProbe"), R = P.Num("plotLevelR"), inner = P.Num("plotLevelInner");
            foreach (var p in _allPlots)
            {
                double sm = 0;
                int c = 0;
                for (double b = 0; b < _turn; b += P.Num("plotLevelStep"))
                {
                    sm += _t.HeightAt(p.X + DMath.Cos(b) * probe, p.Z + DMath.Sin(b) * probe);
                    c++;
                }
                double Hh = Math.Max(P.Num("plotMinH"), sm / c);
                double px = p.X, pz = p.Z;
                Level(px - R, pz - R, px + R, pz + R, (x, zz) =>
                {
                    double d = DMath.Hypot(x - px, zz - pz);
                    return d > R ? 0.0 : 1.0 - Maps.Smooth(inner, R, d);
                }, Hh);
            }
            Repass();
            foreach (var p in _allPlots) p.Y = _t.HeightAt(p.X, p.Z);
        }

        // ---------- ground levelling (web level / repass) ----------

        /// <summary>Blend heights toward Hh with weight w(x, z) in a box, and remember which cells to recheck.</summary>
        void Level(double x0, double z0, double x1, double z1, Func<double, double, double> w, double Hh)
        {
            double cell = _t.Cell;
            int j1 = Math.Min(_t.GH, (int)Math.Ceiling((z1 - _t.Z0) / cell));
            int i1 = Math.Min(_t.GW, (int)Math.Ceiling((x1 - _t.X0) / cell));
            for (int j = Math.Max(0, (int)Math.Floor((z0 - _t.Z0) / cell)); j <= j1; j++)
                for (int i = Math.Max(0, (int)Math.Floor((x0 - _t.X0) / cell)); i <= i1; i++)
                {
                    double wt = w(_t.X0 + i * cell, _t.Z0 + j * cell);
                    if (wt <= 0.0) continue;
                    int k = j * _t.VW + i;
                    _t.Hv[k] = (float)(_t.Hv[k] * (1.0 - wt) + Hh * wt);
                    Touch(j * _t.GW + i);
                    Touch(j * _t.GW + i - 1);
                    Touch((j - 1) * _t.GW + i);
                    Touch((j - 1) * _t.GW + i - 1);
                }
        }

        void Touch(int k)
        {
            if (_touchedSet.Add(k)) _touched.Add(k);
        }

        bool NearProp(double x, double z)
        {
            double pad = P.Num("propPad");
            foreach (var q in _t.Props)
                foreach (var c in q.Circles)
                    if (DMath.Hypot(c.X - x, c.Z - z) <= c.R + pad) return true;
            return false;
        }

        void Repass()
        {
            var T = _sim.Data.Mapgen.Obj("terrain");
            double minH = T.Num("passMinH"), maxAvg = T.Num("passMaxAvg"), maxSlope = T.Num("passMaxSlope");
            int GW = _t.GW, VW = _t.VW;
            var hv = _t.Hv;
            foreach (int k in _touched)
            {
                if (k < 0 || k >= GW * _t.GH) continue;
                int i = k % GW, j = (k - i) / GW;
                double a = hv[j * VW + i], b = hv[j * VW + i + 1], c = hv[(j + 1) * VW + i], d = hv[(j + 1) * VW + i + 1];
                double mx = Math.Max(Math.Max(a, b), Math.Max(c, d)), mn = Math.Min(Math.Min(a, b), Math.Min(c, d));
                double av = (a + b + c + d) / 4.0;
                bool ok = mn > minH && av < maxAvg && mx - mn < maxSlope;
                if (!ok) _t.LandGrid[k] = 0;
                else if (_t.LandGrid[k] == 0 && !NearProp(_t.X0 + (i + 0.5) * _t.Cell, _t.Z0 + (j + 0.5) * _t.Cell)) _t.LandGrid[k] = 1;
                if (_sim.WallCell != null && _sim.WallCell[k] != 0) _t.LandGrid[k] = 0;   // wall cells stay blocked
                _sim.SyncCell(k);
            }
            _touched.Clear();
            _touchedSet.Clear();
        }

        // ---------- airbases: runway, taxiway, apron (web "airbases, laid out like an airport diagram") ----------

        bool InCorr(double x, double z, double pad)
        {
            foreach (var A in AirCorr)
            {
                double s = (x - A.Cx) * A.Ux + (z - A.Cz) * A.Uz;
                double q = (x - A.Cx) * A.Nx + (z - A.Cz) * A.Nz;
                if (Math.Abs(s) <= A.L / 2.0 + P.Num("corrEnd") + pad && q >= P.Num("corrQ0") - pad && q <= P.Num("corrQ1") + pad) return true;
            }
            return false;
        }

        void Airbases()
        {
            var AB = _sim.Tables.ZTypes["airbase"];
            double off = P.Num("runwayOffset");
            var probeQ = P.Nums("runwayProbeQ");
            int dirs = P.Int("runwayDirs");
            foreach (var z in _sim.Zones)
            {
                if (z.Type != "airbase") continue;
                double L = AB.Runway;
                double half = L / 2.0 + P.Num("runwayEndPad");
                double toC = DMath.Atan2(-z.Z, -z.X);
                double best = toC, bs = _far;
                for (int k = 0; k < dirs; k++)
                {
                    double a = (double)k / P.Num("runwayDirs") * _turn;
                    double ux = DMath.Cos(a), uz = DMath.Sin(a), nx = -uz, nz = ux;
                    double cx = z.X - nx * off, cz = z.Z - nz * off;
                    double sc = AngD(a, toC) * P.Num("runwayAngleWeight");
                    for (double tt = -half; tt <= half; tt += P.Num("runwayProbeStep"))
                        foreach (double q in probeQ)
                        {
                            double x = cx + ux * tt + nx * q, zz = cz + uz * tt + nz * q;
                            double e = P.Num("runwayEdge");
                            if (x < _t.X0 + e || x > _t.X0 + _t.W - e || zz < _t.Z0 + e || zz > _t.Z0 + _t.H - e)
                            {
                                sc += P.Num("runwayOffMapPenalty");
                                continue;
                            }
                            double h = _t.HeightAt(x, zz);
                            sc += Math.Abs(h - z.Y) * P.Num("runwayHeightWeight") + (h < P.Num("runwayLowH") ? P.Num("runwayLowPenalty") : 0.0)
                                + (_t.Passable(x, zz) ? 0.0 : P.Num("runwayBlockedPenalty"));
                            foreach (var o in _sim.Zones)
                                if (!ReferenceEquals(o, z) && DMath.Hypot(o.X - x, o.Z - zz) < o.R + P.Num("runwayZoneClear")) sc += P.Num("runwayZonePenalty");
                        }
                    if (sc < bs) { bs = sc; best = a; }
                }
                {
                    double ang = best;
                    double ux = DMath.Cos(ang), uz = DMath.Sin(ang), nx = -uz, nz = ux;
                    double cx = z.X - nx * off, cz = z.Z - nz * off;
                    var terms = new List<Terminal>();
                    int nt = (int)AB.Terminals;
                    for (int k = 0; k < nt; k++)
                    {
                        double o = (k - (nt - 1) / 2.0) * P.Num("terminalSpacing");
                        terms.Add(new Terminal { X = cx + nx * P.Num("terminalQ") + ux * o, Z = cz + nz * P.Num("terminalQ") + uz * o });
                    }
                    z.Air = new AirField
                    {
                        Ang = ang, Ux = ux, Uz = uz, Nx = nx, Nz = nz, L = L, Cx = cx, Cz = cz,
                        A = new Point { X = cx - ux * L / 2.0, Z = cz - uz * L / 2.0 }, B = new Point { X = cx + ux * L / 2.0, Z = cz + uz * L / 2.0 },
                        Tx = cx + nx * P.Num("taxiQ"), Tz = cz + nz * P.Num("taxiQ"), Terms = terms,
                    };
                    AirCorr.Add(z.Air);
                    // level the strip (full inside, easing out past the perimeter)
                    double ext = half + P.Num("runwayLevelExt"), box = P.Num("runwayLevelBox");
                    double q0 = P.Num("corrQ0"), q1 = P.Num("corrQ1"), endp = P.Num("runwayLevelEndPad");
                    double q0p = P.Num("runwayLevelQ0Pad"), q1p = P.Num("runwayLevelQ1Pad"), fade = P.Num("runwayLevelFade");
                    Level(cx - ext - box, cz - ext - box, cx + ext + box, cz + ext + box, (x, zz) =>
                    {
                        double s = Math.Abs((x - cx) * ux + (zz - cz) * uz);
                        double q = (x - cx) * nx + (zz - cz) * nz;
                        double ds = Math.Max(0.0, s - half - endp);
                        double dq = Math.Max(Math.Max(0.0, q0 - q0p - q), q - q1 - q1p);
                        double d = DMath.Hypot(ds, dq);
                        return d >= fade ? 0.0 : 1.0 - Maps.Smooth(0.0, fade, d);
                    }, z.Y);
                }
            }
        }

        // ---------- streets (web walkStreet, streetQuality, addStreet, lineStreet) ----------

        double StreetDist(Street s, double x, double z)
        {
            double d = _far;
            var pts = s.Pts;
            for (int i = 1; i < pts.Count; i++) d = Math.Min(d, Maps.SegDist(x, z, pts[i - 1][0], pts[i - 1][1], pts[i][0], pts[i][1]));
            return d;
        }

        bool PadFits(double x, double z, Zone zone)
        {
            if (!_t.Passable(x, z) || _t.HeightAt(x, z) < P.Num("padMinH")) return false;
            double lo = _far, hi = _worst, pr = P.Num("padProbeR");
            for (double b = 0; b < _turn; b += P.Num("padStep"))
            {
                double px = x + DMath.Cos(b) * pr, pz = z + DMath.Sin(b) * pr;
                if (!_t.Passable(px, pz)) return false;
                double h = _t.HeightAt(px, pz);
                if (h < lo) lo = h;
                if (h > hi) hi = h;
            }
            if (hi - lo > P.Num("padMaxRise")) return false;
            double spacing = P.Num("padSpacing");
            foreach (var p in _allPlots)
                if (Math.Abs(p.X - x) < spacing && DMath.Hypot(p.X - x, p.Z - z) < spacing) return false;
            foreach (var o in _sim.Zones)
                if (DMath.Hypot(o.X - x, o.Z - z) < o.R + (ReferenceEquals(o, zone) ? P.Num("padOwnZoneClear") : P.Num("padZoneClear"))) return false;
            foreach (var s in Streets)
                if (StreetDist(s, x, z) < s.W / 2.0 + P.Num("padStreetClear")) return false;
            return !InCorr(x, z, P.Num("padCorrClear"));
        }

        /// <summary>Walks a street outward: each step picks the bend that keeps it level and on dry, open ground.
        /// score (may be null) adds to the cost of a step.</summary>
        List<double[]> WalkStreet(Zone zone, double x, double z, double a, double length, Func<double, double, double, double> score)
        {
            var pts = new List<double[]> { new[] { x, z } };
            double L = 0.0, step = P.Num("streetStep");
            var bends = P.Nums("streetBends");
            while (L < length)
            {
                bool found = false;
                double bna = 0, bnx = 0, bnz = 0, bs = _far;
                double h0 = _t.HeightAt(x, z);
                foreach (double da in bends)
                {
                    double na = a + da;
                    double nx = x + DMath.Cos(na) * step, nz = z + DMath.Sin(na) * step;
                    if (!_t.Passable(nx, nz)) continue;
                    double h = _t.HeightAt(nx, nz);
                    if (h < P.Num("streetMinH")) continue;
                    bool clash = false;
                    foreach (var o in _sim.Zones)
                        if (!ReferenceEquals(o, zone) && DMath.Hypot(o.X - nx, o.Z - nz) < o.R + P.Num("streetZoneClear")) { clash = true; break; }
                    if (clash) continue;
                    if (DMath.Hypot(nx - zone.X, nz - zone.Z) < zone.R + P.Num("streetOwnZoneClear") || InCorr(nx, nz, P.Num("streetCorrClear"))) continue;
                    double sc = Math.Abs(h - h0) * P.Num("streetRiseWeight") + Math.Abs(da) * P.Num("streetBendWeight") + (score != null ? score(nx, nz, na) : 0.0);
                    foreach (double sd in new[] { _quarter, -_quarter })
                        if (!_t.Passable(nx + DMath.Cos(na + sd) * P.Num("streetSideProbe"), nz + DMath.Sin(na + sd) * P.Num("streetSideProbe")))
                            sc += P.Num("streetSidePenalty");
                    if (sc < bs) { bs = sc; found = true; bna = na; bnx = nx; bnz = nz; }
                }
                if (!found) break;
                a = bna;
                x = bnx;
                z = bnz;
                pts.Add(new[] { x, z });
                L += step;
            }
            return pts;
        }

        double StreetQuality(Zone zone, double a, double length)
        {
            string key = zone.Id + ":" + (long)DMath.RoundJs(a * P.Num("qualityAngleKey")) + ":" + DMath.Bits(length);
            if (_walkCache.TryGetValue(key, out double cached)) return cached;
            double o = zone.R + P.Num("streetStartOut");
            var p = WalkStreet(zone, zone.X + DMath.Cos(a) * o, zone.Z + DMath.Sin(a) * o, a, length, null);
            int open = 0;
            foreach (var xz in p)
                foreach (double sd in new[] { _quarter, -_quarter })
                    if (_t.Passable(xz[0] + DMath.Cos(a + sd) * P.Num("qualitySideProbe"), xz[1] + DMath.Sin(a + sd) * P.Num("qualitySideProbe"))) open++;
            double q = (p.Count - 1) * P.Num("streetStep") / length + (double)open / (2 * Math.Max(1, p.Count)) * P.Num("qualityOpenWeight");
            _walkCache[key] = q;
            return q;
        }

        Street AddStreet(Zone zone, double a, double length, double w, Func<double, double, double, double> score, double[] from)
        {
            double o = zone.R + P.Num("streetStartOut");
            double sx = from != null ? from[0] : zone.X + DMath.Cos(a) * o;
            double sz = from != null ? from[1] : zone.Z + DMath.Sin(a) * o;
            var pts = WalkStreet(zone, sx, sz, a, length, score);
            if (pts.Count < P.Num("streetMinPts")) return null;
            if (from == null)   // run in through the gate
                pts.Insert(0, new[] { zone.X + DMath.Cos(a) * zone.R * P.Num("streetGateIn"), zone.Z + DMath.Sin(a) * zone.R * P.Num("streetGateIn") });
            var s = new Street { Zone = zone.Id, Pts = pts, W = w };
            Streets.Add(s);
            return s;
        }

        sealed class Spot
        {
            public double X, Z, Ang;
            public string Tag;
        }

        /// <summary>Plot spots either side of a street, every lineEvery metres (sides: +1 left, -1 right). Like the web
        /// `o.start||3`, a start of 0 means the default.</summary>
        void LineStreet(Street s, List<Spot> o, double start = 0, string tag = "street", double[] sides = null)
        {
            double acc = start != 0.0 ? start : P.Num("lineStart");
            double every = P.Num("lineEvery"), off = P.Num("lineOffset");
            sides = sides ?? new[] { 1.0, -1.0 };
            var pts = s.Pts;
            for (int i = 1; i < pts.Count; i++)
            {
                double x0 = pts[i - 1][0], z0 = pts[i - 1][1], x1 = pts[i][0], z1 = pts[i][1];
                acc += DMath.Hypot(x1 - x0, z1 - z0);
                if (acc < every) continue;
                acc = 0.0;
                double dir = DMath.Atan2(z1 - z0, x1 - x0);
                foreach (double sd in sides)
                {
                    double na = dir + sd * _quarter;
                    o.Add(new Spot { X = x1 + DMath.Cos(na) * off, Z = z1 + DMath.Sin(na) * off, Ang = na, Tag = tag });
                }
            }
        }

        void RingSpots(Zone zone, List<Spot> o, IEnumerable<double> radii, int n, string tag, Func<double, bool> skip = null)
        {
            foreach (double rr in radii)
                for (int k = 0; k < n; k++)
                {
                    double a = zone.Gate + (k + 0.5) / n * _turn + rr % 2.0 * P.Num("ringOddShift");
                    if (skip != null && skip(a)) continue;
                    o.Add(new Spot { X = zone.X + DMath.Cos(a) * rr, Z = zone.Z + DMath.Sin(a) * rr, Ang = a, Tag = tag });
                }
        }

        /// <summary>Best rotation for a set of gate directions, judged by how far and how openly streets can run.</summary>
        double PickGate(Zone zone, double[] offs, double length, Func<double, double> bias)
        {
            double best = 0.0, bs = _worst;
            int dirs = P.Int("gateDirs");
            for (int k = 0; k < dirs; k++)
            {
                double g = (double)k / P.Num("gateDirs") * _turn;
                double q = 0.0;
                for (int i = 0; i < offs.Length; i++) q += StreetQuality(zone, g + offs[i], length) * (i == 0 ? P.Num("gateFirstWeight") : 1.0);
                if (bias != null) q += bias(g);
                if (q > bs) { bs = q; best = g; }
            }
            return best;
        }

        double? WaterDir(Zone zone)
        {
            double? best = null;
            double bd = _far;
            int dirs = P.Int("waterDirs");
            for (int k = 0; k < dirs; k++)
            {
                double a = (double)k / P.Num("waterDirs") * _turn;
                for (double d = zone.R + P.Num("waterFrom"); d < zone.R + P.Num("waterTo"); d += P.Num("waterStep"))
                    if (_t.Passable(zone.X + DMath.Cos(a) * d, zone.Z + DMath.Sin(a) * d, _t.WaterGrid))
                    {
                        if (d < bd) { bd = d; best = a; }
                        break;
                    }
            }
            return best;
        }

        /// <summary>A quay down each side of the base's cove, running out toward the sea at a steady height.</summary>
        void CoveQuays(Zone z, List<Spot> o, double length)
        {
            var c = z.Cove;
            double px = -c.Uz, pz = c.Ux;
            foreach (double sd in new[] { 1.0, -1.0 })
            {
                double sx = 0, sz = 0;
                bool ok = false;
                foreach (double off in P.Nums("quayOffsets"))
                {
                    sx = c.Ax + px * sd * (c.R + off) - c.Ux * P.Num("quayBack");
                    sz = c.Az + pz * sd * (c.R + off) - c.Uz * P.Num("quayBack");
                    if (_t.Passable(sx, sz) && !InCorr(sx, sz, P.Num("streetCorrClear"))) { ok = true; break; }
                }
                if (!ok) continue;
                foreach (double dir in new[] { 1.0, -1.0 })
                {
                    double qh = P.Num("quayHeight"), qw = P.Num("quayHeightWeight");
                    var q = AddStreet(z, DMath.Atan2(c.Uz * dir, c.Ux * dir), dir > 0.0 ? length : length * P.Num("quayInlandK"), P.Num("quayWidth"),
                        (x, zz, na) => Math.Abs(_t.HeightAt(x, zz) - qh) * qw, new[] { sx, sz });
                    if (q != null)
                    {
                        q.Quay = true;
                        LineStreet(q, o, P.Num("quayStart"), "quay", new[] { sd * dir });
                    }
                }
            }
        }

        static IEnumerable<double> Around(double r, double[] add)
        {
            foreach (double a in add) yield return r + a;
        }

        List<Spot> Layout(Zone z)
        {
            var o = new List<Spot>();
            string T = z.Type;
            double? wa = null;
            if (z.Coastal && IsPortType(T)) wa = z.Cove != null ? DMath.Atan2(z.Cove.Uz, z.Cove.Ux) : WaterDir(z);
            z.Gate = 0.0;
            if (T == "airbase")
            {
                var A = z.Air;
                z.Gate = DMath.Atan2(A.Nz, A.Nx);
                double q1 = P.Num("corrQ1"), q0 = P.Num("corrQ0");
                foreach (double off in P.Nums("apronOffsets"))
                    o.Add(new Spot { X = A.Cx + A.Nx * (q1 + P.Num("apronQOut")) + A.Ux * off, Z = A.Cz + A.Nz * (q1 + P.Num("apronQOut")) + A.Uz * off, Ang = z.Gate, Tag = "apron" });
                foreach (double e in new[] { 1.0, -1.0 })
                    foreach (double q in P.Nums("endQ"))
                        o.Add(new Spot
                        {
                            X = A.Cx + A.Ux * e * (A.L / 2.0 + P.Num("endOut")) + A.Nx * q, Z = A.Cz + A.Uz * e * (A.L / 2.0 + P.Num("endOut")) + A.Nz * q,
                            Ang = DMath.Atan2(A.Uz * e, A.Ux * e), Tag = "end",
                        });
                foreach (double off in P.Nums("farOffsets"))
                    o.Add(new Spot { X = A.Cx + A.Nx * (q0 - P.Num("farQIn")) + A.Ux * off, Z = A.Cz + A.Nz * (q0 - P.Num("farQIn")) + A.Uz * off, Ang = z.Gate + Math.PI, Tag = "far" });
                var s = AddStreet(z, z.Gate, P.Num("airStreetLen"), P.Num("airStreetW"), null,
                    new[] { A.Cx + A.Nx * (q1 + P.Num("airStreetQ")), A.Cz + A.Nz * (q1 + P.Num("airStreetQ")) });
                if (s != null)
                {
                    s.Pts.Insert(0, new[] { A.Cx + A.Nx * P.Num("airStreetHeadQ"), A.Cz + A.Nz * P.Num("airStreetHeadQ") });
                    LineStreet(s, o, P.Num("airLineStart"));
                }
            }
            else if (T == "fortress")
            {
                double fb = P.Num("fortGateBias");
                double wv = wa ?? 0.0;
                z.Gate = PickGate(z, new[] { 0.0 }, P.Num("fortGateLen"), wa != null ? g => -AngD(g, wv) * fb : (Func<double, double>)null);
                var s = AddStreet(z, z.Gate, P.Num("fortStreetLen"), P.Num("fortStreetW"), null, null);
                if (s != null) LineStreet(s, o, P.Num("fortLineStart"));
                if (z.Cove != null) CoveQuays(z, o, P.Num("fortQuayLen"));
                else if (wa != null)
                {
                    double w = wa.Value;
                    var q = AddStreet(z, w + P.Num("fortWaterTurn"), P.Num("fortQuayLen"), P.Num("fortStreetW"), null,
                        new[] { z.X + DMath.Cos(w) * (z.R + P.Num("fortWaterOut")), z.Z + DMath.Sin(w) * (z.R + P.Num("fortWaterOut")) });
                    if (q != null) LineStreet(q, o, 0, "quay");
                }
                double gclear = P.Num("fortRingGateClear"), gate = z.Gate;
                RingSpots(z, o, Around(z.R, P.Nums("fortRings")), P.Int("fortRingN"), "ring", a => AngD(a, gate) < gclear);
            }
            else
            {
                bool hq = T == "hq";
                var offs = hq ? P.Nums("hqOffsets") : P.Nums("townOffsets");
                double length = hq ? P.Num("hqLen") : P.Num("townLen");
                double wb = P.Num("gateWaterBias");
                double wv = wa ?? 0.0;
                z.Gate = PickGate(z, offs, length, wa != null ? g => -AngD(g, wv + Math.PI) * wb : (Func<double, double>)null);
                var ranked = new List<double>();
                foreach (double off in offs) ranked.Add(z.Gate + off);
                ranked = Maps.SortStable(ranked, (a, b) => StreetQuality(z, b, length) - StreetQuality(z, a, length));
                double quayLen = hq ? P.Num("hqQuayLen") : P.Num("townQuayLen");
                if (z.Cove != null) CoveQuays(z, o, quayLen);
                else if (wa != null)
                {
                    double w = wa.Value;
                    double sx = z.X + DMath.Cos(w) * (z.R + P.Num("shoreOut")), sz = z.Z + DMath.Sin(w) * (z.R + P.Num("shoreOut"));
                    double sh = P.Num("shoreHeight"), qw = P.Num("quayHeightWeight");
                    foreach (double sd in new[] { _quarter, -_quarter })
                    {
                        var q = AddStreet(z, w + sd, quayLen, P.Num("quayWidth"), (x, zz, na) => Math.Abs(_t.HeightAt(x, zz) - sh) * qw, new[] { sx, sz });
                        if (q != null) LineStreet(q, o, P.Num("shoreLineStart"), "quay");
                    }
                }
                for (int i = 0; i < ranked.Count; i++)
                {
                    var s = AddStreet(z, ranked[i], i == 0 ? length : length * P.Num("sideStreetK"), i == 0 ? P.Num("mainStreetW") : P.Num("sideStreetW"), null, null);
                    if (s != null) LineStreet(s, o, i == 0 ? P.Num("mainLineStart") : P.Num("sideLineStart"));
                }
                RingSpots(z, o, Around(z.R, P.Nums("townRings")), hq ? P.Int("hqRingN") : P.Int("townRingN"), "ring");
            }
            RingSpots(z, o, Around(z.R, P.Nums("fallbackRings")), P.Int("fallbackRingN"), "fallback");
            return o;
        }

        // ---------- a walled Town outgrows its walls (web createGame, before the walls are laid) ----------

        /// <summary>Workshops lean on the outside of each Town's barrier and houses, sheds, tank stands and container
        /// yards spread beyond it. They are map props: troops walk round them. Placed from a per-town seed (not the
        /// battle's random numbers), so every player's game gets the same ones. Numbers: mapgen.json "townGrowth".</summary>
        public void TownGrowth()
        {
            var TG = _sim.Data.Mapgen.Obj("townGrowth");
            var W = _sim.Balance.Obj("walls").Obj("town");
            double turn = TG.Num("turn"), radK = TG.Num("radK"), probe = TG.Num("probeStep");
            foreach (var z in _sim.Zones)
            {
                if (z.Type != "town") continue;
                uint sd = unchecked((uint)(z.Id + 1) * 2654435761u + 977u);   // the web game's per-town generator
                double Rn() { unchecked { sd = sd * 1664525u + 1013904223u; } return sd / 4294967296.0; }
                var mine = new List<Prop>();
                double R0 = W.Num("ap") + W.Num("thick") + TG.Num("outPad"), zy = _t.HeightAt(z.X, z.Z);
                bool Put(double ang, double rr, double w, double d, double h, string kind)
                {
                    double x = z.X + DMath.Cos(ang) * rr, zz = z.Z + DMath.Sin(ang) * rr, rad = DMath.Hypot(w, d) / 2 * radK;
                    if (AngD(ang, z.Gate) < TG.Num("gateClear") || !_t.Passable(x, zz)) return false;
                    double hh = _t.HeightAt(x, zz);
                    if (hh < TG.Num("minH") || Math.Abs(hh - zy) > TG.Num("maxRise")) return false;
                    for (double b = 0; b < turn; b += probe)
                        if (!_t.Passable(x + DMath.Cos(b) * rad, zz + DMath.Sin(b) * rad)) return false;
                    foreach (var p in _allPlots) if (DMath.Hypot(p.X - x, p.Z - zz) < rad + TG.Num("plotClear")) return false;
                    foreach (var st in Streets) if (StreetDist(st, x, zz) < st.W / 2 + rad + TG.Num("streetClear")) return false;
                    if (InCorr(x, zz, rad + TG.Num("corrClear"))) return false;
                    foreach (var o in _sim.Zones) if (o != z && DMath.Hypot(o.X - x, o.Z - zz) < o.R + rad + TG.Num("zoneClear")) return false;
                    foreach (var q in _t.Props)
                        foreach (var c in q.Circles) if (DMath.Hypot(c.X - x, c.Z - zz) < c.R + rad + TG.Num("propClear")) return false;
                    var prop = new Prop { Type = kind, X = x, Z = zz, Rot = ang, V = Rn(), H = hh, W = w, D = d, Ht = h, Town = z.Id };
                    prop.Circles.Add(new Circle { X = x, Z = zz, R = rad });
                    double pad = TG.Num("cellPad"), cr = TG.Num("cellR");
                    int j1 = (int)Math.Floor((zz + rad + pad - _t.Z0) / _t.Cell), i1 = (int)Math.Floor((x + rad + pad - _t.X0) / _t.Cell);
                    for (int j = (int)Math.Floor((zz - rad - pad - _t.Z0) / _t.Cell); j <= j1; j++)
                        for (int i = (int)Math.Floor((x - rad - pad - _t.X0) / _t.Cell); i <= i1; i++)
                        {
                            if (i < 0 || j < 0 || i >= _t.GW || j >= _t.GH) continue;
                            if (DMath.Hypot(_t.X0 + (i + 0.5) * _t.Cell - x, _t.Z0 + (j + 0.5) * _t.Cell - zz) <= rad + cr) _t.LandGrid[j * _t.GW + i] = 0;
                        }
                    _t.Props.Add(prop);
                    mine.Add(prop);
                    return true;
                }
                double[] leanD = TG.Nums("leanD"), leanW = TG.Nums("leanW"), leanH = TG.Nums("leanH");
                int n = W.Int("n");
                foreach (double f in TG.Nums("leanFaces"))
                {   // lean-tos on the barrier (arguments drawn in the web game's order)
                    double d = leanD[0] + Rn() * leanD[1];
                    double ang = z.Gate + f / n * turn + (Rn() - 0.5) * TG.Num("leanJitter");
                    double w = leanW[0] + Rn() * leanW[1];
                    double h = leanH[0] + Rn() * leanH[1];
                    Put(ang, R0 + d / 2 - TG.Num("leanIn"), w, d, h, "leanto");
                }
                var B = TG.Obj("block");
                var L = TG.Obj("leanto");
                var Tk = TG.Obj("tanks");
                var Y = TG.Obj("yard");
                for (int k = 0; k < TG.Int("tries") && mine.Count < TG.Int("max"); k++)
                {
                    double ang = z.Gate + (Rn() < TG.Num("sideChance")
                        ? (Rn() < TG.Num("sideSplit") ? 1 : -1) * (TG.Num("sideMin") + Rn() * TG.Num("sideSpread"))
                        : Rn() * turn);
                    double rr = R0 + TG.Num("ringOut") + DMath.Pow(Rn(), TG.Num("ringPow")) * TG.Num("ringSpread");
                    double t = Rn();
                    if (t < TG.Num("blockChance"))
                    {
                        double w = B.Nums("w")[0] + Rn() * B.Nums("w")[1], d = B.Nums("d")[0] + Rn() * B.Nums("d")[1];
                        double h = B.Nums("h")[0] + Math.Floor(Rn() * 2) * B.Nums("h")[1];
                        Put(ang, rr, w, d, h, "block");
                    }
                    else if (t < TG.Num("leanChance"))
                    {
                        double w = L.Nums("w")[0] + Rn() * L.Nums("w")[1], d = L.Nums("d")[0] + Rn() * L.Nums("d")[1], h = L.Nums("h")[0] + Rn() * L.Nums("h")[1];
                        Put(ang, rr, w, d, h, "leanto");
                    }
                    else if (t < TG.Num("tanksChance")) Put(ang, rr, Tk.Num("w"), Tk.Num("d"), Tk.Num("h"), "tanks");
                    else Put(ang, rr, Y.Num("w"), Y.Num("d"), Y.Num("h"), "yard");
                }
            }
        }

        // ---------- plots per base and their kinds ----------

        void PlotsFor(Zone z, ZoneType ZT)
        {
            var want = ZT.Slots.Copy();
            if (z.Coastal && z.Type == "fortress") want.Fort += _sim.Balance.Obj("port").Int("fortressFortSlots"); // Port Fortress: coastal defences
            int n = want.Total;
            var plots = new List<Plot>();
            z.Budget = n;
            double reach = z.Coastal ? _sim.Balance.Obj("mapMix").Num("portFallbackReach") + P.Num("waterNearPad") : P.Num("waterNearInland");
            foreach (var c in Layout(z))
            {
                if (plots.Count >= n) break;
                if (!PadFits(c.X, c.Z, z)) continue;
                var pl = new Plot { I = plots.Count, X = c.X, Z = c.Z, Ang = c.Ang, Tag = c.Tag };
                int wc = _sim.Pathing.NearestPassCell(_t.CellOf(c.X, c.Z), _t.WaterGrid);
                if (wc >= 0)
                {
                    var w = _sim.Pathing.CellCenter(wc);
                    if (DMath.Hypot(w[0] - c.X, w[1] - c.Z) < reach) pl.Water = new Point { X = w[0], Z = w[1] };
                }
                plots.Add(pl);
                _allPlots.Add(pl);
            }
            // plot kinds: defences on the outskirts, economy nearest the centre, military the rest
            int have = plots.Count;
            var kinds = new List<string> { "fort", "mil", "eco" };
            int Want(string k) => k == "fort" ? want.Fort : k == "mil" ? want.Mil : want.Eco;
            var share = new Dictionary<string, int>();
            int left = have;
            foreach (var k in kinds)
            {
                share[k] = (int)Math.Floor(Want(k) * have / (double)n);
                left -= share[k];
            }
            var order = Maps.SortStable(kinds, (a, b) => (Want(b) * have / (double)n - share[b]) - (Want(a) * have / (double)n - share[a]));
            foreach (var k in order)
                if (left > 0) { share[k]++; left--; }
            var free = new List<Plot>(plots);
            double Dc(Plot p) => DMath.Hypot(p.X - z.X, p.Z - z.Z);
            z.Port = IsPortType(z.Type) && z.Coastal && plots.Exists(p => p.Water != null);
            if (z.Port && share["mil"] > 0)
            {
                var wet = Maps.SortStable(free.FindAll(p => p.Water != null),
                    (a, b) => DMath.Hypot(a.Water.X - a.X, a.Water.Z - a.Z) - DMath.Hypot(b.Water.X - b.X, b.Water.Z - b.Z));
                var w = wet[0];
                w.Kind = "mil";
                free.Remove(w);
                share["mil"]--;
            }
            double maxD = 1.0;
            foreach (var p in free) maxD = Math.Max(maxD, Dc(p));
            var chosen = new List<Plot>();
            for (int k = 0; k < share["fort"]; k++)
            {
                Plot best = null;
                double bs = _worst;
                foreach (var p in free)
                {
                    double a = DMath.Atan2(p.Z - z.Z, p.X - z.X);
                    double sep = _turn;
                    foreach (var q in chosen) sep = Math.Min(sep, AngD(a, DMath.Atan2(q.Z - z.Z, q.X - z.X)));
                    double s = Dc(p) / maxD * P.Num("fortFarWeight") + (chosen.Count > 0 ? sep : 0.0)
                        + (p.Tag == "end" || p.Tag == "ring" ? P.Num("fortEdgeBonus") : 0.0);
                    if (s > bs) { bs = s; best = p; }
                }
                if (best == null) break;
                best.Kind = "fort";
                chosen.Add(best);
                free.Remove(best);
            }
            free = Maps.SortStable(free, (a, b) => Dc(a) - Dc(b));
            int k2 = 0;
            while (k2 < share["eco"] && free.Count > 0)
            {
                free[0].Kind = "eco";
                free.RemoveAt(0);
                k2++;
            }
            foreach (var p in free) p.Kind = "mil";
            z.Slots = new ZoneSlots();
            foreach (var pl in plots)
            {
                if (pl.Kind == "mil") z.Slots.Mil++;
                else if (pl.Kind == "eco") z.Slots.Eco++;
                else z.Slots.Fort++;
            }
            z.Spots = plots;   // buildings are placed freely now; these laid-out spots are suggestions (and the AI's choices)
            z.Plots = new List<Plot>();
        }
    }
}
